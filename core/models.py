from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Product(models.Model):
    LEVEL_CHOICES = [('SSC', 'SSC'), ('HSC', 'HSC')]

    name        = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True)
    category    = models.ForeignKey(Category, on_delete=models.CASCADE)
    level       = models.CharField(max_length=3, choices=LEVEL_CHOICES)
    description = models.TextField()
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    stock       = models.IntegerField(default=0)
    image       = models.ImageField(upload_to='products/')
    featured    = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.level} - {self.name}"

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(r.rating for r in reviews) / len(reviews), 1)
        return 0


class Coupon(models.Model):
    code            = models.CharField(max_length=20, unique=True)
    discount_type   = models.CharField(max_length=10, choices=[('percent','Percent'),('flat','Flat')], default='percent')
    discount_value  = models.DecimalField(max_digits=6, decimal_places=2)
    min_order       = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_uses        = models.IntegerField(default=100)
    used_count      = models.IntegerField(default=0)
    active          = models.BooleanField(default=True)
    expires_at      = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type=='percent' else '৳'})"

    def is_valid(self):
        from django.utils import timezone
        if not self.active:
            return False, "কুপন inactive।"
        if self.used_count >= self.max_uses:
            return False, "কুপন শেষ হয়ে গেছে।"
        if self.expires_at and timezone.now() > self.expires_at:
            return False, "কুপনের মেয়াদ শেষ।"
        return True, "valid"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('confirmed',  'Confirmed'),
        ('processing', 'Processing'),
        ('dispatched', 'Dispatched'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
    ]

    user          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=100)
    phone         = models.CharField(max_length=15)
    address       = models.TextField()
    total_amount  = models.DecimalField(max_digits=10, decimal_places=2)
    discount      = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    coupon        = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_note = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} — {self.customer_name}"

    def final_amount(self):
        return float(self.total_amount) - float(self.discount) + 110  # +delivery


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price    = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def subtotal(self):
        return float(self.price) * self.quantity


class Review(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name       = models.CharField(max_length=80)
    rating     = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment    = models.TextField()
    approved   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.product.name} ({self.rating}★)"

    class Meta:
        ordering = ['-created_at']