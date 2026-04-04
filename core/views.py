from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Product, Category, Order, OrderItem, Coupon, Review
import os, re, json, unicodedata

# ─────────────────────────────────────────────
#  HOME & PRODUCTS
# ─────────────────────────────────────────────

def home(request):
    return render(request, 'home.html', {
        'featured_products': Product.objects.filter(featured=True)[:6],
        'categories': Category.objects.all(),
    })

def product_list(request, category_slug=None):
    products   = Product.objects.all()
    categories = Category.objects.all()
    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=current_category)
    return render(request, 'products.html', {
        'products': products,
        'categories': categories,
        'current_category': current_category,
    })

def product_detail(request, slug):
    product  = get_object_or_404(Product, slug=slug)
    related  = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    reviews  = product.reviews.filter(approved=True)
    return render(request, 'product_detail.html', {
        'product': product,
        'related_products': related,
        'reviews': reviews,
    })

def search_products(request):
    query    = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query) if query else Product.objects.all()
    return render(request, 'products.html', {'products': products, 'search_query': query})


# ─────────────────────────────────────────────
#  CART
# ─────────────────────────────────────────────

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart    = request.session.get('cart', {})
    pid     = str(product_id)
    if pid in cart:
        cart[pid]['quantity'] += 1
    else:
        cart[pid] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': 1,
            'image': product.image.url if product.image else None,
        }
    request.session['cart'] = cart
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_count': sum(i['quantity'] for i in cart.values())})
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    pid  = str(product_id)
    cart.pop(pid, None)
    request.session['cart'] = cart
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        total = sum(float(i['price']) * i['quantity'] for i in cart.values())
        return JsonResponse({'success': True, 'cart_count': sum(i['quantity'] for i in cart.values()), 'total': total})
    return redirect('cart')

@require_POST
def update_cart(request, product_id):
    try:
        payload  = json.loads(request.body.decode('utf-8'))
        quantity = int(payload.get('quantity', 0))
    except Exception:
        return JsonResponse({'success': False, 'error': 'invalid_payload'}, status=400)

    cart = request.session.get('cart', {})
    pid  = str(product_id)
    if quantity <= 0:
        cart.pop(pid, None)
    else:
        if pid in cart:
            cart[pid]['quantity'] = quantity
        else:
            product = Product.objects.filter(id=product_id).first()
            if product:
                cart[pid] = {'name': product.name, 'price': float(product.price),
                             'quantity': quantity, 'image': product.image.url if product.image else None}
    request.session['cart'] = cart
    item_subtotal = float(cart[pid]['price']) * cart[pid]['quantity'] if pid in cart else 0
    total         = sum(float(i['price']) * i['quantity'] for i in cart.values())
    return JsonResponse({'success': True,
                         'cart_count': sum(i['quantity'] for i in cart.values()),
                         'item_subtotal': item_subtotal, 'total': total})

def cart_view(request):
    cart  = request.session.get('cart', {})
    total = 0
    for item in cart.values():
        item['price']    = float(item['price'])
        item['subtotal'] = item['price'] * item['quantity']
        total           += item['subtotal']
    coupon_discount = request.session.get('coupon_discount', 0)
    coupon_code     = request.session.get('coupon_code', '')
    return render(request, 'cart.html', {
        'cart': cart, 'total': total,
        'coupon_discount': coupon_discount,
        'coupon_code': coupon_code,
    })

@require_POST
def apply_coupon(request):
    code  = request.POST.get('coupon_code', '').strip().upper()
    cart  = request.session.get('cart', {})
    total = sum(float(i['price']) * i['quantity'] for i in cart.values())

    try:
        coupon = Coupon.objects.get(code=code)
        valid, msg = coupon.is_valid()
        if not valid:
            messages.error(request, msg)
            return redirect('cart')
        if float(coupon.min_order) > total:
            messages.error(request, f"Minimum order ৳{coupon.min_order} লাগবে।")
            return redirect('cart')
        if coupon.discount_type == 'percent':
            discount = round(total * float(coupon.discount_value) / 100, 2)
        else:
            discount = float(coupon.discount_value)
        request.session['coupon_code']     = code
        request.session['coupon_discount'] = discount
        messages.success(request, f"✅ কুপন applied! ৳{discount:.0f} ছাড় পেলে।")
    except Coupon.DoesNotExist:
        messages.error(request, "কুপন কোড সঠিক নয়।")
        request.session.pop('coupon_code', None)
        request.session.pop('coupon_discount', None)

    return redirect('cart')


# ─────────────────────────────────────────────
#  CHECKOUT & ORDER TRACKING
# ─────────────────────────────────────────────

def checkout(request):
    cart = request.session.get('cart', {})
    total = sum(float(i['price']) * i['quantity'] for i in cart.values())
    coupon_discount = float(request.session.get('coupon_discount', 0))
    coupon_code     = request.session.get('coupon_code', '')
    final_total     = total - coupon_discount

    if request.method == 'POST':
        name    = request.POST.get('name')
        phone   = request.POST.get('phone')
        address = request.POST.get('address')

        coupon_obj = None
        if coupon_code:
            try:
                coupon_obj = Coupon.objects.get(code=coupon_code)
                coupon_obj.used_count += 1
                coupon_obj.save()
            except Coupon.DoesNotExist:
                pass

        order = Order.objects.create(
            user          = request.user if request.user.is_authenticated else None,
            customer_name = name,
            phone         = phone,
            address       = address,
            total_amount  = final_total,
            discount      = coupon_discount,
            coupon        = coupon_obj,
        )
        for pid, item in cart.items():
            product = Product.objects.filter(id=pid).first()
            if product:
                OrderItem.objects.create(
                    order=order, product=product,
                    quantity=item['quantity'], price=item['price']
                )

        # Clear cart & coupon
        request.session['cart']            = {}
        request.session['coupon_code']     = ''
        request.session['coupon_discount'] = 0

        # WhatsApp redirect
        items_text = '%0A'.join([f"• {i['name']} ×{i['quantity']} = ৳{int(float(i['price'])*i['quantity'])}" for i in cart.values()])
        msg = (f"আসসালামু আলাইকুম!%0A"
               f"নতুন অর্ডার #{order.id}%0A"
               f"নাম: {name}%0A"
               f"ফোন: {phone}%0A"
               f"ঠিকানা: {address}%0A%0A"
               f"{items_text}%0A%0A"
               f"Subtotal: ৳{int(total)}%0A"
               f"Discount: ৳{int(coupon_discount)}%0A"
               f"Delivery: ৳110%0A"
               f"মোট: ৳{int(final_total)+110}%0A%0A"
               f"Order tracking: http://127.0.0.1:8000/order/{order.id}/tracking/")
        return redirect(f"https://wa.me/8801707591255?text={msg}")

    for item in cart.values():
        item['price']    = float(item['price'])
        item['subtotal'] = item['price'] * item['quantity']

    return render(request, 'checkout.html', {
        'cart': cart, 'total': total,
        'coupon_discount': coupon_discount,
        'coupon_code': coupon_code,
        'final_total': final_total,
    })

def order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    steps = ['pending', 'confirmed', 'processing', 'dispatched', 'delivered']
    step_labels = {
        'pending':    ('⏳', 'অর্ডার পেয়েছি'),
        'confirmed':  ('✅', 'Confirmed'),
        'processing': ('📝', 'তৈরি হচ্ছে'),
        'dispatched': ('🚚', 'পাঠানো হয়েছে'),
        'delivered':  ('🎉', 'পৌঁছে গেছে'),
    }
    current_idx = steps.index(order.status) if order.status in steps else 0
    return render(request, 'order_tracking.html', {
        'order': order,
        'steps': steps,
        'step_labels': step_labels,
        'current_idx': current_idx,
    })


# ─────────────────────────────────────────────
#  AUTH — Register / Login / Logout / Dashboard
# ─────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        email      = request.POST.get('email', '').strip()
        password   = request.POST.get('password', '')
        password2  = request.POST.get('password2', '')
        if password != password2:
            messages.error(request, 'পাসওয়ার্ড মিলছে না।')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'এই username আগেই আছে।')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, f'স্বাগতম {username}! Account তৈরি হয়েছে।')
            return redirect('dashboard')
    return render(request, 'register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user     = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Username বা password ভুল।')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'dashboard.html', {'orders': orders})


# ─────────────────────────────────────────────
#  REVIEWS
# ─────────────────────────────────────────────

@require_POST
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    name    = request.POST.get('name', '').strip()
    rating  = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '').strip()
    if name and comment and 1 <= rating <= 5:
        Review.objects.create(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            name=name, rating=rating, comment=comment, approved=False,
        )
        messages.success(request, '✅ Review submit হয়েছে। Approve হলে দেখাবে।')
    else:
        messages.error(request, 'সব field পূরণ করুন।')
    return redirect('product_detail', slug=slug)


# ─────────────────────────────────────────────
#  PRODUCT MANAGEMENT
# ─────────────────────────────────────────────

@login_required
def manage_products(request):
    products   = Product.objects.all().order_by('-id')
    categories = Category.objects.all()
    return render(request, 'manageProduct.html', {'products': products, 'categories': categories})

@login_required
def add_product(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        level       = request.POST.get('level', '').strip()
        description = request.POST.get('description', '').strip()
        price       = request.POST.get('price', '0').strip()
        stock       = request.POST.get('stock', '0').strip()
        category_id = request.POST.get('category', '').strip()
        featured    = request.POST.get('featured') == 'on'
        image       = request.FILES.get('image')
        if not all([name, level, description, price, category_id, image]):
            messages.error(request, 'সব ফিল্ড পূরণ করুন।')
            return render(request, 'add_product.html', {'categories': categories})
        base_slug = re.sub(r'[^a-z0-9]+', '-',
                           unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()).strip('-') or 'product'
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"; counter += 1
        category = get_object_or_404(Category, id=category_id)
        Product.objects.create(name=name, slug=slug, level=level, description=description,
                               price=price, stock=int(stock), category=category,
                               featured=featured, image=image)
        messages.success(request, f'✅ "{name}" যোগ হয়েছে!')
        return redirect('manage_products')
    return render(request, 'add_product.html', {'categories': categories})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" মুছে ফেলা হয়েছে।')
    return redirect('manage_products')


# ─────────────────────────────────────────────
#  ADMIN ORDER DASHBOARD
# ─────────────────────────────────────────────

@login_required
def admin_orders(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all().order_by('-created_at').prefetch_related('items__product')
    if status_filter:
        orders = orders.filter(status=status_filter)
    total_revenue  = sum(float(o.total_amount) for o in Order.objects.all())
    pending_count  = Order.objects.filter(status='pending').count()
    today_orders   = Order.objects.filter(created_at__date=__import__('datetime').date.today()).count()
    return render(request, 'admin_orders.html', {
        'orders': orders,
        'status_filter': status_filter,
        'total_revenue': total_revenue,
        'pending_count': pending_count,
        'today_orders': today_orders,
        'status_choices': Order.STATUS_CHOICES,
    })

@login_required
@require_POST
def update_order_status(request, order_id):
    order  = get_object_or_404(Order, id=order_id)
    status = request.POST.get('status', '')
    note   = request.POST.get('tracking_note', '')
    if status in dict(Order.STATUS_CHOICES):
        order.status        = status
        order.tracking_note = note
        order.save()
        messages.success(request, f'Order #{order_id} → {status}')
    return redirect('admin_orders')


# ─────────────────────────────────────────────
#  ADMIN REVIEWS
# ─────────────────────────────────────────────

@login_required
def admin_reviews(request):
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'admin_reviews.html', {'reviews': reviews})

@login_required
def approve_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.approved = not review.approved
    review.save()
    return redirect('admin_reviews')


# ─────────────────────────────────────────────
#  COUPON MANAGEMENT
# ─────────────────────────────────────────────

@login_required
def manage_coupons(request):
    coupons = Coupon.objects.all().order_by('-id')
    return render(request, 'manage_coupons.html', {'coupons': coupons})

@login_required
def add_coupon(request):
    if request.method == 'POST':
        from django.utils import timezone
        import datetime
        code           = request.POST.get('code', '').strip().upper()
        discount_type  = request.POST.get('discount_type', 'percent')
        discount_value = request.POST.get('discount_value', '10')
        min_order      = request.POST.get('min_order', '0')
        max_uses       = request.POST.get('max_uses', '100')
        expires_days   = request.POST.get('expires_days', '')
        expires_at     = timezone.now() + datetime.timedelta(days=int(expires_days)) if expires_days else None
        Coupon.objects.create(
            code=code, discount_type=discount_type,
            discount_value=discount_value, min_order=min_order,
            max_uses=max_uses, expires_at=expires_at,
        )
        messages.success(request, f'Coupon "{code}" তৈরি হয়েছে!')
    return redirect('manage_coupons')

@login_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        coupon.delete()
        messages.success(request, 'Coupon মুছে ফেলা হয়েছে।')
    return redirect('manage_coupons')


# ─────────────────────────────────────────────
#  AI CHAT
# ─────────────────────────────────────────────

@require_POST
def ai_chat(request):
    try:
        payload  = json.loads(request.body.decode('utf-8'))
        question = payload.get('question', '').strip()
    except Exception:
        return JsonResponse({'error': 'invalid_payload'}, status=400)
    if not question:
        return JsonResponse({'answer': 'প্রশ্ন করুন।'})

    hf_key = getattr(settings, 'HUGGINGFACE_API_KEY', '') or os.getenv('HUGGINGFACE_API_KEY', '')
    if hf_key:
        try:
            import requests as req
            url  = "https://router.huggingface.co/hf-inference/models/google/flan-t5-small"
            resp = req.post(url, headers={"Authorization": f"Bearer {hf_key}"},
                            json={"inputs": question, "parameters": {"max_new_tokens": 200},
                                  "options": {"wait_for_model": True}}, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                answer = ''
                if isinstance(result, list) and result:
                    answer = result[0].get('generated_text', '').strip()
                elif isinstance(result, dict):
                    answer = result.get('generated_text', '').strip()
                if answer:
                    return JsonResponse({'answer': answer})
        except Exception:
            pass

    ql = question.lower()
    if any(w in ql for w in ['ডেলিভারি', 'delivery', 'পৌঁছাবে']):
        answer = 'ডেলিভারি চার্জ ৳১১০। অর্ডারের ২-৩ দিনে পৌঁছাবে। 🚚'
    elif any(w in ql for w in ['দাম', 'price', 'কত', 'মূল্য']):
        answer = 'খাতার দাম ৳২৯০ থেকে শুরু। 💰'
    elif any(w in ql for w in ['coupon', 'কুপন', 'discount', 'ছাড়']):
        answer = 'কার্ট পেজে কুপন কোড enter করলে ছাড় পাবে! 🎟️'
    elif any(w in ql for w in ['track', 'অর্ডার', 'order', 'কোথায়']):
        answer = 'Checkout এর পরে Order Tracking link পাবে। সেখানে live status দেখতে পারবে। 📦'
    elif any(w in ql for w in ['payment', 'পেমেন্ট', 'বিকাশ', 'bkash', 'nagad']):
        answer = 'bKash/Nagad: 01707591255। Send Money → Screenshot → WhatsApp পাঠাও। 📱'
    elif any(w in ql for w in ['hello', 'hi', 'হ্যালো', 'আসসালামু']):
        answer = 'আসসালামু আলাইকুম! 👋 কীভাবে সাহায্য করতে পারি?'
    elif any(w in ql for w in ['return', 'ফেরত', 'problem', 'সমস্যা']):
        answer = 'কোনো সমস্যা হলে WhatsApp এ জানান। আমরা সমাধান করব! 🔄'
    else:
        answer = 'ডেলিভারি, অর্ডার, দাম, কুপন — সব বিষয়ে সাহায্য করতে পারি। কী জানতে চান? 😊'
    return JsonResponse({'answer': answer})