from django.db import models
from django.contrib.auth.models import User

# --- ADDRESS MODEL ---
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    address_type= models.CharField(max_length=20, default='Home')
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.full_name} - {self.address_line_1}"


# --- PRODUCT MODEL ---
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('phones', 'Phones'),
        ('accessories', 'Accessories'),
        ('laptops', 'Laptops'),
    ]

    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Kept as CharField to prevent "DataError: invalid input syntax for type bigint: 'accessories'"
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='accessories')
    stock = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Specification Fields
    storage = models.CharField(max_length=100, blank=True, null=True)        # e.g. "256GB"
    display_specs = models.CharField(max_length=200, blank=True, null=True)  # e.g. "6.1-inch OLED"
    processor = models.CharField(max_length=100, blank=True, null=True)      # e.g. "A18 Bionic"
    camera = models.CharField(max_length=200, blank=True, null=True)         # e.g. "48MP Dual Camera"
    battery = models.CharField(max_length=100, blank=True, null=True)        # e.g. "3274 mAh, Fast Charging"

    def __str__(self):
        return self.name
    
    def is_in_stock(self):
        return self.stock > 0


# --- ORDER MODEL ---
class Order(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders', 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, default='Processing')

    def __str__(self):
        user_str = self.user.username if self.user else "Guest"
        return f"Order #{self.id} ({user_str})"


# --- ORDER ITEM MODEL ---
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}" 