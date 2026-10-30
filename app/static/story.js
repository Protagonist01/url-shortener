(() => {
  const duration = 5200;
  const fadeDuration = 680;
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
    const previousWord = words[index];
    previous.classList.remove('active');
    previous.classList.add('out');
    previousWord.classList.remove('active');
    previousWord.classList.add('out');
    previousWord.setAttribute('aria-hidden', 'true');

    window.setTimeout(() => {
      previous.classList.remove('out');
      previousWord.classList.remove('out');
      index = next;
      scenes[index].classList.add('active');
      words[index].classList.add('active');
      words[index].setAttribute('aria-hidden', 'false');
    }, fadeDuration);
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
