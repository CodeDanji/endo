import adsk.core
import adsk.fusion
import json
import math
import os

app = adsk.core.Application.get()
for doc in app.documents:
    if "antidraft2" in doc.name:
        doc.activate()
        break

design = adsk.fusion.Design.cast(app.activeProduct)
root_comp = design.rootComponent

slider_occ = None
needle_occ = None
for occ in root_comp.occurrences:
    if "Slider" in occ.name:
        slider_occ = occ
    elif "Needle" in occ.name:
        needle_occ = occ

def mm(v): return v / 10.0

xc = mm(9.5)
yc = mm(0.0)
zc = mm(3.2)

body_col = adsk.core.ObjectCollection.create()
for occ in root_comp.occurrences:
    for b in occ.component.bRepBodies:
        body_col.add(b)

steps = [0.0, 22.5, 45.0, 67.5, 90.0]
results = []

for deg in steps:
    rad = math.radians(deg)
    stroke_mm = 6.15 * rad
    
    if slider_occ:
        t_slide = adsk.core.Matrix3D.create()
        t_slide.translation = adsk.core.Vector3D.create(mm(-stroke_mm), 0, 0)
        slider_occ.transform = t_slide

    if needle_occ:
        t_rot = adsk.core.Matrix3D.create()
        t_rot.setToRotation(rad, adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(xc, yc, zc))
        needle_occ.transform = t_rot

    adsk.doEvents()
    
    int_in = design.createInterferenceInput(body_col)
    int_res = design.analyzeInterference(int_in)
    clashes = []
    if int_res and int_res.count > 0:
        for i in range(int_res.count):
            item = int_res.item(i)
            n1 = item.entityOne.parentComponent.name if hasattr(item.entityOne, 'parentComponent') else "Body1"
            n2 = item.entityTwo.parentComponent.name if hasattr(item.entityTwo, 'parentComponent') else "Body2"
            clashes.append(f"{n1} <-> {n2} (vol: {round(item.interferenceBody.volume*1000, 4)} mm3)")
            
    results.append({
        "deg": deg,
        "stroke_mm": round(stroke_mm, 3),
        "clashes_count": len(clashes),
        "clashes": clashes
    })

# Reset
if slider_occ:
    slider_occ.transform = adsk.core.Matrix3D.create()
if needle_occ:
    needle_occ.transform = adsk.core.Matrix3D.create()
adsk.doEvents()

temp_dir = os.environ.get("TEMP", "")
out_path = os.path.join(temp_dir, "AntigravityCAD", "final_5step_interference_audit.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"audit": results, "total_clashes": sum(r["clashes_count"] for r in results)}, f, indent=2)