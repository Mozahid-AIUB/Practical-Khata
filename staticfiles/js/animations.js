// ═══════════════════════════════════════════════════════
//  ✨ ANIMATIONS.JS — Roboto Aesthetic Edition
//  Image Reveal | Navbar Shrink | Scroll Reveal
// ═══════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function () {

    // ── 1. IMAGE SMOOTH LOAD ──────────────────────────────
    document.querySelectorAll('img').forEach(img => {
        if (img.complete) {
            img.classList.add('loaded');
        } else {
            img.addEventListener('load', () => img.classList.add('loaded'));
            img.addEventListener('error', () => img.style.opacity = '1');
        }
    });


    // ── 2. NAVBAR SCROLL SHRINK ───────────────────────────
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 50);
        }, { passive: true });
    }


    // ── 3. SCROLL REVEAL (Intersection Observer) ─────────
    const revealEls = document.querySelectorAll('.will-reveal, .card, .product-card');
    if (revealEls.length) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, i) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.classList.add('revealed');
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, i * 80);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

        revealEls.forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(24px)';
            el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            observer.observe(el);
        });
    }


    // ── 4. RIPPLE EFFECT ON BUTTONS ──────────────────────
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);

            ripple.style.cssText = `
                position: absolute;
                width: ${size}px; height: ${size}px;
                left: ${e.clientX - rect.left - size / 2}px;
                top:  ${e.clientY - rect.top - size / 2}px;
                background: rgba(255,255,255,0.25);
                border-radius: 50%;
                transform: scale(0);
                animation: rippleAnim 0.5s ease forwards;
                pointer-events: none;
                z-index: 10;
            `;

            if (getComputedStyle(this).position === 'static') {
                this.style.position = 'relative';
            }
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Ripple keyframe (injected once)
    if (!document.getElementById('ripple-style')) {
        const s = document.createElement('style');
        s.id = 'ripple-style';
        s.textContent = `
            @keyframes rippleAnim {
                to { transform: scale(2.5); opacity: 0; }
            }
        `;
        document.head.appendChild(s);
    }


    // ── 5. PRODUCT CARD TILT (subtle 3D hover) ───────────
    document.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('mousemove', function (e) {
            const rect = this.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            this.style.transform = `translateY(-10px) rotateX(${-y * 6}deg) rotateY(${x * 6}deg) scale(1.015)`;
        });

        card.addEventListener('mouseleave', function () {
            this.style.transform = '';
            this.style.transition = 'transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
        });
    });


    // ── 6. FLOATING LABEL ANIMATION (checkout inputs) ────
    document.querySelectorAll('.checkout-input').forEach(input => {
        input.addEventListener('focus', function () {
            this.parentElement.classList.add('focused');
        });
        input.addEventListener('blur', function () {
            if (!this.value) this.parentElement.classList.remove('focused');
        });
    });


    console.log('✨ Animations loaded — Roboto Aesthetic Edition');
});