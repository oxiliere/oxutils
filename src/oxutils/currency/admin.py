from django.contrib import admin
from .models import CurrencyState, Currency


class CurrencyInline(admin.TabularInline):
    model = Currency
    extra = 0
    readonly_fields = ('id', 'code', 'rate')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CurrencyState)
class CurrencyStateAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'currency_count', 'created_at', 'updated_at')
    list_filter = ('source', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')
    search_fields = ('id', 'source')
    ordering = ('-created_at',)
    inlines = [CurrencyInline]
    
    def currency_count(self, obj):
        return obj.currencies.count()
    currency_count.short_description = 'Currencies'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'rate', 'state_source', 'state_created_at')
    list_filter = ('code', 'state__source', 'state__created_at')
    readonly_fields = ('id', 'code', 'rate', 'state')
    search_fields = ('code', 'state__id')
    ordering = ('code',)
    
    def state_source(self, obj):
        return obj.state.source
    state_source.short_description = 'Source'
    state_source.admin_order_field = 'state__source'
    
    def state_created_at(self, obj):
        return obj.state.created_at
    state_created_at.short_description = 'State Created'
    state_created_at.admin_order_field = 'state__created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
