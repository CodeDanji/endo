import urllib.request
import json

code = """
import adsk.core, adsk.fusion
app = adsk.core.Application.get()
design = app.activeProduct
root = design.rootComponent

report = []
report.append(f"Occurrences: {[occ.name for occ in root.occurrences]}")
report.append(f"AsBuiltJoints: {[j.name for j in root.asBuiltJoints]}")
report.append(f"MotionLinks: {[m.name for m in root.motionLinks]}")
if root.motionLinks.count > 0:
    ml = root.motionLinks.item(0)
    report.append(f"MotionLink 1: {ml.name}, Joint1: {ml.jointOne.name}, Joint2: {ml.jointTwo.name}, Distance: {ml.distance}, Angle: {ml.angle}")

print("\\n".join(report))
app.userInterface.messageBox("\\n".join(report))
"""

url = "http://localhost:8080/execute_code"
data = json.dumps({"code": code}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req) as resp:
    print(resp.read().decode("utf-8"))
