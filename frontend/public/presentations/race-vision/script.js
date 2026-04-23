const deck = document.getElementById('deck');
const slides = Array.from(document.querySelectorAll('.slide'));
const slideTitle = document.getElementById('slideTitle');
const slideCount = document.getElementById('slideCount');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const fullscreenBtn = document.getElementById('fullscreenBtn');
const printBtn = document.getElementById('printBtn');

let activeIndex = 0;

function updateHud(index) {
  activeIndex = index;
  const title = slides[index]?.dataset?.title || 'Презентация';
  slideTitle.textContent = title;
  slideCount.textContent = `${index + 1} / ${slides.length}`;
}

function goToSlide(index) {
  const bounded = Math.max(0, Math.min(index, slides.length - 1));
  slides[bounded].scrollIntoView({ behavior: 'smooth', block: 'start' });
  updateHud(bounded);
}

const observer = new IntersectionObserver((entries) => {
  const visible = entries
    .filter((entry) => entry.isIntersecting)
    .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

  if (!visible) {
    return;
  }

  const index = slides.indexOf(visible.target);
  if (index >= 0) {
    updateHud(index);
  }
}, {
  root: deck,
  threshold: [0.45, 0.6, 0.8],
});

slides.forEach((slide) => observer.observe(slide));

prevBtn.addEventListener('click', () => goToSlide(activeIndex - 1));
nextBtn.addEventListener('click', () => goToSlide(activeIndex + 1));
printBtn.addEventListener('click', () => window.print());

fullscreenBtn.addEventListener('click', async () => {
  if (!document.fullscreenElement) {
    await document.documentElement.requestFullscreen();
    fullscreenBtn.textContent = 'Шығу';
    return;
  }

  await document.exitFullscreen();
  fullscreenBtn.textContent = 'Толық экран';
});

document.addEventListener('fullscreenchange', () => {
  fullscreenBtn.textContent = document.fullscreenElement ? 'Шығу' : 'Толық экран';
});

window.addEventListener('keydown', (event) => {
  if (['ArrowDown', 'PageDown', ' '].includes(event.key)) {
    event.preventDefault();
    goToSlide(activeIndex + 1);
  } else if (['ArrowUp', 'PageUp'].includes(event.key)) {
    event.preventDefault();
    goToSlide(activeIndex - 1);
  } else if (event.key === 'Home') {
    event.preventDefault();
    goToSlide(0);
  } else if (event.key === 'End') {
    event.preventDefault();
    goToSlide(slides.length - 1);
  } else if (event.key.toLowerCase() === 'f') {
    fullscreenBtn.click();
  }
});

updateHud(0);
