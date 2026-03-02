"""
Analysis Agent - 内容分析与功能点提取
"""

import os
import re
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage


class AnalysisAgent:
    """分析 Agent：负责内容分析，功能点提取、竞品策略解释"""
    
    def __init__(self, provider: str = "google", api_url: str = "", api_key: str = "", model: str = "gemini-2.0-flash-lite", azure_deployment: str = ""):
        self.provider = provider
        self.model = model
        self.azure_deployment = azure_deployment
        
        # 根据 provider 初始化不同的 LLM
        if provider == "google":
            # 使用 Google Gemini
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=0.7,
                convert_system_message_to_human=True
            )
        elif provider == "alibaba" or provider == "dashscope":
            # 使用阿里云 DashScope (OpenAI 兼容模式)
            # 文档: https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions
            dashscope_url = api_url.rstrip('/') if api_url else "https://dashscope.aliyuncs.com/compatible-mode/v1"
            self.llm = ChatOpenAI(
                model=model or "qwen-plus",
                openai_api_base=dashscope_url,
                openai_api_key=api_key,
                temperature=0.7
            )
        elif provider == "azure":
            # 使用 OpenAI 兼容模式调用 Azure (简化版本)
            # Azure OpenAI 兼容端点格式: https://{resource}.cognitiveservices.azure.com/openai/v1/
            azure_url = api_url.rstrip('/') if api_url else ""
            self.llm = ChatOpenAI(
                model=azure_deployment or model,
                openai_api_base=azure_url,
                openai_api_key=api_key,
                temperature=0.7
            )
        else:
            # 使用 OpenAI 兼容接口
            self.llm = ChatOpenAI(
                model=model,
                openai_api_base=api_url or self._get_default_url(provider),
                openai_api_key=api_key or "dummy-key",
                temperature=0.7
            )
    
    def _get_default_url(self, provider: str) -> str:
        """获取默认 API URL"""
        urls = {
            "google": "https://generativelanguage.googleapis.com/v1beta",
            "alibaba": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "azure": os.getenv("AZURE_OPENAI_ENDPOINT", "https://api.openai.com/v1")
        }
        return urls.get(provider, "http://localhost:8000/v1")
    
    async def analyze(self, content: Dict[str, Any], source_url: str) -> Dict[str, Any]:
        """分析内容并提取功能点"""
        text = content.get("text", "")
        is_video = content.get("is_video", False)
        
        # 构建 prompt
        if is_video:
            prompt = self._video_analysis_prompt(content)
        else:
            prompt = self._doc_analysis_prompt(text, source_url)
        
        # 调用 LLM
        response = await self.llm.agenerate([prompt])
        analysis_text = response.generations[0][0].text
        
        # 解析结果
        result = self._parse_analysis(analysis_text, content, source_url)
        
        return result
    
    def _doc_analysis_prompt(self, text: str, source_url: str) -> List:
        """文档分析 Prompt"""
        human_prompt = f"""你是一个专业的竞品分析专家，专门分析 Red Hat OpenShift 及其竞品的产品功能。

请分析以下来自 {source_url} 的内容，提取结构化的功能点信息。

输出格式要求（JSON）：
{{
    "features": [
        {{
            "name": "功能名称",
            "description": "功能描述",
            "open_source_components": ["使用的开源组件"],
            "use_case": "使用场景",
            "competitor_strategy": "竞品策略解释"
        }}
    ],
    "summary": "整体分析总结",
    "key_insights": ["关键洞察1", "关键洞察2"]
}}

注意：
- 功能名称要简洁明确
- 开源组件如果是开源项目请标注
- 竞品策略要分析竞品为什么做这个功能

请分析以下内容：
{text[:8000]}"""
        
        return [HumanMessage(content=human_prompt)]
    
    def _video_analysis_prompt(self, content: Dict[str, Any]) -> List:
        """视频分析 Prompt"""
        video_info = content.get("video_info", {})
        transcript = content.get("transcript", "")
        
        human_prompt = f"""你是一个专业的竞品分析专家，专门分析 Red Hat OpenShift 及其竞品的产品功能。

请分析视频内容，提取功能点和时间戳。

输出格式要求（JSON）：
{{
    "features": [
        {{
            "name": "功能名称",
            "description": "功能描述",
            "timestamp": "时间点，如 02:30",
            "open_source_components": ["使用的开源组件"],
            "use_case": "使用场景",
            "competitor_strategy": "竞品策略解释"
        }}
    ],
    "video_summary": "视频整体总结",
    "key_insights": ["关键洞察1", "关键洞察2"]
}}

注意：timestamp 是功能点出现在视频中的时间点。

请分析以下视频内容：
视频标题: {video_info.get('title', 'N/A')}
视频描述: {video_info.get('description', 'N/A')}

视频文本内容：
{transcript[:8000]}"""
        
        return [HumanMessage(content=human_prompt)]
    
    def _parse_analysis(self, analysis_text: str, content: Dict[str, Any], source_url: str) -> Dict[str, Any]:
        """解析 LLM 返回的分析结果"""
        import json
        
        # 尝试提取 JSON
        try:
            json_match = re.search(r'\{[\s\S]*\}', analysis_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"raw_analysis": analysis_text}
        except json.JSONDecodeError:
            result = {"raw_analysis": analysis_text}
        
        # 添加元数据
        result["source_url"] = source_url
        result["is_video"] = content.get("is_video", False)
        result["timestamp"] = content.get("timestamp")
        
        return result