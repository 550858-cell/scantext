# PyInstaller spec for SimpleOCR
#
# Build (on Windows, inside the activated venv from requirements.txt):
#     pyinstaller ocr_app/build.spec
#
# Output: dist/SimpleOCR.exe  (~200-300 MB — PaddlePaddle is large)
#
# Notes:
#  * paddleocr / paddle pull in many submodules that PyInstaller's
#    static analysis misses -> collect them explicitly below.
#  * If you have already run the app once and the models were
#    downloaded into %APPDATA%/SimpleOCR/models, you may bundle them
#    by adding their path to `datas` (see MODELS block) so the .exe
#    works fully offline. By default models are downloaded on first run.

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

datas = []
binaries = []
hiddenimports = []

for pkg in ("paddle", "paddleocr", "paddlex", "pyclipper", "shapely",
            "skimage", "imgaug", "lmdb"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

hiddenimports += collect_submodules("paddle")
hiddenimports += collect_submodules("paddleocr")
hiddenimports += [
    "scipy.special._cdflib",
    "scipy._lib.array_api_compat.numpy.fft",
    "skimage.filters.rank.core_cy_3d",
]

# --- MODELS (optional offline bundle) -------------------------------
# Uncomment and adjust if you want to ship pre-downloaded models:
# _models = os.path.expandvars(r"%APPDATA%\SimpleOCR\models\.paddleocr")
# if os.path.isdir(_models):
#     datas.append((_models, ".paddleocr"))
# --------------------------------------------------------------------

a = Analysis(
    ["main.py"],
    pathex=[os.path.abspath(os.path.join("ocr_app"))],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PyQt5"],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SimpleOCR",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,            # --windowed
    icon=os.path.join("resources", "icon.ico"),
)
