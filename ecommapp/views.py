import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User 
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

# Internal app imports
from .models import Product, Order, OrderItem, Address,UserLog
from .cart import Cart
from .forms import UserProfileForm, AddressForm


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

    # --- HANDLE PRODUCTS & PAGINATION ---
    products_list = Product.objects.all().order_by('id')
    paginator = Paginator(products_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'home.html', {
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
    return render(request, 'shop.html', {'page_obj': page_obj, 'query': query})


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

def cart_increment(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    success = cart.increment(product)
    if not success:
        messages.warning(
            request, "You cannot purchase more than 3 units of this item per order."
        )
    else:
        messages.success(request, f"Updated quantity for {product.name}.")
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
        # Get payment method from checkout form
        payment_method = request.POST.get('payment_method', 'card')
        
        # Extract last 4 digits if card option was chosen
        card_last_four = None
        if payment_method == 'card':
            raw_card_num = request.POST.get('card_number', '')
            if raw_card_num:
                card_last_four = raw_card_num.replace(" ", "")[-4:]

            # Create order linked to user if logged in
            order = Order.objects.create(
                user = request.user if request.user.is_authenticated else None,
                total_price=cart.get_total_price(),
                payment_method=payment_method,
                card_last_four=card_last_four,
                status='Processing'
            )

            # Create OrderItems
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

            # Store order summary in session
            request.session['last_order'] = {
                'order_id': order.id,
                'total': str(order.total_price),
                'items_count': len(cart),
            }

            # Send Email
            subject = f"🚨 New Order Received! Order #{order.id}"
            items_text = "\n".join(order_items_summary)
            message = f"""
New order received on your store!

Order ID: #{order.id}
Total Amount: ${order.total_price}
Total Items: {len(cart)}

Purchased Items:
{items_text}
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@mystore.com'),
                recipient_list=[getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'admin@mystore.com')],
                fail_silently=True,
            )

            cart.clear()
            return redirect('order_success')

    context = {
        'cart': cart,
        'grand_total': cart.get_total_price(),
    }
    return render(request, 'checkout.html', context)


def order_success(request):
    order_info = request.session.pop('last_order', None)
    
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
    products = Product.objects.filter(category=category) 
    return render(request, 'category_detail.html', {'category': category, 'products': products})


def category_phones(request):
    return render(request, 'categories/phones.html')


def category_laptops(request):
    return render(request, 'categories/laptops.html')


def category_accessories(request):
    products = Product.objects.filter(category__iexact='accessories')
    return render(request, 'categories/accessories.html', {'products': products})


@login_required(login_url='login')
def profile(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. ADD NEW ADDRESS
        if action == 'add_address':
            Address.objects.create(
                user=request.user,
                full_name=request.POST.get('full_name'),
                address_type=request.POST.get('address_type', 'Home'),
                address_line_1=request.POST.get('address_line_1'),
                address_line_2=request.POST.get('address_line_2', ''),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                postal_code=request.POST.get('postal_code'),
                phone_number=request.POST.get('phone_number')
            )
            return redirect('profile')

        # 2. EDIT EXISTING ADDRESS
        elif action == 'edit_address':
            address_id = request.POST.get('address_id')
            addr = get_object_or_404(Address, id=address_id, user=request.user)
            addr.full_name = request.POST.get('full_name')
            addr.address_type = request.POST.get('address_type', 'Home')
            addr.address_line_1 = request.POST.get('address_line_1')
            addr.address_line_2 = request.POST.get('address_line_2', '')
            addr.city = request.POST.get('city')
            addr.state = request.POST.get('state')
            addr.postal_code = request.POST.get('postal_code')
            addr.phone_number = request.POST.get('phone_number')
            addr.save()
            return redirect('profile')

        # 3. EDIT USER PROFILE
        else:
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.last_name = request.POST.get('last_name', request.user.last_name)
            request.user.email = request.POST.get('email', request.user.email)
            request.user.save()
            return redirect('profile')

    addresses = Address.objects.filter(user=request.user)
    return render(request, 'profile.html', {'addresses': addresses})


@login_required
def delete_address(request, address_id):
    addr = get_object_or_404(Address, id=address_id, user=request.user)
    addr.delete()
    return redirect('profile')

def track_order(request):
    order_id = request.GET.get('order_id')
    order = None
    order_error = None

    if order_id:
        try:
            order = Order.objects.get(id=order_id)
        except (Order.DoesNotExist, ValueError):
            order_error = f"No order found matching reference ID #{order_id}."

    context = {
        'order': order,
        'order_id': order_id,
        'order_error': order_error,
    }
    return render(request, 'track_order.html', context)


@login_required
def order_history(request):
    orders = (
      Order.objects.filter(user=request.user)
      .prefetch_related('items')
      .order_by('-created_at')
  )
    return render(request, 'order_history.html', {'orders':orders})

def log_user_event(request, action, details=None, level='INFO'):
    ip = request.META.get('REMOTE_ADDR')
    UserLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        details=details,
        log_level=level,
        ip_address=ip
    )