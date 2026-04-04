// ═══════════════════════════════════════════════════════
//  🛒 CART.JS - Shopping Cart Functionality
//  AJAX Add to Cart | Remove Items | Animations
// ═══════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function () {

    // ───────────────────────────────────────────────────
    //  🎯 ADD TO CART - AJAX with Animation
    // ───────────────────────────────────────────────────
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', async function (e) {
            e.preventDefault();
            e.stopPropagation();

            const productId = this.dataset.productId;
            const originalText = this.innerHTML;

            // Disable button during request
            this.disabled = true;
            this.style.transform = 'scale(0.95)';

            try {
                const response = await fetch(`/add-to-cart/${productId}/`, {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    // Success animation
                    this.classList.add('added');
                    this.innerHTML = '<i class="fas fa-check"></i> Added!';
                    this.style.background = 'linear-gradient(135deg, #00ff87, #00d084)';

                    // Update cart count in navbar
                    updateCartCount(data.cart_count);

                    // Show floating notification
                    showNotification('Added to cart!', 'success');

                    // Create flying cart animation
                    createFlyingCartEffect(this);

                    // Reset button after 2 seconds
                    setTimeout(() => {
                        this.classList.remove('added');
                        this.innerHTML = originalText;
                        this.style.background = '';
                        this.disabled = false;
                        this.style.transform = '';
                    }, 2000);
                } else {
                    throw new Error('Failed to add to cart');
                }

            } catch (error) {
                console.error('Error:', error);
                showNotification('Failed to add to cart', 'error');
                this.disabled = false;
                this.style.transform = '';
            }
        });
    });


    // ───────────────────────────────────────────────────
    //  ✨ FLYING CART EFFECT
    // ───────────────────────────────────────────────────
    function createFlyingCartEffect(button) {
        const cart = document.querySelector('.nav-link[href*="cart"]');
        if (!cart) return;

        const buttonRect = button.getBoundingClientRect();
        const cartRect = cart.getBoundingClientRect();

        // Create flying icon
        const flyingIcon = document.createElement('div');
        flyingIcon.innerHTML = '<i class="fas fa-shopping-cart"></i>';
        flyingIcon.style.cssText = `
            position: fixed;
            left: ${buttonRect.left + buttonRect.width / 2}px;
            top: ${buttonRect.top + buttonRect.height / 2}px;
            font-size: 24px;
            color: #00ff87;
            z-index: 10000;
            pointer-events: none;
            transition: all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            filter: drop-shadow(0 0 10px #00ff87);
        `;

        document.body.appendChild(flyingIcon);

        // Animate to cart
        setTimeout(() => {
            flyingIcon.style.left = `${cartRect.left + cartRect.width / 2}px`;
            flyingIcon.style.top = `${cartRect.top + cartRect.height / 2}px`;
            flyingIcon.style.transform = 'scale(0.3)';
            flyingIcon.style.opacity = '0';
        }, 50);

        setTimeout(() => flyingIcon.remove(), 850);
    }


    // ───────────────────────────────────────────────────
    //  🗑️ REMOVE FROM CART
    // ───────────────────────────────────────────────────
    const removeButtons = document.querySelectorAll('.remove-item-btn');

    removeButtons.forEach(button => {
        button.addEventListener('click', async function (e) {
            e.preventDefault();

            const href = this.getAttribute('href');
            const cartCard = this.closest('.cart-card');

            // Confirm deletion
            if (!confirm('Remove this item from cart?')) {
                return;
            }

            try {
                const response = await fetch(href, {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    // Animate removal
                    cartCard.style.animation = 'slideOutRight 0.5s ease forwards';

                    setTimeout(() => {
                        cartCard.remove();

                        // Update cart count
                        updateCartCount(data.cart_count);

                        // Update total
                        if (data.total !== undefined) {
                            updateCartTotal(data.total);
                        }

                        // If cart is empty, reload page
                        if (data.cart_count === 0) {
                            location.reload();
                        }
                    }, 500);

                    showNotification('Item removed', 'info');
                }

            } catch (error) {
                console.error('Error:', error);
                showNotification('Failed to remove item', 'error');
            }
        });
    });

    // Slide out animation
    const slideStyle = document.createElement('style');
    slideStyle.innerHTML = `
        @keyframes slideOutRight {
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(slideStyle);


    // ───────────────────────────────────────────────────
    //  🔢 UPDATE CART COUNT IN NAVBAR
    // ───────────────────────────────────────────────────
    function updateCartCount(count) {
        // Find or create cart badge
        let cartBadge = document.querySelector('.cart-count-badge');
        const cartLink = document.querySelector('.nav-link[href*="cart"]');

        if (!cartLink) return;

        if (!cartBadge) {
            cartBadge = document.createElement('span');
            cartBadge.className = 'cart-count-badge';
            cartBadge.style.cssText = `
                position: absolute;
                top: -8px;
                right: -8px;
                background: linear-gradient(135deg, #ff006e, #ff0080);
                color: white;
                border-radius: 50%;
                width: 22px;
                height: 22px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 11px;
                font-weight: 700;
                box-shadow: 0 0 15px rgba(255, 0, 110, 0.6);
                animation: bounce 0.5s ease;
            `;
            cartLink.style.position = 'relative';
            cartLink.appendChild(cartBadge);
        }

        // Update count with animation
        cartBadge.textContent = count;
        cartBadge.style.animation = 'none';
        setTimeout(() => {
            cartBadge.style.animation = 'bounce 0.5s ease';
        }, 10);

        // Hide badge if count is 0
        if (count === 0) {
            cartBadge.style.display = 'none';
        } else {
            cartBadge.style.display = 'flex';
        }
    }

    // Bounce animation for cart badge
    const bounceStyle = document.createElement('style');
    bounceStyle.innerHTML = `
        @keyframes bounce {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.3); }
        }
    `;
    document.head.appendChild(bounceStyle);


    // ───────────────────────────────────────────────────
    //  💰 UPDATE CART TOTAL
    // ───────────────────────────────────────────────────
    function updateCartTotal(total) {
        const totalElements = document.querySelectorAll('.text-success');
        totalElements.forEach(el => {
            if (el.textContent.includes('৳')) {
                el.textContent = `৳${parseFloat(total).toFixed(2)}`;
                el.style.animation = 'pulse 0.5s ease';
            }
        });
    }


    // ───────────────────────────────────────────────────
    //  📢 NOTIFICATION SYSTEM
    // ───────────────────────────────────────────────────
    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `cart-notification ${type}`;

        const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
        const bgColor = type === 'success' ? 'rgba(0, 255, 135, 0.95)' :
            type === 'error' ? 'rgba(255, 0, 110, 0.95)' :
                'rgba(91, 127, 255, 0.95)';

        notification.innerHTML = `
            <span class="notif-icon">${icon}</span>
            <span class="notif-text">${message}</span>
        `;

        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: -400px;
            background: ${bgColor};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            display: flex;
            align-items: center;
            gap: 0.8rem;
            font-weight: 600;
            transition: right 0.5s cubic-bezier(0.68, -0.55, 0.27, 1.55);
        `;

        document.body.appendChild(notification);

        // Slide in
        setTimeout(() => {
            notification.style.right = '30px';
        }, 100);

        // Slide out and remove
        setTimeout(() => {
            notification.style.right = '-400px';
            setTimeout(() => notification.remove(), 500);
        }, 3000);
    }


    // ───────────────────────────────────────────────────
    //  🎨 INITIALIZE CART COUNT ON PAGE LOAD
    // ───────────────────────────────────────────────────
    // You can fetch cart count via AJAX if needed
    // For now, it will be updated when items are added


    console.log('🛒 Cart functionality loaded!');
});