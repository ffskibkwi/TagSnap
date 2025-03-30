import os
import configparser
import google.generativeai as genai

class GeminiHandler:
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
        self._initialize_model()
        
    def _initialize_model(self):
        """初始化模型并设置基础prompt"""
        response = self.model.generate_content(
            "你好，接下来你将扮演一位笔记整理专家，接下来的回答请不要加入任何我没有提及的联想，"
            "只按照我的要求用markdown语法用中文回答。"
        )
        print(response.text)
        
    def analyze_image(self, image):
        """分析图片内容"""
        summary = self.image_summary_analyze(image)
        category = self.image_category_judge(image)
        tags = self.image_tag_analyze(summary.text)
        
        return {
            'summary': summary.text,
            'category': category.text,
            'tags': tags.text
        }

    def image_summary_analyze(self, image):
        """获取图片描述"""
        return self.model.generate_content([
            "请认真分析这张图片，用中文概述它包括它可能出现的场合以及具体的内容，"
            "回答不要加入问候语，只回答我提问的内容且只可以用一段话来回答，不可以分点", 
            image
        ])

    def image_tag_analyze(self, image_summary):
        """分析图片标签"""
        return self.model.generate_content([
            "概括这段话的若干个关键词，每个关键词用空格分隔，回答不要加入问候语，只回答我提问的内容", 
            image_summary
        ])

    def image_category_judge(self, image):
        """判断图片类别"""
        return self.model.generate_content([
            "请认真分析这张图片，判断这个图片属于[动漫截图/文字材料/影视截图/实拍照片/meme图/其他图片]中的具体哪一个类型，"
            "回答不要加入问候语，只回答类型的名字", 
            image
        ]) 