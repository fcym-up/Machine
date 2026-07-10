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
      document.getElementById('core-title').textContent = '我在听。';
      document.getElementById('core-subtitle').textContent = '';
      document.getElementById('core-hint').textContent = '';
      document.getElementById('core-response').textContent = '';
      document.getElementById('core-response').style.opacity = '0';
      document.getElementById('analyzing-list').innerHTML = '';
      var vs = document.getElementById('voice-status-text');
      if (vs) vs.textContent = '对话中...';
    },
    onSilence: () => {
      core.setState('idle');
      document.getElementById('core-title').textContent = 'AI Consciousness';
      document.getElementById('core-subtitle').textContent = '我一直都在。';
      document.getElementById('core-hint').textContent = '说 "终端"';
      document.getElementById('core-response').style.opacity = '0';
      setTimeout(() => {
        document.getElementById('analyzing-list').innerHTML = '';
      }, 1000);
      var vs = document.getElementById('voice-status-text');
      if (vs) vs.textContent = '唤醒词模式';
    },
    onTranscript: (text) => {
      core.setState('thinking');
      document.getElementById('core-title').textContent = '你说: ';
      document.getElementById('core-response').textContent = text;
      document.getElementById('core-response').style.opacity = '1';
      var vs = document.getElementById('voice-status-text');
      if (vs) vs.textContent = '思考中...';
    },
    onLLMReply: (reply) => {
      core.setState('speaking');
      document.getElementById('core-title').textContent = '';
      document.getElementById('core-response').textContent = reply;
      document.getElementById('core-response').style.transition = 'opacity 0.5s ease';
      document.getElementById('core-response').style.opacity = '1';
      var vs = document.getElementById('voice-status-text');
      if (vs) vs.textContent = '说话中...';
    },
    onStateChange: (state) => {
      const statusEl = document.getElementById('voice-status-text');
      if (statusEl) {
        const labels = {
          idle: '唤醒词模式',
          listening: '对话中...',
          thinking: '思考中...',
          speaking: '说话中...',
        };
        statusEl.textContent = labels[state] || state;
      }
    },
    onUnavailable: () => {
      var vs = document.getElementById('voice-status-text');
      if (vs) vs.textContent = '麦克风不可用';
      var h = document.getElementById('core-hint');
      if (!h) return;
      h.textContent = '麦克风不可用，请在浏览器中打开并授权麦克风';
      h.style.animation = 'none';
      h.style.opacity = '0.4';
    },
  });

  timeline = new Timeline(
    document.getElementById('timeline-list'),
    document.getElementById('understanding-body')
  );

  timeline.startPolling();
  _startObservePolling();

  core = new ParticleCore(document.getElementById('three-container'));
}

window.addEventListener('core:ready', () => {
  voice.start();
});

function _startObservePolling() {
  _updateObservePanel();
  setInterval(_updateObservePanel, 10000);
}

async function _updateObservePanel() {
  try {
    console.log('[Observe] Fetching...');
    const resp = await fetch('/api/v1/conversation/think', {
      headers: { 'X-API-Key': 'machine-dev-key-change-me' }
    });
    const data = await resp.json();
    const el = function(id) { return document.getElementById(id); };
    console.log('[Observe] Got data:', data.main_activity, data.emotional_state, data.events_analyzed);

    if (el('current-activity')) {
      el('current-activity').textContent = data.main_activity || '--';
    }
    if (el('focus-level')) {
      const emo = data.emotional_state || '';
      const focus = (emo.includes('焦虑') || emo.includes('分心')) ? '低' : '高';
      el('focus-level').textContent = focus;
    }
    if (el('today-session')) {
      const count = data.events_analyzed || 0;
      el('today-session').textContent = Math.round(count / 10) + '小时';
    }
    if (el('current-phase')) {
      el('current-phase').textContent = '分析中';
    }
  } catch (err) {
    console.error('Observe panel update failed:', err);
  }
}

document.addEventListener('DOMContentLoaded', init);