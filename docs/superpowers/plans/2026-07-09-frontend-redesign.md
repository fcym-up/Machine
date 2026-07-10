# Machine Frontend Redesign - Implementation Plan
> For agentic workers: Use subagent-driven-development or executing-plans to implement.
Goal: Redesign Machine frontend to sci-fi AI interface.
Architecture: Vanilla JS + Three.js + Web Speech API + FastAPI.

## Task 1: HTML + CSS Layout
Files: index.html, style.css, animations.css
Three-column Grid layout. Left status panel, center Three.js overlay, right timeline, bottom Dock.
Color: bg #05070A, text #EAF4FF, accent #67B8FF.

## Task 2: Three.js Particle Core
Files: particle-core.js
ParticleCore class. 1800 particles, 3 orbit rings, 500 stars. 4 states: idle/listening/analyzing/answering.
Exposes setState(state). Dispatches core:ready event.

## Task 3: Voice Wake-up
Files: voice.js
VoiceController with Web Speech API continuous mode.
Detect Machine keyword -> onWake callback.
5s silence timeout -> onSilence callback.
onTranscript callback for speech text.
Auto-restart on speech recognition end event.

## Task 4: Timeline + Understanding Panel
Files: timeline.js
Timeline class polling events and think endpoints every 8s.
Uses: GET /api/v1/events/search?limit=30, GET /api/v1/conversation/think
Renders events with entrance animation. Shows understanding data.

## Task 5: Main App Integration
Files: app.js
Initializes all modules. Manages state flow.
Wake -> listening -> analyzing (show context with stagger) -> answering -> back to listening.
POST /api/v1/conversation/chat for AI replies.

## Task 6: Icon Assets
Files: assets/icons.js
Inline Lucide SVGs: mic, eye, brain, database, settings.
Stored as window.MACHINE_ICONS object for easy lookup.

---
## File Structure
```
app/static/
  index.html
  css/style.css
  css/animations.css
  js/particle-core.js
  js/voice.js
  js/timeline.js
  js/app.js
  assets/icons.js
```
