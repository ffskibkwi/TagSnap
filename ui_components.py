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
        self.current_display = None  # 用于跟踪当前显示的内容类型
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

        # 图片显示区域
        self.image_label = ttk.Label(self.display_frame)
        self.image_label.pack(expand=True)
        self.image_label.pack_forget()  # 初始隐藏

        # 文本显示区域
        self.text_area = tk.Text(self.display_frame, wrap=tk.WORD, 
                               font=('Microsoft YaHei', 12),
                               borderwidth=0, highlightthickness=0,
                               background=self.root.cget('bg'))
        self.text_area.pack(expand=True, fill='both')
        self.text_area.configure(state='disabled')
        self.text_area.pack_forget()  # 初始隐藏

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
        # 隐藏图片显示区域
        self.image_label.pack_forget()
        
        # 显示文本区域
        self.text_area.pack(expand=True, fill='both')
        
        # 启用文本框编辑
        self.text_area.configure(state='normal')
        
        # 清空当前内容
        self.text_area.delete('1.0', tk.END)
        
        # 插入新内容
        self.text_area.insert('1.0', text)
        
        # 禁用文本框编辑
        self.text_area.configure(state='disabled')
        
        # 标记当前显示的是文本
        self.current_display = 'text'
        
        self.update_status("文本内容已显示")

    def show_analysis_result(self, text):
        """显示分析结果"""
        # 隐藏图片显示区域
        self.image_label.pack_forget()
        
        # 显示文本区域
        self.text_area.pack(expand=True, fill='both')
        
        # 启用文本框编辑
        self.text_area.configure(state='normal')
        
        # 清空当前内容
        self.text_area.delete('1.0', tk.END)
        
        # 插入新内容
        self.text_area.insert('1.0', text)
        
        # 文本居中对齐
        self.text_area.tag_add('center', '1.0', tk.END)
        self.text_area.tag_configure('center', justify='center')
        
        # 设置背景色与窗口一致
        self.text_area.configure(background=self.root.cget('bg'))
        
        # 禁用文本框编辑
        self.text_area.configure(state='disabled')
        
        # 标记当前显示的是文本
        self.current_display = 'text'
        
        self.update_status("分析结果已显示")

    def show_image(self, image):
        """显示图片"""
        if self._exiting or not self.image_label.winfo_exists():
            return
            
        try:
            self.current_image = image
            
            # 隐藏文本区域
            self.text_area.pack_forget()
            
            # 显示图片区域
            self.image_label.pack(expand=True)
            
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
            self.image_label.config(image=tk_image)
            self.image_reference = tk_image
            
            # 标记当前显示的是图片
            self.current_display = 'image'
            
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
        # 只在当前显示的是图片时重新显示图片
        if hasattr(self, 'current_image') and self.current_image and self.current_display == 'image':
            self.show_image(self.current_image)

    def show_window(self):
        """显示窗口"""
        self.root.deiconify()
        self.root.focus_force()

    def clear_labels(self):
        """清空底部标签"""
        self.category_label.config(text="")
        self.tags_label.config(text="")
        self.hint_label.config(text="使用 Ctrl+V 粘贴内容") 