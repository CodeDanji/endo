import adsk.core
import adsk.fusion
import math
import os
import json
import time

def mm(val):
    return val / 10.0

def run_joint_motion_audit():
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"error": "No design"}

    root_comp = design.rootComponent
    vp = app.activeViewport

    # Find the joints
    needle_joint = None
    slider_joint = None
    for j in root_comp.asBuiltJoints:
        if "Needle" in j.name:
            needle_joint = j
        elif "Slider" in j.name:
            slider_joint = j

    for j in root_comp.joints:
        if not needle_joint and "Needle" in j.name:
            needle_joint = j
        if not slider_joint and "Slider" in j.name:
            slider_joint = j

    temp_dir = os.environ.get("TEMP", "")
    out_dir = os.path.join(temp_dir, "AntigravityCAD", "joint_audit")
    os.makedirs(out_dir, exist_ok=True)

    # 5 test angles: 0, 22.5, 45, 67.5, 90 degrees
    test_angles_deg = [0.0, 22.5, 45.0, 67.5, 90.0]
    results = []

    # Camera setup
    if vp:
        cam = vp.camera
        cam.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
        cam.eye = adsk.core.Point3D.create(mm(-15.0), mm(-35.0), mm(25.0))
        cam.target = adsk.core.Point3D.create(mm(-4.0), mm(0.0), mm(3.25))
        cam.upVector = adsk.core.Vector3D.create(0.0, 0.0, 1.0)
        cam.isFitView = True
        vp.camera = cam
        vp.refresh()

    r_capstan = 6.15 # mm

    for idx, deg in enumerate(test_angles_deg):
        rad = math.radians(deg)
        theoretical_slider_disp_mm = -(r_capstan * rad) # mm

        # Apply rotation to needle joint (CW is negative in standard Z-up or depending on joint direction)
        if needle_joint:
            needle_joint.jointMotion.rotationValue = -rad
        
        # Apply slider translation
        if slider_joint:
            slider_joint.jointMotion.sliderOneTranslationValue = mm(theoretical_slider_disp_mm)

        if vp:
            vp.refresh()
            adsk.doEvents()
            time.sleep(0.15)

        # Capture high-res frame
        frame_path = os.path.join(out_dir, f"frame_{idx}_{int(deg)}deg.png")
        if vp:
            vp.saveAsImageFile(frame_path, 1920, 1080)

        # Perform Interference Check between Chassis and Needle / Slider
        interference_data = []
        try:
            body_col = adsk.core.ObjectCollection.create()
            for occ in root_comp.occurrences:
                for b in occ.component.bRepBodies:
                    body_col.add(b)

            if body_col.count > 1:
                int_in = design.createInterferenceInput(body_col)
                int_res = design.analyzeInterference(int_in)
                if int_res:
                    for i in range(int_res.count):
                        item = int_res.item(i)
                        body1_name = item.entityOne.parentComponent.name if hasattr(item.entityOne, 'parentComponent') else "Entity1"
                        body2_name = item.entityTwo.parentComponent.name if hasattr(item.entityTwo, 'parentComponent') else "Entity2"
                        interference_data.append({
                            "pair": f"{body1_name} <-> {body2_name}",
                            "has_interference": True
                        })
        except Exception as ex:
            interference_data.append({"error": str(ex)})

        # Bounding box tracking
        bboxes = {}
        for occ in root_comp.occurrences:
            box = occ.boundingBox
            bboxes[occ.name] = {
                "min": [round(box.minPoint.x * 10, 2), round(box.minPoint.y * 10, 2), round(box.minPoint.z * 10, 2)],
                "max": [round(box.maxPoint.x * 10, 2), round(box.maxPoint.y * 10, 2), round(box.maxPoint.z * 10, 2)]
            }

        results.append({
            "step": idx,
            "angle_deg": deg,
            "needle_rotation_rad": round(rad, 4),
            "slider_disp_mm": round(theoretical_slider_disp_mm, 3),
            "interferences_detected": len(interference_data),
            "interference_details": interference_data,
            "bounding_boxes_mm": bboxes,
            "frame_image": frame_path
        })

    # Reset joints to 0
    if needle_joint:
        needle_joint.jointMotion.rotationValue = 0.0
    if slider_joint:
        slider_joint.jointMotion.sliderOneTranslationValue = 0.0
    if vp:
        vp.refresh()
        adsk.doEvents()

    audit_summary = {
        "device": "EndoCrab antidraft2",
        "tested_mechanism": "Capstan Wire Drive (Slider to Curved Ring Needle)",
        "total_steps": len(results),
        "kinematic_stroke_stroke_range_mm": f"0.0 to {round(r_capstan * math.radians(90), 3)} mm",
        "needle_rotation_range_deg": "0° to 90° (Clockwise Tissue Penetration)",
        "total_interferences": sum(r["interferences_detected"] for r in results),
        "steps_data": results,
        "overall_status": "PERFECT_CLEARANCE_PASS" if sum(r["interferences_detected"] for r in results) == 0 else "INTERFERENCE_ALERT"
    }

    summary_file = os.path.join(out_dir, "joint_motion_audit_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2, ensure_ascii=False)

    return audit_summary

run_joint_motion_audit()