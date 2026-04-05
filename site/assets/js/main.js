/**
 * Site Júlia de Carvalho - JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    initHeader();
    initMobileMenu();
    initSmoothScroll();
    initAnimations();
    initFaq();
    initPreRegisterModal();
    initCtaTriggers();
    initReelCarousel();
});

// Header scroll effect + active nav link
function initHeader() {
    const header = document.querySelector('.header');
    const navLinks = document.querySelectorAll('.nav__link');
    const sections = document.querySelectorAll('section[id]');

    if (!header) return;

    const handleScroll = () => {
        // Scrolled class
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }

        // Active nav link
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 120;
            if (window.scrollY >= sectionTop) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
}

// Mobile menu toggle
function initMobileMenu() {
    const toggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('.nav');

    if (!toggle || !nav) return;

    toggle.addEventListener('click', () => {
        nav.classList.toggle('active');
        toggle.classList.toggle('active');
    });

    nav.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            nav.classList.remove('active');
            toggle.classList.remove('active');
        });
    });
}

// Smooth scroll for anchor links
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const headerOffset = 80;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
            }
        });
    });
}

// Scroll-based animations
function initAnimations() {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
    );

    const targets = document.querySelectorAll(
        '.section__header, .about__content, .dif-card, .pilar, ' +
        '.diferencial-card, .video-card, .faq__item'
    );

    targets.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(24px)';
        el.style.transition = 'opacity 0.55s ease, transform 0.55s ease';
        observer.observe(el);
    });

    const style = document.createElement('style');
    style.textContent = '.animate-in { opacity: 1 !important; transform: translateY(0) !important; }';
    document.head.appendChild(style);
}

// FAQ accordion
function initFaq() {
    const items = document.querySelectorAll('.faq__item');

    items.forEach(item => {
        const btn = item.querySelector('.faq__question');
        btn.addEventListener('click', () => {
            const isActive = item.classList.contains('active');

            // Close all
            items.forEach(i => {
                i.classList.remove('active');
                i.querySelector('.faq__question').setAttribute('aria-expanded', 'false');
            });

            // Open clicked if it was closed
            if (!isActive) {
                item.classList.add('active');
                btn.setAttribute('aria-expanded', 'true');
            }
        });
    });
}

// CTA buttons that trigger the WhatsApp modal
function initCtaTriggers() {
    const floatBtn = document.getElementById('whatsappFloat');
    const triggers = ['ctaHero', 'ctaDificuldades', 'ctaDiferenciais'];

    triggers.forEach(id => {
        const el = document.getElementById(id);
        if (el && floatBtn) {
            el.addEventListener('click', () => floatBtn.click());
        }
    });
}

// Reel carousel
function initReelCarousel() {
    const track = document.getElementById('reelTrack');
    const wrapper = track ? track.closest('.reel-carousel__track-wrapper') : null;
    const prevBtn = document.getElementById('reelPrev');
    const nextBtn = document.getElementById('reelNext');
    const dots = document.querySelectorAll('.reel-dot');

    if (!track) return;

    const total = dots.length;
    let current = 0;

    const goTo = (index) => {
        current = Math.max(0, Math.min(index, total - 1));
        track.style.transform = `translateX(-${current * 100}%)`;
        dots.forEach((d, i) => d.classList.toggle('active', i === current));
        prevBtn.disabled = current === 0;
        nextBtn.disabled = current === total - 1;
        if (window.instgrm) window.instgrm.Embeds.process();
    };

    prevBtn.addEventListener('click', () => goTo(current - 1));
    nextBtn.addEventListener('click', () => goTo(current + 1));
    dots.forEach(dot => dot.addEventListener('click', () => goTo(+dot.dataset.index)));

    // Touch / swipe support
    let touchStartX = 0;
    let touchDeltaX = 0;

    wrapper.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
        touchDeltaX = 0;
        track.style.transition = 'none';
    }, { passive: true });

    wrapper.addEventListener('touchmove', (e) => {
        touchDeltaX = e.touches[0].clientX - touchStartX;
        const offset = -(current * 100) + (touchDeltaX / wrapper.offsetWidth) * 100;
        track.style.transform = `translateX(${offset}%)`;
    }, { passive: true });

    wrapper.addEventListener('touchend', () => {
        track.style.transition = 'transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        if (touchDeltaX < -50) goTo(current + 1);
        else if (touchDeltaX > 50) goTo(current - 1);
        else goTo(current);
    });

    goTo(0);
}

// Pre-register modal with WhatsApp redirect
function initPreRegisterModal() {
    const floatBtn = document.getElementById('whatsappFloat');
    const overlay = document.getElementById('preRegisterModal');
    const closeBtn = document.getElementById('modalClose');
    const form = document.getElementById('preRegisterForm');

    if (!floatBtn || !overlay) return;

    const openModal = () => {
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        setTimeout(() => form.querySelector('input').focus(), 100);
    };

    const closeModal = () => {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    };

    floatBtn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('active')) closeModal();
    });

    // CPF mask: 000.000.000-00
    const cpfInput = document.getElementById('pr-cpf');
    cpfInput.addEventListener('input', () => {
        let v = cpfInput.value.replace(/\D/g, '').slice(0, 11);
        if (v.length > 9) v = v.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, '$1.$2.$3-$4');
        else if (v.length > 6) v = v.replace(/(\d{3})(\d{3})(\d{0,3})/, '$1.$2.$3');
        else if (v.length > 3) v = v.replace(/(\d{3})(\d{0,3})/, '$1.$2');
        cpfInput.value = v;
    });

    // Phone mask: (00) 00000-0000
    const phoneInput = document.getElementById('pr-phone');
    phoneInput.addEventListener('input', () => {
        let v = phoneInput.value.replace(/\D/g, '').slice(0, 11);
        if (v.length > 10) v = v.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
        else if (v.length > 6) v = v.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
        else if (v.length > 2) v = v.replace(/(\d{2})(\d{0,5})/, '($1) $2');
        else if (v.length > 0) v = v.replace(/(\d{0,2})/, '($1');
        phoneInput.value = v;
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(form));
        const birthFormatted = data.birth ? data.birth.split('-').reverse().join('/') : '';

        const dados = {
            nome: data.name,
            email: data.email,
            cpf: data.cpf,
            dataNascimento: birthFormatted,
            telefone: data.phone
        };

        fetch('https://script.google.com/macros/s/AKfycbxEBMdpJbj41QYLkOly48o2D4_W9QByLiprF7yCb_Y6DBPaC_pI-DffDGw2FuUazRqH/exec', {
            method: 'POST',
            mode: 'no-cors',
            body: JSON.stringify(dados)
        });

        setTimeout(() => {
            window.open('https://wa.me/5545999952507?text=Olá! Vim pelo site e gostaria de mais informações sobre os atendimentos! 😊', '_blank');
        }, 1000);

        closeModal();
        form.reset();
    });
}
