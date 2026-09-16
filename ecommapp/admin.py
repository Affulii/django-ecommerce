from django.contrib import admin
from .models import Product, Order, OrderItem

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
    list_display = ['id', 'status', 'total_price', 'created_at']
    
    # Filter sidebar by status and date created
    list_filter = ['status', 'created_at']
    
    # Search bar for Order ID or User info
    search_fields = ['id',]
    
    # Allows changing order status directly from the table list
    list_editable = ['status']
    
    # Displays purchased items inside the Order edit view
    inlines = [OrderItemInline]
    
    # Shows newest orders first
    ordering = ['-created_at']