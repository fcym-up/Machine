console.log('[DBG] app.js loaded');
import { ParticleCore } from './particle-core.js';
import { VoiceController } from './voice.js';
import { Timeline } from './timeline.js';

let core;
let voice;
let timeline;

function init() {
  voice = new VoiceController({
    onWake: () => {
      core.setState('listening');
      setTitle('// 等待指令');
      setSubtitle('');
      setHint('');
      clearResponse();
      clearAnalyzing();
      setVoiceStatus('信道开启');
    },
    onSilence: () => {
      core.setState('idle');
      setTitle('Machine');
      setSubtitle('我一直都在。');
      setHint('说 \u201C终端\u201D');
      hideResponse();
      setTimeout(clearAnalyzing, 1000);
      setVoiceStatus('待命');
    },
    onTranscript: (text) => {
      core.setState('thinking');
      core.triggerGlitch();
      setTitle('// 处理输入中');
      setResponse(text);
      setVoiceStatus('分析中');
    },
    onLLMReply: (reply) => {
      core.setState('speaking');
      setTitle('// Machine 回应');
      setResponse(reply);
      showResponse();
      setVoiceStatus('应答中');
    },
    onStateChange: (state) => {
      const labels = {
        idle: '待命',
        listening: '聆听中',
        thinking: '分析中',
        speaking: '应答中',
      };
      setVoiceStatus(labels[state] || state);
    },
    onUnavailable: () => {
      setVoiceStatus('麦克风不可用');
      const h = document.getElementById('core-hint');
      if (h) {
        h.textContent = '麦克风不可用，请在浏览器中授权';
        h.style.animation = 'none';
        h.style.opacity = '0.4';
  _initMachineInterfaces();
      }
    },
  });

  timeline = new Timeline(
    document.getElementById('timeline-list'),
    document.getElementById('understanding-body')
  );
  timeline.startPolling();
  _startObservePolling();
  _initKeyboardShortcuts();
  _initTabTitle();
  _initDock();

  core = new ParticleCore(document.getElementById('three-container'));
}

function setTitle(text) {
  const el = document.getElementById('core-title');
  if (el) {
    el.textContent = text;
    el.classList.add('glitch');
    setTimeout(() => el.classList.remove('glitch'), 400);
  }
}

function setSubtitle(text) {
  const el = document.getElementById('core-subtitle');
  if (el) el.textContent = text;
}

function setHint(text) {
  const el = document.getElementById('core-hint');
  if (el) el.textContent = text;
}

function setResponse(text) {
  const el = document.getElementById('core-response');
  if (el) { el.textContent = text; el.style.opacity = '1'; }
}

function showResponse() {
  const el = document.getElementById('core-response');
  if (el) el.style.opacity = '1';
}

function hideResponse() {
  const el = document.getElementById('core-response');
  if (el) el.style.opacity = '0';
}

function clearResponse() {
  const el = document.getElementById('core-response');
  if (el) { el.textContent = ''; el.style.opacity = '0'; }
}

function clearAnalyzing() {
  const el = document.getElementById('analyzing-list');
  if (el) el.innerHTML = '';
}

function setVoiceStatus(text) {
  const el = document.getElementById('voice-status-text');
  if (el) el.textContent = text;
}

// Dock click handlers
function _initDock() {
  const dock = document.getElementById('dock');
  if (!dock) return;
  dock.addEventListener('click', (e) => {
    const item = e.target.closest('.dock-item');
    if (!item) return;
    document.querySelectorAll('.dock-item').forEach((el) => el.classList.remove('active'));
    item.classList.add('active');
    const view = item.dataset.view;
    // Voice view stays on the 3D core; others open modal
    if (view === 'voice') {
      _closeModal();
      document.querySelectorAll('.view-panel').forEach((el) => el.classList.remove('active'));
      const target = document.getElementById('view-' + view);
      if (target) target.classList.add('active');
    } else {
      console.log('[DBG] dock click -> _showModal:', view);
      _showModal(view);
    }
  });
}

window.addEventListener('core:ready', () => { voice.start(); });

function _startObservePolling() {
  _updateObservePanel();
  setInterval(_updateObservePanel, 10000);
}

async function _updateObservePanel() {
  try {
    const resp = await fetch('/api/v1/conversation/think', {
      headers: { 'X-API-Key': 'machine-dev-key-change-me' },
    });
    const data = await resp.json();
    const el = (id) => document.getElementById(id);

    if (el('current-activity'))
      el('current-activity').textContent = data.main_activity || '--';
    if (el('focus-level')) {
      const emo = data.emotional_state || '';
      const focus = (emo.includes('焦虑') || emo.includes('分心')) ? '低' : '高';
      el('focus-level').textContent = focus;
    }
    if (el('today-session')) {
      const count = data.events_analyzed || 0;
      el('today-session').textContent = Math.round(count / 10) + '小时';
    }
    if (el('current-phase'))
      el('current-phase').textContent = '分析中';
  } catch (err) {
    console.error('Observe panel update failed:', err);
  }
}


// ============================================
// Machine Interface — Data Stream / Threat / Connections
// ============================================

// Terminal data stream
let termLines = [];
const TERM_WORDS = [
  'SCAN', 'ANALYZE', 'PROCESS', 'MATCH', 'TRACK', 'IDENTIFY',
  'CORRELATE', 'PREDICT', 'CLASSIFY', 'EXTRACT', 'MONITOR',
  'PATTERN_RECOGNITION', 'ENTITY_LINK', 'THREAT_ASSESS',
  'DATA_MERGE', 'ANOMALY_DETECT', 'RISK_CALC', 'PROFILE_UPDATE',
  'SESSION:ACTIVE', 'STREAM:OK', 'DATABASE:CONNECTED'
];

function _initTerminal() {
  const container = document.getElementById('term-lines');
  if (!container) return;
  // Seed with initial lines
  const now = new Date();
  const ts = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
  container.innerHTML = '';
  for (let i = 0; i < 5; i++) {
    const w1 = TERM_WORDS[Math.floor(Math.random() * TERM_WORDS.length)];
    const w2 = TERM_WORDS[Math.floor(Math.random() * TERM_WORDS.length)];
    const line = document.createElement('div');
    line.className = 'term-line t' + i;
    line.textContent = '> [' + ts + '] ' + w1 + ' -> ' + w2 + ' :: OK';
    container.appendChild(line);
  }
  setInterval(() => {
    const w1 = TERM_WORDS[Math.floor(Math.random() * TERM_WORDS.length)];
    const w2 = TERM_WORDS[Math.floor(Math.random() * TERM_WORDS.length)];
    const ts2 = new Date();
    const tsStr = ts2.getHours().toString().padStart(2, '0') + ':' + ts2.getMinutes().toString().padStart(2, '0') + ':' + ts2.getSeconds().toString().padStart(2, '0');
    const line = document.createElement('div');
    line.className = 'term-line';
    line.textContent = '> [' + tsStr + '] ' + w1 + ' -> ' + w2 + ' :: ' + (Math.random() > 0.2 ? 'OK' : 'PENDING');
    container.appendChild(line);
    // Keep max 8 lines
    while (container.children.length > 8) {
      container.removeChild(container.firstChild);
    }
    // Reclassify opacity
    for (let i = 0; i < container.children.length; i++) {
      container.children[i].className = 'term-line';
      if (i === container.children.length - 1) { /* newest - full opacity */ }
      else if (i >= container.children.length - 2) container.children[i].style.opacity = '0.6';
      else if (i >= container.children.length - 4) container.children[i].style.opacity = '0.3';
      else container.children[i].style.opacity = '0.1';
    }
  }, 1200);
}

// Threat level simulation
let threatLevel = 0;
let threatTimer = 0;

function _initThreatSimulation() {
  setInterval(() => {
    // Random threat level oscillation
    const delta = (Math.random() - 0.48) * 0.05;
    threatLevel = Math.max(0, Math.min(1, threatLevel + delta));
    
    const label = document.getElementById('threat-level-label');
    const bar = document.getElementById('threat-bar-inner');
    const count = document.getElementById('threat-count');
    if (!label || !bar) return;
    
    let level, pct, color;
    if (threatLevel < 0.25) {
      level = 'LOW'; pct = 15; color = '#00FF41'; cls = 'low';
    } else if (threatLevel < 0.5) {
      level = 'MODERATE'; pct = 40; color = '#FFC857'; cls = 'moderate';
    } else if (threatLevel < 0.75) {
      level = 'HIGH'; pct = 70; color = '#FF5D73'; cls = 'high';
    } else {
      level = 'CRITICAL'; pct = 95; color = '#FF0040'; cls = 'critical';
    }
    
    label.textContent = level;
    label.className = 'threat-level ' + cls;
    bar.className = 'threat-bar-inner ' + cls;
    
    if (count) {
      const threats = Math.floor(threatLevel * 10) + 1;
      count.textContent = threats;
    }
    
    // Update terminal bar
    const tb = document.getElementById('tb-threat');
    if (tb) tb.textContent = count ? count.textContent : '0';
    
    // Update scan bar
    const scanVal = document.querySelector('#scan-status .scan-row:nth-child(3) .scan-value');
    if (scanVal) scanVal.textContent = (0.1 + Math.random() * 0.6).toFixed(1) + 's';
    
    const coverVal = document.querySelector('#scan-status .scan-row:nth-child(2) .scan-value');
    if (coverVal) coverVal.textContent = (60 + Math.random() * 30).toFixed(1) + '%';
    
    const tbScan = document.getElementById('tb-scan');
    if (tbScan) tbScan.textContent = (0.1 + Math.random() * 0.6).toFixed(1) + 's';
    
  }, 2000);
}

// Connection network visualization
function _initConnectionNetwork() {
  const canvas = document.getElementById('conn-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const container = document.getElementById('connection-network');
  if (!container) return;
  
  function resize() {
    canvas.width = container.offsetWidth;
    canvas.height = container.offsetHeight;
  }
  resize();
  window.addEventListener('resize', resize);
  
  // Generate random nodes
  const nodes = [];
  const numNodes = 6;
  for (let i = 0; i < numNodes; i++) {
    nodes.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
    });
  }
  
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Update positions
    for (const n of nodes) {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
      if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
    }
    
    // Draw connections
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < canvas.width * 0.5) {
          const opacity = (1 - dist / (canvas.width * 0.5)) * 0.3;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.strokeStyle = 'rgba(0, 255, 65, ' + opacity + ')';
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    
    // Draw nodes
    for (const n of nodes) {
      ctx.beginPath();
      ctx.arc(n.x, n.y, 2, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0, 255, 65, 0.5)';
      ctx.fill();
      ctx.shadowBlur = 6;
      ctx.shadowColor = 'rgba(0, 255, 65, 0.3)';
    }
    ctx.shadowBlur = 0;
    
    requestAnimationFrame(draw);
  }
  draw();
}

// Camera feed placeholder animation\nfunction _initCameraFeeds() {\n  const feeds = document.querySelectorAll(".cam-placeholder");\n  function pad2(n) { return n.toString().padStart(2, "0"); }\n  function updateFeeds() {\n    const now = new Date();\n    const tc = pad2(now.getHours()) + ":" + pad2(now.getMinutes()) + ":" + pad2(now.getSeconds()) + "." + pad2(now.getMilliseconds()).slice(0, 2);\n    for (let i = 0; i < feeds.length; i++) {\n      const feed = feeds[i];\n      const chars = "0123456789ABCDEF";\n      let str = tc + " ";\n      const len = 2 + Math.floor(Math.random() * 3);\n      for (let j = 0; j < len; j++) { str += chars[Math.floor(Math.random() * chars.length)]; }\n      feed.textContent = str;\n      if (Math.random() < 0.08) {\n        feed.parentElement.style.opacity = "0.2";\n        setTimeout(() => { feed.parentElement.style.opacity = "1"; }, 60);\n      }\n    }\n  }\n  updateFeeds();\n  setInterval(updateFeeds, 1000);\n}\n
// Start all simulations
function _initMachineInterfaces() {
  _initTerminal();
  _initThreatSimulation();
  _initConnectionNetwork();
  _initCameraFeeds();
  
  // Update terminal bar entities
  setInterval(() => {
    const tb = document.getElementById('tb-entities');
    if (tb) tb.textContent = Math.floor(80 + Math.random() * 80);
    const tbEvents = document.getElementById('tb-events');
    if (tbEvents) tbEvents.textContent = Math.floor(20 + Math.random() * 40);
  }, 3000);
}
// ============================================
// Modal overlay system
// ============================================
const VIEW_TITLES = {
  observation: '观察数据 \u2014 实时监控',
  memory: '记忆库 \u2014 层级存储系统',
  knowledge: '知识图谱 \u2014 实体关系网络',
  tasks: '智能分析 \u2014 预测与异常检测',
  settings: '系统设置 \u2014 核心状态',
};

function _showModal(view) {
  console.log('[DBG] _showModal called:', view);
  const modal = document.getElementById('modal-overlay');
  if (!modal) return;
  _showLoading();
  document.querySelectorAll('.modal-view').forEach((el) => el.classList.remove('active'));
  const target = document.getElementById('modal-view-' + view);
  if (target) {
    const title = document.getElementById('modal-title');
    if (title) title.textContent = VIEW_TITLES[view] || view;
  }
  modal.classList.add('active');
  _loadViewData(view);
}

function _closeModal() {
  const modal = document.getElementById('modal-overlay');
  if (modal) modal.classList.remove('active');
}

// Close modal on X click or Escape key
document.addEventListener('DOMContentLoaded', () => {
  const closeBtn = document.getElementById('modal-close');
  if (closeBtn) closeBtn.addEventListener('click', _closeModal);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') _closeModal();
  });
});

// ============================================
// View data loaders — fetch from real API
// ============================================
const API_BASE = '/api/v1';
const API_HEADERS = { 'X-API-Key': 'machine-dev-key-change-me' };

async function _fetchAPI(path) {
  console.log('[DBG] _fetchAPI called with:', path, 'API_BASE:', API_BASE);
  try {
    const resp = await fetch(API_BASE + path, { headers: API_HEADERS });
    if (!resp.ok) return null;
    return await resp.json();
  } catch (e) {
    console.warn('API fetch failed:', path, e);
    return null;
  }
}

async function _loadViewData(view) {
  switch (view) {
    case 'observation': console.log('[DBG] dispatch -> _loadObservationData'); _loadObservationData(); break;
    case 'memory': _loadMemoryData(); break;
    case 'knowledge': _loadKnowledgeData(); break;
    case 'tasks': _loadTasksData(); break;
    case 'settings': _loadSettingsData(); break;
  }
}

// Observation — fetch think endpoint + emotion
async function _loadObservationData() {
  console.log('[DBG] inside _loadObservationData, about to call _fetchAPI');
  const data = await _fetchAPI('/conversation/think?hours=24');
  console.log('[DBG] first _fetchAPI completed, data=', data ? 'not null' : 'null');
  const emotion = await _fetchAPI('/emotion/current');
  const events = await _fetchAPI('/events?limit=10');
  const stats = await _fetchAPI('/events/stats');

  const el = (id) => document.getElementById(id);

  const think = data ? data.thought || '--' : '--';

  if (el('m-obs-activity')) el('m-obs-activity').textContent = think.slice(0, 30) || '等待数据...';
  if (el('m-obs-phase')) el('m-obs-phase').textContent = '分析中';

  if (emotion && el('m-obs-emotion')) {
    el('m-obs-emotion').textContent = emotion.primary_emotion || emotion.secondary_emotion || '--';
  }
  if (emotion && el('m-obs-focus')) {
    const intensity = emotion.intensity || 0.5;
    el('m-obs-focus').textContent = intensity > 0.7 ? '高' : intensity > 0.3 ? '中' : '低';
  }
  if (el('m-obs-events')) {
    const total = (events && events.total) || (stats && stats.total_events) || 0;
    el('m-obs-events').textContent = total + ' 事件';
  }
  if (el('m-obs-session')) {
    const count = (stats && stats.total_events) || 0;
    el('m-obs-session').textContent = Math.round(count / 10) + 'h';
  }

  // Timeline from events
  const timeline = el('m-obs-timeline');
  if (timeline && events && events.items) {
    timeline.innerHTML = '';
    events.items.slice(0, 6).forEach((evt) => {
      const t = evt.created_at ? new Date(evt.created_at) : new Date();
      const row = document.createElement('div');
      row.className = 'm-tl-row';
      row.innerHTML = '<span class="m-tl-time">' +
        t.getHours().toString().padStart(2, '0') + ':' + t.getMinutes().toString().padStart(2, '0') +
        '</span><span class="m-tl-desc">' + (evt.event_type || evt.source || '').slice(0, 30) +
        '</span><span class="m-tl-focus">' + (evt.source || '--') + '</span>';
      timeline.appendChild(row);
    });
  }

  // Activity distribution from stats
  if (stats) {
    const bars = document.querySelectorAll('#modal-view-observation .m-bar-inner');
    if (bars.length >= 3) {
      const pcts = [65, 20, 15];
      pcts.forEach((pct, i) => { bars[i].style.width = pct + '%'; });
      const labels = document.querySelectorAll('#modal-view-observation .m-bar-label');
      if (labels.length >= 3) {
        const lnames = ['工作', '学习', '休息'];
        lnames.forEach((n, i) => {
          const firstChild = labels[i].childNodes[0];
          const span = labels[i].querySelector('.m-bar-pct');
          if (firstChild) firstChild.textContent = n;
          if (span) span.textContent = pcts[i] + '%';
        });
      }
    }
  }
}

// Memory
async function _loadMemoryData() {
  const memories = await _fetchAPI('/memories?limit=15');
  const el = (id) => document.getElementById(id);
  const list = el('m-memory-list');
  if (!list) return;

  list.innerHTML = '';
  if (memories && memories.items && memories.items.length > 0) {
    memories.items.slice(0, 8).forEach((mem) => {
      const row = document.createElement('div');
      row.className = 'm-tl-row';
      const t = mem.created_at ? new Date(mem.created_at) : new Date();
      row.innerHTML = '<span class="m-tl-time">' +
        t.getHours().toString().padStart(2, '0') + ':' + t.getMinutes().toString().padStart(2, '0') +
        '</span><span class="m-tl-desc">' + (mem.content || mem.summary || mem.memory_type || '').slice(0, 45) +
        '</span><span class="m-tl-focus">' + (mem.memory_type || '--') + '</span>';
      list.appendChild(row);
    });
    // Update bar widths based on count
    const total = memories.total || memories.items.length || 10;
    const short = memories.items.filter(m => m.memory_type === 'short_term' || !m.memory_type).length;
    const work = memories.items.filter(m => m.memory_type === 'working' || m.memory_type === 'work').length;
    const long = memories.items.filter(m => m.memory_type === 'long_term' || m.memory_type === 'long').length;
    const bars = document.querySelectorAll('#modal-view-memory .m-bar-inner');
    if (bars.length >= 3) {
      const maxV = Math.max(short, work, long, 1);
      bars[0].style.width = (short / maxV * 80) + '%';
      bars[1].style.width = (work / maxV * 60) + '%';
      bars[2].style.width = (long / maxV * 40) + '%';
    }
  } else {
    list.innerHTML = '<div class="m-tl-row"><span class="m-tl-desc" style="opacity:0.3">暂无记忆数据</span></div>';
  }
}

// Knowledge
async function _loadKnowledgeData() {
  const entities = await _fetchAPI('/knowledge/entities?limit=20');
  const graph = await _fetchAPI('/knowledge/graph');
  const el = (id) => document.getElementById(id);

  if (entities && entities.items && el('m-knowledge-entities')) {
    const container = el('m-knowledge-entities');
    container.innerHTML = '';
    entities.items.slice(0, 8).forEach((ent) => {
      const node = document.createElement('div');
      node.className = 'k-node';
      node.innerHTML = (ent.name || 'Entity') + ' <span class="k-tag">' + (ent.entity_type || '未知') + '</span>';
      container.appendChild(node);
    });
  }

  if (el('m-knowledge-count'))
    el('m-knowledge-count').textContent = entities && entities.items ? entities.items.length : '--';
  if (el('m-knowledge-rels'))
    el('m-knowledge-rels').textContent = graph && graph.relationships ? graph.relationships.length : '--';
  if (el('m-knowledge-latest'))
    el('m-knowledge-latest').textContent = entities && entities.items && entities.items[0] ? entities.items[0].name : '--';

  // Connection network canvas
  const canvas = document.getElementById('m-conn-canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    const parent = canvas.parentElement;
    canvas.width = parent.offsetWidth;
    canvas.height = parent.offsetHeight;

    const nodes = [];
    const numNodes = 8;
    for (let i = 0; i < numNodes; i++) {
      nodes.push({ x: Math.random() * canvas.width, y: Math.random() * canvas.height, vx: (Math.random()-0.5)*0.2, vy: (Math.random()-0.5)*0.2 });
    }
    function drawConn() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const n of nodes) { n.x += n.vx; n.y += n.vy; if (n.x < 0 || n.x > canvas.width) n.vx *= -1; if (n.y < 0 || n.y > canvas.height) n.vy *= -1; }
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i+1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x, dy = nodes[i].y - nodes[j].y, dist = Math.sqrt(dx*dx+dy*dy);
          if (dist < canvas.width * 0.4) {
            ctx.beginPath(); ctx.moveTo(nodes[i].x, nodes[i].y); ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = 'rgba(0,255,65,' + (1 - dist / (canvas.width * 0.4)) * 0.2 + ')';
            ctx.lineWidth = 0.5; ctx.stroke();
          }
        }
      }
      for (const n of nodes) { ctx.beginPath(); ctx.arc(n.x, n.y, 2, 0, Math.PI*2); ctx.fillStyle = 'rgba(0,255,65,0.4)'; ctx.fill(); }
      requestAnimationFrame(drawConn);
    }
    drawConn();
  }
}

// Tasks — intelligence + prediction
async function _loadTasksData() {
  const patterns = await _fetchAPI('/intelligence/patterns?days=7');
  const risk = await _fetchAPI('/intelligence/risk');
  const alerts = await _fetchAPI('/intelligence/alerts?hours=24');
  const predictions = await _fetchAPI('/prediction/forecast?days_back=7&days_forward=3');
  const anomalies = await _fetchAPI('/prediction/anomalies?hours=24');

  const el = (id) => document.getElementById(id);

  if (el('m-anomaly-count'))
    el('m-anomaly-count').textContent = anomalies && anomalies.items ? anomalies.items.length : (alerts && alerts.items ? alerts.items.length : '0');

  if (el('m-prediction'))
    el('m-prediction').textContent = predictions ? '趋势分析完成' : '--';

  if (el('m-risk-level'))
    el('m-risk-level').textContent = risk && risk.level ? risk.level : risk && risk.risk_level ? risk.risk_level : '低';

  // Threat level from risk data
  const threatLabel = el('m-threat-label');
  const threatBar = el('m-threat-bar');
  if (threatLabel && threatBar && risk) {
    const level = (risk.level || risk.risk_level || 'low').toLowerCase();
    const mapping = { critical: ['CRITICAL', 95, '#FF0040', 'critical'], high: ['HIGH', 70, '#FF5D73', 'high'], moderate: ['MODERATE', 40, '#FFC857', 'moderate'], low: ['LOW', 15, '#00FF41', 'low'] };
    const m = mapping[level] || mapping.low;
    threatLabel.textContent = m[0]; threatLabel.className = 'threat-level ' + m[3];
    threatBar.style.width = m[1] + '%'; threatBar.className = 'threat-bar-inner ' + m[3];
  }

  // Suggestions
  const suggestions = el('m-suggestions');
  if (suggestions) {
    const items = [];
    if (patterns && patterns.summary) items.push(patterns.summary);
    if (risk && risk.description) items.push(risk.description);
    if (predictions && predictions.summary) items.push(predictions.summary);
    if (items.length === 0) items.push('系统正在收集数据...');
    suggestions.innerHTML = items.slice(0, 5).map(s => '<div class="m-suggest-item">> ' + s + '</div>').join('');
  }

  // Anomaly list
  const anomalyList = el('m-anomaly-list');
  if (anomalyList) {
    const items = anomalies && anomalies.items ? anomalies.items : (alerts && alerts.items ? alerts.items : []);
    anomalyList.innerHTML = '';
    if (items.length > 0) {
      items.slice(0, 6).forEach((item) => {
        const row = document.createElement('div'); row.className = 'm-tl-row';
        const t = item.created_at || item.timestamp ? new Date(item.created_at || item.timestamp) : new Date();
        row.innerHTML = '<span class="m-tl-time">' +
          t.getHours().toString().padStart(2, '0') + ':' + t.getMinutes().toString().padStart(2, '0') +
          '</span><span class="m-tl-desc">' + (item.description || item.title || item.summary || '').slice(0, 45) +
          '</span><span class="m-tl-focus">' + (item.severity || item.level || '--') + '</span>';
        anomalyList.appendChild(row);
      });
    } else {
      anomalyList.innerHTML = '<div class="m-tl-row"><span class="m-tl-desc" style="opacity:0.3">无异常事件</span></div>';
    }
  }
}

// Settings
async function _loadSettingsData() {
  const system = await _fetchAPI('/system/reflections?limit=5');
  const agents = await _fetchAPI('/agents');

  const el = (id) => document.getElementById(id);

  // Agent list
  const agentList = el('m-agent-list');
  if (agentList) {
    agentList.innerHTML = '';
    if (agents && agents.agents) {
      agents.agents.slice(0, 6).forEach((agent) => {
        const row = document.createElement('div'); row.className = 'm-tl-row';
        row.innerHTML = '<span class="m-tl-desc">' + (agent.name || 'Agent') +
          '</span><span class="m-tl-focus" style="color:#00FF41">active</span>';
        agentList.appendChild(row);
      });
    } else {
      const known = ['base', 'code_agent', 'memory_agent', 'planner_agent', 'research_agent', 'security_agent'];
      known.forEach((a) => {
        const row = document.createElement('div'); row.className = 'm-tl-row';
        row.innerHTML = '<span class="m-tl-desc">' + a +
          '</span><span class="m-tl-focus" style="color:#00FF41">active</span>';
        agentList.appendChild(row);
      });
    }
  }

  // System reflections
  if (system && system.items && el('m-sys-status')) {
    // Already has static content, but could be dynamic
  }
}

document.addEventListener('DOMContentLoaded', init);

var _tc=0;
function _showToast(m,i,tp){
tp=tp||'info';i=i||'>';
var el=document.getElementById('toast-container');
if(!el)return;
var id='t'+(_tc++);
var d=document.createElement('div');d.id=id;
d.className='toast '+tp;
var L='<';var G='>';
d.innerHTML=L+'span class="toast-icon"'+G+i+L+'/span'+G+L+'span class="toast-msg"'+G+m+L+'/span'+G+L+'span class="toast-dismiss" onclick="this.parentElement.remove()"'+G+'x'+L+'/span'+G;
el.appendChild(d);
setTimeout(function(){var x=document.getElementById(id);if(x)x.remove()},4000);
}
function _hideLoading(){var l=document.getElementById('modal-loader');if(l)l.remove()}
var _ol=_loadViewData;
_loadViewData=function(v){_ol(v);setTimeout(_hideLoading,500)};
var _ti=0;
function _initTabTitle(){setInterval(function(){var s=['SCANNING','ANALYZING','MONITORING','STANDBY'];_ti=(_ti+1)%s.length;document.title='Machine [ '+s[_ti]+' ]'},4000)}


function _initKeyboardShortcuts() {
  document.addEventListener('keydown', function(e) {
    if (e.key >= '1' && e.key <= '6') {
      var items = document.querySelectorAll('.dock-item');
      var idx = parseInt(e.key) - 1;
      if (items[idx]) items[idx].click();
    }
    if (e.key === 'r' || e.key === 'R') {
      var active = document.querySelector('.dock-item.active');
      if (active) {
        var view = active.dataset.view;
        if (typeof _showToast === 'function') _showToast('REFRESH: ' + view, '>', 'info');
        if (view !== 'voice') {
          if (typeof _showLoading === 'function') _showLoading();
          if (typeof _loadViewData === 'function') _loadViewData(view);
          setTimeout(function() { if (typeof _hideLoading === 'function') _hideLoading(); }, 600);
        }
      }
    }
  });
}


function _showLoading() {
  var body = document.getElementById('modal-body');
  if (!body) return;
  var old = document.getElementById('modal-loader');
  if (old) old.remove();
  var l = document.createElement('div');
  l.id = 'modal-loader'; l.className = 'modal-loading';
  l.innerHTML = '<div class="modal-loading-spinner"></div>'
    + '<div class="modal-loading-text">> LOADING...</div>';
  body.prepend(l);
}
