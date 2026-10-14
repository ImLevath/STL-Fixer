@echo off
setlocal
pyinstaller --noconfirm --onefile --windowed --name STL-Fixer --collect-all PySide6 --hidden-import trimesh --hidden-import xatlas app.py
endlocal
