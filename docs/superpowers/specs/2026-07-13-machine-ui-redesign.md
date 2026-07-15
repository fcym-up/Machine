# Machine UI Redesign - POI Cinematic Fusion

## Overview

Transform the existing Machine dashboard from a blue-toned sci-fi UI into the iconic green-terminal aesthetic of Person of Interest's "The Machine", while preserving all existing functionality. The redesign is a reskin + enhancement, not a rewrite.

## Scope

### Files to delete (cleanup)
- app/static/demo.html, e2e-test.html, test-flat.html, test-module.html, test.html
- app/static/js/audio-processor.js
- temp_replace.ps1, weblog.txt
- _build_css.py, _fix_all_bare_html.py, _fix_bare_html.py, _fix_ws_auth.py, _gen_css.py, _rebuild.py, _rebuild_html.py, _rebuild_pipecat.py, _rewrite_fe.py, _test.txt, _test_gen.bat, _wc.py, _write_css.py
- _screenshot.png, _screenshot2.png

### Files to modify
- app/static/index.html
- app/static/css/style.css
- app/static/css/animations.css
- app/static/js/particle-core.js
- app/static/js/app.js

### New code in existing files
- Digital rain Canvas renderer (~80 lines, app.js)
- The Number display controller (~50 lines, app.js)
- Boot sequence controller (~60 lines, app.js)
- Surveillance frame animation (~40 lines, app.js)

## Color Scheme

Background: #000A00 (was #020408)
Accent: #00FF41 phosphor green (was #67B8FF blue)
Text: #B3FFB3 soft green (was #EAF4FF cold white)
Warning: #FFB000 POI orange (was #f59e0b amber)
Critical: #FF0033 intense red (was #EF4444)
Panel bg: rgba(0,10,0,...) black-green (was rgba(6,14,26,...) blue)
Green dim: #00AA22

## UI Components

1. Boot Sequence - green terminal boot log on page load
2. The Number - floating large-digit number on event trigger
3. Digital Rain - full-screen Canvas character fall behind UI
4. Threat Classification - four POI levels: Irrelevant/Monitor/Significant/Critical
5. Surveillance Frame - corner L-brackets in Monitor View
6. Three.js Core - green spectrum, scanning radar ring, 6000 particles

## Non-Goals
- No API or backend changes
- No new JS files or external dependencies
- No removal of existing functionality
