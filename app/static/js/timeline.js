export class Timeline {
  constructor(listEl, understandingBodyEl) {
    this.listEl = listEl;
    this.understandingBodyEl = understandingBodyEl;
    this.eventsUrl = '/api/v1/events/search?limit=30';
    this.thinkUrl = '/api/v1/conversation/think';
    this._intervalId = null;
    this._headers = { "X-API-Key": "machine-dev-key-change-me" };

    const headerEl = document.getElementById('timeline-header');
    if (headerEl) headerEl.textContent = 'Machine 的思考';
  }

  startPolling(intervalMs = 8000) {
    this._fetchUnderstanding();
    this._intervalId = setInterval(() => {
      this._fetchUnderstanding();
    }, intervalMs);
  }

  stopPolling() {
    if (this._intervalId !== null) {
      clearInterval(this._intervalId);
      this._intervalId = null;
    }
  }

  async _fetchEvents() {
    try {
      const resp = await fetch(this.eventsUrl, { headers: this._headers });
      const json = await resp.json();
      const events = json.items || json.data || json.events || [];
    } catch (err) {
      console.error('Timeline._fetchEvents failed:', err);
    }
  }

  async _fetchUnderstanding() {
    try {
      const resp = await fetch(this.thinkUrl, { headers: this._headers });
      const json = await resp.json();
      this._renderUnderstanding(json);
    } catch (err) {
      console.error('Timeline._fetchUnderstanding failed:', err);
    }
  }

  _renderUnderstanding(data) {
    const thoughts = data.thoughts || [];
    const activityDist = data.activity_distribution || {};
    let html = '';

    for (const thought of thoughts) {
      html += '<div class="thought-block">';
      html += '<div class="thought-text">' + this._escape(thought) + '</div>';
      html += '</div>';
    }

    const topActivities = Object.keys(activityDist).slice(0, 3);
    if (topActivities.length > 0) {
      html += '<div class="activity-block">';
      html += '<div class="section-label" style="margin-top:16px;">最近关注</div>';
      for (const activity of topActivities) {
        html += '<div class="activity-tag">' + this._escape(activity) + '</div>';
      }
      html += '</div>';
    }

    if (thoughts.length > 0) {
      const lastThought = thoughts[thoughts.length - 1];
      html += '<div class="suggestion-block" style="margin-top:16px;">';
      html += '<div class="section-label">建议</div>';
      html += '<div class="suggestion-text">' + this._escape(lastThought) + '</div>';
      html += '</div>';
    }

    this.listEl.innerHTML = html;
  }

  _escape(str) {
    const div = document.createElement("div");
    div.textContent = String(str);
    return div.innerHTML;
  }
}
