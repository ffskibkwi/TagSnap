import threading
import ctypes
from ctypes import wintypes
import pystray
from PIL import Image
import time
import tkinter as tk

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
    """安全处理消息队列"""
    msg = MSG()
    while ctypes.windll.user32.PeekMessageW(
        ctypes.byref(msg), 
        None, 
        0, 0, 
        PM_REMOVE
    ):
        ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

class WindowManager:
    def __init__(self, root, show_callback, quit_callback):
        self.root = root
        self.show_callback = show_callback
        self.quit_callback = quit_callback
        
        # 状态标记
        self._exiting = False
        self.icon = None
        self.icon_thread = None
        self.icon_running_event = threading.Event()
        self.icon_lock = threading.Lock()
        self.icon_visible = threading.Event()
        
        # 创建托盘图标
        self.create_tray_icon()
        
        # 设置窗口关闭按钮行为
        self.root.protocol('WM_DELETE_WINDOW', self.safe_hide_window)
        self.root.bind('<FocusIn>', self._sync_window_state)

    def create_tray_icon(self):
        """创建系统托盘图标"""
        if self.icon is None:
            try:
                image = Image.open('icon.png')
            except Exception:
                image = Image.new('RGB', (64, 64), 'black')
                
            menu = (
                pystray.MenuItem("显示", self.show_window),
                pystray.MenuItem("退出", self.quit_app)
            )
            self.icon = pystray.Icon("TagSnap", image, "TagSnap", menu)

    def _run_icon(self):
        """在单独的线程中运行托盘图标"""
        try:
            self.icon.run()
        finally:
            self.is_icon_running = False

    def _cleanup_icon_resources(self):
        """清理托盘图标资源"""
        try:
            if self.icon and hasattr(self.icon, '_hwnd'):
                if not getattr(self.icon, '_stopped', True):
                    ctypes.windll.user32.PostMessageW(
                        self.icon._hwnd,
                        0x0010, 0, 0)
                if self.icon._hwnd:
                    ctypes.windll.user32.DestroyWindow(self.icon._hwnd)
                if self.icon._atom:
                    ctypes.windll.user32.UnregisterClassW(
                        self.icon._atom,
                        ctypes.c_uint(0))
        except Exception as e:
            if not (isinstance(e, OSError) and e.winerror == 1400):
                print(f"资源清理失败: {str(e)}")
        finally:
            self.icon = None
            self.icon_running_event.clear()

    def _sync_window_state(self, event=None):
        """同步窗口状态"""
        if self.root.winfo_viewable() and self.icon_running_event.is_set():
            self.icon_running_event.clear()
            self._cleanup_icon_resources()

    def safe_hide_window(self):
        """安全隐藏窗口"""
        if self.root.winfo_viewable():
            self.hide_window()
        else:
            self.root.withdraw()

    def hide_window(self):
        """隐藏窗口到托盘"""
        with self.icon_lock:
            if self.icon_running_event.is_set():
                self._stop_tray_icon()
            
            if not self.icon_running_event.is_set():
                self.root.withdraw()
                if self.icon is None:
                    self.create_tray_icon()
                self.icon_running_event.set()
                self.icon_thread = threading.Thread(
                    target=self._run_icon_safe,
                    daemon=True)
                self.icon_thread.start()

    def _stop_tray_icon(self):
        """停止托盘图标"""
        try:
            if self.icon:
                self.icon._stopped = True
            
            if self.icon and hasattr(self.icon, '_hwnd') and self.icon._hwnd:
                for msg in [0x0010, 0x0012]:
                    ctypes.windll.user32.PostMessageW(
                        self.icon._hwnd,
                        msg, 0, 0)
                
                for _ in range(3):
                    _pump_messages()
                    time.sleep(0.1)
        except Exception as e:
            if not (isinstance(e, OSError) and e.winerror == 1400):
                print(f"终止托盘异常: {str(e)}")
        finally:
            self._cleanup_icon_resources()

    def show_window(self):
        """显示主窗口"""
        with self.icon_lock:
            self._stop_tray_icon()
            
            if not self.root.winfo_viewable():
                self.root.deiconify()
                
            self.root.attributes('-topmost', 1)
            self.root.focus_force()
            self.root.lift()
            
            self.root.after(200, lambda: self.root.attributes('-topmost', 0))
            
            self.icon_visible.clear()
            
            if self.show_callback:
                self.show_callback()

    def _run_icon_safe(self):
        """安全运行托盘图标"""
        try:
            if self.icon and not getattr(self.icon, '_stopped', False):
                self.icon._stopped = False
                self.icon.run()
        except Exception as e:
            if not (isinstance(e, OSError) and e.winerror == 1400):
                print(f"托盘运行异常: {str(e)}")
        finally:
            if self.icon:
                self.icon._stopped = True
            self.icon_running_event.clear()
            self._cleanup_icon_resources()

    def quit_app(self):
        """退出应用程序"""
        self._exiting = True
        
        if threading.current_thread() is not threading.main_thread():
            self.root.after_idle(self._perform_cleanup)
            with self.icon_lock:
                if self.icon_running_event.is_set():
                    self._stop_tray_icon()
        else:
            self._perform_cleanup()

    def _perform_cleanup(self):
        """执行清理操作"""
        if self.quit_callback:
            self.quit_callback() 