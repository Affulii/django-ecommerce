from decimal import Decimal
from django.conf import settings
from ecommapp.models import Product  


class Cart:
    def __init__(self, request):
        """Initialize the shopping cart session and clean invalid entries."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        
        # Ensure cart is a dictionary
        if not cart or not isinstance(cart, dict):
            cart = self.session[settings.CART_SESSION_ID] = {}
        
        # Self-healing check: filter out non-dict items saved by mistake
        cleaned_cart = {}
        for key, item in cart.items():
            if isinstance(item, dict) and 'quantity' in item:
                cleaned_cart[str(key)] = item

        self.cart = cleaned_cart
        self.session[settings.CART_SESSION_ID] = self.cart

    def add(self, product, quantity=1, override_quantity=False):
        """Add a product to the cart or increment its quantity."""
        product_id = str(product.id)
        if product_id not in self.cart:
            # Save price as string so session remains JSON-serializable
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def decrement(self, product):
        """Decrements product quantity by 1. Removes item completely if quantity reaches 0."""
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id]['quantity'] -= 1
            
            # If quantity drops to 0 or lower, delete the product from cart
            if self.cart[product_id]['quantity'] <= 0:
                del self.cart[product_id]
            self.save()

    def remove(self, product):
        """Remove a product entirely from the cart regardless of quantity."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        """Mark session as modified to ensure changes persist in DB/session backend."""
        self.session.modified = True

    def __iter__(self):
        """Iterate over cart items without corrupting JSON session serialization."""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        
        # Deep copy dictionary items to avoid mutating original session objects
        cart_display = {}
        for key, value in self.cart.items():
            if isinstance(value, dict):
                cart_display[key] = value.copy()

        # Attach Model objects to temporary display cart
        for product in products:
            product_id_str = str(product.id)
            if product_id_str in cart_display:
                cart_display[product_id_str]['product'] = product

        # Yield items with computed Decimal prices for template rendering only
        for item in cart_display.values():
            if 'price' in item:
                item['price'] = Decimal(str(item['price']))
                item['total_price'] = item['price'] * item['quantity']
                yield item

    def __len__(self):
        """Count all item quantities in the cart safely."""
        return sum(
            item['quantity'] for item in self.cart.values() 
            if isinstance(item, dict) and 'quantity' in item
        )

    def get_total_price(self):
        """Calculate total cost of all items in cart safely."""
        return sum(
            Decimal(str(item['price'])) * item['quantity'] 
            for item in self.cart.values() 
            if isinstance(item, dict) and 'price' in item
        )

    def clear(self):
        """Remove cart completely from session on successful checkout."""
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()