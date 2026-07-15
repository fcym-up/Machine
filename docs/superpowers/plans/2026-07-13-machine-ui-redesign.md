# Machine UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reskin the Machine dashboard with green-terminal POI aesthetic and add Machjine-signature visual components (digital rain, The Number, boot sequence, surveillance frame).

**Architecture:** Pure frontend reskin — no API/backend changes. Color scheme shift in CSS, Three.js particle recolor in particle-core.js, new Canvas/HTML overlay controllers in app.js. index.html switches to ES module imports.

**Tech Stack:** CSS3 custom properties, Three.js (ES module), Canvas 2D, ES modules

## Global Constraints
- No new JS files or external npm dependencies
- No API or backend changes
- No removal of existing functionality
- All new code goes into existing files (style.css, animations.css, particle-core.js, app.js, index.html)
- index.html must use ES module `<script type="module">` instead of bundled scripts

---

### Task 1: File Cleanup

**Files:**
- Delete: ~20 files listed in spec (test HTMLs, audio-processor.js, temp scripts, screenshots, build scripts, shortcuts)

**Interfaces:**
- Consumes: nothing
- Produces: clean workspace

- [ ] **Step 1: Delete static test/demo files**

```powershell
Remove-Item -Path "D:\workplace\app\static\demo.html" -Force
Remove-Item -Path "D:\workplace\app\static\e2e-test.html" -Force
Remove-Item -Path "D:\workplace\app\static\test-flat.html" -Force
Remove-Item -Path "D:\workplace\app\static\test-module.html" -Force
Remove-Item -Path "D:\workplace\app\static\test.html" -Force
Remove-Item -Path "D:\workplace\app\static\js\audio-processor.js" -Force
```

Expected: Files removed.

- [ ] **Step 2: Delete root temp files**

```powershell
Remove-Item -Path "D:\workplace\_*.py" -Force
Remove-Item -Path "D:\workplace\_*.txt" -Force
Remove-Item -Path "D:\workplace\_*.bat" -Force
Remove-Item -Path "D:\workplace\_screenshot.png" -Force
Remove-Item -Path "D:\workplace\_screenshot2.png" -Force
Remove-Item -Path "D:\workplace\temp_replace.ps1" -Force
Remove-Item -Path "D:\workplace\weblog.txt" -Force
```

Expected: Files removed.

- [ ] **Step 3: Delete old helper scripts**

```powershell
Remove-Item -Path "D:\workplace\app\static\assets" -Recurse -Force
Remove-Item -Path "D:\workplace\app\static\lib" -Recurse -Force
```

Expected: icons.js and d3/three libs removed.

Wait — we need d3 and three.js for the app. Let me NOT delete lib/. Let me skip lib/ and assets/ deletion.

Actually, looking again — index.html uses `lib/d3.v7.min.js` and `lib/three.module.js`. These are still needed. And `assets/icons.js` might still be used. Let me keep these.

- [ ] **Step 1: Delete test/demo HTML files**

```powershell
Remove-Item "D:\workplace\app\static\demo.html" -Force
Remove-Item "D:\workplace\app\static\e2e-test.html" -Force
Remove-Item "D:\workplace\app\static\test-flat.html" -Force
Remove-Item "D:\workplace\app\static\test-module.html" -Force
Remove-Item "D:\workplace\app\static\test.html" -Force
Remove-Item "D:\workplace\app\static\js\audio-processor.js" -Force
```

- [ ] **Step 2: Delete root temp/build files**

```powershell
Get-ChildItem "D:\workplace\_*" | Remove-Item -Force
Remove-Item "D:\workplace\temp_replace.ps1" -Force
Remove-Item "D:\workplace\weblog.txt" -Force
```

- [ ] **Step 3: Delete screenshots**

```powershell
Remove-Item "D:\workplace\_screenshot.png" -Force
Remove-Item "D:\workplace\_screenshot2.png" -Force
```

- [ ] **Step 4: Commit cleanup**

```bash
git add -A
git commit -m "cleanup: remove unused test files, temp scripts, and build artifacts"
```

---

### Task 2: CSS Overhaul — Green Theme + New Components

**Files:**
- Modify: `app/static/css/style.css` — full color scheme + new component styles
- Modify: `app/static/css/animations.css` — new Machine animations

**Interfaces:**
- Consumes: nothing
- Produces: CSS variables and classes used by index.html and app.js

**Color Variable Changes (style.css `:root`):**

```
--bg-deep: #000A00;
--bg-panel: rgba(0,10,0,0.7);
--bg-card: rgba(0,10,0,0.55);
--accent: #00FF41;
--accent-dim: #00AA22;
--amber: #FFB000;
--amber-glow: rgba(255,176,0,0.15);
--amber-dim: rgba(255,176,0,0.08);
--green: #00FF41;
--yellow: #FFD700;
--red: #FF0033;
--red-dim: rgba(255,0,51,0.12);
--text: #B3FFB3;
--text-dim: rgba(179,255,179,0.5);
--text-subtle: rgba(179,255,179,0.25);
--border: rgba(179,255,179,0.06);
--border-glow: rgba(0,255,65,0.12);
--glass-bg: linear-gradient(135deg,rgba(0,10,0,0.65),rgba(0,5,0,0.75));
--glass-border: rgba(0,255,65,0.08);
--top-strip: linear-gradient(90deg,transparent,rgba(0,255,65,0.2),transparent);
```

**New Styles to Add (style.css):**

- `#boot-sequence` — full-screen overlay for boot log, z-index 200, bg #000A00
- `.boot-line` — monospace green text, typewriter animation
- `#the-number` — absolute center, font-size 72px, color var(--accent), text-shadow green glow
- `#digital-rain` — fixed canvas, z-index 0, pointer-events none, opacity 0.25
- `#surveillance-frame` — fixed inset-0, pointer-events none, z-index 98
- `.corner-bracket` — absolute L-shaped borders in green
- `.scan-line` — rotating line for viewfinder effect
- `.threat-irrelevant` / `.threat-monitor` / `.threat-significant` / `.threat-critical` — color-coded badge variants

- [ ] **Step 1: Rewrite CSS variables in style.css `:root`**

Change all color custom properties from blue (#67B8FF family) to green (#00FF41 family).

- [ ] **Step 2: Add new component styles to style.css**

Add styles for #boot-sequence, #the-number, #digital-rain, #surveillance-frame, corner brackets, scan line, threat badge variants.

- [ ] **Step 3: Update existing component styles for green theme**

Update all rgba references from blue-toned to green-toned in panel-section, panel-card, dock, input-field, btn, etc. Update scanline overlay from blue to green.

- [ ] **Step 4: Add new animations to animations.css**

```css
@keyframes boot-scroll {
  0% { transform: translateY(100%); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateY(-200%); opacity: 0; }
}

@keyframes phosphor-glow {
  0%, 100% { text-shadow: 0 0 4px rgba(0,255,65,0.3), 0 0 8px rgba(0,255,65,0.1); }
  50% { text-shadow: 0 0 8px rgba(0,255,65,0.6), 0 0 20px rgba(0,255,65,0.2), 0 0 40px rgba(0,255,65,0.1); }
}

@keyframes number-appear {
  0% { opacity: 0; transform: scale(0.8); filter: blur(4px); clip-path: inset(0 0 100% 0); }
  30% { opacity: 1; transform: scale(1); filter: blur(0); clip-path: inset(0 0 0 0); }
  80% { opacity: 1; }
  100% { opacity: 0; transform: scale(0.95); }
}

@keyframes scan-radar {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

- [ ] **Step 5: Run and verify no syntax errors**

---

### Task 3: Three.js Particle Core — Green Recolor + Scan Radar

**Files:**
- Modify: `app/static/js/particle-core.js`

**Interfaces:**
- Consumes: `<div id="three-container">` (already exists)
- Produces: Updated `ParticleCore` class with green theme and new scanning radar ring

- [ ] **Step 1: Change particle colors**

In `_createParticleSphere()`, change:
```javascript
var innerColor = new THREE.Color("#00FF41");  // was #67B8FF
var outerColor = new THREE.Color("#00AA22");  // was #3F89D7
```

- [ ] **Step 2: Increase particle count**

```javascript
var count = 6000;  // was 4000
```

- [ ] **Step 3: Change all material colors to green**

- `_createStars()`: star color `#B3FFB3` (was `#EAF4FF`)
- `_createCoreLight()`: core color `#00FF41`, aura `#00FF41`, bloom `#00AA22`
- `_createNeuralConnections()`: line color `#00FF41`
- `_createOrbitRings()`: ring color `#00AA22`
- `_createDataStreams()`: stream color `#00FF41`
- `_createScanRing()`: ring color `#00FF41`, ring2 color `#00AA22`
- `_createRadialLines()`: line color `#00AA22`
- `_createAmberAlertCore()`: color `#FFB000` (keep as orange)

- [ ] **Step 4: Add scanning radar ring**

Add a new method `_createScanRadar()` that creates a rotating green wedge (RingGeometry with a start angle / arc) that rotates around the sphere:

```javascript
_createScanRadar() {
  var geom = new THREE.RingGeometry(0.5, 4.5, 64, 1, 0, Math.PI * 0.25);
  this.scanRadar = new THREE.Mesh(geom, new THREE.MeshBasicMaterial({
    color: "#00FF41",
    transparent: true,
    opacity: 0.03,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  }));
  this.scanRadar.rotation.x = Math.PI * 0.5;
  this.scene.add(this.scanRadar);
}
```

Call it from `_initThree()`. In `animate()`, rotate it:
```javascript
if (this.scanRadar) {
  this.scanRadar.rotation.z += dt * 0.5;
}
```

- [ ] **Step 5: Update state animations for green glow**

In `_animateListening()`, `_animateThinking()`, etc., update the opacity multipliers and glow colors for the new green theme.

---

### Task 4: app.js — Digital Rain + Boot Sequence + The Number + Surveillance Frame

**Files:**
- Modify: `app/static/js/app.js`

**Interfaces:**
- Consumes: CSS classes from style.css, canvas element from index.html
- Produces: Controllers instantiated in `init()` that manage new UI overlays

- [ ] **Step 1: Add Digital Rain controller**

```javascript
class DigitalRain {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.columns = [];
    this.chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾙﾚﾛﾜ';
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
    this.columns = [];
    var colCount = Math.floor(this.canvas.width / 14);
    for (var i = 0; i < colCount; i++) {
      this.columns.push({
        x: i * 14,
        y: Math.random() * this.canvas.height,
        speed: 0.5 + Math.random() * 3,
        chars: Math.floor(Math.random() * 20) + 5
      });
    }
  }

  draw() {
    var ctx = this.ctx;
    ctx.fillStyle = 'rgba(0,10,0,0.05)';
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.font = '12px monospace';
    ctx.textAlign = 'center';
    for (var i = 0; i < this.columns.length; i++) {
      var col = this.columns[i];
      for (var j = 0; j < col.chars; j++) {
        var y = col.y - j * 14;
        if (y < -20 || y > this.canvas.height + 20) continue;
        var ch = this.chars[Math.floor(Math.random() * this.chars.length)];
        var brightness = 1 - (j / col.chars);
        ctx.fillStyle = j === 0 ? 'rgba(180,255,180,0.9)' : 'rgba(0,255,65,' + (brightness * 0.5) + ')';
        ctx.fillText(ch, col.x, y);
      }
      col.y += col.speed;
      if (col.y > this.canvas.height + 50) { col.y = -50; col.speed = 0.5 + Math.random() * 3; }
    }
  }

  start() {
    var self = this;
    function loop() { self._raf = requestAnimationFrame(loop); self.draw(); }
    loop();
  }

  stop() { if (this._raf) cancelAnimationFrame(this._raf); }

  setIntensity(val) {
    // val: 0-1, controls opacity
    this.canvas.style.opacity = 0.05 + val * 0.25;
  }
}
```

- [ ] **Step 2: Add Boot Sequence controller**

```javascript
class BootSequence {
  constructor(overlayEl) {
    this.el = overlayEl;
    this.lines = [
      'MACHINE v0.6.0',
      'COPYRIGHT (C) 2026 — ALL RIGHTS RESERVED',
      '',
      'INITIALIZING CORE SYSTEMS...',
      '  [OK]  MEMORY SUBSYSTEM',
      '  [OK]  EVENT ENGINE',
      '  [OK]  KNOWLEDGE GRAPH',
      '  [OK]  INTELLIGENCE ANALYSIS',
      '  [OK]  SENSOR NETWORK',
      '',
      'ESTABLISHING SECURE LINK...',
      '  [OK]  ENCRYPTION HANDSHAKE',
      '  [OK]  AUTHENTICATION',
      '',
      'LOADING BEHAVIORAL MODELS... 100%',
      'SYNCHRONIZING DATA STREAMS... 100%',
      '',
      'MACHINE ONLINE.',
      '',
      'YOU ARE BEING WATCHED.'
    ];
  }

  start(callback) {
    var self = this;
    this.el.style.display = 'flex';
    this.el.innerHTML = '';
    var lineIdx = 0;
    function typeLine() {
      if (lineIdx >= self.lines.length) {
        setTimeout(function() { self.el.style.opacity = '0'; }, 800);
        setTimeout(function() { self.el.style.display = 'none'; if (callback) callback(); }, 2800);
        return;
      }
      var line = document.createElement('div');
      line.className = 'boot-line';
      line.textContent = self.lines[lineIdx];
      line.style.animationDelay = '0s';
      self.el.appendChild(line);
      lineIdx++;
      setTimeout(typeLine, 120 + Math.random() * 80);
    }
    typeLine();
  }
}
```

- [ ] **Step 3: Add The Number controller**

```javascript
class NumberDisplay {
  constructor(el) {
    this.el = el;
  }

  show(number) {
    var self = this;
    var n = number || Math.floor(100000000 + Math.random() * 900000000);
    this.el.textContent = n;
    this.el.style.display = 'block';
    this.el.style.animation = 'none';
    void this.el.offsetWidth; // reflow
    this.el.style.animation = 'number-appear 4s ease-out forwards';
    clearTimeout(this._hideTimer);
    this._hideTimer = setTimeout(function() { self.el.style.display = 'none'; }, 4200);
  }
}
```

- [ ] **Step 4: Add Surveillance Frame controller**

```javascript
class SurveillanceFrame {
  constructor(containerEl) {
    this.el = containerEl;
    this.active = false;
  }

  show() {
    this.el.classList.add('active');
    this.active = true;
  }

  hide() {
    this.el.classList.remove('active');
    this.active = false;
  }
}
```

- [ ] **Step 5: Wire everything up in `init()`**

After existing init code, add:
```javascript
// Boot sequence
var bootEl = document.getElementById('boot-sequence');
if (bootEl) {
  var boot = new BootSequence(bootEl);
  boot.start(function() {
    // After boot completes, start digital rain
    var rainCanvas = document.getElementById('digital-rain');
    if (rainCanvas) {
      var rain = new DigitalRain(rainCanvas);
      rain.start();
      window.__digitalRain = rain;
    }
  });
}

// The Number
var numberEl = document.getElementById('the-number');
if (numberEl) window.__numberDisplay = new NumberDisplay(numberEl);

// Surveillance frame
var frameEl = document.getElementById('surveillance-frame');
if (frameEl) window.__surveillanceFrame = new SurveillanceFrame(frameEl);

// Show surveillance frame on monitor view enter
var origEnter = enterMonitorView;
enterMonitorView = function() {
  origEnter();
  if (window.__surveillanceFrame) window.__surveillanceFrame.show();
};

var origExit = exitMonitorView;
exitMonitorView = function() {
  origExit();
  if (window.__surveillanceFrame) window.__surveillanceFrame.hide();
};

// Trigger The Number periodically for demo (remove when real events come)
setInterval(function() {
  if (window.__numberDisplay && !document.getElementById('layer-core').classList.contains('hidden')) {
    window.__numberDisplay.show();
  }
}, 30000);
```

---

### Task 5: index.html — Module Scripts + New Component HTML

**Files:**
- Modify: `app/static/index.html`

**Interfaces:**
- Consumes: CSS classes from style.css, JS classes from app.js
- Produces: DOM elements consumed by controllers in app.js

- [ ] **Step 1: Replace bundled script tags with ES module**

Remove:
```html
<script src="js/bundled_voice.js?v=99"></script>
<script src="js/bundled_particle-core.js?v=99"></script>
<script src="js/bundled_timeline.js?v=99"></script>
<script src="js/bundled_data.js?v=99"></script>
<script src="js/bundled_app.js?v=99"></script>
```

Add:
```html
<script type="module" src="js/app.js?v=101"></script>
```

- [ ] **Step 2: Add boot sequence overlay after body opening**

```html
<div id="boot-sequence"></div>
```

- [ ] **Step 3: Add digital rain canvas after three-container**

```html
<canvas id="digital-rain"></canvas>
```

- [ ] **Step 4: Add The Number element after core-title**

```html
<div id="the-number"></div>
```

- [ ] **Step 5: Add surveillance frame inside layer-monitor**

```html
<div id="surveillance-frame">
  <div class="corner-bracket tl"></div>
  <div class="corner-bracket tr"></div>
  <div class="corner-bracket bl"></div>
  <div class="corner-bracket br"></div>
</div>
```

- [ ] **Step 6: Update favicon to green theme**

Change favicon to green machine icon.

