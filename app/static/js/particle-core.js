 import * as THREE from 'three';
 
export class ParticleCore {



   constructor(container) {
     this.container = container;
     this.state = 'idle';
     this.clock = new THREE.Clock();
     this.elapsedTime = 0;
 
     // Scene
     this.scene = new THREE.Scene();
 
     // Camera
     const aspect = container.clientWidth / container.clientHeight;
     this.camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);
     this.camera.position.z = 8;
 
     // Renderer
     this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
     this.renderer.setSize(container.clientWidth, container.clientHeight);
     this.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
     container.appendChild(this.renderer.domElement);
 
     // Background stars
     this._createStars();
 
     // Main particle sphere
     this._createParticleSphere();
 
     // Orbit rings with moving dots
     this._createOrbitRings();
 
      // Core Light — represents AI consciousness
      const coreLightGeo = new THREE.SphereGeometry(0.8, 16, 16);
      const coreLightMat = new THREE.MeshBasicMaterial({
        color: '#67B8FF',
        transparent: true,
        opacity: 0.15,
      });
      this.coreLight = new THREE.Mesh(coreLightGeo, coreLightMat);
      this.scene.add(this.coreLight);
 
      // Resize handler
      this._bindResize();
 
     // Start animation loop
     this.animate();
 
     // Notify the application that the core is ready
     window.dispatchEvent(new CustomEvent('core:ready', { detail: { core: this } }));
   }
 
   _createStars() {
     const count = 500;
     const positions = new Float32Array(count * 3);
     for (let i = 0; i < count * 3; i++) {
       positions[i] = (Math.random() - 0.5) * 80;
     }
     const geometry = new THREE.BufferGeometry();
     geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
     this.starMaterial = new THREE.PointsMaterial({
       color: '#EAF4FF',
       size: 0.02,
       opacity: 0.06,
       transparent: true,
       blending: THREE.AdditiveBlending,
       depthWrite: false
     });
     this.starPoints = new THREE.Points(geometry, this.starMaterial);
     this.scene.add(this.starPoints);
   }
 
   _createParticleSphere() {
     const count = 1800;
     const positions = new Float32Array(count * 3);
     const colors = new Float32Array(count * 3);
     const innerColor = new THREE.Color('#67B8FF');
     const outerColor = new THREE.Color('#3F89D7');
 
     let minR = Infinity;
     let maxR = -Infinity;
     const radii = [];
 
     // Generate points on a sphere with radius 2.5 ± 0.5
     for (let i = 0; i < count; i++) {
       const theta = Math.random() * Math.PI * 2;
       const phi = Math.acos(2 * Math.random() - 1);
       const r = 2.5 + (Math.random() - 0.5) * 1.0;
       radii.push(r);
       if (r < minR) minR = r;
       if (r > maxR) maxR = r;
 
       positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
       positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
       positions[i * 3 + 2] = r * Math.cos(phi);
     }
 
     // Assign vertex colors: inner (#67B8FF) to outer (#3F89D7) gradient
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
       size: 0.04,
       vertexColors: true,
       transparent: true,
       opacity: 0.8,
       blending: THREE.AdditiveBlending,
       depthWrite: false
     });
 
     this.spherePoints = new THREE.Points(geometry, this.particleMaterial);
     this.scene.add(this.spherePoints);
     this.particlePositions = geometry.attributes.position;
   }
 
   _createOrbitRings() {
     this.rings = [];
     const ringRadii = [3.2, 3.4, 3.6];
     const tilts = [
       { x: 0.3, y: 0.1 },
       { x: -0.2, y: 0.4 },
       { x: 0.5, y: -0.2 }
     ];
 
     for (let i = 0; i < 3; i++) {
       const radius = ringRadii[i];
       const group = new THREE.Group();
 
       // Thin ring mesh
       const ringGeo = new THREE.RingGeometry(radius - 0.02, radius + 0.02, 64);
       const ringMat = new THREE.MeshBasicMaterial({
         color: '#67B8FF',
         opacity: 0.08,
         transparent: true,
         side: THREE.DoubleSide
       });
       const ringMesh = new THREE.Mesh(ringGeo, ringMat);
       group.add(ringMesh);
 
       // Moving dots on this ring
       const numDots = 6 + Math.floor(Math.random() * 5);
       const dotAngles = [];
       const dotPositions = new Float32Array(numDots * 3);
 
       for (let j = 0; j < numDots; j++) {
         const angle = Math.random() * Math.PI * 2;
         dotAngles.push(angle);
         dotPositions[j * 3] = radius * Math.cos(angle);
         dotPositions[j * 3 + 1] = radius * Math.sin(angle);
         dotPositions[j * 3 + 2] = 0;
       }
 
       const dotGeo = new THREE.BufferGeometry();
       dotGeo.setAttribute('position', new THREE.BufferAttribute(dotPositions, 3));
       const dotMat = new THREE.PointsMaterial({
         color: '#67B8FF',
         size: 0.03,
         transparent: true,
         opacity: 0.6,
         blending: THREE.AdditiveBlending,
         depthWrite: false
       });
       const dotPoints = new THREE.Points(dotGeo, dotMat);
       group.add(dotPoints);
 
       // Apply unique tilt
       group.rotation.x = tilts[i].x;
       group.rotation.y = tilts[i].y;
 
       this.scene.add(group);
 
       this.rings.push({
         group,
         radius,
         numDots,
         dotAngles,
         dotGeo,
         dotPositions,
         speed: 0.1 + i * 0.05
       });
     }
   }
 
   _bindResize() {
     this.resizeHandler = () => {
       const w = this.container.clientWidth;
       const h = this.container.clientHeight;
       this.camera.aspect = w / h;
       this.camera.updateProjectionMatrix();
       this.renderer.setSize(w, h);
     };
     window.addEventListener('resize', this.resizeHandler);
   }
 
   setState(state) {
    if (['idle', 'listening', 'thinking', 'analyzing', 'speaking', 'answering', 'sleeping'].includes(state)) {
       this.state = state;
     }
   }
 
   animate() {
     requestAnimationFrame(() => this.animate());
 
     const dt = this.clock.getDelta();
    this._dt = dt;
     this.elapsedTime += dt;
     const t = this.elapsedTime;
 
 
     switch (this.state) {
       case 'idle': this._animateIdle(t); break;
       case 'listening': this._animateListening(t); break;
       case 'thinking':
       case 'analyzing': this._animateThinking(t); break;
       case 'speaking':
       case 'answering': this._animateSpeaking(t); break;
       case 'sleeping': this._animateSleeping(t); break;
     }
     this.particlePositions.needsUpdate = true;
 
     // Advance orbit dots
     for (const ring of this.rings) {
       for (let j = 0; j < ring.numDots; j++) {
         ring.dotAngles[j] += dt * ring.speed;
         const angle = ring.dotAngles[j];
         ring.dotPositions[j * 3] = ring.radius * Math.cos(angle);
         ring.dotPositions[j * 3 + 1] = ring.radius * Math.sin(angle);
         ring.dotPositions[j * 3 + 2] = 0;
       }
       ring.dotGeo.attributes.position.needsUpdate = true;
     }
 
     // Animate star twinkle
     this.starMaterial.opacity = 0.06 + Math.sin(t * 0.3) * 0.03;
 
     this.renderer.render(this.scene, this.camera);
   }

   _animateIdle(t) {
     const positions = this.particlePositions.array;
     const count = this.particleCount;
     const scale = 1 + Math.sin(t * 0.5) * 0.03;
     for (let i = 0; i < count; i++) {
       const i3 = i * 3;
       positions[i3] = this.originalPositions[i3] * scale;
       positions[i3 + 1] = this.originalPositions[i3 + 1] * scale;
       positions[i3 + 2] = this.originalPositions[i3 + 2] * scale;
     }
     this.particleMaterial.opacity = 0.7 + Math.sin(t * 1.5) * 0.1;
     this.spherePoints.rotation.y = t * 0.1;
     if (this.coreLight) this.coreLight.material.opacity = 0.15;
   }

   _animateListening(t) {
     const positions = this.particlePositions.array;
     const count = this.particleCount;
     const baseScale = 1.3;
     for (let i = 0; i < count; i++) {
       const i3 = i * 3;
       const wave = Math.sin(t * 4 + i * 0.01) * 0.1;
       const factor = baseScale + wave;
       positions[i3] = this.originalPositions[i3] * factor;
       positions[i3 + 1] = this.originalPositions[i3 + 1] * factor;
       positions[i3 + 2] = this.originalPositions[i3 + 2] * factor;
     }
     this.particleMaterial.opacity = 0.9 + Math.sin(t * 3) * 0.05;
     this.spherePoints.rotation.y += 0.02;
     if (this.coreLight) this.coreLight.material.opacity = 0.6;
   }

   _animateAnalyzing(t) {
     const positions = this.particlePositions.array;
     const count = this.particleCount;
     for (let i = 0; i < count; i++) {
       const i3 = i * 3;
       const dist = Math.sqrt(
         this.originalPositions[i3] ** 2 +
         this.originalPositions[i3 + 1] ** 2 +
         this.originalPositions[i3 + 2] ** 2
       );
       const ripple = Math.sin(t * 2 - dist * 3) * 0.08;
       const factor = 1 + ripple;
       positions[i3] = this.originalPositions[i3] * factor;
       positions[i3 + 1] = this.originalPositions[i3 + 1] * factor;
       positions[i3 + 2] = this.originalPositions[i3 + 2] * factor;
     }
     this.particleMaterial.opacity = 0.8;
   }

   _animateAnswering(t) {
     const positions = this.particlePositions.array;
     const count = this.particleCount;
     for (let i = 0; i < count; i++) {
       const i3 = i * 3;
       positions[i3] += (this.originalPositions[i3] - positions[i3]) * 0.02;
       positions[i3 + 1] += (this.originalPositions[i3 + 1] - positions[i3 + 1]) * 0.02;
       positions[i3 + 2] += (this.originalPositions[i3 + 2] - positions[i3 + 2]) * 0.02;
     }
     this.particleMaterial.opacity = 0.75 + Math.sin(t * 2) * 0.05;
   }
   _animateThinking(t) {
     const pos = this.particlePositions.array;
     const orig = this.originalPositions;
     for (let i = 0; i < this.particleCount; i++) {
       const i3 = i * 3;
       const dist = Math.sqrt(orig[i3]**2 + orig[i3+1]**2 + orig[i3+2]**2);
       const swirl = Math.sin(t * 3 + i * 0.05) * 0.18;
       const ripple = Math.sin(t * 4 - dist * 3) * 0.1;
       pos[i3]   = orig[i3] * (1 + ripple) + swirl;
       pos[i3+1] = orig[i3+1] * (1 + ripple) + Math.cos(t * 3 + i * 0.05) * 0.18;
       pos[i3+2] = orig[i3+2] * (1 + ripple);
     }
     this.particlePositions.needsUpdate = true;
     this.particleMaterial.opacity = 0.85 + Math.sin(t * 5) * 0.1;
     this.spherePoints.rotation.y = t * 2.5;
     if (this.coreLight) {
       this.coreLight.material.opacity = 0.25 + Math.sin(t * 4) * 0.35;
     }
   }

   _animateSpeaking(t) {
     const pos = this.particlePositions.array;
     const orig = this.originalPositions;
     for (let i = 0; i < this.particleCount; i++) {
       const i3 = i * 3;
       const dist = Math.sqrt(orig[i3]**2 + orig[i3+1]**2 + orig[i3+2]**2);
       const wave = Math.sin(t * 1.2 - dist * 1.5) * 0.05 / (1 + dist * 0.3);
       pos[i3]   += (orig[i3] * (1 + wave) - pos[i3]) * 0.03;
       pos[i3+1] += (orig[i3+1] * (1 + wave) - pos[i3+1]) * 0.03;
       pos[i3+2] += (orig[i3+2] * (1 + wave) - pos[i3+2]) * 0.03;
     }
     this.particlePositions.needsUpdate = true;
     this.particleMaterial.opacity = 0.78;
     this.spherePoints.rotation.y = t * 0.2;
     if (this.coreLight) {
       this.coreLight.material.opacity = 0.5 + Math.sin(t * 0.4) * 0.12;
     }
   }

   _animateSleeping(t) {
     const pos = this.particlePositions.array;
     const orig = this.originalPositions;
     this.particleMaterial.opacity = 0.3;
     for (let i = 0; i < this.particleCount; i++) {
       const i3 = i * 3;
       pos[i3] += (orig[i3] - pos[i3]) * 0.005;
       pos[i3 + 1] += (orig[i3 + 1] - pos[i3 + 1]) * 0.005;
       pos[i3 + 2] += (orig[i3 + 2] - pos[i3 + 2]) * 0.005;
     }
     this.particlePositions.needsUpdate = true;
     if (this.coreLight) {
       this.coreLight.material.opacity = 0.05;
     }
   }
 }
