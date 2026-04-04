from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product, Category, Order, OrderItem
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
import os
import re
import json
import requests
import unicodedata


def home(request):
    featured_products = Product.objects.filter(featured=True)[:6]
    categories = Category.objects.all()
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'categories': categories,
    })

def product_list(request, category_slug=None):
    products = Product.objects.all()
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
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    return render(request, 'product_detail.html', {
        'product': product,
        'related_products': related_products,
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    pid = str(product_id)
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
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
    request.session['cart'] = cart
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        total = sum(float(i['price']) * i['quantity'] for i in cart.values())
        return JsonResponse({'success': True, 'cart_count': sum(i['quantity'] for i in cart.values()), 'total': total})
    return redirect('cart')

@require_POST
def update_cart(request, product_id):
    try:
        payload = json.loads(request.body.decode('utf-8'))
        quantity = int(payload.get('quantity', 0))
    except Exception:
        return JsonResponse({'success': False, 'error': 'invalid_payload'}, status=400)
    cart = request.session.get('cart', {})
    pid = str(product_id)
    if quantity <= 0:
        cart.pop(pid, None)
    else:
        if pid in cart:
            cart[pid]['quantity'] = quantity
        else:
            product = Product.objects.filter(id=product_id).first()
            if product:
                cart[pid] = {'name': product.name, 'price': float(product.price), 'quantity': quantity,
                             'image': product.image.url if product.image else None}
    request.session['cart'] = cart
    item_subtotal = float(cart[pid]['price']) * cart[pid]['quantity'] if pid in cart else 0
    total = sum(float(i['price']) * i['quantity'] for i in cart.values())
    return JsonResponse({'success': True, 'cart_count': sum(i['quantity'] for i in cart.values()),
                         'item_subtotal': item_subtotal, 'total': total})

def cart_view(request):
    cart = request.session.get('cart', {})
    total = 0
    for item in cart.values():
        item['price'] = float(item['price'])
        item['subtotal'] = item['price'] * item['quantity']
        total += item['subtotal']
    return render(request, 'cart.html', {'cart': cart, 'total': total})

def checkout(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        cart = request.session.get('cart', {})
        total = sum(float(i['price']) * i['quantity'] for i in cart.values())
        order = Order.objects.create(customer_name=name, phone=phone, address=address, total_amount=total)
        for pid, item in cart.items():
            product = Product.objects.get(id=pid)
            OrderItem.objects.create(order=order, product=product, quantity=item['quantity'], price=item['price'])
        request.session['cart'] = {}
        msg = f"নতুন অর্ডার #{order.id}\nনাম: {name}\nফোন: {phone}\nঠিকানা: {address}\nমোট: {total}৳"
        return redirect(f"https://wa.me/01707591255?text={msg}")

    cart = request.session.get('cart', {})
    total = 0
    for item in cart.values():
        item['price'] = float(item['price'])
        item['subtotal'] = item['price'] * item['quantity']
        total += item['subtotal']
    return render(request, 'checkout.html', {'cart': cart, 'total': total})


# ─────────────────────────────────────────────
#  PRODUCT MANAGEMENT (no /admin/ needed)
# ─────────────────────────────────────────────

@login_required
def manage_products(request):
    products = Product.objects.all().order_by('-id')
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

        # Validation
        if not all([name, level, description, price, category_id, image]):
            messages.error(request, 'সব ফিল্ড পূরণ করুন এবং ছবি দিন।')
            return render(request, 'add_product.html', {'categories': categories})

        # Auto-generate unique slug from name
        base_slug = re.sub(r'[^a-z0-9]+', '-',
                           unicodedata.normalize('NFKD', name)
                           .encode('ascii', 'ignore').decode().lower()).strip('-') or 'product'
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        category = get_object_or_404(Category, id=category_id)
        Product.objects.create(
            name=name,
            slug=slug,
            level=level,
            description=description,
            price=price,
            stock=int(stock),
            category=category,
            featured=featured,
            image=image,
        )
        messages.success(request, f'✅ "{name}" সফলভাবে যোগ করা হয়েছে!')
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
#  AI CHAT
# ─────────────────────────────────────────────

@require_POST
def ai_chat(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
        question = payload.get('question', '').strip()
    except Exception:
        return JsonResponse({'error': 'invalid_payload'}, status=400)

    if not question:
        return JsonResponse({'answer': 'প্রশ্ন করুন।'})

    # ✅ Correct HuggingFace URL (new router)
    hf_key = getattr(settings, 'HUGGINGFACE_API_KEY', '') or os.getenv('HUGGINGFACE_API_KEY', '')
    if hf_key:
        try:
            url = "https://router.huggingface.co/hf-inference/models/google/flan-t5-small"
            headers = {"Authorization": f"Bearer {hf_key}"}
            data = {"inputs": question, "parameters": {"max_new_tokens": 200}, "options": {"wait_for_model": True}}
            resp = requests.post(url, headers=headers, json=data, timeout=30)
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

    # Bangla + English fallback
    ql = question.lower()
    if any(w in ql for w in ['ডেলিভারি', 'delivery', 'shipping', 'পৌঁছাবে']):
        answer = 'ডেলিভারি চার্জ ৳১১০ টাকা। অর্ডার করার ২-৩ দিনের মধ্যে পৌঁছে যাবে। 🚚'
    elif any(w in ql for w in ['দাম', 'price', 'cost', 'কত', 'মূল্য']):
        answer = 'প্রতিটি পণ্যের দাম প্রোডাক্ট পেজে দেওয়া আছে। খাতার দাম ৳২৯০ থেকে শুরু। 💰'
    elif any(w in ql for w in ['অর্ডার', 'order', 'কিনব', 'buy', 'purchase']):
        answer = 'অর্ডার করতে: কার্টে যোগ করুন → চেকআউট → WhatsApp-এ কনফার্ম করুন। ✅'
    elif any(w in ql for w in ['payment', 'পেমেন্ট', 'টাকা', 'pay']):
        answer = 'আমরা ক্যাশ অন ডেলিভারি (COD) গ্রহণ করি। পণ্য পেলে টাকা দিলেই হবে! 💵'
    elif any(w in ql for w in ['whatsapp', 'হোয়াটসঅ্যাপ', 'contact', 'যোগাযোগ']):
        answer = 'চেকআউটের পরে সরাসরি WhatsApp-এ অর্ডার যাবে। আমরা দ্রুত রিপ্লাই দিই! 📱'
    elif any(w in ql for w in ['খাতা', 'notebook', 'practical', 'khata', 'ssc', 'hsc']):
        answer = 'SSC ও HSC-র Physics, Chemistry, Biology, Higher Math — সব প্র্যাকটিক্যাল খাতা পাবেন! 📚'
    elif any(w in ql for w in ['stock', 'আছে', 'available']):
        answer = 'স্টক সম্পর্কে জানতে প্রোডাক্ট পেজে দেখুন। In Stock দেখালে অর্ডার করতে পারবেন। ✅'
    elif any(w in ql for w in ['hello', 'hi', 'হ্যালো', 'আসসালামু', 'সালাম']):
        answer = 'আসসালামু আলাইকুম! 👋 Practical Khata-তে স্বাগতম। কীভাবে সাহায্য করতে পারি?'
    elif any(w in ql for w in ['bangla', 'বাংলা']):
        answer = 'জি, আমি বাংলায় কথা বলতে পারি! 😊 কী জানতে চান বলুন।'
    elif any(w in ql for w in ['return', 'ফেরত', 'exchange']):
        answer = 'পণ্যে সমস্যা হলে WhatsApp-এ জানান। আমরা সমাধান করব! 🔄'
    elif any(w in ql for w in ['thank', 'ধন্যবাদ', 'thanks']):
        answer = 'আপনাকেও ধন্যবাদ! 😊 আর কিছু লাগলে বলবেন।'
    else:
        answer = 'আমি ডেলিভারি, অর্ডার, দাম ও পণ্য সম্পর্কে সাহায্য করতে পারি। কী জানতে চান? 😊'

    return JsonResponse({'answer': answer})


def search_products(request):
    query = request.GET.get('q')
    products = Product.objects.filter(name__icontains=query) if query else Product.objects.all()
    return render(request, 'products.html', {'products': products, 'search_query': query})