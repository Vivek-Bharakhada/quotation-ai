# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

# Hidden imports for FastAPI and Uvicorn
hidden_imports = [
    'search_engine',
    'pdf_reader',
    'cloud_storage',
    'email_service',
    'quotation',
    'app_paths',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'pydantic',
    'pydantic_core',
    'pydantic_core._pydantic_core',
    'email_validator',
    'multipart',
    'python-multipart',
    'sentence_transformers',
    'faiss',
    'numpy',
    'pymupdf',
    'fitz',
    'reportlab',
    'PIL',
    'PIL._imaging',
    'httpx',
    'aiofiles'
]

metadata_datas = []
for package_name in ('email_validator', 'pydantic', 'fastapi'):
    metadata_datas += copy_metadata(package_name)

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[
        ('static', 'static'),
        ('search_index_v2.json', '.'),
        ('image_path_cache.json', '.'),
    ] + metadata_datas,
    hiddenimports=hidden_imports,
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
    [],
    exclude_binaries=True,
    name='backend_sidecar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend_sidecar',
)
