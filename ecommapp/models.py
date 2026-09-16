from django.db import models



class Product(models.Model):
    CATEGORY_CHOICES = [
        ('phones', 'Phones'),
        ('accessories', 'Accessories'),
        ('laptops', 'Laptops'),
    ]

    # Core Fields
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='accessories')
    stock = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Specification Fields (Optional for items like phones/laptops)
    storage = models.CharField(max_length=100, blank=True, null=True)        # e.g. "256GB"
    display_specs = models.CharField(max_length=200, blank=True, null=True)  # e.g. "6.1-inch OLED"
    processor = models.CharField(max_length=100, blank=True, null=True)      # e.g. "A18 Bionic"
    camera = models.CharField(max_length=200, blank=True, null=True)         # e.g. "48MP Dual Camera"
    battery = models.CharField(max_length=100, blank=True, null=True)        # e.g. "3274 mAh, Fast Charging"

    def __str__(self):
        return self.name
    
    def is_in_stock(self):
        return self.stock > 0
    
class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, default='Processing')

    def __str__(self):
        return f"Order #{self.id}"

class OrderItem(models.Model):
    # 'related_name' allows you to query order.items.all() on the homepage
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"