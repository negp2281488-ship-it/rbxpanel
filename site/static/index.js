document.addEventListener('DOMContentLoaded', () => {
    const gridSize = 150;
    const gridHighlights = document.querySelector('.grid-highlights');
    const cols = Math.ceil(window.innerWidth / gridSize) + 1;
    const rows = Math.ceil(window.innerHeight / gridSize) + 1;
    
    const cells = [];
    for (let i = 0; i < 3; i++) {
        const cell = document.createElement('div');
        cell.className = 'grid-cell';
        gridHighlights.appendChild(cell);
        cells.push(cell);
    }
    
    function getRandomPosition() {
        const col = Math.floor(Math.random() * cols);
        const row = Math.floor(Math.random() * rows);
        return {
            left: col * gridSize + 'px',
            top: row * gridSize + 'px'
        };
    }
    
    function animateCell(cell) {
        cell.classList.remove('active');
        
        setTimeout(() => {
            const pos = getRandomPosition();
            cell.style.left = pos.left;
            cell.style.top = pos.top;
            
            setTimeout(() => {
                cell.classList.add('active');
            }, 100);
        }, 1000);
    }
    
    cells.forEach((cell, index) => {
        const pos = getRandomPosition();
        cell.style.left = pos.left;
        cell.style.top = pos.top;
        
        setTimeout(() => {
            cell.classList.add('active');
        }, 500 + index * 300);
        
        setInterval(() => {
            animateCell(cell);
        }, 4000 + index * 1000);
    });
    
    const carouselTrack = document.getElementById('carouselTrack');
    const carouselColumns = carouselTrack ? carouselTrack.querySelectorAll('.carousel-column') : [];
    
    carouselColumns.forEach(column => {
        const items = Array.from(column.children);
        items.forEach(item => {
            const clone = item.cloneNode(true);
            column.appendChild(clone);
        });
    });
    
    const baseOffsets = [-200, -50, -280];
    
    function handleCarouselScroll() {
        if (!carouselTrack) return;
        
        const sectionRect = carouselTrack.closest('.integrations-section').getBoundingClientRect();
        const windowHeight = window.innerHeight;
        
        if (sectionRect.top < windowHeight && sectionRect.bottom > 0) {
            const scrollProgress = (windowHeight - sectionRect.top) / windowHeight;
            const scrollValue = scrollProgress * 200;
            
            carouselColumns.forEach((column, index) => {
                if (index === 1) {
                    column.style.transform = `translateY(${baseOffsets[index] - scrollValue}px)`;
                } else {
                    column.style.transform = `translateY(${baseOffsets[index] + scrollValue}px)`;
                }
            });
        }
    }
    
    window.addEventListener('scroll', handleCarouselScroll);
    handleCarouselScroll();
    
    const testimonialsTrack = document.getElementById('testimonialsTrack');
    const prevBtn = document.getElementById('prevTestimonial');
    const nextBtn = document.getElementById('nextTestimonial');
    let currentSlide = 0;
    const totalCards = testimonialsTrack ? testimonialsTrack.children.length : 0;
    const cardsToShow = 2;
    const maxSlide = Math.max(0, totalCards - cardsToShow);
    
    function updateTestimonialPosition() {
        if (!testimonialsTrack) return;
        const cardWidth = testimonialsTrack.children[0].offsetWidth;
        const gap = 30;
        const offset = currentSlide * (cardWidth + gap);
        testimonialsTrack.style.transform = `translateX(-${offset}px)`;
        
        if (prevBtn) {
            prevBtn.disabled = currentSlide === 0;
            prevBtn.style.opacity = currentSlide === 0 ? '0.3' : '1';
        }
        if (nextBtn) {
            nextBtn.disabled = currentSlide === maxSlide;
            nextBtn.style.opacity = currentSlide === maxSlide ? '0.3' : '1';
        }
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentSlide > 0) {
                currentSlide--;
                updateTestimonialPosition();
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentSlide < maxSlide) {
                currentSlide++;
                updateTestimonialPosition();
            }
        });
    }
    
    updateTestimonialPosition();
    
    const scrollToToolsBtns = document.querySelectorAll('.scroll-to-tools');
    scrollToToolsBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const toolsSection = document.getElementById('tools-section');
            if (toolsSection) {
                toolsSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    const toolsCarousel = document.getElementById('toolsCarousel');
    const prevToolBtn = document.getElementById('prevTool');
    const nextToolBtn = document.getElementById('nextTool');
    let currentToolSlide = 0;
    const totalToolCards = toolsCarousel ? toolsCarousel.children.length : 0;
    const toolCardsToShow = 3;
    const maxToolSlide = Math.max(0, totalToolCards - toolCardsToShow);
    
    function updateToolsPosition() {
        if (!toolsCarousel) return;
        const cardWidth = toolsCarousel.children[0].offsetWidth;
        const gap = 30;
        const offset = currentToolSlide * (cardWidth + gap);
        toolsCarousel.style.transform = `translateX(-${offset}px)`;
        
        if (prevToolBtn) {
            prevToolBtn.disabled = currentToolSlide === 0;
            prevToolBtn.style.opacity = currentToolSlide === 0 ? '0.3' : '1';
        }
        if (nextToolBtn) {
            nextToolBtn.disabled = currentToolSlide === maxToolSlide;
            nextToolBtn.style.opacity = currentToolSlide === maxToolSlide ? '0.3' : '1';
        }
    }
    
    if (prevToolBtn) {
        prevToolBtn.addEventListener('click', () => {
            if (currentToolSlide > 0) {
                currentToolSlide--;
                updateToolsPosition();
            }
        });
    }
    
    if (nextToolBtn) {
        nextToolBtn.addEventListener('click', () => {
            if (currentToolSlide < maxToolSlide) {
                currentToolSlide++;
                updateToolsPosition();
            }
        });
    }
    
    updateToolsPosition();
    
    const newsletterForm = document.getElementById('newsletterForm');
    const emailInput = document.getElementById('emailInput');
    const successMessage = document.getElementById('successMessage');
    
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            if (emailInput.value.trim()) {
                successMessage.classList.add('show');
                emailInput.value = '';
                
                setTimeout(() => {
                    successMessage.classList.remove('show');
                }, 5000);
            }
        });
    }
    
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', (e) => {
            const ripple = document.createElement('span');
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            button.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    const title = document.querySelector('.main-title');
    const subtitle = document.querySelector('.subtitle');
    const badge = document.querySelector('.badge');
    const buttonsContainer = document.querySelector('.buttons');
    
    badge.style.opacity = '0';
    badge.style.transform = 'translateY(-20px)';
    
    title.style.opacity = '0';
    title.style.transform = 'translateY(20px)';
    
    subtitle.style.opacity = '0';
    subtitle.style.transform = 'translateY(20px)';
    
    buttonsContainer.style.opacity = '0';
    buttonsContainer.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        badge.style.transition = 'all 0.8s ease';
        badge.style.opacity = '1';
        badge.style.transform = 'translateY(0)';
    }, 100);
    
    setTimeout(() => {
        title.style.transition = 'all 0.8s ease';
        title.style.opacity = '1';
        title.style.transform = 'translateY(0)';
    }, 300);
    
    setTimeout(() => {
        subtitle.style.transition = 'all 0.8s ease';
        subtitle.style.opacity = '1';
        subtitle.style.transform = 'translateY(0)';
    }, 500);
    
    setTimeout(() => {
        buttonsContainer.style.transition = 'all 0.8s ease';
        buttonsContainer.style.opacity = '1';
        buttonsContainer.style.transform = 'translateY(0)';
    }, 700);
});

const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.5);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
    
    .btn {
        position: relative;
        overflow: hidden;
    }
`;
document.head.appendChild(style);

