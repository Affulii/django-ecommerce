from django.contrib import admin
from .models import Product, Order, OrderItem, UserLog

# ------------------------------------------------------------------
# PRODUCT ADMIN
# ------------------------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'storage', 'processor')
    list_filter = ('category',)
    search_fields = ('name', 'description')


# ------------------------------------------------------------------
# ORDER & ORDERITEM ADMIN
# ------------------------------------------------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']  # Helpful dropdown search for products
    extra = 0  # Prevents showing empty extra rows
    readonly_fields = ['price']  # Protects historical purchase price


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Columns displayed on the main Orders table
    list_display = ['id', 'full_name', 'email', 'phone', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id',]
    list_editable = ['status']   
    # Displays purchased items inside the Order edit view
    inlines = [OrderItemInline] 
    # Shows newest orders first
    ordering = ['-created_at']
    fieldsets = (
        ('Customer Verification Info', {
            'fields': ('full_name', 'email', 'phone', 'delivery_address', 'user')
        }),
        ('Order & Payment Details', {
            'fields': ('status', 'total_price', 'card_last_four')
        }),
    )


@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'log_level', 'ip_address')
    list_filter = ('log_level', 'timestamp')
    search_fields = ('user__username', 'action', 'details', 'ip_address')
    readonly_fields = ('timestamp', 'user', 'action', 'log_level', 'details', 'ip_address')