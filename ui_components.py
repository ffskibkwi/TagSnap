import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageGrab
import keyboard

class MainUI:
    def __init__(self, root, on_paste_callback):
        self.root = root
        self.root.title("TagSnap")
        self.image_reference = None
        self.current_image = None
        self._exiting = False
        self.on_paste_callback = on_paste_callback

        # 设置图标
        try:
            self.root.iconbitmap('tagsnap.ico')
        except:
            pass

        # 创建主框架
        self.setup_main_frame()
        
        # 绑定快捷键
        self.setup_shortcuts()
        
        # 设置窗口大小
        self.root.geometry("800x600")
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)

    def setup_main_frame(self):
        """设置主框架和UI组件"""
        # 主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')

        # 显示区域框架
        self.display_frame = ttk.Frame(self.main_frame)
        self.display_frame.pack(expand=True, fill='both', pady=5)

        # 显示区域
        self.display_area = ttk.Label(self.display_frame)
        self.display_area.pack(expand=True)

        # 状态栏
        self.status = ttk.Label(self.root, text="就绪", foreground="gray")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # 标签框架
        self.labels_frame = ttk.Frame(self.root)
        self.labels_frame.pack(fill='x', padx=10, pady=2)

        # 设置字体
        label_font = ('Microsoft YaHei', 10)

        # 分类标签
        self.category_label = ttk.Label(self.labels_frame, wraplength=640, font=label_font)
        self.category_label.pack(pady=1)

        # 标签标签
        self.tags_label = ttk.Label(self.labels_frame, wraplength=640, font=label_font)
        self.tags_label.pack(pady=1)

        # 提示标签
        self.hint_label = ttk.Label(self.labels_frame, text="使用 Ctrl+V 粘贴内容", 
                                  foreground="gray", wraplength=640, font=label_font)
        self.hint_label.pack(pady=1)

    def setup_shortcuts(self):
        """设置快捷键"""
        self.root.bind('<Control-v>', self.paste_content)
        self.root.bind('<Command-v>', self.paste_content)
        keyboard.add_hotkey('ctrl+shift+z', lambda: self.window_manager.show_window() if hasattr(self, 'window_manager') else self.show_window)

    def set_window_manager(self, window_manager):
        """设置窗口管理器实例"""
        self.window_manager = window_manager

    def paste_content(self, event=None):
        """处理粘贴操作"""
        if self._exiting:
            return
            
        if self.on_paste_callback:
            self.on_paste_callback()

    def show_text(self, text):
        """显示文本内容"""
        self.display_area.config(text=text, image='')
        self.update_status("文本内容已显示")

    def show_analysis_result(self, text):
        """显示分析结果"""
        # 设置字体和样式
        style = ttk.Style()
        style.configure('Analysis.TLabel', font=('Microsoft YaHei', 12), wraplength=600, justify='left')
        
        # 配置显示区域
        self.display_area.config(
            text=text,
            image='',
            style='Analysis.TLabel'
        )
        
        self.update_status("分析结果已显示")

    def show_image(self, image):
        """显示图片"""
        if self._exiting or not self.display_area.winfo_exists():
            return
            
        try:
            self.current_image = image
            
            # 获取窗口大小
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            # 设置显示尺寸为窗口大小的62%
            display_width = int(window_width * 0.62)
            display_height = int(window_height * 0.62)
            
            # 计算缩放比例
            img_width, img_height = image.size
            width_ratio = display_width / img_width
            height_ratio = display_height / img_height
            ratio = min(width_ratio, height_ratio)
            
            # 计算新的尺寸
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # 调整图片大小
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 创建PhotoImage并显示
            tk_image = ImageTk.PhotoImage(resized_image)
            self.display_area.config(image=tk_image, text='')
            self.image_reference = tk_image
            
        except tk.TclError as e:
            if not self._exiting:
                self.update_status(f"显示图片失败: {str(e)}")

    def update_status(self, message):
        """更新状态栏消息"""
        if self._exiting or not self.status.winfo_exists():
            return
        try:
            self.status.config(text=message)
        except tk.TclError:
            pass

    def update_labels(self, category, tags, summary):
        """更新标签内容"""
        self.category_label.config(text=f"分类：{category}")
        self.tags_label.config(text=f"标签：{tags}")
        self.hint_label.config(text=f"描述：{summary}")

    def on_window_resize(self, event):
        """处理窗口大小变化"""
        if self._exiting or not self.root.winfo_exists():
            return
        if hasattr(self, 'current_image') and self.current_image:
            self.show_image(self.current_image)

    def show_window(self):
        """显示窗口"""
        self.root.deiconify()
        self.root.focus_force() 