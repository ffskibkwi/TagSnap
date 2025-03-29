import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageGrab
import os
import time
import uuid

import google.generativeai as genai

import datetime #For save md

import configparser #For ini

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
        self.root = root
        self.root.title("TagSnap")
        self.image_reference = None
        self.root.iconbitmap('tagsnap.ico')

        # 创建显示区域
        self.display_area = ttk.Label(root)
        self.display_area.pack(padx=10, pady=10, expand=True, fill='both')

        # 状态栏
        self.status = ttk.Label(root, text="就绪", foreground="gray")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # 绑定快捷键
        self.root.bind('<Control-v>', self.paste_content)
        self.root.bind('<Command-v>', self.paste_content)

        # 提示标签
        ttk.Label(root, text="使用 Ctrl+V 粘贴内容", foreground="gray").pack()

        #Gemini
        self.g_model = g_model

    def paste_content(self, event=None):
        """处理粘贴操作的核心方法"""
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
            img_sum = g_model.image_load(image).text
            img_cate = g_model.category_judge(image).text
            img_tags = g_model.tag_analyse(img_sum).text
            create_md_file(f"{notedir}\{img_filename}.md", f"images/{img_filename}.png", img_cate, img_tags, img_sum)


        except Exception as e:
            self.update_status(f"保存失败: {str(e)}")
            self.show_image(image)  # 仍然尝试显示

    def show_text(self, text):
        """显示文本内容"""
        self.display_area.config(text=text, image='')
        self.update_status("文本内容已显示")

    def show_image(self, image):
        """显示图片并保持比例"""
        try:
            # 调整图片尺寸
            width, height = image.size
            max_size = 600
            if max(width, height) > max_size:
                ratio = max_size / max(width, height)
                new_size = (int(width*ratio), int(height*ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            tk_image = ImageTk.PhotoImage(image)
            self.display_area.config(image=tk_image, text='')
            self.image_reference = tk_image
        except Exception as e:
            self.update_status(f"显示图片失败: {str(e)}")

    def update_status(self, message):
        """更新状态栏"""
        self.status.config(text=message)
        self.root.after(5000, lambda: self.status.config(text="就绪"))

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
