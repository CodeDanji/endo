import adsk.core
import adsk.fusion
import json
import os

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root_comp = design.rootComponent

body_col = adsk.core.ObjectCollection.create()
for occ in root_comp.occurrences:
    for b in occ.component.bRepBodies:
        body_col.add(b)

int_in = design.createInterferenceInput(body_col)
int_res = design.analyzeInterference(int_in)

clashes = []
if int_res:
    for i in range(int_res.count):
        item = int_res.item(i)
        n1 = item.entityOne.parentComponent.name if hasattr(item.entityOne, 'parentComponent') else "Body1"
        n2 = item.entityTwo.parentComponent.name if hasattr(item.entityTwo, 'parentComponent') else "Body2"
        b_box = item.interferenceBody.boundingBox
        clashes.append({
            "pair": f"{n1} <-> {n2}",
            "volume_cm3": item.interferenceBody.volume,
            "min_mm": [round(b_box.minPoint.x*10, 3), round(b_box.minPoint.y*10, 3), round(b_box.minPoint.z*10, 3)],
            "max_mm": [round(b_box.maxPoint.x*10, 3), round(b_box.maxPoint.y*10, 3), round(b_box.maxPoint.z*10, 3)]
        })

temp_dir = os.environ.get("TEMP", "")
out_path = os.path.join(temp_dir, "AntigravityCAD", "clash_details.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(clashes, f, indent=2)