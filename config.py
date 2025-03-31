import os
import configparser
import sys

# 获取程序运行目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe
    application_path = os.path.dirname(sys.executable)
else:
    # 如果是直接运行python脚本
    application_path = os.path.dirname(os.path.abspath(__file__))

# 读取配置文件
config = configparser.ConfigParser()
config_path = os.path.join(application_path, 'config.ini')

if not os.path.exists(config_path):
    raise FileNotFoundError("配置文件 config.ini 未找到，请创建并配置相关设置")
config.read(config_path)

# 应用程序配置
APP_NAME = "TagSnap"
APP_VERSION = "1.0.0"

# 文件路径配置
try:
    IMAGE_NOTE_PATH = config['paths']['image_note_path']
    TEXT_NOTE_PATH = config['paths']['text_note_path']
except KeyError:
    raise KeyError("请在 config.ini 文件的 [paths] 节中配置 image_note_path 和 text_note_path")

# 子目录配置
IMAGES_ASSETS_SUBDIR = "images"  # 图片保存目录
SOURCE_SUBDIR = "source"  # 原始文本保存目录

# 代理配置
PROXY_CONFIG = {
    "http": "http://127.0.0.1:1080",
    "https": "http://127.0.0.1:1080"
}

# UI配置
WINDOW_SIZE = "800x600"
LABEL_FONT = ('Microsoft YaHei', 10)
DISPLAY_RATIO = 0.62  # 显示区域占窗口的比例

# 快捷键配置
SHOW_WINDOW_HOTKEY = 'ctrl+shift+z'

# 文件类型配置
VALID_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']

def setup_proxy():
    """设置代理"""
    os.environ["http_proxy"] = PROXY_CONFIG["http"]
    os.environ["https_proxy"] = PROXY_CONFIG["https"]

def get_image_save_path():
    """获取图片保存路径"""
    return os.path.join(IMAGE_NOTE_PATH, IMAGES_ASSETS_SUBDIR)

def ensure_directories():
    """确保必要的目录存在"""
    # 图片相关目录
    os.makedirs(os.path.join(IMAGE_NOTE_PATH, IMAGES_ASSETS_SUBDIR), exist_ok=True)
    
    # 文本相关目录
    os.makedirs(os.path.join(TEXT_NOTE_PATH, SOURCE_SUBDIR), exist_ok=True) 