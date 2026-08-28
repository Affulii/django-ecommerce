from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('login/', views.login, name='login'),
    path('signup/', views.sign_up, name='sign_up'),
    path('logout/', views.logout_view, name='logout'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remove/<int:product_id>/', views.cart_remove, name='cart_remove'),   
    path('checkout/', views.checkout, name='checkout'),
    path('about/', views.about, name='about'),
    path('catgories/', views.categories, name='categories'),
    path('categories/phones/', views.category_phones, name='category_phones'),
    path('categories/laptops/', views.category_laptops, name='category_laptops'),
    path('categories/accessories/', views.category_accessories, name='category_accessories'),
    path('cart/', views.Cart, name='cart'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('order_success/', views.order_success, name='order_success')
]
      


