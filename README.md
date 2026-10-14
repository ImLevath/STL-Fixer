# STL-Fixer

Standalone GUI utility for automated STL repair and finalization.

## Features
- Drag-and-drop or browse for `.stl` files
- Visible step/status progress during processing
- Save repaired output through a standard Windows **Save As** dialog
- Ordered processing pipeline:
  1. Split disconnected mesh islands
  2. Remove components with fewer than 4 triangles
  3. UV unwrap each retained component (xatlas with planar fallback)
  4. Merge components
  5. Solidify + watertight finalization for export

## Run locally
```bash
python -m pip install -r requirements.txt
python app.py
```

## Build single-file Windows executable
Use the included script:
```bat
build_windows_exe.bat
```
This runs PyInstaller with `--onefile --windowed` to generate a standalone `.exe`.
