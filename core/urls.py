from django.urls import path
from . import views

urlpatterns = [
    # ── Core ──────────────────────────────────────────────
    path('', views.home, name='home'),
    path('products/', views.product_list, name='products'),
    path('products/<slug:category_slug>/', views.product_list, name='products_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search_products, name='search_products'),

    # ── Cart ──────────────────────────────────────────────
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:product_id>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),

    # ── Checkout & Orders ────────────────────────────────
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/tracking/', views.order_tracking, name='order_tracking'),

    # ── Auth ──────────────────────────────────────────────
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # ── Reviews ───────────────────────────────────────────
    path('product/<slug:slug>/review/', views.submit_review, name='submit_review'),

    # ── Admin Product Manage ──────────────────────────────
    path('manage/', views.manage_products, name='manage_products'),
    path('manage/add/', views.add_product, name='add_product'),
    path('manage/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('manage/orders/', views.admin_orders, name='admin_orders'),
    path('manage/orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('manage/reviews/', views.admin_reviews, name='admin_reviews'),
    path('manage/reviews/<int:review_id>/approve/', views.approve_review, name='approve_review'),
    path('manage/coupons/', views.manage_coupons, name='manage_coupons'),
    path('manage/coupons/add/', views.add_coupon, name='add_coupon'),
    path('manage/coupons/delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

    # ── AI Chat ───────────────────────────────────────────
    path('ai-chat/', views.ai_chat, name='ai_chat'),
]