import adsk.core
import adsk.fusion
import traceback
import math

def mm(val):
    return val / 10.0

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        if not design:
            return

        # Clear existing components named P1_Basic_Skeleton to avoid duplicates
        root_comp = design.rootComponent
        for occ in root_comp.occurrences:
            if occ.component.name == "P1_Basic_Skeleton":
                occ.deleteMe()

        # Create a new component
        occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "P1_Basic_Skeleton"

        # 1. Main Body (Rectangular 35 x 12 x 12 mm)
        sk_body = comp.sketches.add(comp.xYConstructionPlane)
        sk_body.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-17.5), mm(-6.0), 0),
            adsk.core.Point3D.create(mm(17.5), mm(6.0), 0)
        )
        if sk_body.profiles.count > 0:
            ext_in = comp.features.extrudeFeatures.createInput(
                sk_body.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByString("12 mm"))
            comp.features.extrudeFeatures.add(ext_in)
            
            # Create a slot for the needle and rack (Cut)
            sk_slot = comp.sketches.add(comp.xZConstructionPlane)
            sk_slot.sketchCurves.sketchLines.addTwoPointRectangle(
                adsk.core.Point3D.create(mm(0), mm(2.0), 0),
                adsk.core.Point3D.create(mm(20.0), mm(10.0), 0)
            )
            if sk_slot.profiles.count > 0:
                slot_in = comp.features.extrudeFeatures.createInput(
                    sk_slot.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
                slot_in.setSymmetricExtent(adsk.core.ValueInput.createByString("2 mm"), True)
                comp.features.extrudeFeatures.add(slot_in)

        # 2. Circular Needle (Diameter 15mm, seated at front)
        needle_occ = comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        n_comp = needle_occ.component
        n_comp.name = "Ring_Needle_Option_A"
        
        xc = mm(12.0)
        zc = mm(6.0)
        
        sk_n = n_comp.sketches.add(n_comp.xZConstructionPlane)
        sk_n.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc, zc, 0), mm(7.5)
        )
        sk_n.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(xc, zc, 0), mm(6.5)
        )
        
        if sk_n.profiles.count > 0:
            for prof in sk_n.profiles:
                if prof.profileLoops.count > 1:
                    ext_n = n_comp.features.extrudeFeatures.createInput(
                        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    ext_n.setSymmetricExtent(adsk.core.ValueInput.createByString("1 mm"), True)
                    n_comp.features.extrudeFeatures.add(ext_n)
                    break

        # 3. Rack Gear Representation
        rack_occ = comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        r_comp = rack_occ.component
        r_comp.name = "Drive_Rack"
        
        sk_r = r_comp.sketches.add(r_comp.xZConstructionPlane)
        sk_r.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-15.0), mm(4.0), 0),
            adsk.core.Point3D.create(mm(10.0), mm(5.5), 0)
        )
        if sk_r.profiles.count > 0:
            ext_r = r_comp.features.extrudeFeatures.createInput(
                sk_r.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_r.setSymmetricExtent(adsk.core.ValueInput.createByString("0.5 mm"), True)
            r_comp.features.extrudeFeatures.add(ext_r)

    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

run(None)
