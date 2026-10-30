(() => {
  const duration = 5200;
  const scenes = [...document.querySelectorAll('.story-scene')];
  const words = [...document.querySelectorAll('.hero-word')];
  const stage = document.querySelector('.story-stage');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  if (!stage || scenes.length !== 3 || words.length !== 3) return;

  let index = 0;
  let timer = null;
  let remaining = duration;
  let started = 0;
  let visible = !document.hidden;
  let onScreen = true;

  function setScene(next) {
    const previous = scenes[index];
    previous.classList.remove('active');
    previous.classList.add('out');
    window.setTimeout(() => previous.classList.remove('out'), 1000);
    index = next;
    scenes[index].classList.add('active');
    words.forEach((word, i) => {
      word.classList.toggle('active', i === index);
      word.classList.toggle('out', i !== index);
      word.setAttribute('aria-hidden', String(i !== index));
      if (i !== index) window.setTimeout(() => word.classList.remove('out'), 900);
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
    if (!visible || !onScreen || reduced.matches || timer !== null) return;
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
    if (!visible || !onScreen || reduced.matches) stop();
    else schedule();
  }

  document.addEventListener('visibilitychange', () => { visible = !document.hidden; sync(); });
  reduced.addEventListener?.('change', sync);
  new IntersectionObserver(([entry]) => { onScreen = entry.isIntersecting; sync(); }).observe(stage);
  sync();
})();
