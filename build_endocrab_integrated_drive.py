import adsk.core
import adsk.fusion
import traceback
import math
import os

def mm(val):
    return val / 10.0

def run(context=None):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Ensure antidraft2 is active if open
        for doc in app.documents:
            if "antidraft2" in doc.name:
                doc.activate()
                break

        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            return

        root_comp = design.rootComponent

        # Clean all existing occurrences for clean rebuild
        while root_comp.occurrences.count > 0:
            root_comp.occurrences.item(0).deleteMe()

        # =========================================================================
        # Authentic ENDOCRAB Dimensions
        # =========================================================================
        xc_needle = mm(9.5)       # Needle Rotation Center X = 9.5 mm
        yc_needle = mm(0.0)       # Centerline Y = 0.0 mm
        zc_mid = mm(3.2)          # Mid-plane Z = 3.2 mm
        
        r_outer = mm(6.5)         # Needle Outer Radius = 6.5 mm (OD = 13.0 mm)
        r_inner = mm(5.2)         # Needle Inner Radius = 5.2 mm (ID = 10.4 mm)
        r_groove = mm(6.15)       # Capstan Cable Groove Radius = 6.15 mm
        y_tangent = yc_needle - r_groove  # Tangent line Y = -6.15 mm

        # =========================================================================
        # 1. Main Chassis (Endocrab_Main_Chassis)
        # =========================================================================
        main_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        main_comp = main_occ.component
        main_comp.name = "Endocrab_Main_Chassis"

        # 1.1 Base Metal Block (-28 to +16 mm X, -7 to +7 mm Y, 0 to 6.5 mm Z)
        sk_base = main_comp.sketches.add(main_comp.xYConstructionPlane)
        sk_base.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-28.0), mm(-7.0), 0),
            adsk.core.Point3D.create(mm(16.0), mm(7.0), 0)
        )
        if sk_base.profiles.count > 0:
            ext_base = main_comp.features.extrudeFeatures.createInput(
                sk_base.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_base.setDistanceExtent(False, adsk.core.ValueInput.createByString("6.5 mm"))
            main_comp.features.extrudeFeatures.add(ext_base)

        # 1.2 Distal Horseshoe Tissue Entry Opening (X: 9.5 to 17.0 mm, Y: -5.2 to +5.2 mm)
        sk_open_notch = main_comp.sketches.add(main_comp.xYConstructionPlane)
        sk_open_notch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc_needle, yc_needle, 0), mm(5.2)
        )
        sk_open_notch.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(xc_needle, mm(-5.2), 0),
            adsk.core.Point3D.create(mm(17.0), mm(5.2), 0)
        )
        prof_col_open = adsk.core.ObjectCollection.create()
        for i in range(sk_open_notch.profiles.count):
            prof_col_open.add(sk_open_notch.profiles.item(i))
        if prof_col_open.count > 0:
            ext_open = main_comp.features.extrudeFeatures.createInput(
                prof_col_open, adsk.fusion.FeatureOperations.CutFeatureOperation)
            ext_open.setDistanceExtent(False, adsk.core.ValueInput.createByString("6.5 mm"))
            main_comp.features.extrudeFeatures.add(ext_open)

        # 1.3 Circular Needle Guide Track (R: 4.9 to 6.9mm, Z: 2.0 to 4.5mm)
        sk_track = main_comp.sketches.add(main_comp.xYConstructionPlane)
        sk_track.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc_needle, yc_needle, 0), mm(6.9)
        )
        sk_track.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc_needle, yc_needle, 0), mm(4.9)
        )
        for prof_t in sk_track.profiles:
            if prof_t.profileLoops.count > 1:
                ext_track = main_comp.features.extrudeFeatures.createInput(
                    prof_t, adsk.fusion.FeatureOperations.CutFeatureOperation)
                ext_track.setDistanceExtent(False, adsk.core.ValueInput.createByString("2.5 mm"))
                ext_track.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.0 mm"))
                main_comp.features.extrudeFeatures.add(ext_track)
                break

        # 1.4 Slider Channel & Tangential Tendon Channel
        sk_slot = main_comp.sketches.add(main_comp.xYConstructionPlane)
        # Central slider guide channel
        sk_slot.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-26.0), mm(-2.0), 0),
            adsk.core.Point3D.create(mm(2.5), mm(2.0), 0)
        )
        # Slider lateral arm pocket
        sk_slot.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-14.0), mm(-6.6), 0),
            adsk.core.Point3D.create(mm(-5.0), mm(-1.8), 0)
        )
        # Lateral tendon routing channel extending to tangent point (X: -14.0 to 9.5 mm, Y: -6.6 to -5.6 mm)
        sk_slot.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-14.0), mm(-6.6), 0),
            adsk.core.Point3D.create(mm(9.5), mm(-5.6), 0)
        )
        prof_col_sl = adsk.core.ObjectCollection.create()
        for i in range(sk_slot.profiles.count):
            prof_col_sl.add(sk_slot.profiles.item(i))
        if prof_col_sl.count > 0:
            ext_slot = main_comp.features.extrudeFeatures.createInput(
                prof_col_sl, adsk.fusion.FeatureOperations.CutFeatureOperation)
            ext_slot.setDistanceExtent(False, adsk.core.ValueInput.createByString("3.5 mm"))
            ext_slot.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("1.5 mm"))
            main_comp.features.extrudeFeatures.add(ext_slot)

        # 1.5 Rear Bowden Cable Port
        sk_sheath = main_comp.sketches.add(main_comp.xYConstructionPlane)
        sk_sheath.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-29.0), mm(-1.2), 0),
            adsk.core.Point3D.create(mm(-24.0), mm(1.2), 0)
        )
        if sk_sheath.profiles.count > 0:
            ext_sheath = main_comp.features.extrudeFeatures.createInput(
                sk_sheath.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
            ext_sheath.setDistanceExtent(False, adsk.core.ValueInput.createByString("2.4 mm"))
            ext_sheath.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.05 mm"))
            main_comp.features.extrudeFeatures.add(ext_sheath)

        # 1.6 Fastener Mounting Holes
        sk_bolts = main_comp.sketches.add(main_comp.xYConstructionPlane)
        sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-20.0), mm(4.5), 0), mm(0.8))
        sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-20.0), mm(-4.5), 0), mm(0.8))
        sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-8.0), mm(4.5), 0), mm(0.8))
        sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(-8.0), mm(-4.5), 0), mm(0.8))
        sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(4.0), mm(5.2), 0), mm(0.8))
        sk_bolts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(mm(4.0), mm(-5.2), 0), mm(0.8))
        prof_col_b = adsk.core.ObjectCollection.create()
        for i in range(sk_bolts.profiles.count):
            prof_col_b.add(sk_bolts.profiles.item(i))
        if prof_col_b.count > 0:
            ext_b = main_comp.features.extrudeFeatures.createInput(
                prof_col_b, adsk.fusion.FeatureOperations.CutFeatureOperation)
            ext_b.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.8 mm"))
            ext_b.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("4.7 mm"))
            main_comp.features.extrudeFeatures.add(ext_b)


        # =========================================================================
        # 2. Ring Needle Assembly (Ring_Needle_Assembly)
        # =========================================================================
        needle_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        needle_comp = needle_occ.component
        needle_comp.name = "Ring_Needle_Assembly"

        # 2.1 Base Needle Ring
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
                base_ext = needle_comp.features.extrudeFeatures.add(ext_n)
                if base_ext.bodies.count > 0:
                    needle_body = base_ext.bodies.item(0)
                break

        # 2.2 Circumferential Capstan Cable Groove (R = 6.15mm, Z = 2.8 to 3.6mm)
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

        # 2.3 Wire Anchor Pocket (at xc_needle, yc_needle - 6.15mm)
        if needle_body:
            sk_anc = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
            sk_anc.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(xc_needle, y_tangent, 0), mm(0.65)
            )
            if sk_anc.profiles.count > 0:
                cut_anc = needle_comp.features.extrudeFeatures.createInput(
                    sk_anc.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
                cut_anc.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.4 mm"))
                cut_anc.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.5 mm"))
                cut_anc.participantBodies = [needle_body]
                needle_comp.features.extrudeFeatures.add(cut_anc)

        # 2.4 C-Shape Opening (90 degree opening at front-top)
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

        # 2.5 Needle Sharp Piercing Tip
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

        # 2.6 Suture Thread Eyelet Hole
        if needle_body:
            sk_eye = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
            sk_eye.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(xc_needle - mm(5.8), yc_needle + mm(2.5), 0), mm(0.35)
            )
            if sk_eye.profiles.count > 0:
                cut_eye = needle_comp.features.extrudeFeatures.createInput(
                    sk_eye.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
                cut_eye.setDistanceExtent(False, adsk.core.ValueInput.createByString("5.0 mm"))
                cut_eye.participantBodies = [needle_body]
                needle_comp.features.extrudeFeatures.add(cut_eye)

        # 2.7 Needle Capstan Anchor Ferrule (Seated inside needle anchor pocket)
        sk_ferrule = needle_comp.sketches.add(needle_comp.xYConstructionPlane)
        sk_ferrule.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc_needle, y_tangent, 0), mm(0.5)
        )
        if sk_ferrule.profiles.count > 0:
            ext_ferrule = needle_comp.features.extrudeFeatures.createInput(
                sk_ferrule.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
            ext_ferrule.setDistanceExtent(False, adsk.core.ValueInput.createByString("0.8 mm"))
            ext_ferrule.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.8 mm"))
            if needle_body:
                ext_ferrule.participantBodies = [needle_body]
            needle_comp.features.extrudeFeatures.add(ext_ferrule)


        # =========================================================================
        # 3. Wire Drive Slider with Integrated Drive Tendon (Wire_Drive_Slider)
        # Tendon wire is physically connected to and integrated into the slider
        # =========================================================================
        slider_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        slider_comp = slider_occ.component
        slider_comp.name = "Wire_Drive_Slider"

        # 3.1 Central Shuttle Body & Front Plunger
        sk_sl = slider_comp.sketches.add(slider_comp.xYConstructionPlane)
        # Main Shuttle
        sk_sl.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-22.0), mm(-1.8), 0),
            adsk.core.Point3D.create(mm(-6.0), mm(1.8), 0)
        )
        # Front Plunger
        sk_sl.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-6.0), mm(-0.8), 0),
            adsk.core.Point3D.create(mm(2.0), mm(0.8), 0)
        )
        # Lateral Clamping Arm reaching Y = -6.15mm
        sk_sl.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-10.0), mm(-6.4), 0),
            adsk.core.Point3D.create(mm(-6.0), mm(-1.8), 0)
        )
        # INTEGRATED PHYSICAL DRIVE TENDON WIRE:
        # Directly attached to slider clamping arm at X = -8.0mm, extending along tangent line Y = -6.15mm to X = 9.5mm
        sk_sl.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-8.0), mm(-6.4), 0),
            adsk.core.Point3D.create(xc_needle, mm(-5.9), 0)
        )

        prof_col_sl = adsk.core.ObjectCollection.create()
        for i in range(sk_sl.profiles.count):
            prof_col_sl.add(sk_sl.profiles.item(i))
        
        slider_body = None
        if prof_col_sl.count > 0:
            ext_sl = slider_comp.features.extrudeFeatures.createInput(
                prof_col_sl, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_sl.setDistanceExtent(False, adsk.core.ValueInput.createByString("2.5 mm"))
            ext_sl.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("2.0 mm"))
            b_ext = slider_comp.features.extrudeFeatures.add(ext_sl)
            if b_ext.bodies.count > 0:
                slider_body = b_ext.bodies.item(0)

        # 3.2 Bowden Wire Coupling Terminal Pin on Slider
        if slider_body:
            sk_spin = slider_comp.sketches.add(slider_comp.xYConstructionPlane)
            sk_spin.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(-16.0), mm(0.0), 0), mm(0.9)
            )
            if sk_spin.profiles.count > 0:
                ext_spin = slider_comp.features.extrudeFeatures.createInput(
                    sk_spin.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
                ext_spin.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.5 mm"))
                ext_spin.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("4.5 mm"))
                ext_spin.participantBodies = [slider_body]
                slider_comp.features.extrudeFeatures.add(ext_spin)

        # 3.3 Wire Clamping Boss & Pin on Lateral Arm
        if slider_body:
            sk_clamp = slider_comp.sketches.add(slider_comp.xYConstructionPlane)
            sk_clamp.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(-8.0), mm(-5.4), 0), mm(0.7)
            )
            if sk_clamp.profiles.count > 0:
                ext_clamp = slider_comp.features.extrudeFeatures.createInput(
                    sk_clamp.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
                ext_clamp.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.2 mm"))
                ext_clamp.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString("4.5 mm"))
                ext_clamp.participantBodies = [slider_body]
                slider_comp.features.extrudeFeatures.add(ext_clamp)


        # =========================================================================
        # 4. As-Built Joints & Kinematic Motion Links
        # =========================================================================
        as_built_joints = root_comp.asBuiltJoints
        main_occ.isGrounded = True

        rev_joint = None
        slider_joint = None

        # 4.1 Revolute Joint for Needle
        needle_circle_edge = None
        if needle_body:
            for edge in needle_body.edges:
                if edge.geometry.curveType == adsk.core.Curve3DTypes.Circle3DCurveType or edge.geometry.curveType == adsk.core.Curve3DTypes.Arc3DCurveType:
                    needle_circle_edge = edge
                    break

        if needle_circle_edge:
            geo_needle = adsk.fusion.JointGeometry.createByCurve(needle_circle_edge, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
            rev_joint_input = as_built_joints.createInput(needle_occ, main_occ, geo_needle)
            rev_joint_input.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
            rev_joint = as_built_joints.add(rev_joint_input)
            rev_joint.name = "Needle_Rotation_Joint"

        # 4.2 Slider Joint for Slider Shuttle along Longitudinal X-Axis
        slider_linear_edge = None
        if slider_body:
            for edge in slider_body.edges:
                if edge.geometry.curveType == adsk.core.Curve3DTypes.Line3DCurveType:
                    evaluator = edge.evaluator
                    ret, start_pt, end_pt = evaluator.getEndPoints()
                    if ret and abs(start_pt.y - end_pt.y) < 1e-4 and abs(start_pt.z - end_pt.z) < 1e-4 and abs(start_pt.x - end_pt.x) > 0.05:
                        slider_linear_edge = edge
                        break

        if slider_linear_edge:
            geo_slider = adsk.fusion.JointGeometry.createByCurve(slider_linear_edge, adsk.fusion.JointKeyPointTypes.MiddleKeyPoint)
            slider_joint_input = as_built_joints.createInput(slider_occ, main_occ, geo_slider)
            slider_joint_input.setAsSliderJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
            slider_joint = as_built_joints.add(slider_joint_input)
            slider_joint.name = "Wire_Slider_Joint"

        # 4.3 Motion Link: Capstan Tendon Transmission with Clockwise (CW) Rotation
        if needle_circle_edge and slider_linear_edge and rev_joint and slider_joint:
            motion_links = root_comp.motionLinks
            ml_input = motion_links.createInput(slider_joint, rev_joint)
            ml_input.distance = mm(math.pi * 6.15)
            ml_input.angle = -math.pi
            ml = motion_links.add(ml_input)
            ml.name = "Capstan_Tendon_Transmission"

        # Hide all sketch entities so viewports are clean
        for comp_i in [main_comp, needle_comp, slider_comp]:
            for sk in comp_i.sketches:
                sk.isVisible = False

        # Apply Opacity
        main_comp.opacity = 0.40
        needle_comp.opacity = 0.95
        slider_comp.opacity = 0.95

        vp = app.activeViewport
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

    except Exception as e:
        app = adsk.core.Application.get()
        if app and app.userInterface:
            app.userInterface.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        raise e

run(None)