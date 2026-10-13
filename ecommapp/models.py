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


class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit / Debit Card'),
        ('cod', 'Cash on Delivery'),
    ]

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

    # NEW: Payment tracking fields
    payment_method = models.CharField(
        max_length=10, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='card'
    )
    card_last_four = models.CharField(max_length=4, blank=True, null=True)

    def __str__(self):
        user_str = self.user.username if self.user else "Guest"
        return f"Order #{self.id} ({user_str})"

    STATUS_CHOICES = [
        ('Processing', 'Processing'),
        ('Approved', 'Approved'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
    ]
    
    # ... other fields (user, total_price, payment_method, etc.) ...
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Processing')
    created_at = models.DateTimeField(auto_now_add=True)    



# --- ORDER ITEM MODEL ---
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}" 


class UserLog(models.Model):
    LOG_LEVEL_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    log_level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES, default='INFO')
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"[{self.log_level}] {user_str} - {self.action} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"