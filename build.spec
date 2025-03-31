# -*- mode: python -*-
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        *collect_data_files('google'),  # 包含Google AI依赖
        ('config.ini', '.'),  # 如果有配置文件需要包含
        ('prompt.ini', '.'),  # 添加prompt.ini文件
    ],
    hiddenimports=[
        'PIL._imagingtk', 
        'PIL._tkinter_finder',
        'google.generativeai',
        'configparser'
    ],
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
    name='TagSnap',  # 生成的exe名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为True可显示控制台
    icon='tagsnap.ico',
    disable_windowed_trace=False,
)
