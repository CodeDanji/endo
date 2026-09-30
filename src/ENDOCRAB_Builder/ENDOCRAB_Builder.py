"""
ENDOCRAB 3D CAD Parametric Builder Script for Autodesk Fusion 360
Reference Paper: Nature Scientific Reports 14:7289 (2024)
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_SCRIPT = os.path.join(SCRIPT_DIR, "build_endocrab_model.py")
if not os.path.exists(MODEL_SCRIPT):
    MODEL_SCRIPT = r"C:\Users\권원중학부재학바이오의공학부\Desktop\ENDO\src\build_endocrab_model.py"


def run(context):
    try:
        with open(MODEL_SCRIPT, "r", encoding="utf-8") as f:
            code = f.read()
        exec_globals = {"__file__": MODEL_SCRIPT, "__name__": "__main__"}
        exec(code, exec_globals)
    except:
        import adsk.core, traceback
        app = adsk.core.Application.get()
        if app and app.userInterface:
            app.userInterface.messageBox("ENDOCRAB Builder Script Failed:\n{}".format(traceback.format_exc()))
