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
        _('invoice number'),
        max_length=50,
        unique=True,
        help_text=_('Unique invoice number')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[(status.value, status.value) for status in InvoiceStatusEnum],
        default=InvoiceStatusEnum.DRAFT,
        help_text=_('Invoice status')
    )
    
    # Amounts
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Amount excluding taxes')
    )
    
    tax_rate = models.DecimalField(
        _('tax rate'),
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text=_('Tax rate as percentage')
    )
    
    tax_amount = models.DecimalField(
        _('tax amount'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_('Tax amount')
    )
    
    total = models.DecimalField(
        _('total'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Total amount including tax')
    )
    
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='USD',
        help_text=_('ISO currency code (CDF, USD, etc.)')
    )
    
    # Dates
    issue_date = models.DateField(
        _('issue date'),
        help_text=_('Invoice issue date')
    )
    
    due_date = models.DateField(
        _('due date'),
        help_text=_('Payment due date')
    )
    
    paid_date = models.DateTimeField(
        _('payment date'),
        null=True,
        blank=True,
        help_text=_('Payment date and time')
    )
    
    # Billing period
    period_start = models.DateField(
        _('period start'),
        help_text=_('Billing period start date')
    )
    
    period_end = models.DateField(
        _('period end'),
        help_text=_('Billing period end date')
    )
    
    # Additional info
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Detailed invoice description')
    )
    
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Internal notes about the invoice')
    )
    
    # External payment system reference
    payment_reference = models.CharField(
        _('payment reference'),
        max_length=100,
        blank=True,
        help_text=_('External payment system reference (Stripe, etc.)')
    )
    
    class Meta:
        abstract = True
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['due_date']),
            models.Index(fields=['invoice_number']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
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
            self.notes = f"{invoice.notes}\nCancelled: {reason}".strip()

        self.save()

    def refund(self, reason= ""):
        """Mark invoice as refunded"""

        if self.status != InvoiceStatusEnum.PAID:
            raise ValueError("Only paid invoices can be refunded")
        
        self.status = InvoiceStatusEnum.REFUNDED
        
        if reason:
            self.notes = f"{invoice.notes}\nRefunded: {reason}".strip()

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
        _('service name'),
        max_length=200,
        help_text=_('Name of the billed service or product')
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Detailed service description')
    )
    
    # Pricing
    quantity = models.DecimalField(
        _('quantity'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text=_('Service quantity (hours, units, etc.)')
    )
    
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Unit price excluding taxes')
    )
    
    total_price = models.DecimalField(
        _('total price'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Total price for this item (quantity × unit price)')
    )
    
    # Metadata
    metadata = models.JSONField(
        _('metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional data in JSON format')
    )
    
    class Meta:
        abstract = True
        verbose_name = _('Invoice item')
        verbose_name_plural = _('Invoice items')
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
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('processed', _('Processed')),
        ('cancelled', _('Cancelled')),
    ]
    
    REFUND_REASON_CHOICES = [
        ('duplicate_payment', _('Duplicate payment')),
        ('service_not_received', _('Service not received')),
        ('billing_error', _('Billing error')),
        ('cancellation', _('Cancellation')),
        ('technical_issue', _('Technical issue')),
        ('other', _('Other')),
    ]
    
    # Refund details
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=REFUND_STATUS_CHOICES,
        default='pending',
        help_text=_('Refund request status')
    )
    
    reason = models.CharField(
        _('reason'),
        max_length=30,
        choices=REFUND_REASON_CHOICES,
        help_text=_('Reason for refund request')
    )
    
    description = models.TextField(
        _('description'),
        help_text=_('Detailed description of the refund request')
    )
    
    # Amount details
    requested_amount = models.DecimalField(
        _('requested amount'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Requested refund amount')
    )
    
    approved_amount = models.DecimalField(
        _('approved amount'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Approved refund amount')
    )
    
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='USD',
        help_text=_('ISO currency code (CDF, USD, etc.)')
    )
    
    # Processing details
    processed_date = models.DateTimeField(
        _('processing date'),
        null=True,
        blank=True,
        help_text=_('Refund processing date and time')
    )
    
    admin_notes = models.TextField(
        _('admin notes'),
        blank=True,
        help_text=_('Internal administrator notes')
    )
    
    # External payment system reference
    refund_reference = models.CharField(
        _('refund reference'),
        max_length=100,
        blank=True,
        help_text=_('External payment system reference (Stripe, etc.)')
    )
    
    class Meta:
        abstract = True
        verbose_name = _('Refund request')
        verbose_name_plural = _('Refund requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['processed_date']),
        ]
    
    def __str__(self):
        return f"Refund {self.requested_amount} {self.currency} - {self.get_status_display()}"
    
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
            raise ValueError("Only approved requests can be processed")
        
        self.status = 'processed'
        self.processed_date = timezone.now()
        self.refund_reference = refund_reference
        
        if admin_notes:
            self.admin_notes = f"{self.admin_notes}\n{admin_notes}".strip()
        
        self.save()
    
    def cancel(self, admin_notes=""):
        """Cancel the refund request"""
        if self.status == 'processed':
            raise ValueError("Cannot cancel an already processed request")
        
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

