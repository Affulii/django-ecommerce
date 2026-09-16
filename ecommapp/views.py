from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User 
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, Order, OrderItem
from .cart import Cart
from django.db import transaction
import uuid
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
def home(request):
    order_id = request.GET.get('order_id', '').strip()
    order = None
    order_error = None

    if order_id:
        if order_id.isdigit():
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                order_error = f"No order found with ID #{order_id}."
        else:
            order_error = "Please enter a valid numeric Order ID."

    # --- 2. HANDLE PRODUCTS & PAGINATION ---
    products_list = Product.objects.all().order_by('id')
    paginator = Paginator(products_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- 3. RETURN CONTEXT ---
    return render(request, 'home.html', {  # Change 'shop.html' to your actual template name
        'page_obj': page_obj,
        'order': order,
        'order_id': order_id,
        'order_error': order_error,
    })
    
def login(request):
    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('/')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('/login/')
        
    return render(request, 'login.html')

def sign_up(request):
    if request.method == 'POST':
        username_input = request.POST.get('username')
        email_input = request.POST.get('email')
        password_input = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password_input != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('/sign_up/')

        if User.objects.filter(username=username_input).exists():
            messages.error(request, "Username already taken!")
            return redirect('/sign_up/')

        # Create user & save to database
        user = User.objects.create_user(
            username=username_input, 
            email=email_input, 
            password=password_input
        )
        user.save()

        # Log user in immediately after creating account
        auth_login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect('/')

    return render(request, 'signup.html') 
    
def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('/')

def shop(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.all().order_by('id')
    if query:
        # Search by name OR description (case-insensitive)
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'shop.html', {'page_obj': page_obj, 'query':query,})

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    # Get current quantity already in the session cart
    product_id_str = str(product.id)
    current_cart_qty = cart.cart.get(product_id_str, {}).get('quantity', 0)
    
    # Calculate requested total quantity (adding 1)
    new_quantity = current_cart_qty + 1

    # Check if requested quantity exceeds available stock
    if new_quantity > product.stock:
        if product.stock <= 0:
            messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        else:
            messages.error(
                request, 
                f"Cannot add more '{product.name}'. Only {product.stock} unit(s) available."
            )
        return redirect('cart_detail')

    # Add item to cart if stock is sufficient
    cart.add(product=product, quantity=1)
    messages.success(request, f"{product.name} added to your cart.")
    return redirect('cart_detail')

def cart_decrement(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    cart.decrement(product)
    messages.info(request, f"Reduced quantity of '{product.name}'.")
    return redirect('cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"{product.name} removed from your cart.")
    return redirect('cart_detail')

def buy_now(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1)
    return redirect('cart_detail')

def checkout(request):
    cart = Cart(request)
    
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('shop')

    if request.method == 'POST':
        # Use an atomic transaction to ensure Order and OrderItems save together cleanly
        with transaction.atomic():
            # 1. Create and save the real Order instance in PostgreSQL
            order = Order.objects.create(
                total_price=cart.get_total_price(),
                status='Processing'
            )

            # 2. Loop through cart items and create OrderItem records linked to the Order
            order_items_summary = []
            for item in cart:
                product = item['product'] if isinstance(item['product'], Product) else Product.objects.get(id=item['product_id'])
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    quantity=item['quantity']
                )
                order_items_summary.append(f"- {product.name} (Qty: {item['quantity']}) - ${item['price']}")

            # 3. Store the database Order ID in session for the order_success view
            request.session['last_order'] = {
                'order_id': order.id,
                'total': str(order.total_price),
                'items_count': len(cart),
            }

            # 4. Send Instant Admin Email Notification
            subject = f"🚨 New Order Received! Order #{order.id}"
            items_text = "\n".join(order_items_summary)
            message = f"""
New order received on your store!

Order ID: #{order.id}
Total Amount: ${order.total_price}
Total Items: {len(cart)}

Purchased Items:
{items_text}

Manage this order in Django Admin:
http://127.0.0.1:8080/admin/ecommapp/order/{order.id}/change/
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@mystore.com'),
                recipient_list=[getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'admin@mystore.com')],
                fail_silently=True,  # Prevents checkout failure if SMTP server is offline
            )

            # 5. Clear cart session upon successful save and redirect
            cart.clear()
            return redirect('order_success')

    context = {
        'cart': cart,
        'grand_total': cart.get_total_price(),
    }
    return render(request, 'checkout.html', context)


def order_success(request):
    # Retrieve recent order info from the session
    order_info = request.session.pop('last_order', None)
    
    # If a user tries to access /order-success/ directly without placing an order
    if not order_info:
        return redirect('shop')
    
    context = {
        'order_id': order_info.get('order_id'),
        'total': order_info.get('total'),
        'items_count': order_info.get('items_count'),
    }

    return render(request, 'order_success.html', context)

def about(request):
    return render(request, 'about.html')

def categories(request):
    return render(request, 'categories.html')

def category_detail(request, category_slug):
    category = get_object_or_404(category, slug=category_slug)
    # Automatically catches any new product assigned to this category!
    products = Product.objects.filter(category=category) 
    return render(request, 'category_detail.html', {'category': category, 'products': products})

def category_phones(request):
    return render(request, 'categories/phones.html')

def category_laptops(request):
    return render(request, 'categories/laptops.html')

#def category_accessories(request):
#   return render(request, 'categories/accessories.html')
def category_accessories(request):
    # Filter products in your database matching accessories
    products = Product.objects.filter(category__iexact='accessories') # Or Product.objects.all()
    return render(request, 'categories/accessories.html', {'products': products})
