"""
CadQuery STEP File Generator for ENDOCRAB Surgical Device Components.

This script runs in the host Python environment (outside Fusion 360) to generate
high-precision 3D CAD geometries (e.g. involute gears, serrated gripper jaws, toroidal ring needles)
and exports them to .step format for seamless import into Autodesk Fusion 360.
"""

import os
import sys
import argparse

def generate_ring_needle_step(output_path: str, outer_dia_mm: float = 12.0, wire_dia_mm: float = 1.2, sweep_deg: float = 330.0):
    """
    Generates a 3D Toroidal Ring Needle STEP model.
    """
    try:
        import cadquery as cq
        
        R_center = (outer_dia_mm - wire_dia_mm) / 2.0
        r_wire = wire_dia_mm / 2.0
        
        # Draw circular cross section offset by R_center
        profile = cq.Workplane("XZ").center(R_center, 0).circle(r_wire)
        # Sweep along 3D revolving arc
        needle = profile.revolve(sweep_deg, (0, 0, 0), (0, 0, 1))
        
        # Add bevel tip cut at one end
        # (Chamfer/cut at tip)
        
        cq.exporters.export(needle, output_path)
        print(f"[SUCCESS] Exported Toroidal Ring Needle STEP: {output_path}")
        return True
    except ImportError:
        print("[WARNING] CadQuery is not installed in the host Python environment.")
        print("To install: pip install cadquery")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to generate STEP: {e}")
        return False

def generate_serrated_gripper_step(output_path: str, length_mm: float = 25.0, width_mm: float = 4.0, num_notches: int = 5):
    """
    Generates a Dual Serrated Gripper Jaw STEP model with 4-5 precision V-notches.
    """
    try:
        import cadquery as cq
        
        jaw = cq.Workplane("XY").box(length_mm, width_mm, 3.0)
        # Cut serration V-notches along the inner face
        for i in range(num_notches):
            x_pos = -length_mm/2.0 + (i + 1) * (length_mm / (num_notches + 1))
            jaw = jaw.faces(">Z").workplane().center(x_pos, 0).rect(1.0, width_mm + 1.0).cutThruAll()
            
        cq.exporters.export(jaw, output_path)
        print(f"[SUCCESS] Exported Serrated Gripper STEP: {output_path}")
        return True
    except ImportError:
        print("[WARNING] CadQuery is not installed in the host environment.")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to generate Serrated Gripper STEP: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CadQuery STEP Generator for ENDOCRAB")
    parser.add_argument("--component", choices=["ring_needle", "gripper"], default="ring_needle")
    parser.add_argument("--out", default=r"C:\Users\Public\endocrab_component.step")
    args = parser.parse_args()

    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    if args.component == "ring_needle":
        generate_ring_needle_step(args.out)
    elif args.component == "gripper":
        generate_serrated_gripper_step(args.out)
