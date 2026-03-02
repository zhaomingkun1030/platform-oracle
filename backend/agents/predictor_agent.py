"""
Predictor Agent - 竞品 Roadmap 预测
"""

import os
import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage


class PredictorAgent:
    """预测 Agent：负责竞品策略解释及 Roadmap 预测"""
    
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
            dashscope_url = api_url.rstrip('/') if api_url else "https://dashscope.aliyuncs.com/compatible-mode/v1"
            self.llm = ChatOpenAI(
                model=model or "qwen-plus",
                openai_api_base=dashscope_url,
                openai_api_key=api_key,
                temperature=0.7
            )
        elif provider == "azure":
            # 使用 OpenAI 兼容模式调用 Azure
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
    
    async def predict(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """基于分析结果预测竞品 Roadmap"""
        prompt = self._build_prediction_prompt(analysis_result)
        
        # 调用 LLM
        response = await self.llm.agenerate([prompt])
        prediction_text = response.generations[0][0].text
        
        # 解析结果
        result = self._parse_prediction(prediction_text, analysis_result)
        
        return result
    
    def _build_prediction_prompt(self, analysis_result: Dict[str, Any]) -> list:
        """构建预测 Prompt"""
        features = analysis_result.get("features", [])
        summary = analysis_result.get("summary", "")
        source_url = analysis_result.get("source_url", "")
        
        features_text = "\n".join([
            f"- {f.get('name', 'N/A')}: {f.get('description', '')}"
            for f in features[:10]
        ])
        
        human_prompt = f"""你是一个专业的技术战略分析师，专门预测竞品的技术发展方向。

基于已分析的功能点，请预测竞品的技术 Roadmap 和战略方向。

输出格式要求（JSON）：
{{
    "technology_trends": [
        {{
            "trend": "技术趋势名称",
            "description": "趋势描述",
            "confidence": "高/中/低"
        }}
    ],
    "capability_directions": [
        {{
            "direction": "能力方向",
            "description": "方向描述",
            "timeline": "短期/中期/长期"
        }}
    ],
    "strategic_predictions": [
        "战略预测1",
        "战略预测2",
        "战略预测3"
    ],
    "competitive_analysis": "竞争分析总结"
}}

注意：
- confidence 表示预测的可信度
- timeline 表示预计实现时间

基于以下来自 {source_url} 的功能分析结果，请预测竞品的 Roadmap：

已识别功能点：
{features_text}

整体分析总结：
{summary}

请预测该竞品的技术发展方向和战略布局。"""
        
        return [HumanMessage(content=human_prompt)]
    
    def _parse_prediction(self, prediction_text: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """解析预测结果"""
        import json
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', prediction_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"raw_prediction": prediction_text}
        except json.JSONDecodeError:
            result = {"raw_prediction": prediction_text}
        
        result["source_url"] = analysis_result.get("source_url", "")
        
        return result