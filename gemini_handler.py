import os
import configparser
import google.generativeai as genai

class GeminiHandler:
    def __init__(self):
        # 读取配置文件
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompt.ini')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError("配置文件 config.ini 未找到，请创建并配置API密钥")
        if not os.path.exists(prompt_path):
            raise FileNotFoundError("配置文件 prompt.ini 未找到，请创建并配置prompt")
            
        config.read(config_path, encoding='utf-8')
        self.prompts = configparser.ConfigParser()
        self.prompts.read(prompt_path, encoding='utf-8')
        
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
            self.prompts['gemini']['initial_prompt']
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
            self.prompts['image']['summary_prompt'], 
            image
        ])

    def image_tag_analyze(self, image_summary):
        """分析图片标签"""
        return self.model.generate_content([
            self.prompts['image']['tag_prompt'], 
            image_summary
        ])

    def image_category_judge(self, image):
        """判断图片类别"""
        return self.model.generate_content([
            self.prompts['image']['category_prompt'], 
            image
        ]) 
    
    def md_category_judge(self, md_text):
        """判断文本类别"""
        return self.model.generate_content([
            self.prompts['markdown']['category_prompt'], 
            md_text
        ])
    
    def md_summary_analyze(self, md_text):
        """获取文本描述"""
        return self.model.generate_content([
            self.prompts['markdown']['summary_prompt'], 
            md_text
        ])
    
    def md_tag_analyze(self, md_text):
        """分析文本标签"""
        return self.model.generate_content([
            self.prompts['markdown']['tag_prompt'], 
            md_text
        ])