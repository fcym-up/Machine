with open("D:/workplace/app/static/index.html", "r", encoding="utf-8") as f:
    d = f.read()

# Remove core-title-center section
target = '  <div id="core-title-center">\n    <h1 id="core-title-main">Machine</h1>\n    <p id="core-title-sub">\u6211\u4e00\u76f4\u90fd\u5728\u3002</p>\n  </div>\n\n    <div id="event-ticker"'
replacement = '    <div id="event-ticker"'
d = d.replace(target, replacement)

# Remove dock-monitor section
target2 = '  </div>\n  <div id="dock-monitor">\n    <div class="dock-item active" data-view="voice" title="Voice"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg><span class="dock-dot"></span></div>\n    <div class="dock-item" data-view="observation" title="Observation"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg><span class="dock-dot"></span></div>\n    <div class="dock-item" data-view="memory" title="Memory"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg><span class="dock-dot"></span></div>\n    <div class="dock-item" data-view="knowledge" title="Knowledge"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/><path d="M9 9.5V8a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v1.5"/></svg><span class="dock-dot"></span></div>\n    <div class="dock-item" data-view="tasks" title="Tasks"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/></svg><span class="dock-dot"></span></div>\n    <div class="dock-item" data-view="settings" title="Settings"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg><span class="dock-dot"></span></div>\n  </div>\n'

idx1 = d.find(target2[:60])
if idx1 >= 0:
    # Find the complete dock-monitor block
    start_m = d.find('<div id="dock-monitor">', idx1 - 20)
    end_m = d.find('</div>\n\n  <!-- Dock -->', start_m)
    if end_m > start_m:
        end_m = end_m + len('</div>')
        d = d[:start_m] + d[end_m:]
        print("dock-monitor removed")

with open("D:/workplace/app/static/index.html", "w", encoding="utf-8") as f:
    f.write(d)

print("Restored")
# Verify
print("Has core-title-center:", '"core-title-center"' in d)
print("Has dock-monitor:", 'dock-monitor' in d)
