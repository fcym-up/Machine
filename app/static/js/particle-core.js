import * as THREE from 'three';

export class ParticleCore {
  constructor(container) {
    this.container = container;
    this.state = 'idle';
    this.clock = new THREE.Clock();
    this.elapsedTime = 0;
    this._glitchTimer = 0;

    // Scene with dark green tint
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x050805);

    // Camera
    const aspect = container.clientWidth / container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(55, aspect, 0.1, 1000);
    this.camera.position.z = 7;

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
    this.renderer.setClearColor(0x050805, 0);
    container.appendChild(this.renderer.domElement);

    // Build the Machine visual
    this._createStars();
    this._createParticleSphere();
    this._createNeuralConnections();
    this._createOrbitRings();
    this._createCoreGlow();
    this._createDataStreams();
    this._createScanRings();
    this._createRadarArc();
    this._createScanBeam();

    this._bindResize();
    this.animate();

    window.dispatchEvent(new CustomEvent('core:ready', { detail: { core: this } }));
  }

  _createStars() {
    const count = 1500;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i++) {
      positions[i] = (Math.random() - 0.5) * 100;
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    this.starMaterial = new THREE.PointsMaterial({
      color: '#00FF41',
      size: 0.015,
      opacity: 0.03,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });
    this.starPoints = new THREE.Points(geometry, this.starMaterial);
    this.scene.add(this.starPoints);
  }

  _createParticleSphere() {
    const count = 2500;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const innerColor = new THREE.Color('#33FF66');
    const outerColor = new THREE.Color('#004D14');

    const radii = [];
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 2.2 + (Math.random() - 0.5) * 1.6;
      radii.push(r);
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
    }

    let minR = Infinity, maxR = -Infinity;
    for (const r of radii) { if (r < minR) minR = r; if (r > maxR) maxR = r; }
    for (let i = 0; i < count; i++) {
      const t = (radii[i] - minR) / (maxR - minR);
      const color = innerColor.clone().lerp(outerColor, t);
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }

    this.originalPositions = new Float32Array(positions);
    this.particleCount = count;

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    this.particleMaterial = new THREE.PointsMaterial({
      size: 0.035,
      vertexColors: true,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true
    });

    this.spherePoints = new THREE.Points(geometry, this.particleMaterial);
    this.scene.add(this.spherePoints);
    this.particlePositions = geometry.attributes.position;
  }

  _createNeuralConnections() {
    // Thin neural lines forming a loose network inside the sphere
    const nodeCount = 60;
    const nodes = [];
    for (let i = 0; i < nodeCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 0.5 + Math.random() * 2.5;
      nodes.push({
        x: r * Math.sin(phi) * Math.cos(theta),
        y: r * Math.sin(phi) * Math.sin(theta),
        z: r * Math.cos(phi)
      });
    }

    const positions = [];
    let count = 0;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dz = nodes[i].z - nodes[j].z;
        const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
        if (dist < 2.0 && Math.random() < 0.12) {
          positions.push(nodes[i].x, nodes[i].y, nodes[i].z,
                         nodes[j].x, nodes[j].y, nodes[j].z);
          count++;
        }
      }
    }

    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(positions), 3));
    this.neuralMat = new THREE.LineBasicMaterial({
      color: '#00FF41',
      transparent: true,
      opacity: Math.min(count * 0.003, 0.06),
      blending: THREE.AdditiveBlending
    });
    this.neuralLines = new THREE.LineSegments(geom, this.neuralMat);
    this.scene.add(this.neuralLines);
  }

  _createOrbitRings() {
    this.rings = [];
    const ringConfigs = [
      { radius: 3.0, tiltX: 0.2, tiltY: 0.1, speed: 0.08, dots: 8, opacity: 0.06 },
      { radius: 3.4, tiltX: -0.3, tiltY: 0.3, speed: 0.12, dots: 10, opacity: 0.05 },
      { radius: 3.8, tiltX: 0.5, tiltY: -0.15, speed: 0.15, dots: 6, opacity: 0.04 }
    ];

    for (const cfg of ringConfigs) {
      const group = new THREE.Group();

      // Ring line
      const rGeo = new THREE.BufferGeometry();
      const rPts = [];
      for (let i = 0; i <= 64; i++) {
        const a = (i / 64) * Math.PI * 2;
        rPts.push(Math.cos(a) * cfg.radius, Math.sin(a) * cfg.radius, 0);
      }
      rGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(rPts), 3));
      const rMat = new THREE.LineBasicMaterial({
        color: '#00FF41',
        transparent: true,
        opacity: cfg.opacity,
        blending: THREE.AdditiveBlending
      });
      const ringLine = new THREE.Line(rGeo, rMat);
      group.add(ringLine);

      // Moving dots
      const numDots = cfg.dots;
      const dPositions = new Float32Array(numDots * 3);
      const dAngles = [];
      for (let j = 0; j < numDots; j++) {
        const angle = Math.random() * Math.PI * 2;
        dAngles.push(angle);
        dPositions[j * 3] = cfg.radius * Math.cos(angle);
        dPositions[j * 3 + 1] = cfg.radius * Math.sin(angle);
        dPositions[j * 3 + 2] = 0;
      }
      const dGeo = new THREE.BufferGeometry();
      dGeo.setAttribute('position', new THREE.BufferAttribute(dPositions, 3));
      const dMat = new THREE.PointsMaterial({
        color: '#00FF41',
        size: 0.04,
        transparent: true,
        opacity: 0.7,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      });
      const dPoints = new THREE.Points(dGeo, dMat);
      group.add(dPoints);

      group.rotation.x = cfg.tiltX;
      group.rotation.y = cfg.tiltY;

      this.scene.add(group);
      this.rings.push({
        group, radius: cfg.radius, numDots, dAngles, dGeo, dPositions: dPositions,
        speed: cfg.speed
      });
    }
  }

  _createCoreGlow() {
    // Inner bright core
    const innerGeo = new THREE.SphereGeometry(0.5, 16, 16);
    this.coreInner = new THREE.Mesh(innerGeo, new THREE.MeshBasicMaterial({
      color: '#33FF66',
      transparent: true,
      opacity: 0.15,
      blending: THREE.AdditiveBlending
    }));
    this.scene.add(this.coreInner);

    // Mid glow
    const midGeo = new THREE.SphereGeometry(1.0, 16, 16);
    this.coreMid = new THREE.Mesh(midGeo, new THREE.MeshBasicMaterial({
      color: '#00FF41',
      transparent: true,
      opacity: 0.06,
      blending: THREE.AdditiveBlending
    }));
    this.scene.add(this.coreMid);

    // Outer bloom
    const outerGeo = new THREE.SphereGeometry(1.8, 16, 16);
    this.coreOuter = new THREE.Mesh(outerGeo, new THREE.MeshBasicMaterial({
      color: '#004D14',
      transparent: true,
      opacity: 0.025,
      blending: THREE.AdditiveBlending
    }));
    this.scene.add(this.coreOuter);
  }

  _createDataStreams() {
    // Lines radiating outward like the Machine's data streams
    const count = 40;
    const positions = [];
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r1 = 1.5 + Math.random() * 1.0;
      const r2 = 3.5 + Math.random() * 1.5;
      const x1 = r1 * Math.sin(phi) * Math.cos(theta);
      const y1 = r1 * Math.sin(phi) * Math.sin(theta);
      const z1 = r1 * Math.cos(phi);
      const x2 = r2 * Math.sin(phi) * Math.cos(theta);
      const y2 = r2 * Math.sin(phi) * Math.sin(theta);
      const z2 = r2 * Math.cos(phi);
      positions.push(x1, y1, z1, x2, y2, z2);
    }
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(positions), 3));
    this.streamMat = new THREE.LineBasicMaterial({
      color: '#00FF41',
      transparent: true,
      opacity: 0.03,
      blending: THREE.AdditiveBlending
    });
    this.streamLines = new THREE.LineSegments(geom, this.streamMat);
    this.scene.add(this.streamLines);
  }

  _createScanRings() {
    // Rotating scan rings like the Machine's surveillance analysis
    const ring1 = new THREE.RingGeometry(0.8, 3.8, 64);
    this.scanRing1 = new THREE.Mesh(ring1, new THREE.MeshBasicMaterial({
      color: '#00FF41',
      transparent: true,
      opacity: 0.03,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    }));
    this.scanRing1.rotation.x = Math.PI * 0.4;
    this.scene.add(this.scanRing1);

    const ring2 = new THREE.RingGeometry(0.6, 4.0, 64);
    this.scanRing2 = new THREE.Mesh(ring2, new THREE.MeshBasicMaterial({
      color: '#004D14',
      transparent: true,
      opacity: 0.02,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    }));
    this.scanRing2.rotation.x = -Math.PI * 0.25;
    this.scene.add(this.scanRing2);
  }

  _createRadarArc() {
    // A thin sweeping radar wedge (like the Machine's POV scan)
    const geom = new THREE.RingGeometry(2.0, 4.5, 48, 1, 0, Math.PI * 0.25);
    this.radarArc = new THREE.Mesh(geom, new THREE.MeshBasicMaterial({
      color: '#00FF41',
      transparent: true,
      opacity: 0.02,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    }));
    this.radarArc.rotation.x = Math.PI * 0.5;
    this.scene.add(this.radarArc);
  }

  _createScanBeam() {
    const geom = new THREE.RingGeometry(0.01, 0.2, 48);
    this.scanBeam = new THREE.Mesh(geom, new THREE.MeshBasicMaterial({
        color: '#00FF41',
        transparent: true,
        opacity: 0,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending,
        depthWrite: false
    }));
    this.scanBeam.rotation.x = Math.PI * 0.5;
    this.scene.add(this.scanBeam);
    this._scanBeamTime = 0;
  }

  _bindResize() {
    this._resizeHandler = () => {
      const w = this.container.clientWidth;
      const h = this.container.clientHeight;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h);
    };
    window.addEventListener('resize', this._resizeHandler);
  }

  setState(state) {
    const valid = ['idle', 'listening', 'thinking', 'analyzing', 'speaking', 'answering', 'sleeping'];
    if (valid.includes(state)) {
      this.state = state;
    }
  }

  triggerGlitch() {
    this._glitchTimer = 0.5;
    const title = document.getElementById('core-title');
    if (title) title.classList.add('glitch');
    setTimeout(() => {
      if (title) title.classList.remove('glitch');
    }, 600);
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    const dt = this.clock.getDelta();
    this.elapsedTime += dt;
    const t = this.elapsedTime;

    // State-driven animation
    switch (this.state) {
      case 'idle':      this._animateIdle(t, dt); break;
      case 'listening': this._animateListening(t, dt); break;
      case 'thinking':
      case 'analyzing': this._animateThinking(t, dt); break;
      case 'speaking':
      case 'answering': this._animateSpeaking(t, dt); break;
      case 'sleeping':  this._animateSleeping(t, dt); break;
    }
    this.particlePositions.needsUpdate = true;

    // Orbit dots
    for (const ring of this.rings) {
      for (let j = 0; j < ring.numDots; j++) {
        ring.dAngles[j] += dt * ring.speed;
        const angle = ring.dAngles[j];
        ring.dPositions[j * 3] = ring.radius * Math.cos(angle);
        ring.dPositions[j * 3 + 1] = ring.radius * Math.sin(angle);
        ring.dPositions[j * 3 + 2] = 0;
      }
      ring.dGeo.attributes.position.needsUpdate = true;
    }

    // Neural lines slow rotation
    if (this.neuralLines) this.neuralLines.rotation.y += dt * 0.03;

    // Data streams rotation
    if (this.streamLines) {
      this.streamLines.rotation.y += dt * 0.05;
      this.streamMat.opacity = 0.02 + Math.sin(t * 0.5) * 0.015;
    }

    // Scan rings
    if (this.scanRing1) {
      const targetOpacity = this.state === 'thinking' || this.state === 'analyzing' ? 0.08 : 0.03;
      this.scanRing1.material.opacity += (targetOpacity - this.scanRing1.material.opacity) * 0.05;
      this.scanRing1.rotation.z += dt * 0.3;
      this.scanRing1.scale.setScalar(1 + Math.sin(t * 1.5) * 0.02);

      this.scanRing2.material.opacity += (targetOpacity * 0.6 - this.scanRing2.material.opacity) * 0.05;
      this.scanRing2.rotation.z -= dt * 0.25;
      this.scanRing2.scale.setScalar(1 + Math.cos(t * 2.0) * 0.02);
    }

    // Radar arc
    if (this.radarArc) {
      this.radarArc.rotation.z += dt * 0.6;
      const sweepOpacity = this.state === 'listening' ? 0.04 : 0.02;
      this.radarArc.material.opacity += (sweepOpacity - this.radarArc.material.opacity) * 0.05;
    }

    // Star twinkle
    this.starMaterial.opacity = 0.03 + Math.sin(t * 0.2) * 0.015;

    // Occasional glitch
    if (this._glitchTimer > 0) {
      this._glitchTimer -= dt;
      if (Math.random() < 0.3) {
        this.particleMaterial.opacity = 0.3 + Math.random() * 0.4;
      }
    }

    // Scan beam pulse
    if (this.scanBeam) {
      this._scanBeamTime += dt;
      const cycle = 3.0;
      const t = (this._scanBeamTime % cycle) / cycle;
      const scale = 0.3 + t * 4.7;
      this.scanBeam.scale.setScalar(scale);
      this.scanBeam.material.opacity = Math.sin(t * Math.PI) * 0.35;
      this.scanBeam.rotation.z += dt * 0.25;
    }

    this.renderer.render(this.scene, this.camera);
  }

  _animateIdle(t, dt) {
    const pos = this.particlePositions.array;
    const orig = this.originalPositions;
    const scale = 1 + Math.sin(t * 0.4) * 0.025;
    for (let i = 0; i < this.particleCount; i++) {
      const i3 = i * 3;
      pos[i3] = orig[i3] * scale;
      pos[i3+1] = orig[i3+1] * scale;
      pos[i3+2] = orig[i3+2] * scale;
    }
    this.particleMaterial.opacity = 0.65 + Math.sin(t * 1.0) * 0.08;
    this.spherePoints.rotation.y = t * 0.05;

    this.coreInner.material.opacity = 0.12 + Math.sin(t * 0.7) * 0.04;
    this.coreMid.material.opacity = 0.05 + Math.sin(t * 1.0) * 0.02;
    this.coreOuter.material.opacity = 0.02 + Math.sin(t * 0.5) * 0.008;
  }

  _animateListening(t, dt) {
    const pos = this.particlePositions.array;
    const orig = this.originalPositions;
    const baseScale = 1.25;
    for (let i = 0; i < this.particleCount; i++) {
      const i3 = i * 3;
      const wave = Math.sin(t * 4 + i * 0.008) * 0.1;
      const factor = baseScale + wave;
      pos[i3] = orig[i3] * factor;
      pos[i3+1] = orig[i3+1] * factor;
      pos[i3+2] = orig[i3+2] * factor;
    }
    this.particleMaterial.opacity = 0.8 + Math.sin(t * 3) * 0.06;
    this.spherePoints.rotation.y += 0.012;

    this.coreInner.material.opacity = 0.3 + Math.sin(t * 5) * 0.1;
    this.coreMid.material.opacity = 0.1 + Math.sin(t * 3) * 0.04;
    this.coreOuter.material.opacity = 0.035 + Math.sin(t * 2) * 0.015;
  }

  _animateThinking(t, dt) {
    const pos = this.particlePositions.array;
    const orig = this.originalPositions;
    for (let i = 0; i < this.particleCount; i++) {
      const i3 = i * 3;
      const dist = Math.sqrt(orig[i3]**2 + orig[i3+1]**2 + orig[i3+2]**2);
      const swirl = Math.sin(t * 3 + i * 0.04) * 0.22;
      const ripple = Math.sin(t * 4 - dist * 3) * 0.12;
      pos[i3] = orig[i3] * (1 + ripple) + swirl;
      pos[i3+1] = orig[i3+1] * (1 + ripple) + Math.cos(t * 3 + i * 0.04) * 0.22;
      pos[i3+2] = orig[i3+2] * (1 + ripple);
    }
    this.particleMaterial.opacity = 0.75 + Math.sin(t * 5) * 0.1;
    this.spherePoints.rotation.y = t * 2.0;

    this.coreInner.material.opacity = 0.15 + Math.sin(t * 4) * 0.25;
    this.coreMid.material.opacity = 0.06 + Math.sin(t * 3) * 0.04;
    this.coreOuter.material.opacity = 0.025 + Math.sin(t * 3) * 0.015;

    // Glitch effect during thinking
    if (Math.sin(t * 7) > 0.95 && this._glitchTimer <= 0) {
      this._glitchTimer = 0.1;
    }
  }

  _animateSpeaking(t, dt) {
    const pos = this.particlePositions.array;
    const orig = this.originalPositions;
    for (let i = 0; i < this.particleCount; i++) {
      const i3 = i * 3;
      const dist = Math.sqrt(orig[i3]**2 + orig[i3+1]**2 + orig[i3+2]**2);
      const wave = Math.sin(t * 1.2 - dist * 1.5) * 0.04 / (1 + dist * 0.3);
      pos[i3] += (orig[i3] * (1 + wave) - pos[i3]) * 0.03;
      pos[i3+1] += (orig[i3+1] * (1 + wave) - pos[i3+1]) * 0.03;
      pos[i3+2] += (orig[i3+2] * (1 + wave) - pos[i3+2]) * 0.03;
    }
    this.particleMaterial.opacity = 0.7;
    this.spherePoints.rotation.y = t * 0.15;

    this.coreInner.material.opacity = 0.3 + Math.sin(t * 0.4) * 0.1;
    this.coreMid.material.opacity = 0.08 + Math.sin(t * 0.6) * 0.025;
    this.coreOuter.material.opacity = 0.03 + Math.sin(t * 0.5) * 0.01;
  }

  _animateSleeping(t, dt) {
    const pos = this.particlePositions.array;
    const orig = this.originalPositions;
    this.particleMaterial.opacity = 0.2;
    for (let i = 0; i < this.particleCount; i++) {
      const i3 = i * 3;
      pos[i3] += (orig[i3] - pos[i3]) * 0.005;
      pos[i3+1] += (orig[i3+1] - pos[i3+1]) * 0.005;
      pos[i3+2] += (orig[i3+2] - pos[i3+2]) * 0.005;
    }
    if (this.coreInner) this.coreInner.material.opacity = 0.02;
    if (this.coreMid) this.coreMid.material.opacity = 0.01;
    if (this.coreOuter) this.coreOuter.material.opacity = 0.005;
  }
}
