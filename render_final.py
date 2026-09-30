import adsk.core
import adsk.fusion
import math
import os
import time

app = adsk.core.Application.get()
for doc in app.documents:
    if "antidraft2" in doc.name:
        doc.activate()
        break

design = adsk.fusion.Design.cast(app.activeProduct)
root_comp = design.rootComponent
vp = app.activeViewport

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

temp_dir = os.environ.get("TEMP", "")
out_dir = os.path.join(temp_dir, "AntigravityCAD", "final_audit_renders")
os.makedirs(out_dir, exist_ok=True)

if vp:
    cam = vp.camera
    cam.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
    cam.eye = adsk.core.Point3D.create(mm(-15.0), mm(-35.0), mm(25.0))
    cam.target = adsk.core.Point3D.create(mm(-4.0), mm(0.0), mm(3.25))
    cam.upVector = adsk.core.Vector3D.create(0.0, 0.0, 1.0)
    cam.isFitView = True
    cam.isSmoothTransition = False
    vp.camera = cam
    vp.refresh()

steps = [
    (0, "0deg_home", 0.0),
    (1, "22deg_bite", 22.5),
    (2, "45deg_mid", 45.0),
    (3, "67deg_deep", 67.5),
    (4, "90deg_full", 90.0)
]

for idx, name, deg in steps:
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

    if vp:
        vp.refresh()
        adsk.doEvents()
        time.sleep(0.1)
        vp.saveAsImageFile(os.path.join(out_dir, f"step_{idx}_{name}.png"), 1920, 1080)

# Reset
if slider_occ:
    slider_occ.transform = adsk.core.Matrix3D.create()
if needle_occ:
    needle_occ.transform = adsk.core.Matrix3D.create()

# Capture top view
if vp:
    cam = vp.camera
    cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    cam.eye = adsk.core.Point3D.create(mm(-6.0), mm(0.0), mm(50.0))
    cam.target = adsk.core.Point3D.create(mm(-6.0), mm(0.0), mm(3.25))
    cam.upVector = adsk.core.Vector3D.create(0.0, 1.0, 0.0)
    cam.isFitView = True
    vp.camera = cam
    vp.refresh()
    vp.saveAsImageFile(os.path.join(out_dir, "top_plan_connected.png"), 1920, 1080)

    # Restore ISO view
    cam.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
    cam.eye = adsk.core.Point3D.create(mm(-15.0), mm(-35.0), mm(25.0))
    cam.target = adsk.core.Point3D.create(mm(-4.0), mm(0.0), mm(3.25))
    cam.upVector = adsk.core.Vector3D.create(0.0, 0.0, 1.0)
    cam.isFitView = True
    vp.camera = cam
    vp.refresh()