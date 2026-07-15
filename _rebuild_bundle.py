import re
import codecs

files = {}
for name in ["data", "voice", "timeline", "particle-core", "app"]:
    with codecs.open("D:/workplace/app/static/js/" + name + ".js", "r", encoding="utf-8-sig") as f:
        files[name] = f.read()
    print(name + ".js:", len(files[name]), "chars")

parts = []

# data.js
datac = files["data"].replace("export const Data", "var Data")
parts.append("/* ===== Data Layer ===== */")
parts.append(datac)

# voice.js
voicec = files["voice"].replace("export class VoiceController", "class VoiceController")
parts.append("/* ===== Voice Controller ===== */")
parts.append(voicec)

# timeline.js
tc = files["timeline"].replace("export class Timeline", "class Timeline")
parts.append("/* ===== Timeline ===== */")
parts.append(tc)

# particle-core.js
pc = files["particle-core"]
pc = pc.replace("export class ParticleCore", "class ParticleCore")
# The original code has: import("three")
# Replace with dynamic import using relative path
# The import line continues with .then(function(ThreeMod) {
# After that line, the code continues with:
#     THREE = ThreeMod;
#     if (!self._initCalled) self._initThree();
# }).catch(function(err) {
# We need to preserve this structure but change the import path
pc = pc.replace('import("three")', 'import("../lib/three.module.js")')
parts.append("/* ===== Particle Core ===== */")
parts.append(pc)

# app.js - remove import statements
ac = files["app"]
ac = re.sub(r"^import .+$", "", ac, flags=re.MULTILINE)
parts.append("/* ===== Main App ===== */")
parts.append(ac)

result = "\n\n".join(parts)
result = re.sub(r"\n{4,}", "\n\n\n", result)
result = result.replace("\ufeff", "")

with open("D:/workplace/app/static/js/bundled_app.js", "w", encoding="utf-8") as f:
    f.write(result)

print("\nFinal:")
print("Length:", len(result))
print("Has BOM:", "\ufeff" in result)
print("Braces: open=" + str(result.count("{")) + " close=" + str(result.count("}")))
print("Parens: open=" + str(result.count("(")) + " close=" + str(result.count(")")))
print("Export statements:", len([l for l in result.split("\n") if re.match(r"^\s*export\s", l)]))
print("Import statements:", len([l for l in result.split("\n") if re.match(r"^\s*import\s", l)]))
print("Has bare import three:", "import(\"three\")" in result)

idx = result.find("import(\"../lib")
if idx >= 0:
    print("\nTHREE init:")
    print(result[idx:idx+300])
