export class Timeline {
  constructor(listEl, understandingBodyEl) {
    this.listEl = listEl;
    this.understandingBodyEl = understandingBodyEl;
    this.eventsUrl = '/api/v1/events?limit=30';
    this.thinkUrl = '/api/v1/conversation/think';
    this._intervalId = null;
    this._headers = { 'X-API-Key': 'machine-dev-key-change-me' };
    const headerEl = document.getElementById('timeline-header');
    if (headerEl) headerEl.textContent = 'Machine Analysis';
  }

  startPolling(intervalMs = 8000) {
    this._fetchUnderstanding();
    this._intervalId = setInterval(() => { this._fetchUnderstanding(); }, intervalMs);
  }

  stopPolling() {
    if (this._intervalId !== null) { clearInterval(this._intervalId); this._intervalId = null; }
  }

  async _fetchEvents() {
    try {
      const resp = await fetch(this.eventsUrl, { headers: this._headers });
      const json = await resp.json();
      const events = json.items || json.data || json.events || [];
    } catch (err) { console.error("Timeline._fetchEvents failed:", err); }
  }

  async _fetchUnderstanding() {
    try {
      const resp = await fetch(this.thinkUrl, { headers: this._headers });
      const json = await resp.json();
      this._renderUnderstanding(json);
    } catch (err) { console.error("Timeline._fetchUnderstanding failed:", err); }
  }

  _renderUnderstanding(data) {
    const thought = data.thought || '';
    const thoughts = thought ? [thought] : [];
    const activityDist = data.activity_distribution || {};
    let html = '';
    const now = new Date();
    const timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
    const _LT = '<';
    const _GT = '>';

    for (const thought of thoughts) {
      html += _LT + 'div class="thought-block"' + _GT;
      html += _LT + 'div class="thought-text"' + _GT + this._escape(thought) + _LT + '/div' + _GT;
      html += _LT + 'div class="thought-time"' + _GT + timeStr + _LT + '/div' + _GT;
      html += _LT + '/div' + _GT;
    }

    const topActivities = Object.keys(activityDist).slice(0, 3);
    if (topActivities.length > 0) {
      html += _LT + 'div class="activity-block" style="margin-top:12px;"' + _GT;
      html += _LT + 'div class="panel-header" style="margin-bottom:8px;"' + _GT + 'Recent Focus' + _LT + '/div' + _GT;
      for (const activity of topActivities) {
        html += _LT + 'span class="activity-tag"' + _GT + this._escape(activity) + _LT + '/span' + _GT;
      }
      html += _LT + '/div' + _GT;
    }

    if (thoughts.length > 0) {
      const lastThought = thoughts[thoughts.length - 1];
      html += _LT + 'div class="suggestion-block" style="margin-top:16px;"' + _GT;
      html += _LT + 'div class="panel-header" style="margin-bottom:4px;"' + _GT + 'Suggestion' + _LT + '/div' + _GT;
      html += _LT + 'div class="suggestion-text"' + _GT + this._escape(lastThought) + _LT + '/div' + _GT;
      html += _LT + '/div' + _GT;
    }
    this.listEl.innerHTML = html;
  }

  _escape(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
  }
}
