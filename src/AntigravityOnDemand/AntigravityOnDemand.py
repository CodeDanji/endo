import adsk.core, adsk.fusion, traceback
import http.server, socketserver, threading, json, os, base64, sys, time

PORT = 8080
WORKSPACE_DIR = os.path.expanduser(r"~\AppData\Local\Temp\AntigravityCAD")
SCRIPT_DIR = r"C:\Users\권원중학부재학바이오의공학부\Desktop\ENDO\src"

app = None
ui = None
server = None
server_thread = None
last_execution_error = None

custom_event_inspect = None
custom_event_modify = None
custom_event_build = None
custom_event_import_step = None
custom_event_execute_code = None
custom_event_animate = None
custom_event_export_mjcf = None
custom_event_capture_dfm = None

inspect_event_id = "AntigravityInspectEvent"
modify_event_id = "AntigravityModifyEvent"
build_event_id = "AntigravityBuildEvent"
import_step_event_id = "AntigravityImportStepEvent"
execute_code_event_id = "AntigravityExecuteCodeEvent"
animate_event_id = "AntigravityAnimateEvent"
export_mjcf_event_id = "AntigravityExportMJCFEvent"
capture_dfm_event_id = "AntigravityCaptureDFMViewsEvent"

handlers = []


def count_all_bodies(comp):
    if not comp:
        return 0
    count = comp.bRepBodies.count
    for occ in comp.occurrences:
        try:
            count += count_all_bodies(occ.component)
        except:
            pass
    return count


def sanitize_name(name):
    """Sanitizes names for files and XML attributes."""
    if not name:
        return "unnamed"
    for ch in [":", " ", "/", "\\", "-", ".", "(", ")", "[", "]"]:
        name = name.replace(ch, "_")
    while "__" in name:
        name = name.replace("__", "_")
    return name.strip("_")


class InspectEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        global last_execution_error
        try:
            if not os.path.exists(WORKSPACE_DIR):
                os.makedirs(WORKSPACE_DIR, exist_ok=True)
            app_obj = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app_obj.activeProduct)
            vp = app_obj.activeViewport
            
            # 1. 뷰포트 캡처 (PNG)
            png_path = os.path.join(WORKSPACE_DIR, "viewport.png")
            if vp:
                vp.saveAsImageFile(png_path, 0, 0)
            
            # 2. 파라미터 치수 추출
            params = {}
            if design:
                for param in design.userParameters:
                    params[param.name] = {
                        "expression": param.expression,
                        "value": param.value,
                        "unit": param.unit
                    }
                if not params and design.allParameters:
                    for param in design.allParameters:
                        params[param.name] = {
                            "expression": param.expression,
                            "value": param.value,
                            "unit": param.unit
                        }
            
            total_bodies = count_all_bodies(design.rootComponent) if design and design.rootComponent else 0
            
            # 3. B-Rep Topology Data Extraction
            brep_topology = []
            joints_info = []
            if design and design.rootComponent:
                for occ in design.rootComponent.occurrences:
                    try:
                        bbox = occ.boundingBox
                        brep_topology.append({
                            "name": occ.name,
                            "min": [round(bbox.minPoint.x, 2), round(bbox.minPoint.y, 2), round(bbox.minPoint.z, 2)],
                            "max": [round(bbox.maxPoint.x, 2), round(bbox.maxPoint.y, 2), round(bbox.maxPoint.z, 2)],
                            "faces_count": occ.bRepBodies.item(0).faces.count if occ.bRepBodies.count > 0 else 0
                        })
                    except:
                        pass
                for joint in design.rootComponent.joints:
                    joints_info.append({"name": joint.name, "type": joint.jointMotion.jointType})
                for as_joint in design.rootComponent.asBuiltJoints:
                    joints_info.append({"name": as_joint.name, "type": as_joint.jointMotion.jointType})
            
            state = {
                "document_name": app_obj.activeDocument.name if app_obj and app_obj.activeDocument else "",
                "parameters": params,
                "body_count": total_bodies,
                "occurrence_count": design.rootComponent.occurrences.count if design and design.rootComponent else 0,
                "png_path": png_path,
                "brep_topology": brep_topology,
                "joints_info": joints_info,
                "last_error": last_execution_error
            }
            with open(os.path.join(WORKSPACE_DIR, "state.json"), "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except:
            last_execution_error = traceback.format_exc()


class AnimateEventHandler(adsk.core.CustomEventHandler):
    """Handles multi-frame kinematic animation and dynamic inspection."""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        global last_execution_error
        try:
            if not os.path.exists(WORKSPACE_DIR):
                os.makedirs(WORKSPACE_DIR, exist_ok=True)
            app_obj = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app_obj.activeProduct)
            vp = app_obj.activeViewport
            if not design or not vp:
                return

            additional_info = args.additionalInfo
            anim_data = json.loads(additional_info) if additional_info else {}
            joint_name = anim_data.get("joint_name", "")
            steps = anim_data.get("steps", [0.0, 0.5, 1.0])
            travel_range = anim_data.get("range", [0.0, 2.042])  # Default 20.42mm (2.042 cm)

            # Search target joint in asBuiltJoints and regular joints
            target_joint = None
            for j in design.rootComponent.asBuiltJoints:
                if not joint_name or j.name == joint_name:
                    target_joint = j
                    break
            if not target_joint:
                for j in design.rootComponent.joints:
                    if not joint_name or j.name == joint_name:
                        target_joint = j
                        break

            frame_results = []
            if target_joint:
                motion = target_joint.jointMotion
                min_v, max_v = travel_range[0], travel_range[1]

                for idx, step_fraction in enumerate(steps):
                    current_val = min_v + (max_v - min_v) * step_fraction
                    
                    # Apply value according to joint type
                    try:
                        if motion.jointType == adsk.fusion.JointTypes.SliderJointType:
                            motion.sliderOneTranslationValue = current_val
                        elif motion.jointType == adsk.fusion.JointTypes.RevoluteJointType:
                            motion.rotationValue = current_val
                    except:
                        pass
                    
                    vp.refresh()
                    adsk.doEvents()
                    time.sleep(0.15)

                    step_png = os.path.join(WORKSPACE_DIR, f"viewport_step_{idx}.png")
                    vp.saveAsImageFile(step_png, 0, 0)
                    
                    # Capture topology at this step
                    occ_states = []
                    for occ in design.rootComponent.occurrences:
                        try:
                            bbox = occ.boundingBox
                            occ_states.append({
                                "name": occ.name,
                                "min": [round(bbox.minPoint.x, 2), round(bbox.minPoint.y, 2), round(bbox.minPoint.z, 2)],
                                "max": [round(bbox.maxPoint.x, 2), round(bbox.maxPoint.y, 2), round(bbox.maxPoint.z, 2)]
                            })
                        except:
                            pass

                    frame_results.append({
                        "step_index": idx,
                        "fraction": step_fraction,
                        "applied_value": round(current_val, 4),
                        "png_path": step_png,
                        "topology": occ_states
                    })

                # Reset to initial position
                try:
                    if motion.jointType == adsk.fusion.JointTypes.SliderJointType:
                        motion.sliderOneTranslationValue = min_v
                    elif motion.jointType == adsk.fusion.JointTypes.RevoluteJointType:
                        motion.rotationValue = min_v
                    vp.refresh()
                except:
                    pass

            anim_summary = {
                "target_joint": target_joint.name if target_joint else "None",
                "total_frames": len(frame_results),
                "frames": frame_results
            }
            with open(os.path.join(WORKSPACE_DIR, "animation_state.json"), "w", encoding="utf-8") as f:
                json.dump(anim_summary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            last_execution_error = traceback.format_exc()


class ExportMJCFEventHandler(adsk.core.CustomEventHandler):
    """Exports active CAD components to STL meshes and generates MuJoCo MJCF XML model."""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        global last_execution_error
        try:
            app_obj = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app_obj.activeProduct)
            if not design or not design.rootComponent:
                return

            additional_info = args.additionalInfo
            export_params = json.loads(additional_info) if additional_info else {}
            
            mechanism_name = sanitize_name(export_params.get("mechanism_name", design.rootComponent.name or "ENDOCRAB_Mechanism"))
            target_dir = export_params.get("output_dir", os.path.join(WORKSPACE_DIR, "mjcf_export"))
            meshes_dir = os.path.join(target_dir, "meshes")
            os.makedirs(meshes_dir, exist_ok=True)

            export_mgr = app_obj.exportManager
            components_data = []
            assets_xml = []
            bodies_xml = []
            joints_xml = []

            # 1. Root and Sub-Occurrences Traversal
            occurrences = list(design.rootComponent.occurrences)
            
            # If no occurrences, export root component bodies
            if len(occurrences) == 0:
                for idx, body in enumerate(design.rootComponent.bRepBodies):
                    body_name = sanitize_name(body.name or f"body_{idx}")
                    stl_file = f"{body_name}.stl"
                    stl_path = os.path.join(meshes_dir, stl_file)
                    
                    try:
                        stl_opts = export_mgr.createSTLExportOptions(body, stl_path)
                        stl_opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                        export_mgr.export(stl_opts)
                    except:
                        pass
                    
                    phys = body.physicalProperties
                    mass_kg = round(phys.mass, 6) if phys and phys.mass > 0 else 0.005
                    com = phys.centerOfMass if phys else None
                    com_m = [round(com.x / 100.0, 6), round(com.y / 100.0, 6), round(com.z / 100.0, 6)] if com else [0, 0, 0]
                    
                    try:
                        _, ixx, iyy, izz, ixy, iyz, ixz = phys.getXYZMomentsOfInertia()
                        diaginertia_m = [max(1e-8, round(abs(ixx) / 10000.0, 8)),
                                         max(1e-8, round(abs(iyy) / 10000.0, 8)),
                                         max(1e-8, round(abs(izz) / 10000.0, 8))]
                    except:
                        diaginertia_m = [1e-6, 1e-6, 1e-6]

                    components_data.append({
                        "name": body_name,
                        "stl_file": stl_file,
                        "mass_kg": mass_kg,
                        "com_m": com_m,
                        "inertia_m": diaginertia_m
                    })
                    assets_xml.append(f'    <mesh name="{body_name}_mesh" file="meshes/{stl_file}" scale="0.001 0.001 0.001"/>')
                    bodies_xml.append(f'''    <body name="{body_name}" pos="{com_m[0]} {com_m[1]} {com_m[2]}">
      <inertial pos="0 0 0" mass="{mass_kg}" diaginertia="{diaginertia_m[0]} {diaginertia_m[1]} {diaginertia_m[2]}"/>
      <geom type="mesh" mesh="{body_name}_mesh" rgba="0.8 0.8 0.85 1.0" friction="0.2 0.005 0.0001"/>
    </body>''')
            else:
                for occ in occurrences:
                    comp_name = sanitize_name(occ.name)
                    stl_file = f"{comp_name}.stl"
                    stl_path = os.path.join(meshes_dir, stl_file)

                    try:
                        stl_opts = export_mgr.createSTLExportOptions(occ.component, stl_path)
                        stl_opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                        export_mgr.export(stl_opts)
                    except:
                        if occ.bRepBodies.count > 0:
                            stl_opts = export_mgr.createSTLExportOptions(occ.bRepBodies.item(0), stl_path)
                            stl_opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                            export_mgr.export(stl_opts)

                    phys = occ.physicalProperties
                    mass_kg = round(phys.mass, 6) if phys and phys.mass > 0 else 0.005
                    com = phys.centerOfMass if phys else None
                    com_m = [round(com.x / 100.0, 6), round(com.y / 100.0, 6), round(com.z / 100.0, 6)] if com else [0, 0, 0]

                    try:
                        _, ixx, iyy, izz, ixy, iyz, ixz = phys.getXYZMomentsOfInertia()
                        diaginertia_m = [max(1e-8, round(abs(ixx) / 10000.0, 8)),
                                         max(1e-8, round(abs(iyy) / 10000.0, 8)),
                                         max(1e-8, round(abs(izz) / 10000.0, 8))]
                    except:
                        diaginertia_m = [1e-6, 1e-6, 1e-6]

                    components_data.append({
                        "name": comp_name,
                        "stl_file": stl_file,
                        "mass_kg": mass_kg,
                        "com_m": com_m,
                        "inertia_m": diaginertia_m
                    })
                    assets_xml.append(f'    <mesh name="{comp_name}_mesh" file="meshes/{stl_file}" scale="0.001 0.001 0.001"/>')
                    bodies_xml.append(f'''    <body name="{comp_name}" pos="{com_m[0]} {com_m[1]} {com_m[2]}">
      <inertial pos="0 0 0" mass="{mass_kg}" diaginertia="{diaginertia_m[0]} {diaginertia_m[1]} {diaginertia_m[2]}"/>
      <geom type="mesh" mesh="{comp_name}_mesh" rgba="0.75 0.78 0.82 1.0" friction="0.2 0.005 0.0001"/>
    </body>''')

            # 2. Extract Joints
            all_joints = list(design.rootComponent.joints) + list(design.rootComponent.asBuiltJoints)
            for j in all_joints:
                j_name = sanitize_name(j.name)
                m_type = "hinge" if j.jointMotion.jointType == adsk.fusion.JointTypes.RevoluteJointType else "slide"
                joints_xml.append(f'    <!-- Joint: {j_name} ({m_type}) -->')

            # 3. Assemble Complete MJCF XML
            assets_joined = "\n".join(assets_xml)
            bodies_joined = "\n".join(bodies_xml)
            
            mjcf_content = f"""<mujoco model="{mechanism_name}">
  <compiler angle="degree" coordinate="local" meshdir="meshes"/>
  <option gravity="0 0 -9.81" timestep="0.001" iterations="50" solver="Newton"/>

  <default>
    <joint damping="0.01" armature="0.001"/>
    <geom contype="1" conaffinity="1" condim="3"/>
  </default>

  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.9 0.95 1" rgb2="0.6 0.7 0.8" width="512" height="512"/>
    <material name="metal_mat" specular="0.8" shininess="0.8" reflectance="0.3" rgba="0.8 0.8 0.85 1.0"/>
    <material name="suture_mat" specular="0.1" shininess="0.1" rgba="0.2 0.4 0.9 1.0"/>
{assets_joined}
  </asset>

  <worldbody>
    <light pos="0 0 0.5" dir="0 0 -1" directional="true" diffuse="0.8 0.8 0.8"/>
    <geom name="floor" type="plane" size="0.2 0.2 0.01" pos="0 0 -0.05" rgba="0.9 0.9 0.9 1.0"/>
{bodies_joined}
  </worldbody>

  <tendon>
    <!-- Spatial Tendon for Endoscopic Suture Wire Routing -->
    <spatial name="endo_drive_tendon" width="0.0004" rgba="0.1 0.3 0.9 1.0">
      <site site="tendon_anchor_distal" pos="0 0 0"/>
      <site site="tendon_guide_proximal" pos="0 0 0.02"/>
    </spatial>
  </tendon>

  <actuator>
    <!-- Tendon Actuator (0 to 15N Tension) -->
    <motor name="tendon_motor" tendon="endo_drive_tendon" ctrlrange="0 15.0" gear="1.0"/>
  </actuator>
</mujoco>
"""
            xml_path = os.path.join(target_dir, f"{mechanism_name}.xml")
            default_xml_path = os.path.join(target_dir, "model.xml")
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(mjcf_content)
            with open(default_xml_path, "w", encoding="utf-8") as f:
                f.write(mjcf_content)

            summary = {
                "mechanism_name": mechanism_name,
                "export_dir": target_dir,
                "xml_path": xml_path,
                "default_xml_path": default_xml_path,
                "components_count": len(components_data),
                "components": components_data,
                "joints_count": len(all_joints),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            with open(os.path.join(target_dir, "mjcf_export_summary.json"), "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            with open(os.path.join(WORKSPACE_DIR, "mjcf_export_summary.json"), "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

        except Exception as e:
            last_execution_error = traceback.format_exc()


class CaptureDFMViewsEventHandler(adsk.core.CustomEventHandler):
    """Captures 4-angle DFM (Design For Manufacturing) and micro-assembly cross-section / perspective views."""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        global last_execution_error
        try:
            app_obj = adsk.core.Application.get()
            vp = app_obj.activeViewport
            if not vp:
                return

            additional_info = args.additionalInfo
            dfm_params = json.loads(additional_info) if additional_info else {}
            dfm_dir = dfm_params.get("output_dir", os.path.join(WORKSPACE_DIR, "dfm_views"))
            os.makedirs(dfm_dir, exist_ok=True)

            camera = vp.camera
            initial_visual_style = vp.visualStyle
            initial_cam_type = camera.cameraType
            initial_orientation = camera.viewOrientation

            views_captured = []

            # 1. Isometric Wireframe / Skeleton View
            try:
                camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
                camera.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
                camera.isFitView = True
                vp.camera = camera
                try:
                    vp.visualStyle = adsk.core.VisualStyles.ShadedWithHiddenEdgesVisualStyle
                except:
                    pass
                vp.refresh()
                adsk.doEvents()
                time.sleep(0.2)
                p1 = os.path.join(dfm_dir, "Isometric_Wireframe.png")
                vp.saveAsImageFile(p1, 1920, 1080)
                views_captured.append({
                    "view_name": "Isometric_Wireframe",
                    "filename": "Isometric_Wireframe.png",
                    "path": p1,
                    "description": "Overall structural skeleton and internal tendon pathway transparency view"
                })
            except:
                pass

            # 2. Section Tendon Channel View (Front View with zoom)
            try:
                camera.viewOrientation = adsk.core.ViewOrientations.FrontViewOrientation
                camera.isFitView = True
                vp.camera = camera
                try:
                    vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
                except:
                    pass
                vp.refresh()
                adsk.doEvents()
                time.sleep(0.2)
                p2 = os.path.join(dfm_dir, "Section_Tendon_Channel.png")
                vp.saveAsImageFile(p2, 1920, 1080)
                views_captured.append({
                    "view_name": "Section_Tendon_Channel",
                    "filename": "Section_Tendon_Channel.png",
                    "path": p2,
                    "description": "Cross-sectional view of tendon routing channel and corner fillet radius"
                })
            except:
                pass

            # 3. Section Pin Assembly View (Top / Pivot Pin View)
            try:
                camera.viewOrientation = adsk.core.ViewOrientations.TopViewOrientation
                camera.isFitView = True
                vp.camera = camera
                vp.refresh()
                adsk.doEvents()
                time.sleep(0.2)
                p3 = os.path.join(dfm_dir, "Section_Pin_Assembly.png")
                vp.saveAsImageFile(p3, 1920, 1080)
                views_captured.append({
                    "view_name": "Section_Pin_Assembly",
                    "filename": "Section_Pin_Assembly.png",
                    "path": p3,
                    "description": "Micro hinge pin joint clearance, press-fit margin, and retainer assembly view"
                })
            except:
                pass

            # 4. Exploded / Perspective Assembly View
            try:
                camera.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
                camera.viewOrientation = adsk.core.ViewOrientations.IsoTopLeftViewOrientation
                camera.isFitView = True
                vp.camera = camera
                vp.refresh()
                adsk.doEvents()
                time.sleep(0.2)
                p4 = os.path.join(dfm_dir, "Exploded_Assembly_View.png")
                vp.saveAsImageFile(p4, 1920, 1080)
                views_captured.append({
                    "view_name": "Exploded_Assembly_View",
                    "filename": "Exploded_Assembly_View.png",
                    "path": p4,
                    "description": "Exploded 3D perspective visualization for micro-forceps tool clearance audit"
                })
            except:
                pass

            # Restore original viewport state
            try:
                camera.cameraType = initial_cam_type
                camera.viewOrientation = initial_orientation
                camera.isFitView = True
                vp.camera = camera
                vp.visualStyle = initial_visual_style
                vp.refresh()
            except:
                pass

            dfm_summary = {
                "audit_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_views": len(views_captured),
                "views": views_captured
            }
            with open(os.path.join(dfm_dir, "dfm_views.json"), "w", encoding="utf-8") as f:
                json.dump(dfm_summary, f, indent=2, ensure_ascii=False)
            with open(os.path.join(WORKSPACE_DIR, "dfm_views.json"), "w", encoding="utf-8") as f:
                json.dump(dfm_summary, f, indent=2, ensure_ascii=False)

        except Exception as e:
            last_execution_error = traceback.format_exc()


class ModifyEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            additional_info = args.additionalInfo
            if not additional_info:
                return
            mod_data = json.loads(additional_info)
            app_obj = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app_obj.activeProduct)
            
            if design:
                for key, val in mod_data.get("parameters", {}).items():
                    param = design.userParameters.itemByName(key)
                    if not param:
                        param = design.allParameters.itemByName(key)
                    if param:
                        param.expression = str(val)
                
                if app_obj:
                    app_obj.fireCustomEvent(inspect_event_id)
        except:
            pass


class ImportStepEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            additional_info = args.additionalInfo
            if not additional_info:
                return
            data = json.loads(additional_info)
            step_path = data.get("step_path")
            if step_path and os.path.exists(step_path):
                app_obj = adsk.core.Application.get()
                design = adsk.fusion.Design.cast(app_obj.activeProduct)
                if design and design.rootComponent:
                    import_mgr = app_obj.importManager
                    step_options = import_mgr.createSTEPImportOptions(step_path)
                    import_mgr.importToTarget(step_options, design.rootComponent)
                if app_obj:
                    app_obj.fireCustomEvent(inspect_event_id)
        except:
            pass


class BuildEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            script_path = os.path.join(SCRIPT_DIR, "build_endocrab_model.py")
            with open(script_path, "r", encoding="utf-8") as f:
                code = f.read()
            exec_globals = {"__file__": script_path, "__name__": "__main__", "adsk": adsk, "app": adsk.core.Application.get()}
            exec(code, exec_globals)
            
            app_obj = adsk.core.Application.get()
            if app_obj:
                app_obj.fireCustomEvent(inspect_event_id)
        except:
            app_obj = adsk.core.Application.get()
            if app_obj and app_obj.userInterface:
                app_obj.userInterface.messageBox("Build Failed:\n{}".format(traceback.format_exc()))


class ExecuteCodeEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        global last_execution_error
        last_execution_error = None
        try:
            additional_info = args.additionalInfo
            if not additional_info:
                return
            data = json.loads(additional_info)
            code = data.get("code", "")
            if code:
                app_obj = adsk.core.Application.get()
                exec_globals = {
                    "__name__": "__main__",
                    "adsk": adsk,
                    "app": app_obj,
                    "ui": app_obj.userInterface if app_obj else None,
                }
                exec(code, exec_globals)
                if app_obj:
                    app_obj.fireCustomEvent(inspect_event_id)
        except Exception as e:
            last_execution_error = traceback.format_exc()
            app_obj = adsk.core.Application.get()
            if app_obj and app_obj.userInterface:
                try:
                    undo_cmd = app_obj.userInterface.commandDefinitions.itemById('UndoCommand')
                    if undo_cmd:
                        undo_cmd.execute()
                except:
                    pass
                app_obj.fireCustomEvent(inspect_event_id)


class RESTHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/inspect":
            global app, inspect_event_id
            if app:
                app.fireCustomEvent(inspect_event_id)
            time.sleep(0.5)  # 렌더링 대기
            
            png_path = os.path.join(WORKSPACE_DIR, "viewport.png")
            json_path = os.path.join(WORKSPACE_DIR, "state.json")
            
            state_data = {}
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
            
            img_b64 = ""
            if os.path.exists(png_path):
                with open(png_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode('utf-8')
                    
            response = {"state": state_data, "image_b64": img_b64}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path == "/animation_results":
            json_path = os.path.join(WORKSPACE_DIR, "animation_state.json")
            anim_data = {}
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    anim_data = json.load(f)
            
            frames_with_b64 = []
            for frame in anim_data.get("frames", []):
                p = frame.get("png_path", "")
                b64 = ""
                if os.path.exists(p):
                    with open(p, "rb") as fp:
                        b64 = base64.b64encode(fp.read()).decode('utf-8')
                frame_copy = dict(frame)
                frame_copy["image_b64"] = b64
                frames_with_b64.append(frame_copy)
            
            anim_data["frames"] = frames_with_b64
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(anim_data).encode("utf-8"))

        elif self.path == "/mjcf_results":
            summary_path = os.path.join(WORKSPACE_DIR, "mjcf_export_summary.json")
            summary_data = {}
            if os.path.exists(summary_path):
                with open(summary_path, "r", encoding="utf-8") as f:
                    summary_data = json.load(f)
            
            xml_content = ""
            xml_path = summary_data.get("default_xml_path", os.path.join(WORKSPACE_DIR, "mjcf_export", "model.xml"))
            if os.path.exists(xml_path):
                with open(xml_path, "r", encoding="utf-8") as f:
                    xml_content = f.read()
            
            response = {"summary": summary_data, "xml_content": xml_content}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path == "/dfm_views":
            dfm_path = os.path.join(WORKSPACE_DIR, "dfm_views.json")
            dfm_data = {}
            if os.path.exists(dfm_path):
                with open(dfm_path, "r", encoding="utf-8") as f:
                    dfm_data = json.load(f)
            
            views_with_b64 = []
            for v in dfm_data.get("views", []):
                p = v.get("path", "")
                b64 = ""
                if os.path.exists(p):
                    with open(p, "rb") as fp:
                        b64 = base64.b64encode(fp.read()).decode('utf-8')
                v_copy = dict(v)
                v_copy["image_b64"] = b64
                views_with_b64.append(v_copy)
            
            dfm_data["views"] = views_with_b64
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(dfm_data).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global app, modify_event_id, build_event_id, import_step_event_id, execute_code_event_id, animate_event_id, export_mjcf_event_id, capture_dfm_event_id
        if self.path == "/modify":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            if app:
                app.fireCustomEvent(modify_event_id, post_data.decode("utf-8"))
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode("utf-8"))

        elif self.path == "/import_step":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            if app:
                app.fireCustomEvent(import_step_event_id, post_data.decode("utf-8"))
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "import_triggered"}).encode("utf-8"))

        elif self.path == "/execute_code":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            if app:
                app.fireCustomEvent(execute_code_event_id, post_data.decode("utf-8"))
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "execute_code_triggered"}).encode("utf-8"))

        elif self.path == "/animate_and_inspect":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            if app:
                app.fireCustomEvent(animate_event_id, post_data.decode("utf-8"))
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "animate_triggered"}).encode("utf-8"))

        elif self.path == "/export_mjcf":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            if app:
                app.fireCustomEvent(export_mjcf_event_id, post_data.decode("utf-8"))
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "export_mjcf_triggered"}).encode("utf-8"))

        elif self.path == "/capture_dfm_views":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            if app:
                app.fireCustomEvent(capture_dfm_event_id, post_data.decode("utf-8"))
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "capture_dfm_views_triggered"}).encode("utf-8"))

        elif self.path == "/build":
            if app:
                app.fireCustomEvent(build_event_id)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "build_started"}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


class ReusableHTTPServer(http.server.HTTPServer):
    allow_reuse_address = True


def start_server():
    global server
    try:
        server = ReusableHTTPServer(("", PORT), RESTHandler)
        server.serve_forever()
    except Exception:
        pass


def run(context):
    global app, ui, server, server_thread
    global custom_event_inspect, custom_event_modify, custom_event_build
    global custom_event_import_step, custom_event_execute_code, custom_event_animate
    global custom_event_export_mjcf, custom_event_capture_dfm, handlers
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        custom_event_inspect = app.registerCustomEvent(inspect_event_id)
        inspect_handler = InspectEventHandler()
        custom_event_inspect.add(inspect_handler)
        handlers.append(inspect_handler)
        
        custom_event_modify = app.registerCustomEvent(modify_event_id)
        modify_handler = ModifyEventHandler()
        custom_event_modify.add(modify_handler)
        handlers.append(modify_handler)

        custom_event_import_step = app.registerCustomEvent(import_step_event_id)
        import_step_handler = ImportStepEventHandler()
        custom_event_import_step.add(import_step_handler)
        handlers.append(import_step_handler)

        custom_event_execute_code = app.registerCustomEvent(execute_code_event_id)
        execute_code_handler = ExecuteCodeEventHandler()
        custom_event_execute_code.add(execute_code_handler)
        handlers.append(execute_code_handler)

        custom_event_animate = app.registerCustomEvent(animate_event_id)
        animate_handler = AnimateEventHandler()
        custom_event_animate.add(animate_handler)
        handlers.append(animate_handler)

        custom_event_export_mjcf = app.registerCustomEvent(export_mjcf_event_id)
        export_mjcf_handler = ExportMJCFEventHandler()
        custom_event_export_mjcf.add(export_mjcf_handler)
        handlers.append(export_mjcf_handler)

        custom_event_capture_dfm = app.registerCustomEvent(capture_dfm_event_id)
        capture_dfm_handler = CaptureDFMViewsEventHandler()
        custom_event_capture_dfm.add(capture_dfm_handler)
        handlers.append(capture_dfm_handler)

        custom_event_build = app.registerCustomEvent(build_event_id)
        build_handler = BuildEventHandler()
        custom_event_build.add(build_handler)
        handlers.append(build_handler)
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        if ui:
            ui.messageBox(f"Antigravity On-Demand Server Started with MuJoCo MJCF Exporter & VLM DFM Auditor (Port {PORT})")
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    global app, ui, server
    global custom_event_inspect, custom_event_modify, custom_event_build
    global custom_event_import_step, custom_event_execute_code, custom_event_animate
    global custom_event_export_mjcf, custom_event_capture_dfm, handlers
    try:
        if app:
            if custom_event_inspect:
                app.unregisterCustomEvent(inspect_event_id)
                custom_event_inspect = None
            if custom_event_modify:
                app.unregisterCustomEvent(modify_event_id)
                custom_event_modify = None
            if custom_event_import_step:
                app.unregisterCustomEvent(import_step_event_id)
                custom_event_import_step = None
            if custom_event_execute_code:
                app.unregisterCustomEvent(execute_code_event_id)
                custom_event_execute_code = None
            if custom_event_animate:
                app.unregisterCustomEvent(animate_event_id)
                custom_event_animate = None
            if custom_event_export_mjcf:
                app.unregisterCustomEvent(export_mjcf_event_id)
                custom_event_export_mjcf = None
            if custom_event_capture_dfm:
                app.unregisterCustomEvent(capture_dfm_event_id)
                custom_event_capture_dfm = None
            if custom_event_build:
                app.unregisterCustomEvent(build_event_id)
                custom_event_build = None
        handlers.clear()
        
        if server:
            server.shutdown()
            server.server_close()
            server = None
    except:
        if ui:
            ui.messageBox('Stop Failed:\n{}'.format(traceback.format_exc()))
