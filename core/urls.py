from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='products'),
    path('products/<slug:category_slug>/', views.product_list, name='products_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:product_id>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('search/', views.search_products, name='search_products'),
    path('manage/', views.manage_products, name='manage_products'),
    path('manage/add/', views.add_product, name='add_product'),
    path('manage/delete/<int:product_id>/', views.delete_product, name='delete_product'),
]