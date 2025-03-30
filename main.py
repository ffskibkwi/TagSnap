import tkinter as tk
from PIL import ImageGrab
import keyboard
import os
import sys

from gemini_handler import GeminiHandler
from image_processor import ImageProcessor
from text_processor import TextProcessor
from window_manager import WindowManager
from ui_components import MainUI
import config

class TagSnap:
    def __init__(self):
        # 设置代理
        config.setup_proxy()
        
        # 初始化根窗口
        self.root = tk.Tk()
        
        # 确保目录存在
        config.ensure_directories(config.DEFAULT_NOTE_DIR)
        
        # 初始化组件
        self.init_components()
        
        # 设置窗口大小
        self.root.geometry(config.WINDOW_SIZE)

    def init_components(self):
        """初始化所有组件"""
        # 初始化AI模型
        self.gemini = GeminiHandler()
        
        # 初始化图片处理器
        self.image_processor = ImageProcessor(config.DEFAULT_NOTE_DIR)
        
        # 初始化文本处理器
        self.text_processor = TextProcessor(config.DEFAULT_NOTE_DIR)
        
        # 初始化UI
        self.ui = MainUI(self.root, self.handle_paste)
        
        # 初始化窗口管理器
        self.window_manager = WindowManager(
            self.root,
            show_callback=self.ui.show_window,
            quit_callback=self.cleanup_and_exit
        )
        
        # 设置UI的窗口管理器
        self.ui.set_window_manager(self.window_manager)

    def handle_paste(self):
        """处理粘贴事件"""
        try:
            # 获取剪贴板内容
            clipboard_content = ImageGrab.grabclipboard()
            
            if clipboard_content:
                # 处理图片
                image = self.image_processor.process_clipboard_image(clipboard_content)
                if image:
                    self.process_image(image)
                    return
                    
            # 尝试获取文本
            try:
                text = self.root.clipboard_get()
                self.process_text(text)
            except tk.TclError:
                self.ui.update_status("剪贴板内容无法识别")
                
        except Exception as e:
            self.ui.update_status(f"错误: {str(e)}")

    def process_image(self, image):
        """处理图片"""
        try:
            # 保存图片
            save_info = self.image_processor.save_image(image)
            
            # 显示图片
            self.ui.show_image(image)
            
            # 使用AI分析图片
            analysis = self.gemini.analyze_image(image)
            
            # 创建markdown文件
            self.image_processor.create_md_file(
                save_info['md_path'],
                save_info['relative_path'],
                analysis['category'],
                analysis['tags'],
                analysis['summary']
            )
            
            # 更新UI标签
            self.ui.update_labels(
                analysis['category'],
                analysis['tags'],
                analysis['summary']
            )
            
            # 更新状态
            self.ui.update_status(f"已保存为 {save_info['filename']}")
            
        except Exception as e:
            self.ui.update_status(f"处理失败: {str(e)}")

    def process_text(self, text):
        """处理文本"""
        try:
            # 处理原始文本
            title = self.text_processor.process_source(text, self.text_processor.source_dir)
            
            # 使用AI分析文本
            category = self.gemini.md_category_judge(text)
            summary = self.gemini.md_summary_analyze(text)
            tags = self.gemini.md_tag_analyze(text)
            
            # 生成新的markdown文件路径
            md_filename = f"{title}.md"
            md_path = os.path.join(config.DEFAULT_NOTE_DIR, md_filename)
            
            # 创建处理后的markdown文件
            self.text_processor.create_md_file(
                md_path,
                title,
                category.text,
                tags.text,
                summary.text
            )
            
            # 构建显示文本
            display_text = f"""标题：{title}
分类：{category.text}
标签：{tags.text}

摘要：
{summary.text}"""
            
            # 显示分析结果
            self.ui.show_analysis_result(display_text)
            
            # 更新UI标签
            self.ui.update_labels(
                category.text,
                tags.text,
                summary.text
            )
            
            # 更新状态
            self.ui.update_status(f"已保存为 {md_filename}")
            
        except Exception as e:
            self.ui.update_status(f"处理失败: {str(e)}")

    def cleanup_and_exit(self):
        """清理资源并退出"""
        try:
            # 解除所有快捷键
            keyboard.unhook_all_hotkeys()
            
            # 销毁窗口
            if self.root.winfo_exists():
                self.root.destroy()
            
            # 退出程序
            sys.exit(0)
        except Exception as e:
            print(f"退出时发生错误: {str(e)}")
            os._exit(1)

    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"运行时发生错误: {str(e)}")
            self.cleanup_and_exit()

if __name__ == "__main__":
    app = TagSnap()
    app.run() 