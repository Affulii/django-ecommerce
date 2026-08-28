from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User 
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product
from .cart import Cart
import uuid

# Create your views here.
def home(request):
    return render(request, 'home.html')

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
    cart.add(product=product, quantity=1)
    messages.success(request, f"{product.name} added to your cart.")
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
        # 1. Generate a temporary order reference number
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # 2. Store minimal details in the session before clearing the cart
        request.session['last_order'] = {
            'order_number': order_number,
            'total': str(cart.get_total_price()),
            'items_count': len(cart),
        }
        # Clear cart upon order completion
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

    return render(request, 'order_success.html', {'order': order_info})

def about(request):
    return render(request, 'about.html')

def categories(request):
    return render(request, 'categories.html')

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
