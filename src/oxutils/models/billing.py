from django.utils.translation import gettext_lazy as _
from django.db import models
from .base import BaseModelMixin




class BillingMixin(BaseModelMixin):
    """Billing information for individual users"""
    
    PAYMENT_METHOD_CHOICES = [
        ('card', _('Carte bancaire')),
        ('paypal', _('PayPal')),
        ('bank_transfer', _('Virement bancaire')),
        ('stripe', _('Stripe')),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', _('Dollar américain')),
        ('CDF', _('Franc congolais')),
    ]
    
    # Billing address
    billing_name = models.CharField(
        _('nom de facturation'),
        max_length=100,
        blank=True,
        help_text=_('Nom complet pour la facturation')
    )
    
    billing_email = models.EmailField(
        _('email de facturation'),
        blank=True,
        help_text=_('Email pour recevoir les factures')
    )
    
    company_name = models.CharField(
        _('nom de l\'entreprise'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Nom de l\'entreprise (optionnel)')
    )
    
    tax_number = models.CharField(
        _('numéro de TVA'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Numéro de TVA ou d\'identification fiscale')
    )
    
    # Address
    street_address = models.CharField(
        _('adresse'),
        max_length=255,
        blank=True
    )
    
    city = models.CharField(
        _('ville'),
        max_length=100,
        blank=True
    )
    
    postal_code = models.CharField(
        _('code postal'),
        max_length=20,
        blank=True
    )
    
    country = models.CharField(
        _('pays'),
        max_length=2,
        blank=True,
        help_text=_('Code pays ISO 3166-1 alpha-2')
    )
    
    # Payment preferences
    preferred_currency = models.CharField(
        _('devise préférée'),
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD'
    )
    
    preferred_payment_method = models.CharField(
        _('méthode de paiement préférée'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='card'
    )
    
    # Stripe customer info
    stripe_customer_id = models.CharField(
        _('ID client Stripe'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Identifiant client Stripe')
    )
    
    # Invoice preferences
    auto_pay = models.BooleanField(
        _('paiement automatique'),
        default=False,
        help_text=_('Activer le paiement automatique des factures')
    )
    
    invoice_notes = models.TextField(
        _('notes de facturation'),
        blank=True,
        max_length=500,
        help_text=_('Notes personnalisées à inclure sur les factures')
    )
    
    class Meta:
        abstract = True
        verbose_name = _('Informations de facturation')
        verbose_name_plural = _('Informations de facturation')
    
    
    @property
    def full_address(self):
        """Return formatted full address"""
        parts = [
            self.street_address,
            self.city,
            self.postal_code,
            self.country
        ]
        return ', '.join(filter(None, parts))
    
    def get_billing_name(self):
        """Get billing name"""
        return self.billing_name
    
    def get_billing_email(self):
        """Get billing email"""
        return self.billing_email
