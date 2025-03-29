import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageGrab
import os
import time
import uuid
import keyboard
import pystray
from PIL import Image
import threading
import sys

import google.generativeai as genai

import datetime #For save md

import configparser #For ini

import ctypes
from ctypes import wintypes

class MSG(ctypes.Structure):
    _fields_ = [
        ("hWnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]
PM_REMOVE = 0x0001

def _pump_messages():
    """安全处理消息队列的替代方案"""
    msg = MSG()
    while ctypes.windll.user32.PeekMessageW(
        ctypes.byref(msg), 
        None, 
        0, 0, 
        PM_REMOVE
    ):
        ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

# 设置代理（需替换为你的实际代理地址）
os.environ["http_proxy"] = "http://127.0.0.1:1080"  # HTTP代理
os.environ["https_proxy"] = "http://127.0.0.1:1080" # HTTPS代理

class Gemini_model:
    def __init__(self):
        # 读取配置文件
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError("配置文件 config.ini 未找到，请创建并配置API密钥")
        config.read(config_path)
        
        try:
            api_key = config['gemini']['api_key']
        except KeyError:
            raise KeyError("请在 config.ini 文件的 [gemini] 节中配置 api_key")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        response = self.model.generate_content("你好，接下来你将扮演一位笔记整理专家，接下来的回答请不要加入任何我没有提及的联想，只按照我的要求用markdown语法用中文回答。")
        print(response.text)
    def image_load(self, image):
        return self.model.generate_content(["请认真分析这张图片，用中文概述它包括它可能出现的场合以及具体的内容，回答不要加入问候语，只回答我提问的内容且只可以用一段话来回答，不可以分点", image])
    def tag_analyse(self, image_summary):
        return self.model.generate_content(["概括这段话的若干个关键词，每个关键词用空格分隔，回答不要加入问候语，只回答我提问的内容", image_summary])
    def category_judge(self, image):
        return self.model.generate_content(["请认真分析这张图片，判断这个图片属于[动漫截图/文字材料/影视截图/实拍照片/meme图/其他图片]中的具体哪一个类型，回答不要加入问候语，只回答类型的名字", image])


class ClipboardApp:
    def __init__(self, root, g_model):
        # 新增退出状态标记
        self._exiting = False
        
        self.root = root
        self.root.title("TagSnap")
        self.image_reference = None
        self.root.iconbitmap('tagsnap.ico')
        
        # 设置窗口关闭按钮的行为
        self.root.protocol('WM_DELETE_WINDOW', self.safe_hide_window)
        self.root.bind('<FocusIn>', self._sync_window_state)
        
        # 初始化托盘图标变量
        self.icon = None
        self.icon_thread = None
        self.icon_running_event = threading.Event()
        self.icon_lock = threading.Lock()
        self.icon_visible = threading.Event()
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
        # 注册全局快捷键
        keyboard.add_hotkey('ctrl+shift+z', self._safe_show_window_wrapper)
        
        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(expand=True, fill='both')

        # 创建显示区域框架
        self.display_frame = ttk.Frame(self.main_frame)
        self.display_frame.pack(expand=True, fill='both', pady=5)

        # 创建显示区域
        self.display_area = ttk.Label(self.display_frame)
        self.display_area.pack(expand=True)

        # 状态栏
        self.status = ttk.Label(root, text="就绪", foreground="gray")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # 绑定快捷键
        self.root.bind('<Control-v>', self.paste_content)
        self.root.bind('<Command-v>', self.paste_content)

        # 创建标签框架
        self.labels_frame = ttk.Frame(root)
        self.labels_frame.pack(fill='x', padx=10, pady=2)

        # 设置字体
        label_font = ('Microsoft YaHei', 10)

        # 分类标签
        self.category_label = ttk.Label(self.labels_frame, wraplength=640, font=label_font)
        self.category_label.pack(pady=1)

        # 标签标签
        self.tags_label = ttk.Label(self.labels_frame, wraplength=640, font=label_font)
        self.tags_label.pack(pady=1)

        # 提示标签（图片描述）
        self.hint_label = ttk.Label(self.labels_frame, text="使用 Ctrl+V 粘贴内容", foreground="gray", wraplength=640, font=label_font)
        self.hint_label.pack(pady=1)

        #Gemini
        self.g_model = g_model

        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)

    def _safe_show_window_wrapper(self):
            """带状态检查的快捷键包装器"""
            if not self.icon_visible.is_set():
                self.show_window()

    def create_tray_icon(self):
        """创建系统托盘图标"""
        if self.icon is None:
            try:
                # 使用icon.png作为托盘图标
                image = Image.open('icon.png')
                menu = (
                    pystray.MenuItem("显示", self.show_window),
                    pystray.MenuItem("退出", self.quit_app)
                )
                self.icon = pystray.Icon("TagSnap", image, "TagSnap", menu)
            except Exception as e:
                # 如果找不到icon.png，使用默认的黑色图标
                image = Image.new('RGB', (64, 64), 'black')
                menu = (
                    pystray.MenuItem("显示", self.show_window),
                    pystray.MenuItem("退出", self.quit_app)
                )
                self.icon = pystray.Icon("TagSnap", image, "TagSnap", menu)
                print(f"无法加载icon.png: {str(e)}")

    def _run_icon(self):
        """在单独的线程中运行托盘图标"""
        try:
            self.icon.run()
        finally:
            self.is_icon_running = False

    def _cleanup_icon_resources(self):
        """增强资源清理（添加状态标记）"""
        try:
            if self.icon and hasattr(self.icon, '_hwnd'):
                # 先停止消息循环
                if not getattr(self.icon, '_stopped', True):
                    ctypes.windll.user32.PostMessageW(
                        self.icon._hwnd,
                        0x0010, 0, 0)  # WM_CLOSE
                # 清理句柄
                if self.icon._hwnd:
                    ctypes.windll.user32.DestroyWindow(self.icon._hwnd)
                # 清除窗口类
                if self.icon._atom:
                    ctypes.windll.user32.UnregisterClassW(
                        self.icon._atom,
                        ctypes.c_uint(0))
        except Exception as e:
            if not (isinstance(e, OSError) and e.winerror == 1400):
                print(f"资源清理失败: {str(e)}")
        finally:
            # 确保释放所有引用
            self.icon = None
            self.icon_running_event.clear()
    def _sync_window_state(self, event=None):
        """同步窗口状态到托盘图标"""
        if self.root.winfo_viewable() and self.icon_running_event.is_set():
            self.icon_running_event.clear()
            self._cleanup_icon_resources()
    def safe_hide_window(self):
        """安全的窗口隐藏入口（优化状态判断）"""
        if self.root.winfo_viewable():  # 改用更可靠的可见性判断
            self.hide_window()
        else:
            self.root.withdraw()
    def hide_window(self):
        """安全隐藏窗口到托盘（修复图标生成逻辑）"""
        with self.icon_lock:
            # 终止可能残留的托盘实例
            if self.icon_running_event.is_set():
                self._stop_tray_icon()
            
            if not self.icon_running_event.is_set():
                self.root.withdraw()
                # 仅在需要时创建新图标
                if self.icon is None:
                    self.create_tray_icon()
                self.icon_running_event.set()
                self.icon_thread = threading.Thread(
                    target=self._run_icon_safe,
                    daemon=True)
                self.icon_thread.start()
    def _stop_tray_icon(self):
        """优化图标终止方法（修复消息泵问题）"""
        try:
            # 先标记为已停止
            if self.icon:
                self.icon._stopped = True
            
            # 发送退出消息
            if self.icon and hasattr(self.icon, '_hwnd') and self.icon._hwnd:
                for msg in [0x0010, 0x0012]:  # WM_CLOSE, WM_QUIT
                    ctypes.windll.user32.PostMessageW(
                        self.icon._hwnd,
                        msg, 0, 0)
                
                # 替换消息泵处理
                for _ in range(3):
                    _pump_messages()  # 使用自定义消息泵
                    time.sleep(0.1)
        except Exception as e:
            if not (isinstance(e, OSError) and e.winerror == 1400):
                print(f"终止托盘异常: {str(e)}")
        finally:
            self._cleanup_icon_resources()
    def show_window(self):
        """安全显示主窗口（增强同步机制）"""
        # 增加重入锁保护
        with self.icon_lock:
            # 强制终止可能残留的图标
            self._stop_tray_icon()
            
            # 确保窗口状态正确
            if not self.root.winfo_viewable():
                self.root.deiconify()
                
            # 窗口置顶逻辑
            self.root.attributes('-topmost', 1)
            self.root.focus_force()
            self.root.lift()
            
            # 延迟重置置顶属性
            self.root.after(200, lambda: self.root.attributes('-topmost', 0))
            
            # 更新图标可见状态
            self.icon_visible.clear()
    def _run_icon_safe(self):
        """带保护机制的图标运行（修复无效句柄问题）"""
        try:
            # 添加有效性检查
            if self.icon and not getattr(self.icon, '_stopped', False):
                # 设置运行标记防止重复启动
                self.icon._stopped = False
                self.icon.run()
        except Exception as e:
            # 忽略特定错误代码1400
            if not (isinstance(e, OSError) and e.winerror == 1400):
                print(f"托盘运行异常: {str(e)}")
        finally:
            # 强制标记为已停止
            if self.icon:
                self.icon._stopped = True
            self.icon_running_event.clear()
            self._cleanup_icon_resources()
    def quit_app(self):
        """安全退出程序（修复组件访问问题）"""
        # 标记退出状态
        self._exiting = True
        
        # 使用after_idle确保在主线程中执行清理操作
        if threading.current_thread() is not threading.main_thread():
            self.root.after_idle(self._perform_cleanup)
            # 停止托盘图标
            with self.icon_lock:
                if self.icon_running_event.is_set():
                    self._stop_tray_icon()
        else:
            self._perform_cleanup()

    def _perform_cleanup(self):
        """在主线程中执行清理操作"""
        try:
            # 解除全局快捷键
            keyboard.unhook_all_hotkeys()
            
            # 取消所有pending的after事件
            try:
                for timer_id in self.root.tk.eval('after info').split():
                    self.root.after_cancel(timer_id)
            except Exception:
                pass  # 忽略可能的Tcl错误
            
            # 安全销毁窗口组件
            self._safe_destroy_widgets()
            
            # 销毁主窗口
            if self.root.winfo_exists():
                self.root.destroy()
            
            # 正常退出程序
            self.root.after(100, lambda: os._exit(0))
        except Exception as e:
            print(f"清理过程中出现错误: {str(e)}")
            os._exit(1)  # 强制退出

    def _safe_destroy_widgets(self):
        """安全销毁UI组件（防止二次访问）"""
        widgets = [
            self.display_area, self.status, 
            self.category_label, self.tags_label,
            self.hint_label, self.main_frame,
            self.display_frame, self.labels_frame
        ]
        
        for widget in widgets:
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except tk.TclError:
                pass

    def on_window_resize(self, event):
        """增强的窗口缩放处理"""
        if self._exiting or not self.root.winfo_exists():
            return
        if hasattr(self, 'current_image'):
            self.show_image(self.current_image)

    def paste_content(self, event=None):
        """处理粘贴操作的核心方法"""
        if self._exiting:
            return
        try:
            # 先尝试获取图片内容
            clipboard_content = ImageGrab.grabclipboard()
            
            if clipboard_content:
                # 处理微信的特殊情况（文件路径列表）
                if isinstance(clipboard_content, list):
                    self.handle_file_paths(clipboard_content)
                else:
                    self.handle_image(clipboard_content)
                return

            # 如果没有图片内容则尝试获取文本
            text = self.root.clipboard_get()
            self.show_text(text)
            
        except tk.TclError:
            self.update_status("剪贴板内容无法识别")
        except Exception as e:
            self.update_status(f"错误: {str(e)}")

    def handle_file_paths(self, file_list):
        """处理文件路径列表（微信的特殊情况）"""
        # 过滤有效图片文件
        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        for path in file_list:
            if os.path.isfile(path) and os.path.splitext(path)[1].lower() in valid_extensions:
                try:
                    image = Image.open(path)
                    self.handle_image(image)
                    return
                except Exception as e:
                    continue
        self.update_status("未找到有效图片文件")

    def handle_image(self, image): #-----------------------------------------------------
        """统一处理图片对象"""
        try:
            # 保存原始图片
            notedir = r"F:\Users\jzc_f\Documents\Obsidian Library\Images"
            img_filename = f"image_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            # image.save(img_filename)
            image.save(f"{notedir}\images\{img_filename}.png")
            self.update_status(f"图片已保存为 {img_filename}")
            
            # 显示处理后的图片
            self.show_image(image)
            img_sum = self.g_model.image_load(image).text
            img_cate = self.g_model.category_judge(image).text
            img_tags = self.g_model.tag_analyse(img_sum).text
            create_md_file(f"{notedir}\{img_filename}.md", f"images/{img_filename}.png", img_cate, img_tags, img_sum)
            self.update_status(f"已保存为 {img_filename}")

            # 更新所有标签内容
            self.category_label.config(text=f"分类：{img_cate}")
            self.tags_label.config(text=f"标签：{img_tags}")
            self.hint_label.config(text=f"描述：{img_sum}")

        except Exception as e:
            self.update_status(f"保存失败: {str(e)}")
            self.show_image(image)  # 仍然尝试显示

    def show_text(self, text):
        """显示文本内容"""
        self.display_area.config(text=text, image='')
        self.update_status("文本内容已显示")

    def show_image(self, image=None):
        """安全的图片显示方法"""
        if self._exiting or not self.display_area.winfo_exists():
            return
        try:
            # 保存当前图片以供重绘使用
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
            if not self._exiting:  # 仅在非退出状态记录错误
                self.update_status(f"显示图片失败: {str(e)}")

    def update_status(self, message):
        """安全的状态更新方法"""
        if self._exiting or not self.status.winfo_exists():
            return
        try:
            self.status.config(text=message)
        except tk.TclError:
            pass

def create_md_file(filename, image_file, category, tags, summary):
    # 获取当前日期
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 构建文件内容
    md_content = f"""---
category: {category}
tags: {tags}
created: {current_date}
---
![[{image_file}]]
{summary}"""
    
    # 写入文件
    with open(filename, 'w', encoding='utf-8', newline='\n') as f:
        f.write(md_content)

if __name__ == "__main__":
    root = tk.Tk()
    g_model = Gemini_model()
    app = ClipboardApp(root, g_model)
    root.geometry("800x600")
    root.mainloop()
