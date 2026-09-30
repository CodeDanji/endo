import adsk.core
import adsk.fusion
import traceback
import math
import os

def mm(val):
    """Convert millimeters to Fusion 360 database units (centimeters)."""
    return val / 10.0

def run(context=None):
    ui = None
    log_file = r"c:\Users\권원중학부재학바이오의공학부\Desktop\ENDO\output\build_stopper_log.txt"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("Starting build_endocrab_model.py execution...\n")
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

        # 0. Clean previous Knotting_Stopper_Assembly if it exists (preserve manual chassis/needle/slider)
        for i in range(root_comp.occurrences.count - 1, -1, -1):
            occ_i = root_comp.occurrences.item(i)
            if "Knotting_Stopper_Assembly" in occ_i.name or "Stopper" in occ_i.name:
                occ_i.deleteMe()

        temp_dir = os.environ.get("TEMP", "")
        output_dir = os.path.join(temp_dir, "AntigravityCAD")
        os.makedirs(output_dir, exist_ok=True)
        local_output = r"c:\Users\권원중학부재학바이오의공학부\Desktop\ENDO\output"
        os.makedirs(local_output, exist_ok=True)

        # =========================================================================
        # Reference Positions & Coordinates (Point #6 Exit: X=8.0~10.4mm, Y=5.2mm, Z=3.2mm)
        # Stopper Axis along X-Axis, Suture passing through hole along Z/Y
        # =========================================================================
        x_stopper_flange = mm(8.0)       # Stopper Flange Center X = 8.0 mm
        y_suture_axis = mm(5.2)          # Suture / Needle Track Y = 5.2 mm
        z_stopper_axis = mm(3.2)         # Mid-plane Z = 3.2 mm
        x_hole_center = mm(8.8)          # Transverse Hole Center X = 8.8 mm

        # =========================================================================
        # 1. Main Stopper Top Assembly Occurrence
        # =========================================================================
        stopper_top_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        stopper_top_comp = stopper_top_occ.component
        stopper_top_comp.name = "Knotting_Stopper_Assembly"

        # -------------------------------------------------------------------------
        # 1.1 Stopper Outer Housing (Ti-6Al-4V ELI)
        # OD 1.40mm x 2.40mm length, Flange OD 1.60mm x 0.30mm, Bore 0.96mm, Hole 0.35mm
        # -------------------------------------------------------------------------
        housing_occ = stopper_top_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        housing_comp = housing_occ.component
        housing_comp.name = "Stopper_Outer_Housing"

        # Extrude outer solid cylinder (OD 1.4mm, X: 8.0 to 10.4mm)
        sk_out = housing_comp.sketches.add(housing_comp.yZConstructionPlane)
        sk_out.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(y_suture_axis, z_stopper_axis, 0), mm(0.70)
        )
        housing_body = None
        if sk_out.profiles.count > 0:
            ext_in = housing_comp.features.extrudeFeatures.createInput(
                sk_out.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByString("2.4 mm"))
            ext_in.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(x_stopper_flange))
            h_ext = housing_comp.features.extrudeFeatures.add(ext_in)
            if h_ext.bodies.count > 0:
                housing_body = h_ext.bodies.item(0)

        # Add Flange (OD 1.6mm, X: 8.0 to 8.3mm)
        sk_fl = housing_comp.sketches.add(housing_comp.yZConstructionPlane)
        sk_fl.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(y_suture_axis, z_stopper_axis, 0), mm(0.80)
        )
        if sk_fl.profiles.count > 0:
            ext_fl = housing_comp.features.extrudeFeatures.createInput(
                sk_fl.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
            ext_fl.setDistanceExtent(False, adsk.core.ValueInput.createByString("0.3 mm"))
            ext_fl.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(x_stopper_flange))
            housing_comp.features.extrudeFeatures.add(ext_fl)

        # Cut Inner Bore (ID 0.96mm, X: 8.3 to 10.45mm)
        sk_bore = housing_comp.sketches.add(housing_comp.yZConstructionPlane)
        sk_bore.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(y_suture_axis, z_stopper_axis, 0), mm(0.48)
        )
        if sk_bore.profiles.count > 0:
            cut_b = housing_comp.features.extrudeFeatures.createInput(
                sk_bore.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut_b.setDistanceExtent(False, adsk.core.ValueInput.createByString("2.15 mm"))
            cut_b.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(x_stopper_flange + mm(0.3)))
            if housing_body:
                cut_b.participantBodies = [housing_body]
            housing_comp.features.extrudeFeatures.add(cut_b)

        # Cut Front Wire Hole (ID 0.40mm, X: 7.95 to 8.35mm)
        sk_fh = housing_comp.sketches.add(housing_comp.yZConstructionPlane)
        sk_fh.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(y_suture_axis, z_stopper_axis, 0), mm(0.20)
        )
        if sk_fh.profiles.count > 0:
            cut_fh = housing_comp.features.extrudeFeatures.createInput(
                sk_fh.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut_fh.setDistanceExtent(False, adsk.core.ValueInput.createByString("0.4 mm"))
            cut_fh.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(x_stopper_flange - mm(0.05)))
            if housing_body:
                cut_fh.participantBodies = [housing_body]
            housing_comp.features.extrudeFeatures.add(cut_fh)

        # Cut Transverse Suture Free-Pass Hole (Dia 0.35mm on XY plane at X=8.8mm, Y=5.2mm)
        sk_sh = housing_comp.sketches.add(housing_comp.xYConstructionPlane)
        sk_sh.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(x_hole_center, y_suture_axis, 0), mm(0.175)
        )
        if sk_sh.profiles.count > 0:
            cut_sh = housing_comp.features.extrudeFeatures.createInput(
                sk_sh.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut_sh.setDistanceExtent(True, adsk.core.ValueInput.createByString("2.0 mm")) # Symmetric cut through Z
            cut_sh.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(z_stopper_axis - mm(1.0)))
            if housing_body:
                cut_sh.participantBodies = [housing_body]
            housing_comp.features.extrudeFeatures.add(cut_sh)

        # -------------------------------------------------------------------------
        # 1.2 Stopper Inner Serrated Plunger (Ti-6Al-4V / PEEK)
        # OD 0.95mm x 1.60mm length, Transverse Hole Dia 0.30mm, 45/90 deg Teeth
        # -------------------------------------------------------------------------
        plunger_occ = stopper_top_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        plunger_comp = plunger_occ.component
        plunger_comp.name = "Stopper_Serrated_Plunger"

        # Plunger Base Solid Cylinder (X: 8.8 to 10.4 mm in Rest Position)
        sk_pl = plunger_comp.sketches.add(plunger_comp.yZConstructionPlane)
        sk_pl.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(y_suture_axis, z_stopper_axis, 0), mm(0.475) # OD 0.95mm
        )
        plunger_body = None
        if sk_pl.profiles.count > 0:
            ext_pl = plunger_comp.features.extrudeFeatures.createInput(
                sk_pl.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_pl.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.6 mm"))
            ext_pl.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(x_stopper_flange + mm(0.8)))
            p_ext = plunger_comp.features.extrudeFeatures.add(ext_pl)
            if p_ext.bodies.count > 0:
                plunger_body = p_ext.bodies.item(0)

        # Plunger Transverse Suture Hole (Dia 0.30mm on XY plane at X=9.4mm in Rest, moves to 8.8mm on Push)
        sk_ph = plunger_comp.sketches.add(plunger_comp.xYConstructionPlane)
        sk_ph.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(x_hole_center + mm(0.6), y_suture_axis, 0), mm(0.15)
        )
        if sk_ph.profiles.count > 0:
            cut_ph = plunger_comp.features.extrudeFeatures.createInput(
                sk_ph.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut_ph.setDistanceExtent(False, adsk.core.ValueInput.createByString("2.0 mm"))
            cut_ph.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(z_stopper_axis - mm(1.0)))
            if plunger_body:
                cut_ph.participantBodies = [plunger_body]
            plunger_comp.features.extrudeFeatures.add(cut_ph)

        # Serrated Teeth Notches (45 deg entry ramp, 90 deg vertical step)
        sk_teeth = plunger_comp.sketches.add(plunger_comp.xYConstructionPlane)
        lines_t = sk_teeth.sketchCurves.sketchLines
        for tx in [mm(9.0), mm(9.3), mm(9.6)]:
            lines_t.addByTwoPoints(adsk.core.Point3D.create(tx, y_suture_axis - mm(0.475), 0), adsk.core.Point3D.create(tx + mm(0.15), y_suture_axis - mm(0.325), 0))
            lines_t.addByTwoPoints(adsk.core.Point3D.create(tx + mm(0.15), y_suture_axis - mm(0.325), 0), adsk.core.Point3D.create(tx + mm(0.15), y_suture_axis - mm(0.475), 0))
            lines_t.addByTwoPoints(adsk.core.Point3D.create(tx + mm(0.15), y_suture_axis - mm(0.475), 0), adsk.core.Point3D.create(tx, y_suture_axis - mm(0.475), 0))
        
        prof_col_t = adsk.core.ObjectCollection.create()
        for i in range(sk_teeth.profiles.count):
            prof_col_t.add(sk_teeth.profiles.item(i))
        if prof_col_t.count > 0:
            cut_t = plunger_comp.features.extrudeFeatures.createInput(
                prof_col_t, adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut_t.setDistanceExtent(False, adsk.core.ValueInput.createByString("1.0 mm"))
            cut_t.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(z_stopper_axis - mm(0.5)))
            if plunger_body:
                cut_t.participantBodies = [plunger_body]
            plunger_comp.features.extrudeFeatures.add(cut_t)

        # -------------------------------------------------------------------------
        # 1.3 Micro Compression Spring (316LVM / Nitinol)
        # Parametric 3D Solid Coil via 3D FittedSpline + SweepFeatures
        # Wire Dia 0.10mm, OD 0.90mm (Mean Radius 0.40mm), Free Length 1.20mm (5 turns)
        # -------------------------------------------------------------------------
        spring_occ = stopper_top_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        spring_comp = spring_occ.component
        spring_comp.name = "Stopper_Micro_Spring"

        d_wire_mm = 0.10
        od_mm = 0.90
        free_len_mm = 1.20
        pitch_mm = 0.24
        
        r_mean = mm((od_mm - d_wire_mm) / 2.0)  # 0.04 cm
        d_wire = mm(d_wire_mm)                  # 0.01 cm
        total_len = mm(free_len_mm)             # 0.12 cm
        num_turns = free_len_mm / pitch_mm      # 5.0 turns
        points_per_turn = 24
        total_points = int(num_turns * points_per_turn)
        
        sk_helix = spring_comp.sketches.add(spring_comp.xYConstructionPlane)
        sk_helix.is3D = True
        points_col = adsk.core.ObjectCollection.create()
        
        x_spring_base = x_stopper_flange + mm(0.30)
        for i in range(total_points + 1):
            t = i / float(total_points)
            theta = t * num_turns * 2.0 * math.pi
            px = x_spring_base + (t * total_len)
            py = y_suture_axis + (r_mean * math.cos(theta))
            pz = z_stopper_axis + (r_mean * math.sin(theta))
            points_col.add(adsk.core.Point3D.create(px, py, pz))

        spline_curve = sk_helix.sketchCurves.sketchFittedSplines.add(points_col)
        path = spring_comp.features.createPath(spline_curve)
        
        plane_input = spring_comp.constructionPlanes.createInput()
        plane_input.setByDistanceOnPath(path, adsk.core.ValueInput.createByReal(0.0))
        start_plane = spring_comp.constructionPlanes.add(plane_input)
        
        sk_prof = spring_comp.sketches.add(start_plane)
        sk_prof.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), d_wire / 2.0
        )
        
        spring_body = None
        if sk_prof.profiles.count > 0:
            prof = sk_prof.profiles.item(0)
            sweep_input = spring_comp.features.sweepFeatures.createInput(
                prof, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            sweep_input.orientation = adsk.fusion.SweepOrientationTypes.PerpendicularOrientationType
            sweep_feat = spring_comp.features.sweepFeatures.add(sweep_input)
            if sweep_feat.bodies.count > 0:
                spring_body = sweep_feat.bodies.item(0)

        # -------------------------------------------------------------------------
        # 1.4 Coaxial Outer Push Sheath (OD 1.40mm / ID 0.95mm)
        # -------------------------------------------------------------------------
        sheath_occ = stopper_top_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        sheath_comp = sheath_occ.component
        sheath_comp.name = "Coaxial_Push_Sheath"

        sk_sh_tube = sheath_comp.sketches.add(sheath_comp.yZConstructionPlane)
        sk_sh_tube.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(y_suture_axis, z_stopper_axis, 0), mm(0.70) # OD 1.4mm
        )
        sk_sh_tube.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(y_suture_axis, z_stopper_axis, 0), mm(0.48) # ID 0.96mm
        )
        for prof_st in sk_sh_tube.profiles:
            if prof_st.profileLoops.count > 1:
                ext_st = sheath_comp.features.extrudeFeatures.createInput(
                    prof_st, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_st.setDistanceExtent(False, adsk.core.ValueInput.createByString("6.0 mm"))
                ext_st.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(x_stopper_flange + mm(2.4)))
                sheath_comp.features.extrudeFeatures.add(ext_st)
                break

        # -------------------------------------------------------------------------
        # 1.5 Inner Pull Wire & Nitinol U-Loop Tip (Dia 0.25mm wire, Loop width 3.8mm)
        # -------------------------------------------------------------------------
        wire_occ = stopper_top_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        wire_comp = wire_occ.component
        wire_comp.name = "Inner_Pull_Wire_Assembly"

        # Wire Central Core (Dia 0.25mm along X: 7.0 to 16.0mm)
        sk_wc = wire_comp.sketches.add(wire_comp.yZConstructionPlane)
        sk_wc.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(y_suture_axis, z_stopper_axis, 0), mm(0.125)
        )
        if sk_wc.profiles.count > 0:
            ext_wc = wire_comp.features.extrudeFeatures.createInput(
                sk_wc.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_wc.setDistanceExtent(False, adsk.core.ValueInput.createByString("9.0 mm"))
            ext_wc.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(x_stopper_flange - mm(1.0)))
            wire_comp.features.extrudeFeatures.add(ext_wc)

        # Nitinol U-Loop Tip at distal end (Loop width 3.8mm, Z=3.2mm)
        sk_loop = wire_comp.sketches.add(wire_comp.xYConstructionPlane)
        lines_lp = sk_loop.sketchCurves.sketchLines
        lines_lp.addByTwoPoints(adsk.core.Point3D.create(x_stopper_flange - mm(1.0), y_suture_axis - mm(1.9), 0), adsk.core.Point3D.create(x_stopper_flange - mm(2.8), y_suture_axis - mm(1.9), 0))
        lines_lp.addByTwoPoints(adsk.core.Point3D.create(x_stopper_flange - mm(2.8), y_suture_axis - mm(1.9), 0), adsk.core.Point3D.create(x_stopper_flange - mm(2.8), y_suture_axis + mm(1.9), 0))
        lines_lp.addByTwoPoints(adsk.core.Point3D.create(x_stopper_flange - mm(2.8), y_suture_axis + mm(1.9), 0), adsk.core.Point3D.create(x_stopper_flange - mm(1.0), y_suture_axis + mm(1.9), 0))
        lines_lp.addByTwoPoints(adsk.core.Point3D.create(x_stopper_flange - mm(1.0), y_suture_axis + mm(1.9), 0), adsk.core.Point3D.create(x_stopper_flange - mm(1.0), y_suture_axis - mm(1.9), 0))
        if sk_loop.profiles.count > 0:
            ext_lp = wire_comp.features.extrudeFeatures.createInput(
                sk_loop.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_lp.setDistanceExtent(False, adsk.core.ValueInput.createByString("0.3 mm"))
            ext_lp.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(z_stopper_axis - mm(0.15)))
            wire_comp.features.extrudeFeatures.add(ext_lp)


        # =========================================================================
        # 2. As-Built Joints & Kinematic Rest Position
        # =========================================================================
        stopper_top_occ.isGrounded = True
        as_built_joints = stopper_top_comp.asBuiltJoints

        # Find linear edge on plunger for slider joint along X-axis
        plunger_linear_edge = None
        if plunger_body:
            for edge in plunger_body.edges:
                if edge.geometry.curveType == adsk.core.Curve3DTypes.Line3DCurveType:
                    plunger_linear_edge = edge
                    break

        if plunger_linear_edge:
            geo_pl = adsk.fusion.JointGeometry.createByCurve(plunger_linear_edge, adsk.fusion.JointKeyPointTypes.MiddleKeyPoint)
            joint_input = as_built_joints.createInput(plunger_occ, housing_occ, geo_pl)
            joint_input.setAsSliderJointMotion(adsk.fusion.JointDirections.XAxisJointDirection)
            pl_joint = as_built_joints.add(joint_input)
            pl_joint.name = "Plunger_Spring_Locking_Joint"
            
            slider_motion = adsk.fusion.SliderJointMotion.cast(pl_joint.jointMotion)
            if slider_motion:
                limits = slider_motion.jointLimits
                limits.isMinimumValueEnabled = True
                limits.minimumValue = mm(0.0)
                limits.isMaximumValueEnabled = True
                limits.maximumValue = mm(0.6)
                limits.isRestPositionEnabled = True
                limits.restPositionValue = mm(0.0)

        # Hide all sketch entities for clear rendering
        for comp_i in [stopper_top_comp, housing_comp, plunger_comp, spring_comp, sheath_comp, wire_comp]:
            for sk in comp_i.sketches:
                sk.isVisible = False

        # Visual Material Opacities & Colors
        housing_comp.opacity = 0.85
        plunger_comp.opacity = 0.95
        spring_comp.opacity = 1.00
        sheath_comp.opacity = 0.50
        wire_comp.opacity = 0.95

        # =========================================================================
        # 3. 4-Stage Kinematic Simulation & Dynamic Viewport Capture
        # =========================================================================
        vp = app.activeViewport
        if vp:
            camera = vp.camera
            camera.eye = adsk.core.Point3D.create(mm(3.0), mm(-8.0), mm(12.0))
            camera.target = adsk.core.Point3D.create(mm(9.0), mm(5.2), mm(3.2))
            camera.upVector = adsk.core.Vector3D.create(0.0, 0.0, 1.0)
            camera.isFitView = False
            camera.isSmoothTransition = False
            vp.camera = camera
            vp.refresh()

            stages = [
                {
                    "id": 0,
                    "title": "Step 0: Push & Hold Open (Sheath +0.6mm, Free-Pass 100%)",
                    "fname": "stopper_step_0_open.png",
                    "sheath_x": mm(0.6),
                    "plunger_x": mm(-0.6),
                    "wire_x": mm(0.0)
                },
                {
                    "id": 1,
                    "title": "Step 1: Needle Penetration & Capture (Suture through Loop)",
                    "fname": "stopper_step_1_needle_pass.png",
                    "sheath_x": mm(0.6),
                    "plunger_x": mm(-0.6),
                    "wire_x": mm(0.0)
                },
                {
                    "id": 2,
                    "title": "Step 2: Hold Sheath & Pull Wire Cinch (Continuous Suture Cinch)",
                    "fname": "stopper_step_2_cinch.png",
                    "sheath_x": mm(0.6),
                    "plunger_x": mm(-0.6),
                    "wire_x": mm(4.0)
                },
                {
                    "id": 3,
                    "title": "Step 3: Sheath Release & Spring Self-Locking (>20N Lock)",
                    "fname": "stopper_step_3_locked.png",
                    "sheath_x": mm(2.5),
                    "plunger_x": mm(0.0),
                    "wire_x": mm(4.0)
                }
            ]

            for st in stages:
                t_sh = adsk.core.Matrix3D.create()
                t_sh.translation = adsk.core.Vector3D.create(st["sheath_x"], 0, 0)
                sheath_occ.transform = t_sh

                t_pl = adsk.core.Matrix3D.create()
                t_pl.translation = adsk.core.Vector3D.create(st["plunger_x"], 0, 0)
                plunger_occ.transform = t_pl

                t_wr = adsk.core.Matrix3D.create()
                t_wr.translation = adsk.core.Vector3D.create(st["wire_x"], 0, 0)
                wire_occ.transform = t_wr

                vp.refresh()
                adsk.doEvents()

                img_path1 = os.path.join(output_dir, st["fname"])
                img_path2 = os.path.join(local_output, st["fname"])
                vp.saveAsImageFile(img_path1, 1920, 1080)
                vp.saveAsImageFile(img_path2, 1920, 1080)

            # Reset transforms to open state for interactive viewing
            t_open = adsk.core.Matrix3D.create()
            t_open.translation = adsk.core.Vector3D.create(mm(0.6), 0, 0)
            sheath_occ.transform = t_open
            t_pl_open = adsk.core.Matrix3D.create()
            t_pl_open.translation = adsk.core.Vector3D.create(mm(-0.6), 0, 0)
            plunger_occ.transform = t_pl_open
            wire_occ.transform = adsk.core.Matrix3D.create()
            
            vp.refresh()
            vp.saveAsImageFile(os.path.join(local_output, "stopper_final_viewport.png"), 1920, 1080)

        with open(log_file, "a", encoding="utf-8") as f:
            f.write("SUCCESS: Stopper Assembly & 4-Stage Motion Built Successfully!\n")

    except Exception as e:
        err_msg = traceback.format_exc()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"ERROR OCCURRED:\n{err_msg}\n")
        app = adsk.core.Application.get()
        if app and app.userInterface:
            app.userInterface.messageBox('Stopper Build Failed:\n{}'.format(err_msg))
        raise e

if __name__ == "__main__":
    run(None)
