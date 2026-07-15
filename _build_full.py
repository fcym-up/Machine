import re, codecs

def r(name):
    with codecs.open("D:/workplace/app/static/js/" + name + ".js", "r", "utf-8-sig") as f:
        return f.read()

data = r("data").replace("export const Data", "var Data")
voice = r("voice").replace("export class VoiceController", "class VoiceController")
tl = r("timeline").replace("export class Timeline", "class Timeline")
pc = r("particle-core").replace("export class ParticleCore", "class ParticleCore")
pc = pc.replace('import("three")', 'import("/dashboard/lib/three.module.js")')
app_main = re.sub(r"^import .+$", "", r("app"), flags=re.MULTILINE)

# Append ALL missing code (controllers, dock, views, etc.)
app_extra = '''
// ===== POI Feature Controllers =====
function setupLayerSwitching() {
  document.addEventListener("dblclick", function(e) { if (typeof inCoreView !== "undefined" && inCoreView) enterMonitorView(); });
  var logo = document.getElementById("monitor-core-logo");
  if (logo) { logo.addEventListener("click", function() { exitMonitorView(); }); }
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape" && typeof inCoreView !== "undefined" && !inCoreView) exitMonitorView();
    if (e.key === "Enter" && typeof inCoreView !== "undefined" && inCoreView) {
      if (document.activeElement && document.activeElement.id === "timeline-input") return;
      enterMonitorView();
    }
  });
}
'''

# Fix: remove original init call, add new one
base = "\n\n".join([data, voice, tl, pc, app_main + app_extra])

with open("D:/workplace/app/static/js/bundled_app.js", "w", encoding="utf-8") as f:
    f.write(base)

result = base.encode("utf-8")
print("Done size:", len(result))
print("Clock:", b"this.clock = new THREE.Clock()" in result)
print("ScanRadar:", b"createScanRadar()" in result)
print("dblclick:", b'document.addEventListener("dblclick"' in result)
print("Import:", b"import " in result)
print("Export:", b"export " in result)
