import adsk.core
import adsk.fusion
import traceback
import math
import os
import json
import time

def mm(val):
    return val / 10.0

def run_kinematic_audit():
    app = adsk.core.Application.get()
    
    # Ensure antidraft2 is active
    target_doc = None
    for doc in app.documents:
        if "antidraft2" in doc.name:
            target_doc = doc
            break
    if target_doc:
        target_doc.activate()

    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"error": "No active design"}

    root_comp = design.rootComponent
    vp = app.activeViewport

    temp_dir = os.environ.get("TEMP", "")
    out_dir = os.path.join(temp_dir, "AntigravityCAD", "motion_audit")
    os.makedirs(out_dir, exist_ok=True)

    # Identify occurrences
    main_occ = None
    needle_occ = None
    slider_occ = None
    tendon_occ = None

    for occ in root_comp.occurrences:
        name = occ.name
        if "Chassis" in name:
            main_occ = occ
        elif "Needle" in name:
            needle_occ = occ
        elif "Slider" in name:
            slider_occ = occ
        elif "Tendon" in name:
            tendon_occ = occ

    xc_needle = mm(9.5)
    yc_needle = mm(0.0)
    zc_needle = mm(3.2)
    r_capstan = mm(6.15) # 0.615 cm

    steps_deg = [0.0, 22.5, 45.0, 67.5, 90.0]
    audit_frames = []

    # Prepare camera for crisp isometric motion tracking
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

    for idx, deg in enumerate(steps_deg):
        rad = math.radians(deg)
        # Capstan displacement: delta_x = r * theta (pulling backwards = negative X)
        delta_x = -(r_capstan * rad) # in cm

        # 1. Transform Slider
        if slider_occ:
            t_slide = adsk.core.Matrix3D.create()
            t_slide.translation = adsk.core.Vector3D.create(delta_x, 0, 0)
            slider_occ.transform = t_slide

        # 2. Transform Needle (CW rotation around xc, yc)
        if needle_occ:
            t_rot = adsk.core.Matrix3D.create()
            # Rotation around Z axis at center (xc, yc, zc)
            t_rot.setToRotation(rad, adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(xc_needle, yc_needle, zc_needle))
            needle_occ.transform = t_rot

        # Refresh viewport
        if vp:
            vp.refresh()
            adsk.doEvents()
            time.sleep(0.1)

        # 3. Capture image
        frame_png = os.path.join(out_dir, f"kinematic_step_{idx}_{int(deg)}deg.png")
        if vp:
            vp.saveAsImageFile(frame_png, 1920, 1080)

        # 4. Analyze Interference / Overlap
        interference_list = []
        try:
            body_collection = adsk.core.ObjectCollection.create()
            for occ in root_comp.occurrences:
                for b in occ.component.bRepBodies:
                    # Use occurrence body proxy if available
                    body_collection.add(b)

            if body_collection.count > 1:
                int_input = design.createInterferenceInput(body_collection)
                int_input.areInterferenceBodiesKept = False
                int_results = design.analyzeInterference(int_input)
                if int_results and int_results.count > 0:
                    for i in range(int_results.count):
                        item = int_results.item(i)
                        vol = round(item.volume * 1000.0, 4) # cm3 to mm3
                        b1_name = item.entityOne.parentComponent.name if hasattr(item.entityOne, 'parentComponent') else "Body1"
                        b2_name = item.entityTwo.parentComponent.name if hasattr(item.entityTwo, 'parentComponent') else "Body2"
                        interference_list.append({
                            "body1": b1_name,
                            "body2": b2_name,
                            "volume_mm3": vol
                        })
        except Exception as ex:
            interference_list.append({"error": str(ex)})

        # 5. Extract Bounding Boxes
        occ_bboxes = {}
        for occ in root_comp.occurrences:
            bbox = occ.boundingBox
            occ_bboxes[occ.name] = {
                "min": [round(bbox.minPoint.x * 10, 2), round(bbox.minPoint.y * 10, 2), round(bbox.minPoint.z * 10, 2)],
                "max": [round(bbox.maxPoint.x * 10, 2), round(bbox.maxPoint.y * 10, 2), round(bbox.maxPoint.z * 10, 2)]
            }

        audit_frames.append({
            "step_index": idx,
            "angle_deg": deg,
            "angle_rad": round(rad, 4),
            "slider_displacement_mm": round(delta_x * 10, 3),
            "theoretical_stroke_mm": round(r_capstan * 10 * rad, 3),
            "interferences_count": len(interference_list),
            "interferences": interference_list,
            "bounding_boxes": occ_bboxes,
            "image_path": frame_png
        })

    # Reset model to initial state (0 displacement)
    if slider_occ:
        slider_occ.transform = adsk.core.Matrix3D.create()
    if needle_occ:
        needle_occ.transform = adsk.core.Matrix3D.create()
    if vp:
        vp.refresh()
        adsk.doEvents()

    summary = {
        "document_name": target_doc.name if target_doc else "Unknown",
        "total_steps": len(audit_frames),
        "tested_range": "0 to 90 degrees (Full penetration stroke)",
        "capstan_radius_mm": 6.15,
        "max_stroke_mm": round(6.15 * math.radians(90.0), 3),
        "total_interference_events": sum(f["interferences_count"] for f in audit_frames),
        "frames": audit_frames,
        "audit_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdict": "PASS" if sum(f["interferences_count"] for f in audit_frames) == 0 else "INTERFERENCE_DETECTED"
    }

    report_path = os.path.join(out_dir, "kinematic_motion_audit_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary

try:
    res = run_kinematic_audit()
    print("AUDIT_RESULT:" + json.dumps(res, indent=2))
except Exception as e:
    print("AUDIT_FAILED:" + traceback.format_exc())