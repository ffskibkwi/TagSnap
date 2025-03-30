import os
import re
import time
import uuid
import datetime

class TextProcessor:
    def __init__(self, note_dir):
        self.note_dir = note_dir
        self.source_dir = os.path.join(note_dir, "source")
        os.makedirs(self.source_dir, exist_ok=True)

    def process_source(self, md_text, source_dir):
        # 提取标题
        title = None
        title_line_index = None
        lines = md_text.split('\n')
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('# '):
                title = stripped.lstrip('# ').strip()
                title_line_index = i
                break
                
        if not title:
            raise ValueError("未找到标题行（以#开头的行）")
            
        # 删除标题行
        if title_line_index is not None:
            del lines[title_line_index]
            md_text = '\n'.join(lines)
            
        # 处理元数据块
        processed_text = md_text
        metadata_match = re.search(r'^---\n(.*?)\n---', md_text, re.DOTALL)
        
        if metadata_match:
            metadata_block = metadata_match.group(1)
            metadata_lines = metadata_block.split('\n')
            
            tags_idx = None
            source_idx = None
            
            # 查找tags和source的位置
            for i, line in enumerate(metadata_lines):
                line = line.strip()
                if line.startswith('tags:'):
                    tags_idx = i
                if line.startswith('source:') and tags_idx is not None:
                    source_idx = i
                    break
            
            # 删除tags到source之间的内容
            if tags_idx is not None and source_idx is not None and tags_idx < source_idx:
                del metadata_lines[tags_idx:source_idx]
                new_metadata = '\n'.join(metadata_lines)
                processed_text = re.sub(
                    r'^---\n.*?\n---',
                    f'---\n{new_metadata}\n---',
                    md_text,
                    flags=re.DOTALL
                )
        
        # 生成文件名并保存
        filename = f"source_{title}.md".replace('/', '_')  # 处理可能存在的非法字符
        output_path = os.path.join(source_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_text)
        
        return title

    def create_md_file(self, md_path, md_title, category, tags, summary):
        """创建markdown文件"""
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        md_content = f"""---
category: {category}
tags: {tags}
created: {current_date}
link: "[[source/source_{md_title}]]"
---
{summary}"""
        
        try:
            with open(md_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(md_content)
        except Exception as e:
            raise Exception(f"Markdown文件创建失败: {str(e)}")