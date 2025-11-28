from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import (
    UUIDPrimaryKeyMixin, TimestampMixin , UserTrackingMixin
)
from oxutils.enums import InvoiceStatusEnum




class InvoiceMixin(UUIDPrimaryKeyMixin,TimestampMixin, UserTrackingMixin):
    """Model for invoices and billing"""
    
    # Invoice details
    invoice_number = models.CharField(
        _('numéro de facture'),
        max_length=50,
        unique=True,
        help_text=_('Numéro unique de la facture')
    )
    
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=[(status.value, status.value) for status in InvoiceStatusEnum],
        default=InvoiceStatusEnum.DRAFT,
        help_text=_('Statut de la facture')
    )
    
    # Amounts
    subtotal = models.DecimalField(
        _('sous-total'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Montant hors taxes')
    )
    
    tax_rate = models.DecimalField(
        _('taux de taxe'),
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text=_('Taux de taxe en pourcentage')
    )
    
    tax_amount = models.DecimalField(
        _('montant de la taxe'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_('Montant de la taxe')
    )
    
    total = models.DecimalField(
        _('total'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Montant total TTC')
    )
    
    currency = models.CharField(
        _('devise'),
        max_length=3,
        default='USD',
        help_text=_('Code devise ISO (CDF, USD, etc.)')
    )
    
    # Dates
    issue_date = models.DateField(
        _('date d\'émission'),
        help_text=_('Date d\'émission de la facture')
    )
    
    due_date = models.DateField(
        _('date d\'échéance'),
        help_text=_('Date limite de paiement')
    )
    
    paid_date = models.DateTimeField(
        _('date de paiement'),
        null=True,
        blank=True,
        help_text=_('Date et heure du paiement')
    )
    
    # Billing period
    period_start = models.DateField(
        _('début de période'),
        help_text=_('Date de début de la période facturée')
    )
    
    period_end = models.DateField(
        _('fin de période'),
        help_text=_('Date de fin de la période facturée')
    )
    
    # Additional info
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description détaillée de la facture')
    )
    
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Notes internes sur la facture')
    )
    
    # External payment system reference
    payment_reference = models.CharField(
        _('référence de paiement'),
        max_length=100,
        blank=True,
        help_text=_('Référence du système de paiement externe (Stripe, etc.)')
    )
    
    class Meta:
        abstract = True
        verbose_name = _('Facture')
        verbose_name_plural = _('Factures')
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['due_date']),
            models.Index(fields=['invoice_number']),
        ]
    
    def __str__(self):
        return f"Facture {self.invoice_number}"
    
    def save(self, *args, **kwargs):
        if self._state.adding:
            self.tax_rate = 16

        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        self.calculate_amounts()
        
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total = self.subtotal + self.tax_amount
        
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from django.utils import timezone
        year = timezone.now().year
        month = timezone.now().month
        
        # Get last invoice number for this month
        last_invoice = self.__class__.objects.filter(
            invoice_number__startswith=f"INV-{year}{month:02d}"
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            # Extract sequence number and increment
            try:
                sequence = int(last_invoice.invoice_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                sequence = 1
        else:
            sequence = 1
        
        return f"INV-{year}{month:02d}-{sequence:04d}"
    
    def is_overdue(self):
        """Check if invoice is overdue"""
        from django.utils import timezone
        return (
            self.status == InvoiceStatusEnum.PENDING and
            timezone.now().date() > self.due_date
        )
    
    def mark_as_paid(self, payment_reference=None, paid_date=None):
        """Mark invoice as paid"""
        from django.utils import timezone
        self.status = InvoiceStatusEnum.PAID

        if paid_date:
            self.paid_date = paid_date
        else:
            self.paid_date = timezone.now()

        if payment_reference:
            self.payment_reference = payment_reference
        self.save()
    
    def mark_as_overdue(self):
        """Mark invoice as overdue"""
        self.status = InvoiceStatusEnum.OVERDUE
        self.save()
    
    def cancel(self, reason=""):
        """Cancel invoice"""

        if self.status == InvoiceStatusEnum.PAID:
            raise ValueError("Cannot cancel a paid invoice")

        self.status = InvoiceStatusEnum.CANCELLED

        if reason:
            self.notes = f"{invoice.notes}\nAnnulé: {reason}".strip()

        self.save()

    def refund(self, reason= ""):
        """Mark invoice as refunded"""

        if self.status != InvoiceStatusEnum.PAID:
            raise ValueError("Only paid invoices can be refunded")
        
        self.status = InvoiceStatusEnum.REFUNDED
        
        if reason:
            self.notes = f"{invoice.notes}\nRemboursé: {reason}".strip()

        self.save()
    
    def get_plan_name(self):
        """Get the plan name for this invoice"""
        raise NotImplementedError
    
    def is_trial_invoice(self):
        """Check if this invoice is for a trial period"""
        return False

    def calculate_amounts(self):
        raise NotImplementedError


class InvoiceItemMixin(UUIDPrimaryKeyMixin, TimestampMixin):
    """Model for individual items within a user invoice"""
    
    # Item details
    name = models.CharField(
        _('nom du service'),
        max_length=200,
        help_text=_('Nom du service ou produit facturé')
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description détaillée du service')
    )
    
    # Pricing
    quantity = models.DecimalField(
        _('quantité'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text=_('Quantité du service (heures, unités, etc.)')
    )
    
    unit_price = models.DecimalField(
        _('prix unitaire'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Prix unitaire hors taxes')
    )
    
    total_price = models.DecimalField(
        _('prix total'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Prix total pour cet élément (quantité × prix unitaire)')
    )
    
    # Metadata
    metadata = models.JSONField(
        _('métadonnées'),
        default=dict,
        blank=True,
        help_text=_('Données supplémentaires en format JSON')
    )
    
    class Meta:
        abstract = True
        verbose_name = _('Élément de facture')
        verbose_name_plural = _('Éléments de facture')
        ordering = ['id']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total price
        self.total_price = self.quantity * self.unit_price

        super().save(*args, **kwargs)
        self.invoice.update_totals()
    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.invoice.update_totals()


class RefundRequestMixin(UUIDPrimaryKeyMixin, TimestampMixin, UserTrackingMixin):
    """Abstract model for refund requests"""
    
    REFUND_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvé')),
        ('rejected', _('Rejeté')),
        ('processed', _('Traité')),
        ('cancelled', _('Annulé')),
    ]
    
    REFUND_REASON_CHOICES = [
        ('duplicate_payment', _('Paiement en double')),
        ('service_not_received', _('Service non reçu')),
        ('billing_error', _('Erreur de facturation')),
        ('cancellation', _('Annulation')),
        ('technical_issue', _('Problème technique')),
        ('other', _('Autre')),
    ]
    
    # Refund details
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=REFUND_STATUS_CHOICES,
        default='pending',
        help_text=_('Statut de la demande de remboursement')
    )
    
    reason = models.CharField(
        _('raison'),
        max_length=30,
        choices=REFUND_REASON_CHOICES,
        help_text=_('Raison de la demande de remboursement')
    )
    
    description = models.TextField(
        _('description'),
        help_text=_('Description détaillée de la demande de remboursement')
    )
    
    # Amount details
    requested_amount = models.DecimalField(
        _('montant demandé'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Montant du remboursement demandé')
    )
    
    approved_amount = models.DecimalField(
        _('montant approuvé'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Montant du remboursement approuvé')
    )
    
    currency = models.CharField(
        _('devise'),
        max_length=3,
        default='USD',
        help_text=_('Code devise ISO (CDF, USD, etc.)')
    )
    
    # Processing details
    processed_date = models.DateTimeField(
        _('date de traitement'),
        null=True,
        blank=True,
        help_text=_('Date et heure du traitement du remboursement')
    )
    
    admin_notes = models.TextField(
        _('notes administratives'),
        blank=True,
        help_text=_('Notes internes de l\'administrateur')
    )
    
    # External payment system reference
    refund_reference = models.CharField(
        _('référence de remboursement'),
        max_length=100,
        blank=True,
        help_text=_('Référence du système de paiement externe (Stripe, etc.)')
    )
    
    class Meta:
        abstract = True
        verbose_name = _('Demande de remboursement')
        verbose_name_plural = _('Demandes de remboursement')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['processed_date']),
        ]
    
    def __str__(self):
        return f"Remboursement {self.requested_amount} {self.currency} - {self.get_status_display()}"
    
    def approve(self, approved_amount=None, admin_notes=""):
        """Approve the refund request"""
        self.status = 'approved'
        self.approved_amount = approved_amount or self.requested_amount
        if admin_notes:
            self.admin_notes = f"{self.admin_notes}\n{admin_notes}".strip()
        self.save()
    
    def reject(self, admin_notes=""):
        """Reject the refund request"""
        self.status = 'rejected'
        if admin_notes:
            self.admin_notes = f"{self.admin_notes}\n{admin_notes}".strip()
        self.save()
    
    def process(self, refund_reference="", admin_notes=""):
        """Mark refund as processed"""
        from django.utils import timezone
        
        if self.status != 'approved':
            raise ValueError("Seules les demandes approuvées peuvent être traitées")
        
        self.status = 'processed'
        self.processed_date = timezone.now()
        self.refund_reference = refund_reference
        
        if admin_notes:
            self.admin_notes = f"{self.admin_notes}\n{admin_notes}".strip()
        
        self.save()
    
    def cancel(self, admin_notes=""):
        """Cancel the refund request"""
        if self.status == 'processed':
            raise ValueError("Impossible d'annuler une demande déjà traitée")
        
        self.status = 'cancelled'
        if admin_notes:
            self.admin_notes = f"{self.admin_notes}\n{admin_notes}".strip()
        self.save()
    
    def is_pending(self):
        """Check if refund request is pending"""
        return self.status == 'pending'
    
    def is_approved(self):
        """Check if refund request is approved"""
        return self.status == 'approved'
    
    def is_processed(self):
        """Check if refund request is processed"""
        return self.status == 'processed'
    
    def can_be_modified(self):
        """Check if refund request can still be modified"""
        return self.status in ['pending']
    
    def get_final_amount(self):
        """Get the final refund amount"""
        return self.approved_amount or self.requested_amount

