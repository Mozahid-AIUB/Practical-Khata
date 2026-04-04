// ═══════════════════════════════════════════════════════
//  🛒 CART.JS — Fixed & Upgraded
// ═══════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function () {

    // ── ADD TO CART (product pages) ──────────────────────
    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
        btn.addEventListener('click', async function (e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            const orig = this.innerHTML;
            this.disabled = true;

            try {
                const res  = await fetch(`/add-to-cart/${productId}/`, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await res.json();

                if (data.success) {
                    this.innerHTML = '<i class="fas fa-check"></i>';
                    this.style.background = 'linear-gradient(135deg,#00e5b0,#00d084)';
                    updateCartBadge(data.cart_count);
                    showToast('Added to cart ✓', 'success');
                    flyToCart(this);

                    setTimeout(() => {
                        this.innerHTML = orig;
                        this.style.background = '';
                        this.disabled = false;
                    }, 1800);
                }
            } catch (err) {
                this.disabled = false;
                showToast('Failed. Try again.', 'error');
            }
        });
    });


    // ── QTY BUTTONS (cart page) ──────────────────────────
    document.querySelectorAll('.qty-decrease, .qty-increase').forEach(btn => {
        btn.addEventListener('click', async function () {
            const row       = this.closest('[data-product-id]');
            const pid       = row.dataset.productId;
            const qtyEl     = row.querySelector('.qty-num');
            const isIncrease = this.classList.contains('qty-increase');
            let   qty        = parseInt(qtyEl.textContent) + (isIncrease ? 1 : -1);

            if (qty < 1) qty = 1;

            try {
                const res  = await fetch(`/update-cart/${pid}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({ quantity: qty })
                });
                const data = await res.json();

                if (data.success) {
                    qtyEl.textContent = qty;

                    // Update subtotal in this row
                    const subtotalEl = row.querySelector('.ci-subtotal');
                    if (subtotalEl && data.item_subtotal !== undefined) {
                        subtotalEl.textContent = '৳' + parseFloat(data.item_subtotal).toFixed(0);
                    }

                    // Update summary total
                    const totalEl = document.querySelector('.summary-total-amt');
                    if (totalEl && data.total !== undefined) {
                        totalEl.textContent = '৳' + (parseFloat(data.total) + 110).toFixed(0);
                    }

                    updateCartBadge(data.cart_count);

                    // Animate qty badge
                    qtyEl.style.transform = 'scale(1.3)';
                    setTimeout(() => qtyEl.style.transform = '', 200);
                }
            } catch (err) {
                showToast('Update failed', 'error');
            }
        });
    });


    // ── REMOVE FROM CART ─────────────────────────────────
    document.querySelectorAll('.remove-item-btn').forEach(btn => {
        btn.addEventListener('click', async function (e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            const row  = this.closest('[data-product-id]') || this.closest('.cart-item-row');

            try {
                const res  = await fetch(href, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await res.json();

                if (data.success) {
                    row.style.animation = 'slideOutRight 0.35s ease forwards';
                    setTimeout(() => {
                        row.remove();
                        updateCartBadge(data.cart_count);
                        const totalEl = document.querySelector('.summary-total-amt');
                        if (totalEl && data.total !== undefined) {
                            totalEl.textContent = '৳' + (parseFloat(data.total) + 110).toFixed(0);
                        }
                        if (data.cart_count === 0) location.reload();
                    }, 380);
                    showToast('Removed', 'info');
                }
            } catch (err) {
                showToast('Error removing item', 'error');
            }
        });
    });


    // ── HELPERS ──────────────────────────────────────────

    function updateCartBadge(count) {
        let badge = document.querySelector('.cart-nav-badge');
        const link = document.querySelector('.nav-link[href*="cart"]');
        if (!link) return;

        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'cart-nav-badge';
            badge.style.cssText = `
                background: linear-gradient(135deg,#f472b6,#ec4899);
                color: white; font-size: 0.65rem; font-weight: 700;
                padding: 1px 6px; border-radius: 10px; line-height: 1.6;
                margin-left: 2px;
            `;
            link.appendChild(badge);
        }
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline' : 'none';
    }

    function getCookie(name) {
        const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return v ? v.pop() : '';
    }

    function showToast(msg, type) {
        const colors = {
            success: 'rgba(0,229,176,0.92)',
            error:   'rgba(244,114,182,0.92)',
            info:    'rgba(91,127,255,0.92)'
        };
        const t = document.createElement('div');
        t.textContent = msg;
        t.style.cssText = `
            position:fixed; top:80px; right:20px;
            background:${colors[type] || colors.info};
            color:#fff; padding:10px 18px; border-radius:10px;
            font-size:0.85rem; font-weight:600;
            box-shadow:0 4px 20px rgba(0,0,0,0.3);
            z-index:99999; opacity:0;
            transition:opacity 0.3s ease, right 0.3s ease;
        `;
        document.body.appendChild(t);
        setTimeout(() => { t.style.opacity = 1; t.style.right = '24px'; }, 50);
        setTimeout(() => {
            t.style.opacity = 0;
            setTimeout(() => t.remove(), 350);
        }, 2500);
    }

    function flyToCart(btn) {
        const cartLink = document.querySelector('.nav-link[href*="cart"]');
        if (!cartLink) return;
        const bRect = btn.getBoundingClientRect();
        const cRect = cartLink.getBoundingClientRect();
        const dot = document.createElement('div');
        dot.style.cssText = `
            position:fixed;
            left:${bRect.left + bRect.width/2 - 6}px;
            top:${bRect.top + bRect.height/2 - 6}px;
            width:12px; height:12px;
            border-radius:50%;
            background:linear-gradient(135deg,#5b7fff,#00e5b0);
            z-index:99999; pointer-events:none;
            transition:all 0.7s cubic-bezier(0.25,0.46,0.45,0.94);
        `;
        document.body.appendChild(dot);
        requestAnimationFrame(() => {
            dot.style.left = `${cRect.left + cRect.width/2 - 6}px`;
            dot.style.top  = `${cRect.top  + cRect.height/2 - 6}px`;
            dot.style.opacity = '0';
            dot.style.transform = 'scale(0.2)';
        });
        setTimeout(() => dot.remove(), 750);
    }

    // Slide out animation
    const s = document.createElement('style');
    s.textContent = `
        @keyframes slideOutRight {
            to { transform: translateX(60px); opacity: 0; }
        }
        .qty-num { transition: transform 0.2s ease; }
    `;
    document.head.appendChild(s);

    console.log('🛒 Cart.js loaded');
});