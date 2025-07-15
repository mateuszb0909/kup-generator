# MyStreamlitApp.spec
import streamlit
import os
import site

# Find the path to Streamlit's static files and metadata
streamlit_path = os.path.dirname(streamlit.__file__)
streamlit_static_path = os.path.join(streamlit_path, "static")
site_packages = site.getsitepackages()[0]
streamlit_dist_info = os.path.join(site_packages, "streamlit-*.dist-info")

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        (streamlit_static_path, 'streamlit/static'),  # Bundle Streamlit frontend
        (streamlit_dist_info, '.'),  # Bundle Streamlit metadata
        ('app.py', '.'),  # Bundle your app script
        ('.streamlit/config.toml', '.streamlit')  # Bundle Streamlit config
    ],
    collect_metadata=['streamlit'],  # <-- ADD THIS LINE
    hiddenimports=['streamlit', 'watchdog'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MyStreamlitApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # Set to False for a .app bundle
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
    )

app = BUNDLE(
    exe,
    name='MyStreamlitApp.app',
    bundle_identifier=None,
)