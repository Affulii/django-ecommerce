from django.contrib import admin
from .models import Product


admin.site.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'storage', 'processor')
    list_filter = ('category',)
    search_fields = ('name', 'description')