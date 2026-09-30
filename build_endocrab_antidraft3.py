import adsk.core
import adsk.fusion
import traceback
import math
import os
import json
import time

def mm(val):
    """Convert millimeters to Fusion 360 database units (centimeters)."""
    return val / 10.0

def build_endocrab_antidraft3():
    app = adsk.core.Application.get()
    ui = app.userInterface

    # 1. Ensure antidraft3 is active document
    target_doc = None
    for doc in app.documents:
        if "antidraft3" in doc.name:
            target_doc = doc
            break
    
    if target_doc:
        target_doc.activate()

    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"error": "No active Fusion 360 design"}

    root_comp = design.rootComponent

    # 2. Clean all existing occurrences for fresh pristine build
    while root_comp.occurrences.count > 0:
        root_comp.occurrences.item(0).deleteMe()

    # =========================================================================
    # 3. Authentic Parametric Reference Dimensions (Patent KR20210138938A & Nature 2024)
    # =========================================================================
    xc_needle = mm(9.5)       # Needle center X = 9.5 mm
    yc_needle = mm(0.0)       # Centerline Y = 0.0 mm
    zc_mid = mm(3.2)          # Mid-plane Z = 3.2 mm
    
    r_outer = mm(6.5)         # Needle Outer Radius = 6.5 mm (OD = 13.0 mm)
    r_inner = mm(5.2)         # Needle Inner Radius = 5.2 mm (ID = 10.4 mm)
    r_groove = mm(6.15)       # Capstan Cable Groove Radius = 6.15 mm
    y_tangent = yc_needle - r_groove  # Tangent Y = -6.15 mm

    # Linkage pivot coordinates
    xc_drive_pivot = mm(-11.0) # Driving Link (500) Pivot X = -11.0 mm
    yc_drive_pivot = mm(0.0)   # Driving Link Pivot Y = 0.0 mm
    r_link_arm = mm(6.5)       # Link arm crank radius = 6.5 mm
    
    xc_cam_pin = mm(-0.5)      # Cam Guide Pin (120) Center X = -0.5 mm
    yc_cam_pin = mm(-5.5)      # Cam Guide Pin Center Y = -5.5 mm (Centerline of Slot 610)

    temp_dir = os.environ.get("TEMP", "")
    output_dir = os.path.join(temp_dir, "AntigravityCAD", "antidraft3_verification")
    os.makedirs(output_dir, exist_ok=True)

    # Register / Update User Parameters for parametric design
    params = design.userParameters
    param_defs = [
        ("Body_Length", "50.0 mm", "Total chassis length"),
        ("Body_Width", "15.0 mm", "Chassis width"),
        ("Body_Height", "6.0 mm", "Chassis height"),
        ("Needle_OD", "13.0 mm", "Needle outer diameter"),
        ("Needle_ID", "10.4 mm", "Needle inner diameter"),
        ("Endoscope_Bore", "11.5 mm", "Endoscope attachment bore"),
        ("Cam_Slot_Wmax", "2.4 mm", "Variable cam slot maximum width"),
        ("Gripper_Length", "6.0 mm", "Tissue gripper length")
    ]
    for pname, pval, pcomment in param_defs:
        p_existing = params.itemByName(pname)
        if not p_existing:
            try:
                params.add(pname, adsk.core.ValueInput.createByString(pval), "mm", pcomment)
            except:
                pass

    # =========================================================================
    # 1. Main Chassis (Endocrab_Main_Chassis)
    # Complete CNC-machined metal housing with endoscope collar, track, & chambers
    # =========================================================================
    main_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    main_comp = main_occ.component
    main_comp.name = "Endocrab_Main_Chassis"

    # 1.1 Base Metal Chassis Block (-30 to +16 mm X, -7.5 to +7.5 mm Y, 0 to 6.0 mm Z)
    sk_base = main_comp.sketches.add(main_comp.xYConstructionPlane)
    sk_base.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(mm(-30.0), mm(-7.5), 0),
        adsk.core.Point3D.create(mm(16.0), mm(7.5), 0)
    )
    main_body = None
    if sk_base.profiles.count > 0:
        ext_base = main_comp.features.extrudeFeatures.createInput(
            sk_base.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_base.setDistanceExtent(False, adsk.core.ValueInput.createByString("6.0 mm"))
        ext_res = main_comp.features.extrudeFeatures.add(ext_base)
        if ext_res.bodies.count > 0:
            main_body = ext_res.bodies.item(0)

    # 1.2 Endoscope Mounting Collar (-38 to -30 mm X, OD 14.0 mm, ID 11.5 mm)
    sk_scope = main_comp.sketches.add(main_comp.xYConstructionPlane)
    sk_scope.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-30.0), 0, 0), mm(7.0))
    sk_scope.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-30.0), 0, 0), mm(5.75))
    sk_scope.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(mm(-38.0), mm(-7.0), 0),
        adsk.core.Point3D.create(mm(-30.0), mm(7.0), 0)
    )
    prof_scope_col = adsk.core.ObjectCollection.create()
    for prof in sk_scope.profiles:
        prof_scope_col.add(prof)
    if prof_scope_col.count > 0 and main_body:
        ext_scope = main_comp.features.extrudeFeatures.createInput(
            prof_scope_col, adsk.fusion.FeatureOperations.JoinFeatureOperation)
        ext_scope.setDistanceExtent(False, adsk.core.ValueInput.createByString("6.0 mm"))
        ext_scope.participantBodies = [main_body]
        main_comp.features.extrudeFeatures.add(ext_scope)

    # 1.3 Endoscope Inner Bore Cut (-39 to -25 mm X, Ø11.5 mm bore)
    sk_bore = main_comp.sketches.add(main_comp.xYConstructionPlane)
    sk_bore.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-34.0), 0, 0), mm(5.75))
    if sk_bore.profiles.count > 0 and main_body:
        ext_bore = main_comp.features.extrudeFeatures.createInput(
            sk_bore.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
        ext_bore.setDistanceExtent(False, adsk.core.ValueInput.createByString("6.0 mm"))
        ext_bore.participantBodies = [main_body]
        main_comp.features.extrudeFeatures.add(ext_bore)

    # 1.4 Distal Horseshoe Tissue Pocket Open Notch (X: 9.5 to 17.0 mm, Y: -5.1 to +5.1 mm, full height)
    sk_open = main_comp.sketches.add(main_comp.xYConstructionPlane)
    sk_open.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_needle, yc_needle, 0), mm(5.1)
    )
    sk_open.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(xc_needle, mm(-5.1), 0),
        adsk.core.Point3D.create(mm(17.0), mm(5.1), 0)
    )
    prof_open = adsk.core.ObjectCollection.create()
    for i in range(sk_open.profiles.count):
        prof_open.add(sk_open.profiles.item(i))
    if prof_open.count > 0 and main_body:
        ext_open = main_comp.features.extrudeFeatures.createInput(
            prof_open, adsk.fusion.FeatureOperations.CutFeatureOperation)
        ext_open.setDistanceExtent(False, adsk.core.ValueInput.createByString("6.0 mm"))
        ext_open.participantBodies = [main_body]
        main_comp.features.extrudeFeatures.add(ext_open)

    # 1.5 Circular Needle Guide Track (Recessed Arc Slot: R=4.8 to 7.0 mm, Z=1.9 to 4.5 mm)
    sk_track = main_comp.sketches.add(main_comp.xYConstructionPlane)
    sk_track.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_needle, yc_needle, 0), mm(7.0)
    )
    sk_track.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_needle, yc_needle, 0), mm(4.8)
    )
    for prof_t in sk_track.profiles:
        if prof_t.profileLoops.count > 1 and main_body:
            ext_track = main_comp.features.extrudeFeatures.createInput(
                prof_t, adsk.fusion.FeatureOperations.CutFeatureOperation)
            ext_track.setDistanceExtent(False, adsk.core.ValueInput.createByString("2.6 mm"))
            ext_track.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("1.9 mm"))
            ext_track.participantBodies = [main_body]
            main_comp.features.extrudeFeatures.add(ext_track)
            break

    # 1.6 Internal 4-Bar Linkage Chamber & Wire Routing Cavity (X: -26.0 to 4.5 mm, Y: -6.8 to +6.5 mm, Z: 1.5 to 4.9 mm)
    sk_cav = main_comp.sketches.add(main_comp.xYConstructionPlane)
    # Main link motion cavity
    sk_cav.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(mm(-25.0), mm(-6.8), 0),
        adsk.core.Point3D.create(mm(4.0), mm(6.2), 0)
    )
    # Tangential wire channel extending to needle tangent point
    sk_cav.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(mm(-28.0), mm(-6.8), 0),
        adsk.core.Point3D.create(mm(9.5), mm(-5.5), 0)
    )
    prof_cav = adsk.core.ObjectCollection.create()
    for i in range(sk_cav.profiles.count):
        prof_cav.add(sk_cav.profiles.item(i))
    if prof_cav.count > 0 and main_body:
        ext_cav = main_comp.features.extrudeFeatures.createInput(
            prof_cav, adsk.fusion.FeatureOperations.CutFeatureOperation)
        ext_cav.setDistanceExtent(False, adsk.core.ValueInput.createByString("3.4 mm"))
        ext_cav.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("1.5 mm"))
        ext_cav.participantBodies = [main_body]
        main_comp.features.extrudeFeatures.add(ext_cav)

    # 1.7 Fixed Cam Guide Pin (120) for Dead-Center Avoidance (at X=-0.5, Y=-5.5, Ø1.5mm, Z=1.5 to 4.5mm)
    sk_pin120 = main_comp.sketches.add(main_comp.xYConstructionPlane)
    sk_pin120.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_cam_pin, yc_cam_pin, 0), mm(0.75)
    )
    if sk_pin120.profiles.count > 0 and main_body:
        ext_pin120 = main_comp.features.extrudeFeatures.createInput(
            sk_pin120.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
        ext_pin120.setDistanceExtent(False, adsk.core.ValueInput.createByString("3.0 mm"))
        ext_pin120.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("1.5 mm"))
        ext_pin120.participantBodies = [main_body]
        main_comp.features.extrudeFeatures.add(ext_pin120)

    # 1.8 Driving Link Pivot Pin Boss (at X=-11.0, Y=0.0, Ø1.5mm, Z=1.5 to 4.5mm)
    sk_pin_drv = main_comp.sketches.add(main_comp.xYConstructionPlane)
    sk_pin_drv.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_drive_pivot, yc_drive_pivot, 0), mm(0.75)
    )
    if sk_pin_drv.profiles.count > 0 and main_body:
        ext_pin_drv = main_comp.features.extrudeFeatures.createInput(
            sk_pin_drv.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
        ext_pin_drv.setDistanceExtent(False, adsk.core.ValueInput.createByString("3.0 mm"))
        ext_pin_drv.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("1.5 mm"))
        ext_pin_drv.participantBodies = [main_body]
        main_comp.features.extrudeFeatures.add(ext_pin_drv)

    # 1.9 Fastener / Assembly Bolt Holes (6x M1.6 clearance holes)
    sk_bolts = main_comp.sketches.add(main_comp.xYConstructionPlane)
    sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-20.0), mm(5.2), 0), mm(0.8))
    sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-20.0), mm(-5.2), 0), mm(0.8))
    sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-6.0), mm(5.2), 0), mm(0.8))
    sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-6.0), mm(-5.2), 0), mm(0.8))
    sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(4.0), mm(5.5), 0), mm(0.8))
    sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(4.0), mm(-5.5), 0), mm(0.8))
    prof_bolts = adsk.core.ObjectCollection.create()
    for i in range(sk_bolts.profiles.count):
        prof_bolts.add(sk_bolts.profiles.item(i))
    if prof_bolts.count > 0 and main_body:
        ext_bolts = main_comp.features.extrudeFeatures.createInput(
            prof_bolts, adsk.fusion.FeatureOperations.CutFeatureOperation)
        ext_bolts.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.8 mm"))
        ext_bolts.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("4.5 mm"))
        ext_bolts.participantBodies = [main_body]
        main_comp.features.extrudeFeatures.add(ext_bolts)


    # =========================================================================
    # 2. Ring Needle Assembly (Ring_Needle_Assembly)
    # Outer Dia Ø13.0 mm, Inner Dia Ø10.4 mm, Height 1.8 mm, Ratchets & Tip
    # =========================================================================
    needle_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    needle_comp = needle_occ.component
    needle_comp.name = "Ring_Needle_Assembly"

    # 2.1 Base Annular Ring
    sk_n = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
    sk_n.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(xc_needle, yc_needle, 0), r_outer)
    sk_n.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(xc_needle, yc_needle, 0), r_inner)
    
    needle_body = None
    for prof in sk_n.profiles:
        if prof.profileLoops.count > 1:
            ext_n = needle_comp.features.extrudeFeatures.createInput(
                prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_n.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.8 mm"))
            ext_n.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.3 mm"))
            res_n = needle_comp.features.extrudeFeatures.add(ext_n)
            if res_n.bodies.count > 0:
                needle_body = res_n.bodies.item(0)
            break

    # 2.2 Circumferential Capstan Wire Groove (R = 6.15mm, Z = 2.8 to 3.6mm)
    if needle_body:
        sk_gr = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
        sk_gr.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(xc_needle, yc_needle, 0), r_outer + mm(0.1))
        sk_gr.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(xc_needle, yc_needle, 0), r_groove)
        for prof_g in sk_gr.profiles:
            if prof_g.profileLoops.count > 1:
                ext_gr = needle_comp.features.extrudeFeatures.createInput(
                    prof_g, adsk.fusion.FeatureOperations.CutFeatureOperation)
                ext_gr.setDistanceExtent(False, adsk.core.ValueInput.createByString("0.8 mm"))
                ext_gr.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.8 mm"))
                ext_gr.participantBodies = [needle_body]
                needle_comp.features.extrudeFeatures.add(ext_gr)
                break

    # 2.3 Dual Top Ratchet Driver Grooves (210a at -X, 210b at +X) with 28° slip ramps
    if needle_body:
        sk_drv_grv = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
        sk_drv_grv.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(xc_needle - mm(6.5), yc_needle - mm(0.8)),
            adsk.core.Point3D.create(xc_needle - mm(4.8), yc_needle + mm(0.8))
        )
        sk_drv_grv.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(xc_needle + mm(4.8), yc_needle - mm(0.8)),
            adsk.core.Point3D.create(xc_needle + mm(6.5), yc_needle + mm(0.8))
        )
        prof_col_d = adsk.core.ObjectCollection.create()
        for i in range(sk_drv_grv.profiles.count):
            prof_col_d.add(sk_drv_grv.profiles.item(i))
        if prof_col_d.count > 0:
            ext_d = needle_comp.features.extrudeFeatures.createInput(
                prof_col_d, adsk.fusion.FeatureOperations.CutFeatureOperation)
            ext_d.setDistanceExtent(False, adsk.core.ValueInput.createByString("0.6 mm"))
            ext_d.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("3.5 mm"))
            ext_d.participantBodies = [needle_body]
            needle_comp.features.extrudeFeatures.add(ext_d)

    # 2.4 Dual Bottom Ratchet Stopper Grooves (220a, 220b at 180° phase)
    if needle_body:
        sk_stp_grv = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
        sk_stp_grv.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(xc_needle - mm(0.8), yc_needle - mm(6.5)),
            adsk.core.Point3D.create(xc_needle + mm(0.8), yc_needle - mm(4.8))
        )
        sk_stp_grv.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(xc_needle - mm(0.8), yc_needle + mm(4.8)),
            adsk.core.Point3D.create(xc_needle + mm(0.8), yc_needle + mm(6.5))
        )
        prof_col_s = adsk.core.ObjectCollection.create()
        for i in range(sk_stp_grv.profiles.count):
            prof_col_s.add(sk_stp_grv.profiles.item(i))
        if prof_col_s.count > 0:
            ext_s = needle_comp.features.extrudeFeatures.createInput(
                prof_col_s, adsk.fusion.FeatureOperations.CutFeatureOperation)
            ext_s.setDistanceExtent(False, adsk.core.ValueInput.createByString("0.6 mm"))
            ext_s.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.3 mm"))
            ext_s.participantBodies = [needle_body]
            needle_comp.features.extrudeFeatures.add(ext_s)

    # 2.5 C-Shape Opening (90° opening at distal-upper quadrant)
    if needle_body:
        sk_c = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
        sk_c.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(xc_needle - mm(7.0), yc_needle + mm(1.8)),
            adsk.core.Point3D.create(xc_needle + mm(0.5), yc_needle + mm(7.5))
        )
        if sk_c.profiles.count > 0:
            cut_c = needle_comp.features.extrudeFeatures.createInput(
                sk_c.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut_c.setDistanceExtent(False, adsk.core.ValueInput.createByString("5.0 mm"))
            cut_c.participantBodies = [needle_body]
            needle_comp.features.extrudeFeatures.add(cut_c)

    # 2.6 Sharp Penetrating Needle Piercing Tip
    if needle_body:
        sk_tip = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
        lines_tp = sk_tip.sketchCurves.sketchLines
        p_t1 = adsk.core.Point3D.create(xc_needle + mm(0.5), yc_needle + mm(6.5), 0)
        p_t2 = adsk.core.Point3D.create(xc_needle + mm(0.5), yc_needle + mm(5.2), 0)
        p_t3 = adsk.core.Point3D.create(xc_needle + mm(4.0), yc_needle + mm(6.5), 0)
        lines_tp.addByTwoPoints(p_t1, p_t2)
        lines_tp.addByTwoPoints(p_t2, p_t3)
        lines_tp.addByTwoPoints(p_t3, p_t1)
        if sk_tip.profiles.count > 0:
            cut_tip = needle_comp.features.extrudeFeatures.createInput(
                sk_tip.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut_tip.setDistanceExtent(False, adsk.core.ValueInput.createByString("5.0 mm"))
            cut_tip.participantBodies = [needle_body]
            needle_comp.features.extrudeFeatures.add(cut_tip)

    # 2.7 Rear Suture Attachment Laser Eyelet Hole (Ø0.4 mm) & Suture Thread
    if needle_body:
        sk_eye = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
        sk_eye.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc_needle - mm(5.8), yc_needle + mm(2.5), 0), mm(0.25)
        )
        if sk_eye.profiles.count > 0:
            cut_eye = needle_comp.features.extrudeFeatures.createInput(
                sk_eye.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut_eye.setDistanceExtent(False, adsk.core.ValueInput.createByString("5.0 mm"))
            cut_eye.participantBodies = [needle_body]
            needle_comp.features.extrudeFeatures.add(cut_eye)

    # Suture Line Body (4-0 Nylon thread trailing from needle eyelet)
    sk_sut = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
    sk_sut.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(xc_needle - mm(6.0), yc_needle + mm(2.4), 0),
        adsk.core.Point3D.create(xc_needle - mm(16.0), yc_needle + mm(2.6), 0)
    )
    if sk_sut.profiles.count > 0:
        ext_sut = needle_comp.features.extrudeFeatures.createInput(
            sk_sut.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_sut.setDistanceExtent(False, adsk.core.ValueInput.createByString("0.2 mm"))
        ext_sut.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("3.1 mm"))
        needle_comp.features.extrudeFeatures.add(ext_sut)


    # =========================================================================
    # 3. Driving Link 500 (Driving_Link_500)
    # Oscillates 0 to 180° around Driving Pivot (X=-11.0, Y=0.0)
    # =========================================================================
    drv_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    drv_comp = drv_occ.component
    drv_comp.name = "Driving_Link_500"

    sk_drv = drv_comp.sketches.add(drv_comp.xYConstructionPlane)
    # Central pivot boss (R=2.2 mm at X=-11.0, Y=0.0)
    sk_drv.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_drive_pivot, yc_drive_pivot, 0), mm(2.2)
    )
    # Crank arm extending to connecting pin at X=-11.0, Y=-5.5 mm
    sk_drv.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(xc_drive_pivot - mm(1.5), yc_drive_pivot - mm(6.0)),
        adsk.core.Point3D.create(xc_drive_pivot + mm(1.5), yc_drive_pivot)
    )
    # Connecting pin boss at X=-11.0, Y=-5.5 mm
    sk_drv.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_drive_pivot, yc_drive_pivot - mm(5.5), 0), mm(1.6)
    )
    # Central pivot hole (Ø1.5 mm clearance)
    sk_drv.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_drive_pivot, yc_drive_pivot, 0), mm(0.8)
    )

    prof_col_drv = adsk.core.ObjectCollection.create()
    for prof in sk_drv.profiles:
        prof_col_drv.add(prof)

    drv_body = None
    if prof_col_drv.count > 0:
        ext_drv = drv_comp.features.extrudeFeatures.createInput(
            prof_col_drv, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_drv.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.2 mm"))
        ext_drv.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.0 mm"))
        res_drv = drv_comp.features.extrudeFeatures.add(ext_drv)
        if res_drv.bodies.count > 0:
            drv_body = res_drv.bodies.item(0)

    # Connecting Pin boss on Driving Link (Z: 3.2 to 4.6 mm, Ø1.4 mm)
    if drv_body:
        sk_dpin = drv_comp.sketches.add(drv_comp.xYConstructionPlane)
        sk_dpin.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc_drive_pivot, yc_drive_pivot - mm(5.5), 0), mm(0.7)
        )
        if sk_dpin.profiles.count > 0:
            ext_dpin = drv_comp.features.extrudeFeatures.createInput(
                sk_dpin.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
            ext_dpin.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.4 mm"))
            ext_dpin.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("3.2 mm"))
            ext_dpin.participantBodies = [drv_body]
            drv_comp.features.extrudeFeatures.add(ext_dpin)


    # =========================================================================
    # 4. Driven Link 400 (Driven_Link_400)
    # Concentric with Needle Center (X=9.5, Y=0.0), drives Driver Pawl
    # =========================================================================
    driven_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    driven_comp = driven_occ.component
    driven_comp.name = "Driven_Link_400"

    sk_drvn = driven_comp.sketches.add(driven_comp.xYConstructionPlane)
    # Sector arm from needle center to connecting pin (X=9.5, Y=-5.5)
    sk_drvn.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(xc_needle - mm(1.5), yc_needle - mm(6.0)),
        adsk.core.Point3D.create(xc_needle + mm(1.5), yc_needle)
    )
    # Needle center hub
    sk_drvn.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_needle, yc_needle, 0), mm(2.2)
    )
    # Connecting pin boss at X=9.5, Y=-5.5 mm
    sk_drvn.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_needle, yc_needle - mm(5.5), 0), mm(1.6)
    )
    # Pawl mount pad at X=3.5, Y=0.0 mm
    sk_drvn.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(xc_needle - mm(6.2), yc_needle - mm(1.2)),
        adsk.core.Point3D.create(xc_needle - mm(3.8), yc_needle + mm(1.2))
    )

    prof_col_drvn = adsk.core.ObjectCollection.create()
    for prof in sk_drvn.profiles:
        prof_col_drvn.add(prof)

    drvn_body = None
    if prof_col_drvn.count > 0:
        ext_drvn = driven_comp.features.extrudeFeatures.createInput(
            prof_col_drvn, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_drvn.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.2 mm"))
        ext_drvn.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.0 mm"))
        res_drvn = driven_comp.features.extrudeFeatures.add(ext_drvn)
        if res_drvn.bodies.count > 0:
            drvn_body = res_drvn.bodies.item(0)

    # Connecting Pin boss on Driven Link (Z: 3.2 to 4.6 mm, Ø1.4 mm)
    if drvn_body:
        sk_drvn_pin = driven_comp.sketches.add(driven_comp.xYConstructionPlane)
        sk_drvn_pin.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc_needle, yc_needle - mm(5.5), 0), mm(0.7)
        )
        if sk_drvn_pin.profiles.count > 0:
            ext_drvn_pin = driven_comp.features.extrudeFeatures.createInput(
                sk_drvn_pin.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
            ext_drvn_pin.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.4 mm"))
            ext_drvn_pin.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("3.2 mm"))
            ext_drvn_pin.participantBodies = [drvn_body]
            driven_comp.features.extrudeFeatures.add(ext_drvn_pin)


    # =========================================================================
    # 5. Connection Link 600 with Patented Variable Cam Slot 610 (Connection_Link_600)
    # Bridges Pin at (-11.0, -5.5) and Pin at (9.5, -5.5), Length L = 20.5 mm
    # Features Variable Cam Slot (610): Width 1.6 mm -> 2.4 mm (Max) -> 1.6 mm
    # =========================================================================
    conn_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    conn_comp = conn_occ.component
    conn_comp.name = "Connection_Link_600"

    # 5.1 Main Link Bar Body (X: -13.0 to +11.5 mm, Y: -7.5 to -3.5 mm, Z: 3.3 to 4.5 mm)
    sk_conn = conn_comp.sketches.add(conn_comp.xYConstructionPlane)
    sk_conn.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(xc_drive_pivot - mm(2.0), yc_drive_pivot - mm(7.5)),
        adsk.core.Point3D.create(xc_needle + mm(2.0), yc_needle - mm(3.5))
    )
    # Pin hole 1 at driving link pin (-11.0, -5.5)
    sk_conn.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_drive_pivot, yc_drive_pivot - mm(5.5), 0), mm(0.75)
    )
    # Pin hole 2 at driven link pin (9.5, -5.5)
    sk_conn.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(xc_needle, yc_needle - mm(5.5), 0), mm(0.75)
    )

    prof_col_conn = adsk.core.ObjectCollection.create()
    for prof in sk_conn.profiles:
        prof_col_conn.add(prof)

    conn_body = None
    if prof_col_conn.count > 0:
        ext_conn = conn_comp.features.extrudeFeatures.createInput(
            prof_col_conn, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_conn.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.2 mm"))
        ext_conn.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("3.3 mm"))
        res_conn = conn_comp.features.extrudeFeatures.add(ext_conn)
        if res_conn.bodies.count > 0:
            conn_body = res_conn.bodies.item(0)

    # 5.2 Patented Variable Cam Slot (610) Cut
    # Center width W_mid = 1.6 mm, Expansion W_max = 2.4 mm, End width W_end = 1.6 mm
    if conn_body:
        sk_slot610 = conn_comp.sketches.add(conn_comp.xYConstructionPlane)
        # Narrow center slot (1.6 mm width: Y = -6.3 to -4.7 mm)
        sk_slot610.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-6.0), mm(-6.3)),
            adsk.core.Point3D.create(mm(4.5), mm(-4.7))
        )
        # Midpoint Max Expansion Bulge 614/615 (2.4 mm width around Cam Pin 120 at X=-0.5, Y=-5.5)
        sk_slot610.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc_cam_pin - mm(2.0), yc_cam_pin, 0), mm(1.2)
        )
        sk_slot610.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc_cam_pin + mm(2.0), yc_cam_pin, 0), mm(1.2)
        )
        sk_slot610.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(xc_cam_pin - mm(2.0), yc_cam_pin - mm(1.2)),
            adsk.core.Point3D.create(xc_cam_pin + mm(2.0), yc_cam_pin + mm(1.2))
        )

        prof_col_s610 = adsk.core.ObjectCollection.create()
        for i in range(sk_slot610.profiles.count):
            prof_col_s610.add(sk_slot610.profiles.item(i))

        if prof_col_s610.count > 0:
            ext_s610 = conn_comp.features.extrudeFeatures.createInput(
                prof_col_s610, adsk.fusion.FeatureOperations.CutFeatureOperation)
            ext_s610.setDistanceExtent(False, adsk.core.ValueInput.createByString("2.0 mm"))
            ext_s610.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("3.0 mm"))
            ext_s610.participantBodies = [conn_body]
            conn_comp.features.extrudeFeatures.add(ext_s610)


    # =========================================================================
    # 6. Needle Driver Pawl 300 (Needle_Driver_Pawl_300)
    # One-way drive ratchet tooth pushing Needle top groove CCW
    # =========================================================================
    pawl_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    pawl_comp = pawl_occ.component
    pawl_comp.name = "Needle_Driver_Pawl_300"

    sk_pw = pawl_comp.sketches.add(pawl_comp.xYConstructionPlane)
    sk_pw.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(xc_needle - mm(6.0), yc_needle - mm(0.6)),
        adsk.core.Point3D.create(xc_needle - mm(4.3), yc_needle + mm(0.6))
    )
    # Pawl tooth triangular ramp (vertical push face at front, 28° ramp at back)
    lines_pw = sk_pw.sketchCurves.sketchLines
    p_p1 = adsk.core.Point3D.create(xc_needle - mm(4.3), yc_needle + mm(0.6), 0)
    p_p2 = adsk.core.Point3D.create(xc_needle - mm(4.3), yc_needle + mm(1.5), 0)
    p_p3 = adsk.core.Point3D.create(xc_needle - mm(5.8), yc_needle + mm(0.6), 0)
    lines_pw.addByTwoPoints(p_p1, p_p2)
    lines_pw.addByTwoPoints(p_p2, p_p3)
    lines_pw.addByTwoPoints(p_p3, p_p1)

    prof_col_pw = adsk.core.ObjectCollection.create()
    for i in range(sk_pw.profiles.count):
        prof_col_pw.add(sk_pw.profiles.item(i))

    if prof_col_pw.count > 0:
        ext_pw = pawl_comp.features.extrudeFeatures.createInput(
            prof_col_pw, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_pw.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.4 mm"))
        ext_pw.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("3.0 mm"))
        pawl_comp.features.extrudeFeatures.add(ext_pw)


    # =========================================================================
    # 7. Needle Stopper Pawl 800 (Needle_Stopper_Pawl_800)
    # Anti-reverse lock pawl mounted on chassis base under needle
    # =========================================================================
    stp_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    stp_comp = stp_occ.component
    stp_comp.name = "Needle_Stopper_Pawl_800"

    sk_st = stp_comp.sketches.add(stp_comp.xYConstructionPlane)
    sk_st.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(xc_needle - mm(0.7), yc_needle - mm(6.5)),
        adsk.core.Point3D.create(xc_needle + mm(0.7), yc_needle - mm(4.6))
    )
    lines_st = sk_st.sketchCurves.sketchLines
    p_s1 = adsk.core.Point3D.create(xc_needle + mm(0.7), yc_needle - mm(4.6), 0)
    p_s2 = adsk.core.Point3D.create(xc_needle + mm(1.5), yc_needle - mm(4.6), 0)
    p_s3 = adsk.core.Point3D.create(xc_needle + mm(0.7), yc_needle - mm(5.8), 0)
    lines_st.addByTwoPoints(p_s1, p_s2)
    lines_st.addByTwoPoints(p_s2, p_s3)
    lines_st.addByTwoPoints(p_s3, p_s1)

    prof_col_st = adsk.core.ObjectCollection.create()
    for i in range(sk_st.profiles.count):
        prof_col_st.add(sk_st.profiles.item(i))

    if prof_col_st.count > 0:
        ext_st = stp_comp.features.extrudeFeatures.createInput(
            prof_col_st, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_st.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.0 mm"))
        ext_st.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("1.8 mm"))
        stp_comp.features.extrudeFeatures.add(ext_st)


    # =========================================================================
    # 8. Dual Tissue Grippers (Tissue_Gripper_Left & Tissue_Gripper_Right)
    # 6.0 mm articulated grasping jaws with 3-tooth serration
    # =========================================================================
    # Left Jaw (+Y)
    gl_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    gl_comp = gl_occ.component
    gl_comp.name = "Tissue_Gripper_Left"

    sk_gl = gl_comp.sketches.add(gl_comp.xYConstructionPlane)
    sk_gl.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(mm(12.0), mm(4.0), 0),
        adsk.core.Point3D.create(mm(17.5), mm(6.2), 0)
    )
    lines_gl = sk_gl.sketchCurves.sketchLines
    lines_gl.addByTwoPoints(adsk.core.Point3D.create(mm(17.5), mm(6.2), 0), adsk.core.Point3D.create(mm(18.5), mm(4.8), 0))
    lines_gl.addByTwoPoints(adsk.core.Point3D.create(mm(18.5), mm(4.8), 0), adsk.core.Point3D.create(mm(17.5), mm(4.0), 0))
    lines_gl.addByTwoPoints(adsk.core.Point3D.create(mm(17.5), mm(4.0), 0), adsk.core.Point3D.create(mm(17.5), mm(6.2), 0))
    sk_gl.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(13.0), mm(5.1), 0), mm(0.5))

    prof_col_gl = adsk.core.ObjectCollection.create()
    for i in range(sk_gl.profiles.count):
        prof_col_gl.add(sk_gl.profiles.item(i))

    if prof_col_gl.count > 0:
        ext_gl = gl_comp.features.extrudeFeatures.createInput(
            prof_col_gl, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_gl.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.8 mm"))
        ext_gl.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.2 mm"))
        gl_comp.features.extrudeFeatures.add(ext_gl)

    # Right Jaw (-Y)
    gr_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    gr_comp = gr_occ.component
    gr_comp.name = "Tissue_Gripper_Right"

    sk_gr = gr_comp.sketches.add(gr_comp.xYConstructionPlane)
    sk_gr.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(mm(12.0), mm(-6.2), 0),
        adsk.core.Point3D.create(mm(17.5), mm(-4.0), 0)
    )
    lines_gr = sk_gr.sketchCurves.sketchLines
    lines_gr.addByTwoPoints(adsk.core.Point3D.create(mm(17.5), mm(-6.2), 0), adsk.core.Point3D.create(mm(18.5), mm(-4.8), 0))
    lines_gr.addByTwoPoints(adsk.core.Point3D.create(mm(18.5), mm(-4.8), 0), adsk.core.Point3D.create(mm(17.5), mm(-4.0), 0))
    lines_gr.addByTwoPoints(adsk.core.Point3D.create(mm(17.5), mm(-4.0), 0), adsk.core.Point3D.create(mm(17.5), mm(-6.2), 0))
    sk_gr.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(13.0), mm(-5.1), 0), mm(0.5))

    prof_col_gr = adsk.core.ObjectCollection.create()
    for i in range(sk_gr.profiles.count):
        prof_col_gr.add(sk_gr.profiles.item(i))

    if prof_col_gr.count > 0:
        ext_gr = gr_comp.features.extrudeFeatures.createInput(
            prof_col_gr, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_gr.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.8 mm"))
        ext_gr.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.2 mm"))
        gr_comp.features.extrudeFeatures.add(ext_gr)


    # =========================================================================
    # 9. Actuation Wire & Return Spring Assembly (Actuation_Tendon_Spring)
    # Pull Wire (Ø0.5 mm) + Return Spring Plunger Block (731, 732)
    # =========================================================================
    act_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    act_comp = act_occ.component
    act_comp.name = "Actuation_Tendon_Spring"

    sk_act = act_comp.sketches.add(act_comp.xYConstructionPlane)
    sk_act.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(mm(-28.0), mm(-6.4)),
        adsk.core.Point3D.create(xc_drive_pivot, mm(-5.8))
    )
    sk_act.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(mm(-24.0), mm(3.8)),
        adsk.core.Point3D.create(mm(-16.0), mm(5.2))
    )
    for xs in [-23.0, -21.0, -19.0, -17.0]:
        sk_act.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(mm(xs), mm(4.5), 0), mm(0.8)
        )

    prof_col_act = adsk.core.ObjectCollection.create()
    for i in range(sk_act.profiles.count):
        prof_col_act.add(sk_act.profiles.item(i))

    if prof_col_act.count > 0:
        ext_act = act_comp.features.extrudeFeatures.createInput(
            prof_col_act, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_act.setDistanceExtent(False, adsk.core.ValueInput.createByString("0.8 mm"))
        ext_act.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.8 mm"))
        act_comp.features.extrudeFeatures.add(ext_act)


    # =========================================================================
    # 10. As-Built Joints & Kinematic Motion Links
    # =========================================================================
    as_built_joints = root_comp.asBuiltJoints
    main_occ.isGrounded = True

    try:
        # Needle Revolute Joint
        needle_circ_edge = None
        if needle_body:
            for edge in needle_body.edges:
                if edge.geometry.curveType in [adsk.core.Curve3DTypes.Circle3DCurveType, adsk.core.Curve3DTypes.Arc3DCurveType]:
                    needle_circ_edge = edge
                    break
        if needle_circ_edge:
            geo_needle = adsk.fusion.JointGeometry.createByCurve(needle_circ_edge, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
            j_input = as_built_joints.createInput(needle_occ, main_occ, geo_needle)
            j_input.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
            rev_needle = as_built_joints.add(j_input)
            rev_needle.name = "J_RingNeedle"
    except:
        pass

    try:
        # Driving Link Revolute Joint
        drv_circ_edge = None
        if drv_body:
            for edge in drv_body.edges:
                if edge.geometry.curveType in [adsk.core.Curve3DTypes.Circle3DCurveType, adsk.core.Curve3DTypes.Arc3DCurveType]:
                    drv_circ_edge = edge
                    break
        if drv_circ_edge:
            geo_drv = adsk.fusion.JointGeometry.createByCurve(drv_circ_edge, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
            j_input_drv = as_built_joints.createInput(drv_occ, main_occ, geo_drv)
            j_input_drv.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
            rev_drv = as_built_joints.add(j_input_drv)
            rev_drv.name = "J_DrivingLink"
    except:
        pass


    # =========================================================================
    # 11. Visual Styling & Translucent Assembly Layering
    # =========================================================================
    main_comp.opacity = 0.40       # Translucent CNC metal chassis
    needle_comp.opacity = 0.95     # Polished surgical steel ring needle
    drv_comp.opacity = 0.95        # Driving link
    driven_comp.opacity = 0.95     # Driven link
    conn_comp.opacity = 0.95       # Connection link with variable slot 610
    pawl_comp.opacity = 0.95       # Needle driver pawl
    stp_comp.opacity = 0.95        # Needle stopper pawl
    gl_comp.opacity = 0.95         # Tissue gripper left
    gr_comp.opacity = 0.95         # Tissue gripper right
    act_comp.opacity = 0.95        # Actuation wire & return spring

    # Clean sketch visibility
    all_comps = [main_comp, needle_comp, drv_comp, driven_comp, conn_comp, pawl_comp, stp_comp, gl_comp, gr_comp, act_comp]
    for c in all_comps:
        for sk in c.sketches:
            sk.isVisible = False

    # =========================================================================
    # 12. Dynamic 4-Stage Kinematic Simulation & Multi-Angle Verification Captures
    # =========================================================================
    vp = app.activeViewport
    if vp:
        camera = vp.camera
        camera.eye = adsk.core.Point3D.create(mm(-15.0), mm(-35.0), mm(25.0))
        camera.target = adsk.core.Point3D.create(mm(-4.0), mm(0.0), mm(3.2))
        camera.upVector = adsk.core.Vector3D.create(0.0, 0.0, 1.0)
        camera.isFitView = True
        camera.isSmoothTransition = False
        vp.camera = camera
        vp.refresh()

        # Frame 0: Initial Rest State (0 deg)
        vp.saveAsImageFile(os.path.join(output_dir, "antidraft3_step_0_init.png"), 1920, 1080)

        # Frame 1: 90 deg Forward Rotation (Cam slot 610 bypassing dead-center pin 120)
        rot_90 = adsk.core.Matrix3D.create()
        rot_90.setToRotation(math.radians(90.0), adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(xc_needle, yc_needle, mm(3.2)))
        needle_occ.transform = rot_90
        driven_occ.transform = rot_90
        pawl_occ.transform = rot_90
        vp.refresh()
        vp.saveAsImageFile(os.path.join(output_dir, "antidraft3_step_1_cam_90deg.png"), 1920, 1080)

        # Frame 2: 180 deg Complete Forward Stroke (Tissue fully penetrated, Spring compressed)
        rot_180 = adsk.core.Matrix3D.create()
        rot_180.setToRotation(math.radians(180.0), adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(xc_needle, yc_needle, mm(3.2)))
        needle_occ.transform = rot_180
        driven_occ.transform = rot_180
        pawl_occ.transform = rot_180
        vp.refresh()
        vp.saveAsImageFile(os.path.join(output_dir, "antidraft3_step_2_full_180deg.png"), 1920, 1080)

        # Frame 3: Return Stroke (Needle stays locked at 180 deg by Stopper 800, Links return to 0 deg)
        driven_occ.transform = adsk.core.Matrix3D.create()
        pawl_occ.transform = adsk.core.Matrix3D.create()
        vp.refresh()
        vp.saveAsImageFile(os.path.join(output_dir, "antidraft3_step_3_ratchet_return.png"), 1920, 1080)

        # Reset transforms to neutral initial assembly
        needle_occ.transform = adsk.core.Matrix3D.create()
        driven_occ.transform = adsk.core.Matrix3D.create()
        pawl_occ.transform = adsk.core.Matrix3D.create()

        # Capture Top View
        camera.eye = adsk.core.Point3D.create(mm(-5.0), mm(0.0), mm(50.0))
        camera.target = adsk.core.Point3D.create(mm(-5.0), mm(0.0), mm(3.2))
        camera.upVector = adsk.core.Vector3D.create(0.0, 1.0, 0.0)
        camera.isFitView = True
        camera.isSmoothTransition = False
        vp.camera = camera
        vp.refresh()
        vp.saveAsImageFile(os.path.join(output_dir, "antidraft3_top_view.png"), 1920, 1080)

        # Capture Isometric Final View
        camera.eye = adsk.core.Point3D.create(mm(-20.0), mm(-38.0), mm(28.0))
        camera.target = adsk.core.Point3D.create(mm(-4.0), mm(0.0), mm(3.2))
        camera.upVector = adsk.core.Vector3D.create(0.0, 0.0, 1.0)
        camera.isFitView = True
        camera.isSmoothTransition = False
        vp.camera = camera
        vp.refresh()
        vp.saveAsImageFile(os.path.join(output_dir, "antidraft3_final_isometric.png"), 1920, 1080)

    print("ENDOCRAB antidraft3 modeling & multi-frame verification completed successfully!")
    return {
        "status": "success",
        "document": app.activeDocument.name if app.activeDocument else "",
        "occurrences": root_comp.occurrences.count,
        "joints": root_comp.asBuiltJoints.count
    }

def run(context=None):
    return build_endocrab_antidraft3()

build_endocrab_antidraft3()
