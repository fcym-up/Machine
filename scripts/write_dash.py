import os

html = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>MACHINE · 全息监控面板</title>
<style>
:root {
  --bg-primary: #080a1a;
  --bg-panel: rgba(10, 15, 30, 0.55);
  --accent-primary: #00d4ff;
  --accent-secondary: #4af0ff;
  --accent-warning: #ffb347;
  --accent-danger: #ff4757;
  --accent-success: #00e676;
  --text-primary: #e8f0ff;
  --text-secondary: rgba(200, 220, 255, 0.7);
  --text-dim: rgba(150, 180, 220, 0.35);
  --glow-primary: 0 0 20px rgba(0, 212, 255, 0.25);
  --glow-strong: 0 0 40px rgba(0, 212, 255, 0.4);
  --border-panel: 1px solid rgba(0, 212, 255, 0.15);
  --radius: 6px;
  --font-xs: 11px;
  --font-sm: 13px;
  --font-md: 15px;
  --font-lg: 22px;
  --font-xl: 32px;
  --font-xxl: 48px;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: 'Courier New', 'SF Mono', 'Fira Code', monospace;
  background: var(--bg-primary);
  color: var(--text-primary);
  overflow-x: hidden;
  min-height: 100vh;
}
/* Scanline overlay */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,212,255,0.015) 2px, rgba(0,212,255,0.015) 4px);
  pointer-events: none;
  z-index: 9999;
}
.scanline {
  position: fixed;
  top: -10%;
  left: 0;
  width: 100%;
  height: 8px;
  background: linear-gradient(180deg, transparent, rgba(0,212,255,0.06), transparent);
  animation: scanMove 4s linear infinite;
  pointer-events: none;
  z-index: 9998;
}
@keyframes scanMove { 0% { top: -10%; } 100% { top: 110%; } }
.container { max-width: 1400px; margin: 0 auto; padding: 16px 20px; position: relative; }
/* Header */
header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 0 16px; border-bottom: var(--border-panel); margin-bottom: 16px;
  position: relative;
}
header::after {
  content: ''; position: absolute; bottom: -1px; left: 0; right: 0;
  height: 1px; background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
  animation: headerGlow 3s ease-in-out infinite;
}
@keyframes headerGlow { 0%,100% { opacity: 0.4; } 50% { opacity: 1; } }
header h1 {
  font-size: var(--font-lg); font-weight: 400;
  letter-spacing: 6px; color: var(--accent-primary);
  text-shadow: var(--glow-primary);
}
.header-right { display: flex; align-items: center; gap: 16px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; animation: pulseDot 2s ease-in-out infinite; }
.status-dot.online { background: var(--accent-success); box-shadow: 0 0 8px var(--accent-success); }
.status-dot.offline { background: var(--accent-danger); box-shadow: 0 0 8px var(--accent-danger); }
@keyframes pulseDot { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
.header-time { font-size: var(--font-xs); color: var(--text-dim); letter-spacing: 1px; }
/* Grid */
.grid-main {
  display: grid;
  grid-template-columns: 280px 1fr 340px;
  gap: 12px;
  margin-bottom: 12px;
}
.grid-bottom { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 1100px) {
  .grid-main { grid-template-columns: 1fr 1fr; }
  .grid-main > :nth-child(3) { grid-column: 1 / -1; }
}
@media (max-width: 768px) {
  .grid-main, .grid-bottom { grid-template-columns: 1fr; }
  .container { padding: 10px; }
}
/* Panel base */
.panel {
  background: var(--bg-panel);
  border: var(--border-panel);
  border-radius: var(--radius);
  padding: 14px 16px;
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: border-color 0.3s;
}
.panel::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
  opacity: 0.6;
}
.panel:hover { border-color: rgba(0, 212, 255, 0.35); }
.panel-label {
  font-size: var(--font-xs);
  letter-spacing: 3px;
  color: var(--text-dim);
  margin-bottom: 10px;
  text-transform: uppercase;
}
/* Emotion */
.emotion-icon { font-size: 36px; margin-bottom: 6px; display: inline-block; }
.emotion-value { font-size: var(--font-xl); font-weight: 300; color: var(--accent-primary); text-shadow: var(--glow-primary); }
.emotion-secondary { font-size: var(--font-sm); color: var(--text-secondary); margin-top: 2px; }
.confidence-ring { position: relative; width: 60px; height: 60px; margin: 8px 0; }
.confidence-ring svg { transform: rotate(-90deg); }
.confidence-ring .bg { fill: none; stroke: rgba(0,212,255,0.1); stroke-width: 4; }
.confidence-ring .bar {
  fill: none; stroke: var(--accent-primary); stroke-width: 4;
  stroke-linecap: round; transition: stroke-dashoffset 0.8s ease;
}
.confidence-ring .label {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: var(--font-sm); color: var(--text-secondary);
}
.emotion-factors { margin-top: 8px; }
.factor-item {
  font-size: var(--font-xs); color: var(--text-secondary);
  padding: 3px 8px; margin: 2px 0;
  border-left: 1px solid rgba(0,212,255,0.2);
}
/* Activity */
.activity-bar { margin: 4px 0; display: flex; align-items: center; gap: 8px; font-size: var(--font-sm); }
.activity-bar .label { width: 56px; text-align: right; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.activity-bar .track { flex:1; height: 8px; background: rgba(0,212,255,0.06); border-radius: 4px; overflow: hidden; }
.activity-bar .bar-fill {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}
.activity-bar .bar-fill::after {
  content: ''; position: absolute; right: 0; top: 0; bottom: 0; width: 20px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3));
}
.activity-bar .count { font-size: var(--font-xs); color: var(--text-dim); width: 30px; text-align: right; }
/* Chat */
.chat-panel { display: flex; flex-direction: column; }
.chat-area {
  flex: 1; max-height: 380px; overflow-y: auto;
  margin-bottom: 10px; padding-right: 4px;
  scrollbar-width: thin; scrollbar-color: rgba(0,212,255,0.15) transparent;
}
.chat-area::-webkit-scrollbar { width: 3px; }
.chat-area::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.2); border-radius: 2px; }
.msg { padding: 8px 12px; border-radius: 4px; max-width: 88%; font-size: var(--font-sm); line-height: 1.6; margin: 4px 0; }
.msg-machine { background: rgba(0,212,255,0.06); border-left: 2px solid var(--accent-primary); align-self: flex-start; }
.msg-user { background: rgba(0,212,255,0.1); border-right: 2px solid var(--accent-secondary); align-self: flex-end; text-align: right; }
.msg-typing { border-left-color: var(--text-dim); opacity: 0.7; }
.chat-input-row { display: flex; gap: 8px; align-items: center; border-top: var(--border-panel); padding-top: 10px; }
.chat-input-row input {
  flex: 1; background: rgba(0,212,255,0.04);
  border: var(--border-panel); border-radius: 4px;
  padding: 8px 12px; color: var(--text-primary);
  font-family: inherit; font-size: var(--font-sm);
  outline: none; transition: border-color 0.3s;
}
.chat-input-row input:focus { border-color: var(--accent-primary); }
.chat-input-row input::placeholder { color: var(--text-dim); }
.btn {
  background: transparent; border: var(--border-panel);
  color: var(--text-secondary); padding: 8px 12px;
  border-radius: 4px; cursor: pointer; font-family: inherit;
  font-size: var(--font-sm); transition: all 0.3s;
  display: flex; align-items: center; gap: 4px;
}
.btn:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
.btn-mic { width: 36px; height: 36px; border-radius: 50%; justify-content: center; position: relative; }
.btn-mic.listening { border-color: var(--accent-danger); color: var(--accent-danger); animation: micPulse 1s ease-in-out infinite; }
@keyframes micPulse { 0%,100% { box-shadow: 0 0 0 0 rgba(255,71,87,0); } 50% { box-shadow: 0 0 20px 4px rgba(255,71,87,0.2); } }
.btn-mic .wave { display: none; position: absolute; inset: -4px; border-radius: 50%; border: 1px solid var(--accent-danger); animation: waveExpand 1.2s ease-out infinite; }
.btn-mic.listening .wave { display: block; }
@keyframes waveExpand { 0% { transform: scale(1); opacity: 0.6; } 100% { transform: scale(1.3); opacity: 0; } }
.mic-waves { display: none; position: absolute; bottom: -20px; left: 50%; transform: translateX(-50%); gap: 2px; align-items: flex-end; }
.mic-waves.active { display: flex; }
.mic-waves span { width: 3px; background: var(--accent-danger); border-radius: 2px; animation: waveBar 0.5s ease-in-out infinite; }
.mic-waves span:nth-child(1) { height: 8px; animation-delay: 0s; }
.mic-waves span:nth-child(2) { height: 14px; animation-delay: 0.1s; }
.mic-waves span:nth-child(3) { height: 10px; animation-delay: 0.2s; }
.mic-waves span:nth-child(4) { height: 18px; animation-delay: 0.3s; }
.mic-waves span:nth-child(5) { height: 12px; animation-delay: 0.15s; }
@keyframes waveBar { 0%,100% { opacity: 0.4; } 50% { opacity: 1; } }
/* Digest */
.digest-number { font-size: var(--font-xxl); font-weight: 300; color: var(--accent-primary); text-shadow: var(--glow-primary); line-height: 1; }
.digest-label { font-size: var(--font-xs); color: var(--text-dim); margin-top: 4px; }
.digest-text { font-size: var(--font-xs); color: var(--text-secondary); margin-top: 8px; line-height: 1.5; }
/* Timeline */
.timeline-item { display: flex; gap: 10px; padding: 6px 0; border-bottom: 1px solid rgba(0,212,255,0.04); font-size: var(--font-sm); }
.timeline-time { color: var(--text-dim); width: 50px; flex-shrink: 0; }
.timeline-content { color: var(--text-secondary); flex: 1; }
.timeline-content .cat { color: var(--accent-primary); }
/* Thought */
.thought-item { padding: 8px 12px; margin: 4px 0; border-left: 2px solid var(--accent-secondary); font-size: var(--font-sm); line-height: 1.5; color: var(--text-secondary); }
/* Particles */
.particles-container { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.particle { position: absolute; width: 2px; height: 2px; background: var(--accent-primary); border-radius: 50%; opacity: 0; animation: floatParticle 8s linear infinite; }
@keyframes floatParticle { 0% { transform: translateY(100vh) translateX(0); opacity: 0; } 10% { opacity: 0.6; } 90% { opacity: 0.6; } 100% { transform: translateY(-100px) translateX(80px); opacity: 0; } }
@keyframes rippleOut { 0% { width: 0; height: 0; opacity: 0.6; } 100% { width: 200px; height: 200px; opacity: 0; } }
.tts-toggle { font-size: var(--font-xs); color: var(--text-dim); cursor: pointer; display: flex; align-items: center; gap: 4px; }
.tts-toggle:hover { color: var(--accent-primary); }
.tts-toggle.active { color: var(--accent-success); }
.error { color: var(--accent-danger); font-size: var(--font-sm); padding: 8px; border: 1px solid rgba(255,71,87,0.2); border-radius: 4px; }
.empty { color: var(--text-dim); font-size: var(--font-sm); padding: 12px 0; text-align: center; }
.last-refresh { font-size: var(--font-xs); color: var(--text-dim); margin-top: 6px; }
</style>
</head>
<body>
<div class="scanline"></div>
<div class="particles-container" id="particles"></div>
<div class="container">
  <header>
    <h1>MACHINE</h1>
    <div class="header-right">
      <div class="status-dot online" id="statusDot"></div>
      <span class="header-time" id="headerTime">--:--:--</span>
      <span class="header-time" id="headerStatus">初始化...</span>
    </div>
  </header>
  <div class="grid-main">
    <div class="panel" id="panel-emotion">
      <div class="panel-label">情绪状态</div>
      <div id="emotionRipple">
        <div class="emotion-icon" id="emotionIcon">&#9674;</div>
        <div class="emotion-value" id="emotionPrimary">--</div>
        <div class="emotion-secondary" id="emotionSecondary"></div>
        <div class="confidence-ring">
          <svg width="60" height="60"><circle class="bg" cx="30" cy="30" r="24"/><circle class="bar" id="confidenceBar" cx="30" cy="30" r="24" stroke-dasharray="150.8" stroke-dashoffset="150.8"/></svg>
          <div class="label" id="confidenceLabel">0%</div>
        </div>
        <div class="emotion-factors" id="emotionFactors"></div>
      </div>
    </div>
    <div class="panel" id="panel-activity">
      <div class="panel-label">活动分布</div>
      <div id="activityContent"><div class="empty">加载中...</div></div>
    </div>
    <div class="panel chat-panel" id="panel-chat">
      <div class="panel-label">Machine 会话</div>
      <div class="chat-area" id="chatArea">
        <div class="msg msg-machine">系统就绪 &#183; 等待指令</div>
      </div>
      <div class="chat-input-row">
        <button class="btn btn-mic" id="micBtn" title="语音输入">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="2" width="6" height="11" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="22"/></svg>
          <div class="wave"></div>
        </button>
        <input type="text" id="chatInput" placeholder="输入消息或点击麦克风说话...">
        <button class="btn" onclick="sendMsg()">发送</button>
        <div class="tts-toggle active" id="ttsToggle" onclick="toggleTTS()" title="语音输出">&#x1F50A;</div>
      </div>
      <div class="mic-waves" id="micWaves"><span></span><span></span><span></span><span></span><span></span></div>
    </div>
  </div>
  <div class="grid-bottom">
    <div class="panel" id="panel-digest">
      <div class="panel-label">今日概览</div>
      <div class="digest-number" id="digestNumber">--</div>
      <div class="digest-label">今日事件</div>
      <div class="digest-text" id="digestText">加载中...</div>
    </div>
    <div class="panel" id="panel-timeline">
      <div class="panel-label">时间线</div>
      <div id="timelineContent"><div class="empty">加载中...</div></div>
    </div>
  </div>
  <div style="margin-top:12px;display:flex;justify-content:space-between;font-size:var(--font-xs);color:var(--text-dim);border-top:var(--border-panel);padding-top:10px;">
    <span>STATUS: <span id="footerStatus">初始化</span></span>
    <span>v0.7.0 &#183; MACHINE</span>
  </div>
</div>

<script>
const API = '/api/v1';
const H = { 'X-API-Key': 'machine-dev-key-change-me' };
let ttsEnabled = true;
let recognition = null;

// Particles
(function() {
  const c = document.getElementById('particles');
  for (let i = 0; i < 30; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.left = Math.random() * 100 + '%';
    p.style.animationDelay = Math.random() * 8 + 's';
    p.style.animationDuration = (6 + Math.random() * 6) + 's';
    c.appendChild(p);
  }
})();

// Voice Input
function initSpeech() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { console.log('Speech not supported'); return; }
  recognition = new SR();
  recognition.lang = 'zh-CN';
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.onresult = function(e) {
    let final = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) final += e.results[i][0].transcript;
    }
    if (final) {
      document.getElementById('chatInput').value = final;
      sendMsg();
    }
  };
  recognition.onend = function() {
    const btn = document.getElementById('micBtn');
    btn.classList.remove('listening');
    document.getElementById('micWaves').classList.remove('active');
    document.getElementById('chatInput').placeholder = '输入消息或点击麦克风说话...';
  };
}

function toggleMic() {
  const btn = document.getElementById('micBtn');
  if (btn.classList.contains('listening')) {
    if (recognition) recognition.stop();
    btn.classList.remove('listening');
    document.getElementById('micWaves').classList.remove('active');
    return;
  }
  if (!recognition) initSpeech();
  if (!recognition) return;
  try {
    recognition.start();
    btn.classList.add('listening');
    document.getElementById('micWaves').classList.add('active');
    document.getElementById('chatInput').placeholder = '正在聆听...';
  } catch(e) { console.log('Speech error:', e); }
}

document.getElementById('micBtn').addEventListener('click', toggleMic);

// Voice Output
function toggleTTS() {
  ttsEnabled = !ttsEnabled;
  const el = document.getElementById('ttsToggle');
  el.classList.toggle('active');
  el.textContent = ttsEnabled ? '\uD83D\uDD0A' : '\uD83D\uDD07';
}

function speak(text) {
  if (!ttsEnabled || !window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(text.replace(/<[^>]+>/g, ''));
  u.lang = 'zh-CN';
  u.rate = 1.0;
  u.volume = 0.8;
  window.speechSynthesis.speak(u);
}

// Chat
const EMOTION_ICONS = { '\u7126\u8651': '\u26A0', '\u5F00\u5FC3': '\u263A', '\u9AD8\u5174': '\u263A', '\u7B11': '\u263A', '\u75B2\u60EB': '\u25D0', '\u4E13\u6CE8': '\u25C8', '\u653E\u677E': '\u2601', '\u5E73\u9759': '\u25CB', '\u6CAE\u4E27': '\u2639', '\u597D\u5947': '\u25C7' };

async function fetchWithKey(path) {
  try {
    const r = await fetch(API + path, { headers: H });
    if (!r.ok) return { _error: true, status: r.status };
    return await r.json();
  } catch(e) { return { _error: true }; }
}

function escapeHtml(t) {
  const d = document.createElement('div');
  d.textContent = t;
  return d.innerHTML;
}

async function sendMsg() {
  const input = document.getElementById('chatInput');
  const msg = input.value.trim();
  if (!msg) return;

  const area = document.getElementById('chatArea');
  area.innerHTML += '<div class="msg msg-user">' + escapeHtml(msg) + '</div>';
  input.value = '';

  const typingEl = document.createElement('div');
  typingEl.className = 'msg msg-machine msg-typing';
  typingEl.textContent = '\u25B3 \u6C89\u9ED8...';
  area.appendChild(typingEl);
  area.scrollTop = area.scrollHeight;

  try {
    const r = await fetch(API + '/conversation/chat', {
      method: 'POST',
      headers: { ...H, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    const data = await r.json();
    const replyText = data.reply || '\u6682\u65E0\u56DE\u5E94';
    typingEl.className = 'msg msg-machine';
    typingEl.textContent = '';
    typeWriter(typingEl, replyText, 0);
    speak(replyText);
  } catch(e) {
    typingEl.className = 'msg msg-machine';
    typingEl.textContent = '\u62B1\u6B49\uFF0C\u6211\u6682\u65F6\u65E0\u6CD5\u56DE\u5E94\u3002';
  }
  area.scrollTop = area.scrollHeight;
}

function typeWriter(el, text, i) {
  if (i < text.length) {
    el.textContent += text[i];
    setTimeout(() => typeWriter(el, text, i + 1), 25);
    el.parentElement.scrollTop = el.parentElement.scrollHeight;
  }
}

function animateNumber(el, target) {
  const current = parseInt(el.textContent) || 0;
  if (current === target) return;
  const diff = target - current;
  const steps = Math.min(Math.abs(diff), 30);
  const stepVal = diff / steps;
  let i = 0;
  const timer = setInterval(() => {
    i++;
    el.textContent = Math.round(current + stepVal * i);
    if (i >= steps) {
      el.textContent = target;
      clearInterval(timer);
    }
  }, 30);
}

// Refresh
async function refreshAll() {
  const results = await Promise.all([
    fetchWithKey('/emotion/current'),
    fetchWithKey('/profile/full?days=1'),
    fetchWithKey('/profile/digest'),
    fetchWithKey('/events/timeline?limit=50')
  ]);
  const [emotion, profile, digest, timeline] = results;

  // Emotion
  if (!emotion._error && emotion.primary_emotion) {
    const pe = emotion.primary_emotion;
    document.getElementById('emotionIcon').textContent = EMOTION_ICONS[pe] || '\u25CB';
    document.getElementById('emotionPrimary').textContent = pe;
    document.getElementById('emotionSecondary').textContent = emotion.secondary_emotion ? '\u526F: ' + emotion.secondary_emotion : '';
    const conf = Math.round((emotion.confidence || 0) * 100);
    const circ = 150.8;
    document.getElementById('confidenceBar').style.strokeDashoffset = circ - (circ * conf / 100);
    document.getElementById('confidenceLabel').textContent = conf + '%';
    const factors = document.getElementById('emotionFactors');
    factors.innerHTML = (emotion.factors || []).slice(0, 3).map(f => '<div class="factor-item">' + f + '</div>').join('');
  }

  // Activity
  const ac = document.getElementById('activityContent');
  if (!profile._error && profile.categories) {
    const total = Object.values(profile.categories).reduce((a, b) => a + b, 0);
    const items = Object.entries(profile.categories).sort((a, b) => b[1] - a[1]);
    ac.innerHTML = items.map(([cat, cnt]) => {
      const pct = Math.round(cnt / total * 100);
      return '<div class="activity-bar"><span class="label">' + cat + '</span><div class="track"><div class="bar-fill" style="width:' + pct + '%"></div></div><span class="count">' + cnt + '</span></div>';
    }).join('');
  } else {
    ac.innerHTML = '<div class="empty">暂无数据</div>';
  }

  // Digest
  if (!digest._error) {
    animateNumber(document.getElementById('digestNumber'), digest.total_events || 0);
    document.getElementById('digestText').textContent = digest.summary || '暂无数据';
  }

  // Timeline
  const tc = document.getElementById('timelineContent');
  if (!timeline._error && timeline.timeline && timeline.timeline.length > 0) {
    tc.innerHTML = timeline.timeline.slice(-15).reverse().map(e => {
      const t = e.time || e.created_at || '';
      const timeStr = t ? t.substring(11, 19) : '--:--:--';
      const cat = e.category || e.event_type || 'other';
      const desc = e.description || (e.payload ? e.payload.description : '') || '';
      return '<div class="timeline-item"><span class="timeline-time">' + timeStr + '</span><span class="timeline-content"><span class="cat">[' + cat + ']</span> ' + desc + '</span></div>';
    }).join('');
  } else {
    tc.innerHTML = '<div class="empty">暂无数据</div>';
  }

  // Status
  const now = new Date();
  document.getElementById('headerTime').textContent = now.toLocaleTimeString('zh-CN');
  document.getElementById('headerStatus').textContent = emotion._error ? '离线' : '运行中';
  document.getElementById('footerStatus').textContent = emotion._error ? '离线' : '在线';
  document.getElementById('statusDot').className = 'status-dot ' + (emotion._error ? 'offline' : 'online');
}

// Init
initSpeech();
refreshAll();
setInterval(refreshAll, 20000);
</script>
</body>
</html>
"""

with open("D:/workplace/app/static/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Dashboard written successfully")
