# Fusion 360 Python API Reference & Cheat Sheet

This cheat sheet summarizes key Autodesk Fusion 360 API snippets, B-Rep selection rules, unit conversion formulas, and thread-marshaling patterns.

---

## 1. Application, Product, and Design Access

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
ui = app.userInterface
product = app.activeProduct
design = adsk.fusion.Design.cast(product)
root_comp = design.rootComponent
```

---

## 2. Unit Conversions (Internal Database Unit: cm)

Fusion 360 stores lengths in **centimeters (cm)**.

```python
def mm(val_in_mm):
    return val_in_mm / 10.0  # Convert mm to cm for ValueInput.createByReal()

# Option A: By Real Value (Must be cm!)
val_input_real = adsk.core.ValueInput.createByReal(mm(50.0))  # 50.0 mm -> 5.0 cm

# Option B: By String (Parsed automatically with units)
val_input_str = adsk.core.ValueInput.createByString("50.0 mm")
```

---

## 3. Parametric User Parameters (`fx`)

```python
# Read parameter
param = design.allParameters.itemByName("Body_Length")
if param:
    print(f"Current expression: {param.expression}, Real value (cm): {param.value}")

# Update parameter safely
param.expression = "65.0 mm"
```

---

## 4. Importing STEP Files Programmatically

```python
importManager = app.importManager
stepOptions = importManager.createSTEPImportOptions(r"C:\temp\model.step")
targetComponent = root_comp
importManager.importToTarget(stepOptions, targetComponent)
```

---

## 5. Main-Thread CustomEvent Marshaling (Crash Prevention)

```python
# 1. Register event in run()
custom_event = app.registerCustomEvent("AntigravityModifyEvent")
handler = ModifyEventHandler()
custom_event.add(handler)

# 2. Fire from socket thread
app.fireCustomEvent("AntigravityModifyEvent", json_string_payload)

# 3. Handle in main thread
class ModifyEventHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        payload = json.loads(args.additionalInfo)
        # Modify CAD safely on UI thread!
```
