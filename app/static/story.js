(() => {
  const duration = 5200;
  const scenes = [...document.querySelectorAll('.story-scene')];
  const words = [...document.querySelectorAll('.hero-word')];
  const stage = document.querySelector('.story-stage');
  const toggle = document.getElementById('motionToggle');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  if (!stage || !toggle || scenes.length !== 3 || words.length !== 3) return;

  let index = 0;
  let timer = null;
  let remaining = duration;
  let started = 0;
  let paused = false;
  let visible = !document.hidden;
  let onScreen = true;

  function setScene(next) {
    const previous = scenes[index];
    previous.classList.remove('active');
    previous.classList.add('out');
    window.setTimeout(() => previous.classList.remove('out'), duration);
    index = next;
    scenes[index].classList.add('active');
    words.forEach((word, i) => {
      word.hidden = i !== index;
      if (i === index) {
        word.style.animation = 'none';
        void word.offsetWidth;
        word.style.animation = '';
      }
    });
  }

  function stop() {
    if (timer === null) return;
    window.clearTimeout(timer);
    timer = null;
    remaining = Math.max(0, remaining - (performance.now() - started));
    stage.classList.remove('playing');
  }

  function schedule() {
    if (paused || !visible || !onScreen || reduced.matches || timer !== null) return;
    stage.classList.add('playing');
    started = performance.now();
    timer = window.setTimeout(() => {
      timer = null;
      remaining = duration;
      setScene((index + 1) % scenes.length);
      schedule();
    }, remaining);
  }

  function sync() {
    toggle.hidden = reduced.matches;
    if (paused || !visible || !onScreen || reduced.matches) stop();
    else schedule();
  }

  toggle.addEventListener('click', () => {
    paused = !paused;
    toggle.setAttribute('aria-pressed', String(paused));
    toggle.setAttribute('aria-label', paused ? 'Play animation' : 'Pause animation');
    toggle.textContent = paused ? 'Play motion' : 'Pause motion';
    if (!paused) remaining = duration;
    sync();
  });
  document.addEventListener('visibilitychange', () => { visible = !document.hidden; sync(); });
  reduced.addEventListener?.('change', sync);
  new IntersectionObserver(([entry]) => { onScreen = entry.isIntersecting; sync(); }).observe(stage);
  sync();
})();
