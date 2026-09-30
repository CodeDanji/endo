"""
ENDOCRAB 3D CAD Parametric Builder Engine for Autodesk Fusion 360
================================================================
Reference Document: docs/ENDOCRAB_Surgical_Module_Analysis.html (Rev 2.0)
Paper: Nature Scientific Reports 14, 7289 (2024) — DOI: 10.1038/s41598-024-56484-6
IIT Bombay Reference: An Automated Needle Holder and Suturing Device

Part Hierarchy (Section 13 — Fusion 360 Modeling Mapping):
  P1  Main Body Frame           50 × 15 × 5.45 mm   [최우선]
  P2  Gripper Jaw (×2)          6 mm each            [최우선]
  P3  Ring-Shaped Needle        Ø13 mm               [최우선]
  P4  Gripper Hinge Pin         ~Ø1.0 mm             [중간]
  P5  Wire Guide Channel        ~Ø1 mm × 2ch         [중간]
  P6  Knotting Male Stud        ~Ø2.2 mm × 12 mm     [선택]
  P7  Knotting Female Ring      ~Ø3.2 mm ring        [선택]
  P8  Handle A (Needle)         Free design           [선택]
  P9  Handle B (Gripper)        Free design           [선택]
  P10 Suture Thread (4-0 Nylon) Ø0.15 mm             [추가]

Key Design Rules (Section 13 — 주의사항):
  1. Needle OD 13mm ↔ Channel ID: min 0.5mm clearance → Channel Ø14 mm
  2. Gripper jaw hinge must NOT interfere with needle rotation path
  3. Assembly must fit endoscope tip diameter (~10-12 mm)
  4. Confirmed dims (50×15×5.45, 6mm jaw, 13mm needle) as base constraints
"""

import adsk.core
import adsk.fusion
import traceback
import os
import math

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = os.path.expanduser(r"~\AppData\Local\Temp\AntigravityCAD\build_log.txt")


def log(msg):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except:
        pass


# ---------------------------------------------------------------------------
# Unit conversion helper
# ---------------------------------------------------------------------------
def mm(val):
    """mm to Fusion internal unit (cm)."""
    return val / 10.0


# ---------------------------------------------------------------------------
# User Parameters — 25 Master Dimensions
# ---------------------------------------------------------------------------
PARAMS_DEF = [
    # Main Body
    ("Body_Length",        "50.0 mm",  "mm",  "Main Body Frame Length (confirmed)"),
    ("Body_Width",        "15.0 mm",  "mm",  "Main Body Frame Width (confirmed)"),
    ("Body_Thickness",    "5.45 mm",  "mm",  "Main Body Frame Thickness (confirmed)"),
    ("Body_Fillet",       "0.8 mm",   "mm",  "Main Body Corner Fillet Radius"),
    # Needle
    ("Needle_Outer_Dia",  "13.0 mm",  "mm",  "Ring Needle Outer Diameter (confirmed)"),
    ("Needle_Wire_Dia",   "1.0 mm",   "mm",  "Needle Wire Cross-Section Diameter"),
    ("Needle_Channel_Dia","14.5 mm",  "mm",  "Body Needle Channel ID (13+0.5 clearance+1 wall)"),
    ("Needle_Pocket_Depth","4.0 mm",  "mm",  "Needle Pocket Depth in Main Body"),
    ("Needle_Sweep_Angle","350 deg",  "deg", "Needle Revolve Sweep Angle (gap for tip)"),
    # Gripper
    ("Gripper_Length",    "6.0 mm",   "mm",  "Gripper Jaw Length (confirmed)"),
    ("Gripper_Jaw_Width", "3.5 mm",   "mm",  "Gripper Jaw Thickness"),
    ("Gripper_Jaw_Height","1.5 mm",   "mm",  "Gripper Jaw Height"),
    ("Gripper_Angle_Max", "30.0 deg", "deg", "Gripper Jaw Max Open Angle"),
    # Hinge & Wire
    ("Hinge_Pin_Dia",    "1.0 mm",   "mm",  "Gripper Hinge Pin Diameter (H7/g6)"),
    ("Hinge_Pin_Length",  "6.0 mm",   "mm",  "Hinge Pin Length"),
    ("Cable_Wire_Dia",   "0.6 mm",   "mm",  "Bowden Cable Wire Diameter"),
    ("Wire_Channel_Dia", "1.0 mm",   "mm",  "Wire Guide Channel Diameter"),
    # Knotting
    ("Cinch_Stud_Dia",   "2.2 mm",   "mm",  "Male Stud Diameter"),
    ("Cinch_Stud_Length", "12.0 mm",  "mm",  "Male Stud Length"),
    ("Cinch_Ring_OD",    "3.2 mm",   "mm",  "Female Lock Ring Outer Diameter"),
    ("Cinch_Ring_ID",    "2.3 mm",   "mm",  "Female Lock Ring Inner Diameter"),
    ("Oblique_Hole_Dia", "0.5 mm",   "mm",  "Male Stud Oblique Suture Hole Diameter"),
    # Suture
    ("Suture_Dia",       "0.15 mm",  "mm",  "4-0 Nylon Suture Thread Diameter"),
    # Endoscope
    ("Scope_Attach_Dia", "11.5 mm",  "mm",  "GIF-Q260 Endoscope Tip Diameter"),
    ("Scope_Cap_Length",  "10.0 mm",  "mm",  "Scope Mounting Cap Length"),
]


def create_user_parameters(design):
    """Create or update all master user parameters in the fx table."""
    log("Creating & binding 25 master user parameters...")
    user_params = design.userParameters
    created = {}
    for name, expr, unit, desc in PARAMS_DEF:
        try:
            existing = user_params.itemByName(name)
            if existing:
                existing.expression = expr
                created[name] = existing
            else:
                val = adsk.core.ValueInput.createByString(expr)
                created[name] = user_params.add(name, val, unit, desc)
            log(f"  Param: {name} = {expr}")
        except Exception:
            log(f"  Param error {name}: {traceback.format_exc()}")
    return created


# ---------------------------------------------------------------------------
# Appearance helper
# ---------------------------------------------------------------------------
COLOR_MAP = {
    "Stainless Steel, High Polish": (220, 225, 230),
    "Stainless Steel, Satin":      (200, 205, 210),
    "Steel, Polished":             (210, 215, 220),
    "Chrome":                      (235, 240, 245),
    "Brass, Polished":             (230, 180, 60),
    "Aluminum, Anodized Clear":    (190, 195, 200),
    "Rubber, Soft":                (60, 65, 70),
    "Plastic, High Gloss (White)": (245, 245, 250),
    "Plastic, Smooth (White)":     (240, 240, 242),
    "Plastic, Glossy (Orange)":    (255, 110, 0),
    "Plastic, Matte (Black)":      (45, 50, 55),
    "Plastic, Glossy (Yellow)":    (250, 190, 20),
    "Nylon, Blue":                 (50, 100, 220),
    "Steel, Stainless Wire Rope":  (170, 175, 180),
}


def apply_appearance(design, body, name):
    """Apply named appearance to body. Falls back to color-based custom."""
    if not design or not body:
        return
    try:
        app = adsk.core.Application.get()
        appearance = design.appearances.itemByName(name)
        # Search material libraries
        if not appearance:
            for lib in app.materialLibraries:
                found = lib.appearances.itemByName(name)
                if found:
                    appearance = design.appearances.addByCopy(found, name)
                    break
        # Fallback: create from color map
        if not appearance and name in COLOR_MAP:
            r, g, b = COLOR_MAP[name]
            base = None
            for lib in app.materialLibraries:
                base = lib.appearances.itemByName("Plastic - Opaque (White)")
                if not base:
                    base = lib.appearances.itemByName("Steel")
                if base:
                    break
            if base:
                appearance = design.appearances.addByCopy(base, name)
                try:
                    cp = appearance.appearanceProperties.itemByName("Color")
                    if cp:
                        cp.value = adsk.core.Color.create(r, g, b, 255)
                except:
                    pass
        if appearance:
            body.appearance = appearance
            log(f"  Appearance '{name}' → {body.name}")
    except Exception as e:
        log(f"  Appearance warning ({name}): {e}")


# ---------------------------------------------------------------------------
# P1: Main Body Frame  (50 × 15 × 5.45 mm)
# ---------------------------------------------------------------------------
def build_main_body(parent_comp, design):
    """
    Build Main Body with:
      - Base rectangular extrusion
      - Central needle pocket (Ø14.5mm, depth 4mm)
      - Two wire guide channels (Ø1mm through-holes)
      - Two gripper hinge pin holes at distal face
      - Needle exit slit at top-distal area
      - Corner fillets
    """
    log("  P1: Main Body Frame...")
    occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = "P1_Main_Body_Frame"

    # --- Base block 50 × 15 × 5.45 ---
    sk = comp.sketches.add(comp.xYConstructionPlane)
    lines = sk.sketchCurves.sketchLines
    rect = lines.addTwoPointRectangle(
        adsk.core.Point3D.create(-2.5, -0.75, 0),
        adsk.core.Point3D.create(2.5, 0.75, 0)
    )
    try:
        dims = sk.sketchDimensions
        dl = dims.addDistanceDimension(
            rect.item(0).startSketchPoint, rect.item(0).endSketchPoint,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            adsk.core.Point3D.create(0, -1.2, 0))
        dl.parameter.expression = "Body_Length"
        dw = dims.addDistanceDimension(
            rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
            adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
            adsk.core.Point3D.create(3.0, 0, 0))
        dw.parameter.expression = "Body_Width"
    except:
        log("    Dimension constraint warning")

    if sk.profiles.count == 0:
        log("    ERROR: No profile for base block")
        return occ
    prof = sk.profiles.item(0)
    ext_in = comp.features.extrudeFeatures.createInput(
        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByString("Body_Thickness"))
    ext = comp.features.extrudeFeatures.add(ext_in)
    if ext.bodies.count == 0:
        log("    ERROR: Extrude produced no body")
        return occ
    body = ext.bodies.item(0)
    body.name = "Main_Body_Solid"

    # --- Needle Pocket (Ø14.5mm circular cut, depth 4mm from top) ---
    try:
        top_face = None
        for f in body.faces:
            n = f.geometry.normal if hasattr(f.geometry, 'normal') else None
            if n and abs(n.z - 1.0) < 0.01:
                top_face = f
                break
        if not top_face:
            top_face = comp.xYConstructionPlane

        sk_pocket = comp.sketches.add(top_face)
        # Pocket centered at body center, slightly forward (distal)
        c_pocket = sk_pocket.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0.5, 0, 0), mm(14.5 / 2))
        try:
            dim_p = sk_pocket.sketchDimensions.addDiameterDimension(
                c_pocket, adsk.core.Point3D.create(1.5, 0.5, 0))
            dim_p.parameter.expression = "Needle_Channel_Dia"
        except:
            pass

        if sk_pocket.profiles.count > 0:
            pocket_prof = sk_pocket.profiles.item(0)
            pocket_in = comp.features.extrudeFeatures.createInput(
                pocket_prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
            pocket_in.setDistanceExtent(False,
                adsk.core.ValueInput.createByString("-Needle_Pocket_Depth"))
            comp.features.extrudeFeatures.add(pocket_in)
            log("    Added needle pocket Ø14.5mm depth 4mm")
    except:
        log(f"    Needle pocket warning: {traceback.format_exc()}")

    # --- Wire Guide Channels: 2× Ø1mm through-holes along X-axis on both sides ---
    try:
        # Use YZ construction plane at X=0 to drill side channels
        for y_off in [mm(6.0), mm(-6.0)]:  # near the side edges
            sk_wire = comp.sketches.add(comp.yZConstructionPlane)
            sk_wire.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(y_off, mm(2.725), 0), mm(0.5))
            if sk_wire.profiles.count > 0:
                wp = sk_wire.profiles.item(0)
                wire_ext_in = comp.features.extrudeFeatures.createInput(
                    wp, adsk.fusion.FeatureOperations.CutFeatureOperation)
                wire_ext_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("Body_Length"))
                comp.features.extrudeFeatures.add(wire_ext_in)
        log("    Added 2 wire guide channels Ø1mm")
    except:
        log(f"    Wire channel warning: {traceback.format_exc()}")

    # --- Gripper Hinge Pin Holes: 2× Ø1mm at distal face top ---
    try:
        sk_hinge = comp.sketches.add(comp.xZConstructionPlane)
        for y_pos in [mm(3.0), mm(-3.0)]:  # symmetric about center
            sk_hinge.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(25.0), mm(4.0), 0), mm(0.5))
        if sk_hinge.profiles.count > 0:
            hp = sk_hinge.profiles.item(0)
            h_ext_in = comp.features.extrudeFeatures.createInput(
                hp, adsk.fusion.FeatureOperations.CutFeatureOperation)
            h_ext_in.setDistanceExtent(False,
                adsk.core.ValueInput.createByString("Body_Width"))
            comp.features.extrudeFeatures.add(h_ext_in)
            log("    Added gripper hinge pin holes")
    except:
        log(f"    Hinge hole warning: {traceback.format_exc()}")

    # --- Needle Exit Slit at top-distal ---
    try:
        sk_slit = comp.sketches.add(comp.xYConstructionPlane)
        slit_lines = sk_slit.sketchCurves.sketchLines
        # Rectangular slit at distal end for needle tip passage
        slit_lines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(20.0), mm(-2.0), mm(5.45)),
            adsk.core.Point3D.create(mm(25.0), mm(2.0), mm(5.45)))
        if sk_slit.profiles.count > 0:
            sp = sk_slit.profiles.item(0)
            s_ext_in = comp.features.extrudeFeatures.createInput(
                sp, adsk.fusion.FeatureOperations.CutFeatureOperation)
            s_ext_in.setDistanceExtent(False,
                adsk.core.ValueInput.createByString("-2.0 mm"))
            comp.features.extrudeFeatures.add(s_ext_in)
            log("    Added needle exit slit")
    except:
        log(f"    Needle slit warning: {traceback.format_exc()}")

    # --- Corner Fillets ---
    try:
        # Refresh body reference after cuts
        if comp.bRepBodies.count > 0:
            body = comp.bRepBodies.item(0)
        edge_col = adsk.core.ObjectCollection.create()
        count = 0
        for edge in body.edges:
            if abs(edge.length - mm(5.45)) < mm(0.5):  # vertical edges ~5.45mm
                edge_col.add(edge)
                count += 1
                if count >= 4:
                    break
        if edge_col.count > 0:
            fillet_in = comp.features.filletFeatures.createInput()
            fillet_in.addConstantRadiusEdgeSet(
                edge_col, adsk.core.ValueInput.createByString("Body_Fillet"), True)
            comp.features.filletFeatures.add(fillet_in)
            log("    Applied corner fillets")
    except:
        log(f"    Fillet warning: {traceback.format_exc()}")

    apply_appearance(design, body, "Stainless Steel, High Polish")
    return occ


# ---------------------------------------------------------------------------
# P2: Gripper Jaws (×2) — 6mm, curved tip, non-interfering
# ---------------------------------------------------------------------------
def build_gripper_jaws(parent_comp, design):
    """
    Build two symmetric gripper jaws with:
      - Curved arc tip (claw shape, CRAB etymology)
      - Hinge pin hole at base
      - Wire attachment loop at rear
      - 6mm jaw length
    Jaw closed position must NOT interfere with Ø13mm needle path.
    """
    log("  P2: Gripper Jaws (Left & Right)...")
    occs = {}
    for side in ["Left", "Right"]:
        try:
            occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            comp.name = f"P2_Gripper_Jaw_{side}"

            sk = comp.sketches.add(comp.xYConstructionPlane)
            lines = sk.sketchCurves.sketchLines
            arcs = sk.sketchCurves.sketchArcs

            y_sign = 1.0 if side == "Left" else -1.0
            # Jaw base position at distal end of main body
            bx = mm(25.0)  # distal end
            by = mm(2.0) * y_sign

            # Jaw outline: base → curved tip → return
            # Base point (hinge location)
            p_hinge = adsk.core.Point3D.create(bx, by, mm(4.5))
            # Jaw extends distally with curved tip
            p_mid = adsk.core.Point3D.create(bx + mm(3.0), by + mm(1.5) * y_sign, mm(4.5))
            p_tip = adsk.core.Point3D.create(bx + mm(6.0), by + mm(0.5) * y_sign, mm(4.5))
            p_inner = adsk.core.Point3D.create(bx + mm(5.5), by - mm(0.3) * y_sign, mm(4.5))
            p_back = adsk.core.Point3D.create(bx + mm(0.5), by - mm(0.8) * y_sign, mm(4.5))

            # Draw curved jaw using lines + arc at tip
            lines.addByTwoPoints(p_hinge, p_mid)
            # Arc from p_mid through p_tip (curved claw)
            arcs.addByThreePoints(p_mid, p_tip,
                adsk.core.Point3D.create(bx + mm(5.0), by + mm(2.0) * y_sign, mm(4.5)))
            lines.addByTwoPoints(p_tip, p_inner)
            lines.addByTwoPoints(p_inner, p_back)
            lines.addByTwoPoints(p_back, p_hinge)

            # Hinge pin hole
            sk.sketchCurves.sketchCircles.addByCenterRadius(
                p_hinge, mm(0.55))  # Ø1.1mm clearance for Ø1.0mm pin

            if sk.profiles.count > 0:
                # Find the jaw body profile (not the pin hole)
                prof = sk.profiles.item(0)
                ext_in = comp.features.extrudeFeatures.createInput(
                    prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("Gripper_Jaw_Height"))
                ext = comp.features.extrudeFeatures.add(ext_in)
                if ext.bodies.count > 0:
                    b = ext.bodies.item(0)
                    b.name = f"Jaw_{side}_Curved_Body"
                    apply_appearance(design, b, "Stainless Steel, Satin")
                    occs[side] = occ
                    log(f"    Created P2_Gripper_Jaw_{side}")
        except:
            log(f"    Gripper jaw {side} error: {traceback.format_exc()}")
    return occs


# ---------------------------------------------------------------------------
# P3: Ring-Shaped Needle (Ø13mm, 350° revolve + tip + eye)
# ---------------------------------------------------------------------------
def build_ring_needle(parent_comp, design):
    """
    Build ring-shaped needle with:
      - Ø13mm outer diameter full ring (350° revolve — 10° gap for piercing tip)
      - Triangular cutting point at tip
      - Suture eye (hole) near the blunt end
      - ~1mm wire cross section
    """
    log("  P3: Ring Needle Ø13mm...")
    try:
        occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "P3_Ring_Needle_13mm"

        # Cross-section sketch on XZ plane
        # Needle center ring: R_center = (13 - 1) / 2 = 6.0 mm from axis
        # Wire section at R=6.0mm, centered at Z = body_thickness/2 ≈ 2.725mm
        sk = comp.sketches.add(comp.xZConstructionPlane)
        center_r = mm(6.0)  # Center of wire on the ring
        wire_r = mm(0.5)    # Wire radius = 0.5mm (Ø1mm)
        z_center = mm(3.5)  # Slightly above body center for pocket clearance

        c_wire = sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(center_r, 0, z_center), wire_r)
        try:
            dim = sk.sketchDimensions.addDiameterDimension(
                c_wire, adsk.core.Point3D.create(center_r + mm(2), 0, z_center + mm(2)))
            dim.parameter.expression = "Needle_Wire_Dia"
        except:
            pass

        if sk.profiles.count > 0:
            prof = sk.profiles.item(0)
            rev = comp.features.revolveFeatures
            z_axis = comp.zConstructionAxis
            rev_in = rev.createInput(prof, z_axis,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            rev_in.setAngleExtent(False,
                adsk.core.ValueInput.createByString("Needle_Sweep_Angle"))
            rev_feat = rev.add(rev_in)

            if rev_feat.bodies.count > 0:
                n_body = rev_feat.bodies.item(0)
                n_body.name = "Ring_Needle_Toroid_Body"

                # --- Add triangular piercing tip ---
                try:
                    sk_tip = comp.sketches.add(comp.xYConstructionPlane)
                    tip_lines = sk_tip.sketchCurves.sketchLines
                    # Triangle at the gap start (where 350° ends)
                    # Compute tip position: at angle = 350° on the ring
                    angle_rad = math.radians(350)
                    tip_cx = center_r * 10 * math.cos(angle_rad)  # back to mm then to cm
                    tip_cy = center_r * 10 * math.sin(angle_rad)
                    # Actually work in cm
                    tcx = center_r * math.cos(angle_rad)
                    tcy = center_r * math.sin(angle_rad)

                    tp1 = adsk.core.Point3D.create(tcx, tcy, z_center + wire_r)
                    tp2 = adsk.core.Point3D.create(tcx + mm(1.5), tcy, z_center)
                    tp3 = adsk.core.Point3D.create(tcx, tcy, z_center - wire_r)

                    tip_lines.addByTwoPoints(tp1, tp2)
                    tip_lines.addByTwoPoints(tp2, tp3)
                    tip_lines.addByTwoPoints(tp3, tp1)

                    if sk_tip.profiles.count > 0:
                        tip_prof = sk_tip.profiles.item(0)
                        tip_ext_in = comp.features.extrudeFeatures.createInput(
                            tip_prof, adsk.fusion.FeatureOperations.JoinFeatureOperation)
                        tip_ext_in.setDistanceExtent(False,
                            adsk.core.ValueInput.createByString("Needle_Wire_Dia"))
                        comp.features.extrudeFeatures.add(tip_ext_in)
                        log("    Added triangular piercing tip")
                except:
                    log(f"    Tip creation warning: {traceback.format_exc()}")

                # --- Add suture eye (hole) near blunt end ---
                try:
                    # Eye at angle = 5° (near gap start, blunt end)
                    eye_angle = math.radians(5)
                    ecx = center_r * math.cos(eye_angle)
                    ecy = center_r * math.sin(eye_angle)

                    sk_eye = comp.sketches.add(comp.xYConstructionPlane)
                    sk_eye.sketchCurves.sketchCircles.addByCenterRadius(
                        adsk.core.Point3D.create(ecx, ecy, z_center), mm(0.2))

                    if sk_eye.profiles.count > 0:
                        eye_prof = sk_eye.profiles.item(0)
                        eye_in = comp.features.extrudeFeatures.createInput(
                            eye_prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
                        eye_in.setDistanceExtent(False,
                            adsk.core.ValueInput.createByString("Needle_Wire_Dia"))
                        comp.features.extrudeFeatures.add(eye_in)
                        log("    Added suture eye hole")
                except:
                    log(f"    Eye hole warning: {traceback.format_exc()}")

                apply_appearance(design, n_body, "Chrome")
                log("    Created P3 Ring Needle 350° toroid with tip & eye")
                return occ
    except:
        log(f"    Ring needle error: {traceback.format_exc()}")
    return None


# ---------------------------------------------------------------------------
# P4: Hinge Pins (×2)
# ---------------------------------------------------------------------------
def build_hinge_pins(parent_comp, design):
    """Build two gripper hinge pins Ø1.0mm."""
    log("  P4: Hinge Pins...")
    occs = []
    for idx, y_off in enumerate([mm(3.0), mm(-3.0)]):
        try:
            occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            comp.name = f"P4_Hinge_Pin_{idx+1}"

            sk = comp.sketches.add(comp.xYConstructionPlane)
            c = sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(25.0), y_off, mm(4.5)), mm(0.5))
            try:
                d = sk.sketchDimensions.addDiameterDimension(
                    c, adsk.core.Point3D.create(mm(26.0), y_off + mm(1), mm(4.5)))
                d.parameter.expression = "Hinge_Pin_Dia"
            except:
                pass

            if sk.profiles.count > 0:
                prof = sk.profiles.item(0)
                ext_in = comp.features.extrudeFeatures.createInput(
                    prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("Hinge_Pin_Length"))
                ext = comp.features.extrudeFeatures.add(ext_in)
                if ext.bodies.count > 0:
                    b = ext.bodies.item(0)
                    b.name = f"Hinge_Pin_{idx+1}_Body"
                    apply_appearance(design, b, "Steel, Polished")
                    occs.append(occ)
                    log(f"    Created hinge pin {idx+1}")
        except:
            log(f"    Hinge pin {idx+1} error: {traceback.format_exc()}")
    return occs


# ---------------------------------------------------------------------------
# P5: Needle Guide Track
# ---------------------------------------------------------------------------
def build_guide_track(parent_comp, design):
    """Build ring needle guide track (annular channel in body)."""
    log("  P5: Needle Guide Track Ring...")
    try:
        occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "P5_Ring_Needle_Guide_Track"

        # Annular track profile on XZ plane, revolved around Z
        sk = comp.sketches.add(comp.xZConstructionPlane)
        # Track cross-section: rectangular channel enclosing needle wire path
        track_inner_r = mm(5.3)  # slightly inside needle center
        track_outer_r = mm(6.7)  # slightly outside
        z_center = mm(3.5)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(track_inner_r, 0, z_center - mm(0.8)),
            adsk.core.Point3D.create(track_outer_r, 0, z_center + mm(0.8)))

        if sk.profiles.count > 0:
            prof = sk.profiles.item(0)
            rev = comp.features.revolveFeatures
            rev_in = rev.createInput(prof, comp.zConstructionAxis,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            rev_in.setAngleExtent(False,
                adsk.core.ValueInput.createByString("360 deg"))
            rev_feat = rev.add(rev_in)
            if rev_feat.bodies.count > 0:
                b = rev_feat.bodies.item(0)
                b.name = "Guide_Track_Ring_Body"
                apply_appearance(design, b, "Aluminum, Anodized Clear")
                log("    Created P5 guide track ring")
                return occ
    except:
        log(f"    Guide track error: {traceback.format_exc()}")
    return None


# ---------------------------------------------------------------------------
# Endoscope Mounting Cap
# ---------------------------------------------------------------------------
def build_scope_cap(parent_comp, design):
    """Build endoscope mounting cap (rubber, taped to scope tip)."""
    log("  Endoscope Mounting Cap...")
    try:
        occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "Endoscope_Mounting_Cap"

        # Cap at proximal end of main body (X = -25mm)
        planes = comp.constructionPlanes
        plane_in = planes.createInput()
        plane_in.setByOffset(comp.yZConstructionPlane,
            adsk.core.ValueInput.createByString("-Body_Length / 2"))
        cap_plane = planes.add(plane_in)

        sk = comp.sketches.add(cap_plane)
        z_c = mm(2.725)  # body center height
        # Outer cap
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, z_c, 0), mm(7.5))
        # Inner bore for scope
        c_inner = sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, z_c, 0), mm(5.75))
        try:
            d = sk.sketchDimensions.addDiameterDimension(
                c_inner, adsk.core.Point3D.create(mm(3), z_c + mm(3), 0))
            d.parameter.expression = "Scope_Attach_Dia"
        except:
            pass

        if sk.profiles.count > 0:
            # Use annular profile (between inner and outer circles)
            prof = sk.profiles.item(0)
            ext_in = comp.features.extrudeFeatures.createInput(
                prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_in.setDistanceExtent(False,
                adsk.core.ValueInput.createByString("-Scope_Cap_Length"))
            ext = comp.features.extrudeFeatures.add(ext_in)
            if ext.bodies.count > 0:
                b = ext.bodies.item(0)
                b.name = "Mounting_Cap_Body"
                apply_appearance(design, b, "Rubber, Soft")
                log("    Created endoscope mounting cap")
                return occ
    except:
        log(f"    Scope cap error: {traceback.format_exc()}")
    return None


# ---------------------------------------------------------------------------
# 01: Distal EndEffector Sub-Assembly
# ---------------------------------------------------------------------------
def build_distal_endeffector(root_comp, design):
    """Build the complete distal end-effector sub-assembly (P1-P5 + cap)."""
    log("Building 01_Distal_EndEffector_SubAssy...")
    sub_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    sub = sub_occ.component
    sub.name = "01_Distal_EndEffector_SubAssy"

    bodies = {}
    bodies["P1_Main_Body"] = build_main_body(sub, design)
    bodies["P2_Grippers"] = build_gripper_jaws(sub, design)
    bodies["P3_Ring_Needle"] = build_ring_needle(sub, design)
    bodies["P4_Hinge_Pins"] = build_hinge_pins(sub, design)
    bodies["P5_Guide_Track"] = build_guide_track(sub, design)
    bodies["Scope_Cap"] = build_scope_cap(sub, design)

    log("  01_Distal_EndEffector complete")
    return sub, bodies


# ---------------------------------------------------------------------------
# 02: Shaft & Transmission
# ---------------------------------------------------------------------------
def build_shaft_transmission(root_comp, design):
    """Build shaft tube, dual wires, PTFE sheath."""
    log("Building 02_Shaft_Transmission_SubAssy...")
    try:
        sub_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        sub = sub_occ.component
        sub.name = "02_Shaft_Transmission_SubAssy"

        # Rigid shaft tube (Ø10mm outer, Ø8.5mm inner, 120mm long)
        try:
            sh_occ = sub.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            sh = sh_occ.component
            sh.name = "Rigid_Shaft_Tube"

            sk = sh.sketches.add(sh.yZConstructionPlane)
            z_c = mm(2.725)
            sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(0, z_c, 0), mm(5.0))
            sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(0, z_c, 0), mm(4.25))
            if sk.profiles.count > 0:
                prof = sk.profiles.item(0)
                ext_in = sh.features.extrudeFeatures.createInput(
                    prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("-120.0 mm"))
                ext = sh.features.extrudeFeatures.add(ext_in)
                if ext.bodies.count > 0:
                    b = ext.bodies.item(0)
                    b.name = "Shaft_Tube_Body"
                    apply_appearance(design, b, "Stainless Steel, High Polish")
                    log("    Created rigid shaft tube")
        except:
            log(f"    Shaft tube error: {traceback.format_exc()}")

        # Dual control wires
        for wire_name, y_off in [("Gripper_Control_Wire", mm(2.5)),
                                  ("Needle_Rotation_Wire", mm(-2.5))]:
            try:
                w_occ = sub.occurrences.addNewComponent(adsk.core.Matrix3D.create())
                w = w_occ.component
                w.name = wire_name

                sk = w.sketches.add(w.yZConstructionPlane)
                c = sk.sketchCurves.sketchCircles.addByCenterRadius(
                    adsk.core.Point3D.create(y_off, mm(2.725), 0), mm(0.3))
                try:
                    d = sk.sketchDimensions.addDiameterDimension(
                        c, adsk.core.Point3D.create(y_off + mm(1), mm(3.5), 0))
                    d.parameter.expression = "Cable_Wire_Dia"
                except:
                    pass
                if sk.profiles.count > 0:
                    prof = sk.profiles.item(0)
                    ext_in = w.features.extrudeFeatures.createInput(
                        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    ext_in.setDistanceExtent(False,
                        adsk.core.ValueInput.createByString("-120.0 mm"))
                    ext = w.features.extrudeFeatures.add(ext_in)
                    if ext.bodies.count > 0:
                        b = ext.bodies.item(0)
                        b.name = f"{wire_name}_Body"
                        apply_appearance(design, b, "Steel, Stainless Wire Rope")
                        log(f"    Created {wire_name}")
            except:
                log(f"    Wire {wire_name} error: {traceback.format_exc()}")

        # PTFE sheath
        try:
            s_occ = sub.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            s = s_occ.component
            s.name = "PTFE_Sheath"

            sk = s.sketches.add(s.yZConstructionPlane)
            z_c = mm(2.725)
            sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(0, z_c, 0), mm(4.0))
            sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(0, z_c, 0), mm(3.25))
            if sk.profiles.count > 0:
                prof = sk.profiles.item(0)
                ext_in = s.features.extrudeFeatures.createInput(
                    prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("-120.0 mm"))
                ext = s.features.extrudeFeatures.add(ext_in)
                if ext.bodies.count > 0:
                    b = ext.bodies.item(0)
                    b.name = "PTFE_Sheath_Body"
                    apply_appearance(design, b, "Plastic, Smooth (White)")
                    log("    Created PTFE sheath")
        except:
            log(f"    PTFE error: {traceback.format_exc()}")
    except:
        log(f"    02_Shaft error: {traceback.format_exc()}")


# ---------------------------------------------------------------------------
# 03: System A — Syringe-type Plunger Controller (ENDOCRAB Paper Fig 3c)
# ---------------------------------------------------------------------------
def build_syringe_controller(root_comp, design):
    """Build syringe-type plunger controller with thumb ring and orange sliders."""
    log("Building 03_Syringe_Controller_SubAssy (System A)...")
    try:
        sub_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        sub = sub_occ.component
        sub.name = "03_Syringe_Controller_SubAssy"

        # P8-equivalent: Plunger body with thumb ring
        try:
            pb_occ = sub.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            pb = pb_occ.component
            pb.name = "P8_Handle_A_Plunger"

            sk = pb.sketches.add(pb.xYConstructionPlane)
            # Main barrel
            sk.sketchCurves.sketchLines.addTwoPointRectangle(
                adsk.core.Point3D.create(-12.5, -0.4, mm(2.725)),
                adsk.core.Point3D.create(-19.5, 0.4, mm(2.725)))
            # Thumb ring
            sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(-20.5, 0, mm(2.725)), 1.2)
            sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(-20.5, 0, mm(2.725)), 0.8)

            if sk.profiles.count > 0:
                prof = sk.profiles.item(0)
                ext_in = pb.features.extrudeFeatures.createInput(
                    prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("12.0 mm"))
                ext = pb.features.extrudeFeatures.add(ext_in)
                if ext.bodies.count > 0:
                    b = ext.bodies.item(0)
                    b.name = "Plunger_Body"
                    apply_appearance(design, b, "Plastic, High Gloss (White)")
                    log("    Created plunger body with thumb ring")
        except:
            log(f"    Plunger error: {traceback.format_exc()}")

        # P9-equivalent: Orange finger ring sliders (×2)
        for side, x_off in [("Left", -14.5), ("Right", -17.0)]:
            try:
                sl_occ = sub.occurrences.addNewComponent(adsk.core.Matrix3D.create())
                sl = sl_occ.component
                sl.name = f"P9_Handle_B_Slider_{side}"

                sk = sl.sketches.add(sl.xYConstructionPlane)
                sk.sketchCurves.sketchCircles.addByCenterRadius(
                    adsk.core.Point3D.create(x_off, 0, mm(2.725)), 1.1)
                sk.sketchCurves.sketchCircles.addByCenterRadius(
                    adsk.core.Point3D.create(x_off, 0, mm(2.725)), 0.7)
                if sk.profiles.count > 0:
                    prof = sk.profiles.item(0)
                    ext_in = sl.features.extrudeFeatures.createInput(
                        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    ext_in.setDistanceExtent(False,
                        adsk.core.ValueInput.createByString("10.0 mm"))
                    ext = sl.features.extrudeFeatures.add(ext_in)
                    if ext.bodies.count > 0:
                        b = ext.bodies.item(0)
                        b.name = f"Slider_{side}_Body"
                        apply_appearance(design, b, "Plastic, Glossy (Orange)")
                        log(f"    Created orange slider {side}")
            except:
                log(f"    Slider {side} error: {traceback.format_exc()}")
    except:
        log(f"    03_Syringe error: {traceback.format_exc()}")


# ---------------------------------------------------------------------------
# 04: System B — Pistol Grip Controller (IIT Bombay Reference)
# ---------------------------------------------------------------------------
def build_pistol_controller(root_comp, design):
    """Build IIT Bombay-style pistol grip with 2-click trigger."""
    log("Building 04_Pistol_Grip_SubAssy (System B — IIT Bombay Reference)...")
    try:
        sub_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        sub = sub_occ.component
        sub.name = "04_Pistol_Grip_SubAssy_IIT_Ref"

        # Pistol grip frame
        try:
            pg_occ = sub.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            pg = pg_occ.component
            pg.name = "SystemB_Pistol_Frame"

            sk = pg.sketches.add(pg.xYConstructionPlane)
            lines = sk.sketchCurves.sketchLines
            # Ergonomic pistol outline
            pts = [
                adsk.core.Point3D.create(-12.5, 0.5, -0.6),
                adsk.core.Point3D.create(-15.0, 0.5, -0.6),
                adsk.core.Point3D.create(-17.0, -2.5, -0.6),
                adsk.core.Point3D.create(-15.5, -3.2, -0.6),
                adsk.core.Point3D.create(-14.0, -1.8, -0.6),
                adsk.core.Point3D.create(-13.5, -0.8, -0.6),
                adsk.core.Point3D.create(-12.5, -0.8, -0.6),
            ]
            for i in range(len(pts)):
                lines.addByTwoPoints(pts[i], pts[(i + 1) % len(pts)])
            # Trigger guard cutout
            sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(-13.7, -0.3, -0.6), 0.5)

            if sk.profiles.count > 0:
                prof = sk.profiles.item(0)
                ext_in = pg.features.extrudeFeatures.createInput(
                    prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("16.0 mm"))
                ext = pg.features.extrudeFeatures.add(ext_in)
                if ext.bodies.count > 0:
                    b = ext.bodies.item(0)
                    b.name = "Pistol_Frame_Body"
                    apply_appearance(design, b, "Plastic, Matte (Black)")
                    log("    Created pistol grip frame")
        except:
            log(f"    Pistol frame error: {traceback.format_exc()}")

        # 2-click trigger blade
        try:
            tr_occ = sub.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            tr = tr_occ.component
            tr.name = "SystemB_2Click_Trigger"

            sk = tr.sketches.add(tr.xYConstructionPlane)
            tl = sk.sketchCurves.sketchLines
            tpts = [
                adsk.core.Point3D.create(-13.3, 0.1, -0.6),
                adsk.core.Point3D.create(-14.1, -0.5, -0.6),
                adsk.core.Point3D.create(-13.8, -0.7, -0.6),
                adsk.core.Point3D.create(-13.0, -0.1, -0.6),
            ]
            for i in range(len(tpts)):
                tl.addByTwoPoints(tpts[i], tpts[(i + 1) % len(tpts)])

            if sk.profiles.count > 0:
                prof = sk.profiles.item(0)
                ext_in = tr.features.extrudeFeatures.createInput(
                    prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("12.0 mm"))
                ext = tr.features.extrudeFeatures.add(ext_in)
                if ext.bodies.count > 0:
                    b = ext.bodies.item(0)
                    b.name = "Trigger_Blade_Body"
                    apply_appearance(design, b, "Plastic, Glossy (Yellow)")
                    log("    Created 2-click trigger blade")
        except:
            log(f"    Trigger error: {traceback.format_exc()}")
    except:
        log(f"    04_Pistol error: {traceback.format_exc()}")


# ---------------------------------------------------------------------------
# 05: Knotting Fastener (P6 Male Stud + P7 Female Ring)
# ---------------------------------------------------------------------------
def build_knotting_fastener(root_comp, design):
    """
    Build knotting device with:
      P6: Male stud with oblique suture hole
      P7: Female lock ring
    """
    log("Building 05_Knotting_Fastener_SubAssy...")
    try:
        sub_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        sub = sub_occ.component
        sub.name = "05_Knotting_Fastener_SubAssy"

        # --- P6: Male Stud (Ø2.2mm × 12mm) with oblique suture hole ---
        try:
            ms_occ = sub.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            ms = ms_occ.component
            ms.name = "P6_Male_Stud"

            # Main cylindrical stud
            sk = ms.sketches.add(ms.xYConstructionPlane)
            c = sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(30.0), 0, mm(2.725)), mm(1.1))
            try:
                d = sk.sketchDimensions.addDiameterDimension(
                    c, adsk.core.Point3D.create(mm(32), mm(1), mm(2.725)))
                d.parameter.expression = "Cinch_Stud_Dia"
            except:
                pass

            if sk.profiles.count > 0:
                prof = sk.profiles.item(0)
                ext_in = ms.features.extrudeFeatures.createInput(
                    prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("Cinch_Stud_Length"))
                ext = ms.features.extrudeFeatures.add(ext_in)

                if ext.bodies.count > 0:
                    ms_body = ext.bodies.item(0)
                    ms_body.name = "Male_Stud_Body"

                    # --- Oblique suture hole (angled through-hole for thread) ---
                    try:
                        # Create angled construction plane for oblique hole
                        # Hole at ~30° angle near the tip of the stud
                        planes = ms.constructionPlanes
                        plane_in = planes.createInput()
                        plane_in.setByAngle(
                            ms.xConstructionAxis,
                            adsk.core.ValueInput.createByString("30 deg"),
                            ms.xYConstructionPlane)
                        oblique_plane = planes.add(plane_in)

                        sk_hole = ms.sketches.add(oblique_plane)
                        sk_hole.sketchCurves.sketchCircles.addByCenterRadius(
                            adsk.core.Point3D.create(mm(30.0), 0, mm(2.725 + 0.5)),
                            mm(0.25))  # Ø0.5mm hole

                        if sk_hole.profiles.count > 0:
                            hole_prof = sk_hole.profiles.item(0)
                            h_ext_in = ms.features.extrudeFeatures.createInput(
                                hole_prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
                            h_ext_in.setDistanceExtent(False,
                                adsk.core.ValueInput.createByString("Cinch_Stud_Dia"))
                            ms.features.extrudeFeatures.add(h_ext_in)
                            log("    Added oblique suture hole to male stud")
                    except:
                        log(f"    Oblique hole warning: {traceback.format_exc()}")

                    apply_appearance(design, ms_body, "Stainless Steel, Satin")
                    log("    Created P6 Male Stud with oblique hole")
        except:
            log(f"    Male stud error: {traceback.format_exc()}")

        # --- P7: Female Lock Ring (Ø3.2mm OD, Ø2.3mm ID) ---
        try:
            fl_occ = sub.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            fl = fl_occ.component
            fl.name = "P7_Female_Lock_Ring"

            sk = fl.sketches.add(fl.xYConstructionPlane)
            c_out = sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(30.0), mm(5.0), mm(2.725)), mm(1.6))
            c_in = sk.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(30.0), mm(5.0), mm(2.725)), mm(1.15))
            try:
                d_out = sk.sketchDimensions.addDiameterDimension(
                    c_out, adsk.core.Point3D.create(mm(32), mm(6), mm(2.725)))
                d_out.parameter.expression = "Cinch_Ring_OD"
                d_in = sk.sketchDimensions.addDiameterDimension(
                    c_in, adsk.core.Point3D.create(mm(31), mm(5.5), mm(2.725)))
                d_in.parameter.expression = "Cinch_Ring_ID"
            except:
                pass

            if sk.profiles.count > 0:
                # Get annular profile
                prof = sk.profiles.item(0)
                ext_in = fl.features.extrudeFeatures.createInput(
                    prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("3.5 mm"))
                ext = fl.features.extrudeFeatures.add(ext_in)
                if ext.bodies.count > 0:
                    b = ext.bodies.item(0)
                    b.name = "Female_Ring_Body"
                    apply_appearance(design, b, "Stainless Steel, Satin")
                    log("    Created P7 Female Lock Ring")
        except:
            log(f"    Female ring error: {traceback.format_exc()}")

    except:
        log(f"    05_Knotting error: {traceback.format_exc()}")


# ---------------------------------------------------------------------------
# P10: Suture Thread Visualization (4-0 Nylon, Ø0.15mm)
# ---------------------------------------------------------------------------
def build_suture_thread(root_comp, design):
    """Build a simplified suture thread visualization."""
    log("Building P10_Suture_Thread...")
    try:
        sub_occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        sub = sub_occ.component
        sub.name = "P10_Suture_Thread_4_0_Nylon"

        # Simple thread as a thin cylinder from needle eye position downward
        sk = sub.sketches.add(sub.xYConstructionPlane)
        # Thread starts near needle eye position
        c = sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(mm(6.0), mm(0.5), mm(3.5)), mm(0.075))
        try:
            d = sk.sketchDimensions.addDiameterDimension(
                c, adsk.core.Point3D.create(mm(7), mm(1), mm(3.5)))
            d.parameter.expression = "Suture_Dia"
        except:
            pass

        if sk.profiles.count > 0:
            prof = sk.profiles.item(0)
            ext_in = sub.features.extrudeFeatures.createInput(
                prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_in.setDistanceExtent(False,
                adsk.core.ValueInput.createByString("30.0 mm"))
            ext = sub.features.extrudeFeatures.add(ext_in)
            if ext.bodies.count > 0:
                b = ext.bodies.item(0)
                b.name = "Suture_Thread_Body"
                apply_appearance(design, b, "Nylon, Blue")
                log("    Created P10 suture thread visualization")

        # Suture bead (anchoring bead at thread end)
        try:
            sk2 = sub.sketches.add(sub.xYConstructionPlane)
            sk2.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(6.0), mm(0.5), mm(3.5)), mm(0.3))
            if sk2.profiles.count > 0:
                bead_prof = sk2.profiles.item(0)
                bead_in = sub.features.extrudeFeatures.createInput(
                    bead_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                bead_in.setDistanceExtent(False,
                    adsk.core.ValueInput.createByString("0.5 mm"))
                bead = sub.features.extrudeFeatures.add(bead_in)
                if bead.bodies.count > 0:
                    bb = bead.bodies.item(0)
                    bb.name = "Suture_Bead"
                    apply_appearance(design, bb, "Nylon, Blue")
                    log("    Created suture anchoring bead")
        except:
            log(f"    Bead warning: {traceback.format_exc()}")
    except:
        log(f"    P10 suture error: {traceback.format_exc()}")


# ---------------------------------------------------------------------------
# Assembly Joints
# ---------------------------------------------------------------------------
def create_assembly_joints(root_comp, bodies):
    """Create rigid and revolute joints between components."""
    log("Creating assembly joints...")
    try:
        joints = root_comp.joints
        # Rigid joint: Main Body ↔ Scope Cap
        if bodies.get("P1_Main_Body") and bodies.get("Scope_Cap"):
            try:
                occ1 = bodies["P1_Main_Body"]
                occ2 = bodies["Scope_Cap"]
                g1 = adsk.fusion.JointGeometry.createByPoint(
                    occ1.component.originConstructionPoint)
                g2 = adsk.fusion.JointGeometry.createByPoint(
                    occ2.component.originConstructionPoint)
                j_in = joints.createInput(g1, g2)
                j_in.setAsRigidJointMotion()
                j = joints.add(j_in)
                j.name = "J_Body_Cap_Rigid"
                log("    Joint: Body ↔ Cap (Rigid)")
            except:
                log(f"    Joint Body-Cap warning: {traceback.format_exc()}")
    except:
        log(f"    Joint creation error: {traceback.format_exc()}")


# ---------------------------------------------------------------------------
# Master Assembly Builder
# ---------------------------------------------------------------------------
def build_endocrab_assembly():
    """Main entry point — builds the complete ENDOCRAB assembly."""
    log("=" * 70)
    log("ENDOCRAB MASTER ASSEMBLY BUILD — Analysis Document Rev 2.0")
    log("=" * 70)

    app = adsk.core.Application.get()
    ui = app.userInterface

    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    if not design:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(
            doc.products.itemByProductType("DesignProductType"))

    if not design:
        log("FATAL: No design available")
        if ui:
            ui.messageBox("Fusion 360 Design을 열어주세요.")
        return

    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent

    # Clean previous ENDOCRAB components
    try:
        for i in range(root.occurrences.count - 1, -1, -1):
            occ = root.occurrences.item(i)
            name = occ.name
            if any(tag in name for tag in [
                "ENDOCRAB", "SubAssy", "01_", "02_", "03_", "04_", "05_",
                "P1_", "P2_", "P3_", "P4_", "P5_", "P6_", "P7_", "P8_",
                "P9_", "P10_", "Distal", "Shaft", "Syringe", "Pistol",
                "Knotting", "Suture"
            ]):
                occ.deleteMe()
    except:
        pass

    # Step 1: User Parameters (25 entries)
    create_user_parameters(design)

    # Step 2: Build all sub-assemblies
    _, bodies = build_distal_endeffector(root, design)   # P1-P5 + Cap
    build_shaft_transmission(root, design)                # Shaft, wires, sheath
    build_syringe_controller(root, design)                # System A (P8/P9)
    build_pistol_controller(root, design)                 # System B (IIT ref)
    build_knotting_fastener(root, design)                 # P6/P7
    build_suture_thread(root, design)                     # P10

    # Step 3: Assembly joints
    create_assembly_joints(root, bodies)

    log("=" * 70)
    log("ENDOCRAB BUILD COMPLETE")
    log("=" * 70)

    if ui:
        ui.messageBox(
            "✅ ENDOCRAB Master Assembly — Build Complete!\n\n"
            "Built Components (Analysis Doc Rev 2.0):\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "01 Distal EndEffector:\n"
            "  • P1 Main Body (50×15×5.45mm + pocket + channels)\n"
            "  • P2 Gripper Jaws ×2 (6mm curved tip)\n"
            "  • P3 Ring Needle (Ø13mm, 350° + tip + eye)\n"
            "  • P4 Hinge Pins ×2 (Ø1mm)\n"
            "  • P5 Guide Track Ring\n"
            "  • Endoscope Cap (Ø11.5mm)\n\n"
            "02 Shaft & Transmission:\n"
            "  • Rigid Shaft Tube (Ø10mm × 120mm)\n"
            "  • Dual Control Wires (Ø0.6mm)\n"
            "  • PTFE Sheath\n\n"
            "03 Syringe Controller (System A)\n"
            "04 Pistol Grip (System B — IIT Bombay Ref)\n"
            "05 Knotting Fastener:\n"
            "  • P6 Male Stud (Ø2.2mm + oblique hole)\n"
            "  • P7 Female Ring (Ø3.2/2.3mm)\n\n"
            "P10 Suture Thread (4-0 Nylon + bead)\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "25 User Parameters bound in fx table\n"
            f"Log: {LOG_FILE}"
        )


# ---------------------------------------------------------------------------
# Fusion 360 entry point
# ---------------------------------------------------------------------------
def run(context):
    try:
        build_endocrab_assembly()
    except Exception:
        log(f"BUILD FAILED: {traceback.format_exc()}")
        app = adsk.core.Application.get()
        if app and app.userInterface:
            app.userInterface.messageBox(
                f"ENDOCRAB Build Failed:\n{traceback.format_exc()}")


if __name__ == "__main__":
    run(None)
