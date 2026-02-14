# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('main.py', '.'),
    ('core', 'core'),
    ('integrations', 'integrations'),
    ('utils', 'utils'),
    ('data', 'data'),
    ('config.py', '.'),
    ('.env.example', '.'), 
    # Note: .env is not included by default for security, 
    # users will need create/copy .env next to the .exe
]
binaries = []
hiddenimports = []
tmp_ret = collect_all('streamlit')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Collect all langgraph modules to fix "No module named 'langgraph.prebuilt'"
tmp_ret_lg = collect_all('langgraph')
datas += tmp_ret_lg[0]; binaries += tmp_ret_lg[1]; hiddenimports += tmp_ret_lg[2]

# Add other libraries to ensure they are found
hiddenimports += [
    'langchain',
    'langchain_openai', 
    'langchain_google_genai',
    'langchain_anthropic',
    'langchain_community',
    'notion_client',
    'pydantic',
    'dotenv',
    'PIL',
    'altair',
    'watchdog',
]

block_cipher = None

a = Analysis(
    ['run_app.py'],  # This is our custom entry point
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='NotionAIPersonalAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False if you want to hide the terminal window
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
    name='NotionAIPersonalAssistant',
)
