import os
import time
import uuid
import datetime
from PIL import Image

class ImageProcessor:
    def __init__(self, note_dir):
        self.note_dir = note_dir
        self.images_dir = os.path.join(note_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)

    def save_image(self, image):
        """保存图片并返回相关信息"""
        try:
            # 生成唯一文件名
            img_filename = f"image_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            image_path = os.path.join(self.images_dir, f"{img_filename}.png")
            md_path = os.path.join(self.note_dir, f"{img_filename}.md")
            
            # 保存图片
            image.save(image_path)
            
            return {
                'filename': img_filename,
                'image_path': image_path,
                'md_path': md_path,
                'relative_path': f"images/{img_filename}.png"
            }
        except Exception as e:
            raise Exception(f"图片保存失败: {str(e)}")

    def create_md_file(self, md_path, image_path, category, tags, summary):
        """创建markdown文件"""
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        md_content = f"""---
category: {category}
tags: {tags}
created: {current_date}
---
![[{image_path}]]
{summary}"""
        
        try:
            with open(md_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(md_content)
        except Exception as e:
            raise Exception(f"Markdown文件创建失败: {str(e)}")

    def process_clipboard_image(self, clipboard_content):
        """处理剪贴板图片内容"""
        if isinstance(clipboard_content, list):
            return self._handle_file_paths(clipboard_content)
        elif isinstance(clipboard_content, Image.Image):
            return clipboard_content
        return None

    def _handle_file_paths(self, file_list):
        """处理文件路径列表（微信图片等）"""
        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        for path in file_list:
            if os.path.isfile(path) and os.path.splitext(path)[1].lower() in valid_extensions:
                try:
                    return Image.open(path)
                except Exception:
                    continue
        return None 