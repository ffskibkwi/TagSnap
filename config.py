import os

# 应用程序配置
APP_NAME = "TagSnap"
APP_VERSION = "1.0.0"

# 文件路径配置
DEFAULT_NOTE_DIR = r"F:\Users\jzc_f\Documents\Obsidian Library"
IMAGES_SUBDIR = "Images"
IMAGES_ASSETS_SUBDIR = os.path.join(IMAGES_SUBDIR, "images")

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

def get_image_save_path(note_dir):
    """获取图片保存路径"""
    return os.path.join(note_dir, IMAGES_ASSETS_SUBDIR)

def ensure_directories(note_dir):
    """确保必要的目录存在"""
    os.makedirs(os.path.join(note_dir, IMAGES_SUBDIR), exist_ok=True)
    os.makedirs(os.path.join(note_dir, IMAGES_ASSETS_SUBDIR), exist_ok=True) 