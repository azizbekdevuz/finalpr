/* ─────────────────────────────────────────────────────
   Gabojago — liquid-bg.js
   Global cursor-responsive fluid background (no deps)
───────────────────────────────────────────────────── */
(function () {
  'use strict';

  var canvas = document.querySelector('.liquid-bg__canvas');
  if (!canvas || !canvas.getContext) return;

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var coarsePointer = window.matchMedia('(pointer: coarse)').matches;
  var mobile = window.innerWidth < 768 || coarsePointer;
  var lowPower = (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2)
    || (navigator.deviceMemory && navigator.deviceMemory <= 2);

  var ctx = canvas.getContext('2d', { alpha: true, desynchronized: true });
  if (!ctx) return;

  var offCanvas = document.createElement('canvas');
  var offCtx = offCanvas.getContext('2d', { alpha: true });
  var useOffscreen = !!offCtx;

  var width = 0;
  var height = 0;
  var dpr = 1;
  var renderScale = 1;
  var blurPx = 72;
  var running = false;
  var rafId = 0;
  var lastTime = 0;

  var targetX = 0.5;
  var targetY = 0.42;
  var smoothX = 0.5;
  var smoothY = 0.42;
  var smoothVX = 0;
  var smoothVY = 0;
  var pointerActive = false;
  var touching = false;

  var inflMin = 250;
  var inflMax = 500;

  var blobs = [];
  var blobCount = mobile || lowPower ? 3 : 5;

  var COLORS = [
    { r: 29, g: 95, b: 212, a: 0.42 },
    { r: 107, g: 168, b: 255, a: 0.32 },
    { r: 232, g: 160, b: 32, a: 0.20 },
    { r: 21, g: 72, b: 168, a: 0.30 },
    { r: 130, g: 175, b: 245, a: 0.26 }
  ];

  function clamp(v, min, max) {
    return v < min ? min : v > max ? max : v;
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function rgba(c, alpha) {
    return 'rgba(' + c.r + ',' + c.g + ',' + c.b + ',' + alpha + ')';
  }

  function influenceRadius() {
    return clamp(width * 0.32, inflMin, inflMax);
  }

  function initBlobs() {
    blobs.length = 0;
    var i;
    for (i = 0; i < blobCount; i++) {
      var color = COLORS[i % COLORS.length];
      blobs.push({
        px: 0.3 + i * 0.12,
        py: 0.25 + (i % 3) * 0.18,
        vx: 0,
        vy: 0,
        orbit: 0.18 + i * 0.14,
        angle: i * 1.35,
        drift: 0.00022 + i * 0.00005,
        phase: i * 1.7,
        lerp: 0.028 + i * 0.008,
        radius: 0,
        color: color,
        gradient: null
      });
    }
  }

  function rebuildGradients() {
    var i;
    var baseR = influenceRadius() * (mobile ? 0.42 : 0.48);
    for (i = 0; i < blobs.length; i++) {
      var b = blobs[i];
      var scale = 0.82 + (i % 3) * 0.12;
      b.radius = baseR * scale;
      var g = ctx.createRadialGradient(0, 0, 0, 0, 0, b.radius);
      g.addColorStop(0, rgba(b.color, b.color.a * 1.15));
      g.addColorStop(0.42, rgba(b.color, b.color.a * 0.55));
      g.addColorStop(1, rgba(b.color, 0));
      b.gradient = g;
    }
  }

  function configureQuality() {
    var maxDpr = mobile ? 1.25 : lowPower ? 1.5 : 1.75;
    dpr = Math.min(window.devicePixelRatio || 1, maxDpr);
    renderScale = mobile ? 0.72 : lowPower ? 0.82 : 1;
    blurPx = mobile ? 32 : lowPower ? 44 : 56;
  }

  function applyTransform(context) {
    context.setTransform(dpr * renderScale, 0, 0, dpr * renderScale, 0, 0);
  }

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    configureQuality();
    canvas.width = Math.max(1, Math.floor(width * dpr * renderScale));
    canvas.height = Math.max(1, Math.floor(height * dpr * renderScale));
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    offCanvas.width = canvas.width;
    offCanvas.height = canvas.height;
    applyTransform(ctx);
    if (useOffscreen) applyTransform(offCtx);
    rebuildGradients();
  }

  var resizeTimer = 0;
  function onResize() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(resize, 150);
  }

  function setTarget(clientX, clientY) {
    if (!width || !height) return;
    targetX = clientX / width;
    targetY = clientY / height;
    pointerActive = true;
  }

  function onPointerMove(e) {
    setTarget(e.clientX, e.clientY);
  }

  function onPointerLeave() {
    pointerActive = false;
  }

  function onTouchStart(e) {
    if (!e.touches.length) return;
    touching = true;
    setTarget(e.touches[0].clientX, e.touches[0].clientY);
  }

  function onTouchMove(e) {
    if (!touching || !e.touches.length) return;
    setTarget(e.touches[0].clientX, e.touches[0].clientY);
  }

  function onTouchEnd() {
    touching = false;
  }

  function updatePointer(dt) {
    var follow = pointerActive || touching ? 0.065 : 0.028;
    var dx = targetX - smoothX;
    var dy = targetY - smoothY;
    smoothX += dx * follow;
    smoothY += dy * follow;
    smoothVX = smoothVX * 0.88 + dx * width * 0.06;
    smoothVY = smoothVY * 0.88 + dy * height * 0.06;

    if (!pointerActive && !touching) {
      var t = performance.now();
      smoothX += Math.sin(t * 0.00028) * 0.00035;
      smoothY += Math.cos(t * 0.00024) * 0.0003;
    }
  }

  function updateBlobs(time) {
    var infl = influenceRadius();
    var i;
    for (i = 0; i < blobs.length; i++) {
      var b = blobs[i];
      var driftT = time * b.drift + b.phase;
      var orbitAngle = b.angle + driftT * 0.55;
      var wobble = Math.sin(driftT * 1.4) * 0.06;

      var cx = smoothX * width
        + Math.cos(orbitAngle) * infl * (b.orbit + wobble)
        + smoothVX * 0.00035 * (i + 1);
      var cy = smoothY * height
        + Math.sin(orbitAngle) * infl * (b.orbit + wobble) * 0.88
        + smoothVY * 0.00035 * (i + 1);

      var tx = cx / width;
      var ty = cy / height;
      var lerpAmt = b.lerp * (pointerActive || touching ? 1.15 : 0.75);

      b.vx = (tx - b.px) * width;
      b.vy = (ty - b.py) * height;
      b.px += (tx - b.px) * lerpAmt;
      b.py += (ty - b.py) * lerpAmt;
    }
  }

  function drawBase() {
    ctx.clearRect(0, 0, width, height);
  }

  function drawBlobs() {
    var i;
    var b;
    var x;
    var y;
    var speed;
    var angle;
    var stretch;
    var squash;

    if (useOffscreen) {
      offCtx.clearRect(0, 0, width, height);
      offCtx.globalCompositeOperation = 'source-over';
      for (i = 0; i < blobs.length; i++) {
        b = blobs[i];
        x = b.px * width;
        y = b.py * height;
        speed = Math.hypot(b.vx, b.vy);
        angle = Math.atan2(b.vy, b.vx);
        stretch = 1 + Math.min(speed * 0.0014, 0.45);
        squash = 1 / Math.sqrt(stretch);
        offCtx.save();
        offCtx.translate(x, y);
        if (speed > 0.5) {
          offCtx.rotate(angle);
          offCtx.scale(stretch, squash);
        }
        offCtx.fillStyle = b.gradient;
        offCtx.beginPath();
        offCtx.arc(0, 0, b.radius, 0, Math.PI * 2);
        offCtx.fill();
        offCtx.restore();
      }
      ctx.save();
      ctx.globalCompositeOperation = 'source-over';
      ctx.filter = 'blur(' + blurPx + 'px)';
      ctx.drawImage(offCanvas, 0, 0, width, height);
      ctx.filter = 'none';
      ctx.restore();
      return;
    }

    ctx.save();
    ctx.globalCompositeOperation = 'source-over';
    ctx.filter = 'blur(' + blurPx + 'px)';
    for (i = 0; i < blobs.length; i++) {
      b = blobs[i];
      x = b.px * width;
      y = b.py * height;
      speed = Math.hypot(b.vx, b.vy);
      angle = Math.atan2(b.vy, b.vx);
      stretch = 1 + Math.min(speed * 0.0014, 0.45);
      squash = 1 / Math.sqrt(stretch);
      ctx.save();
      ctx.translate(x, y);
      if (speed > 0.5) {
        ctx.rotate(angle);
        ctx.scale(stretch, squash);
      }
      ctx.fillStyle = b.gradient;
      ctx.beginPath();
      ctx.arc(0, 0, b.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
    ctx.filter = 'none';
    ctx.restore();
  }

  function drawStatic() {
    resize();
    initBlobs();
    var i;
    for (i = 0; i < blobs.length; i++) {
      blobs[i].px = 0.22 + i * 0.16;
      blobs[i].py = 0.18 + (i % 2) * 0.28;
    }
    drawBase();
    drawBlobs();
    drawAmbientVeil();
  }

  function drawAmbientVeil() {
    ctx.save();
    var veil = ctx.createRadialGradient(
      width * 0.5, height * 0.08, 0,
      width * 0.5, height * 0.5, Math.max(width, height) * 0.75
    );
    veil.addColorStop(0, 'rgba(29, 95, 212, 0.08)');
    veil.addColorStop(0.55, 'rgba(238, 242, 248, 0)');
    veil.addColorStop(1, 'rgba(232, 160, 32, 0.04)');
    ctx.fillStyle = veil;
    ctx.fillRect(0, 0, width, height);
    ctx.restore();
  }

  function frame(time) {
    if (!running) return;
    rafId = requestAnimationFrame(frame);

    var dt = Math.min((time - lastTime) / 1000, 0.05);
    lastTime = time;

    updatePointer(dt);
    updateBlobs(time);

    drawBase();
    drawBlobs();
    drawAmbientVeil();
  }

  function start() {
    if (running) return;
    running = true;
    lastTime = performance.now();
    rafId = requestAnimationFrame(frame);
  }

  function stop() {
    running = false;
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = 0;
    }
  }

  function bindEvents() {
    if (!reducedMotion) {
      window.addEventListener('pointermove', onPointerMove, { passive: true });
      window.addEventListener('pointerleave', onPointerLeave, { passive: true });
      window.addEventListener('touchstart', onTouchStart, { passive: true });
      window.addEventListener('touchmove', onTouchMove, { passive: true });
      window.addEventListener('touchend', onTouchEnd, { passive: true });
      window.addEventListener('touchcancel', onTouchEnd, { passive: true });
    }

    window.addEventListener('resize', onResize, { passive: true });

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop();
      else if (!reducedMotion) start();
    });

    var motionMq = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (motionMq.addEventListener) {
      motionMq.addEventListener('change', function (e) {
        reducedMotion = e.matches;
        if (reducedMotion) {
          stop();
          drawStatic();
        } else {
          start();
        }
      });
    }
  }

  function init() {
    initBlobs();
    resize();
    bindEvents();

    if (reducedMotion || window.matchMedia('print').matches) {
      drawStatic();
      return;
    }

    start();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
