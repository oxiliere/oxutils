from django.utils.translation import gettext_lazy as _
from django.db import models
from .base import BaseModelMixin




class BillingMixin(BaseModelMixin):
    """Billing information for individual users"""
    
    PAYMENT_METHOD_CHOICES = [
        ('card', _('Credit card')),
        ('paypal', _('PayPal')),
        ('bank_transfer', _('Bank transfer')),
        ('stripe', _('Stripe')),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', _('US Dollar')),
        ('CDF', _('Congolese Franc')),
    ]
    
    # Billing address
    billing_name = models.CharField(
        _('billing name'),
        max_length=100,
        blank=True,
        help_text=_('Full name for billing')
    )
    
    billing_email = models.EmailField(
        _('billing email'),
        blank=True,
        help_text=_('Email to receive invoices')
    )
    
    company_name = models.CharField(
        _('company name'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Company name (optional)')
    )
    
    tax_number = models.CharField(
        _('VAT number'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('VAT or tax identification number')
    )
    
    # Address
    street_address = models.CharField(
        _('address'),
        max_length=255,
        blank=True
    )
    
    city = models.CharField(
        _('city'),
        max_length=100,
        blank=True
    )
    
    postal_code = models.CharField(
        _('postal code'),
        max_length=20,
        blank=True
    )
    
    country = models.CharField(
        _('country'),
        max_length=2,
        blank=True,
        help_text=_('ISO 3166-1 alpha-2 country code')
    )
    
    # Payment preferences
    preferred_currency = models.CharField(
        _('preferred currency'),
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD'
    )
    
    preferred_payment_method = models.CharField(
        _('preferred payment method'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='card'
    )
    
    # Stripe customer info
    stripe_customer_id = models.CharField(
        _('Stripe customer ID'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Stripe customer identifier')
    )
    
    # Invoice preferences
    auto_pay = models.BooleanField(
        _('automatic payment'),
        default=False,
        help_text=_('Enable automatic invoice payment')
    )
    
    invoice_notes = models.TextField(
        _('billing notes'),
        blank=True,
        max_length=500,
        help_text=_('Custom notes to include on invoices')
    )
    
    class Meta:
        abstract = True
        verbose_name = _('Billing information')
        verbose_name_plural = _('Billing information')
    
    
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
