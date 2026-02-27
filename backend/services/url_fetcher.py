"""
URL Fetcher - URL 内容获取服务
"""

import re
import requests
from typing import Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class URLFetcher:
    """URL 内容获取服务"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    async def fetch(self, url: str) -> Dict[str, Any]:
        """
        获取 URL 内容
        
        Args:
            url: 目标 URL
        
        Returns:
            包含 text, html, is_video 等字段的字典
        """
        parsed = urlparse(url)
        
        # 检测是否为视频 URL
        if self._is_video_url(url):
            return await self._fetch_video(url)
        
        # 否则获取网页内容
        return await self._fetch_webpage(url)
    
    def _is_video_url(self, url: str) -> bool:
        """检测是否为视频 URL"""
        video_patterns = [
            r'youtube\.com',
            r'youtu\.be',
            r'vimeo\.com',
            r'bilibili\.com',
        ]
        return any(re.search(p, url, re.IGNORECASE) for p in video_patterns)
    
    async def _fetch_webpage(self, url: str) -> Dict[str, Any]:
        """获取网页内容"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            
            # 提取文本（去除脚本和样式）
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            
            # 清理空白
            text = re.sub(r'\n+', '\n', text)
            text = text[:50000]  # 限制长度
            
            return {
                "text": text,
                "html": html,
                "is_video": False,
                "title": soup.title.string if soup.title else "",
                "url": url
            }
            
        except Exception as e:
            return {
                "text": f"Error fetching URL: {str(e)}",
                "html": "",
                "is_video": False,
                "error": str(e),
                "url": url
            }
    
    async def _fetch_video(self, url: str) -> Dict[str, Any]:
        """获取视频内容"""
        # 简化实现：尝试获取视频信息
        # 实际生产中需要 YouTube Data API 等
        
        try:
            response = self.session.get(url, timeout=30)
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            
            # 提取视频标题
            title = ""
            if soup.title:
                title = soup.title.string
            
            # 提取 meta 描述
            description = ""
            meta_desc = soup.find("meta", {"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "")
            
            return {
                "text": f"Video: {title}\n\nDescription: {description}",
                "html": html,
                "is_video": True,
                "video_info": {
                    "title": title,
                    "description": description,
                    "url": url
                },
                "transcript": description,  # 简化：使用描述作为 transcript
                "url": url
            }
            
        except Exception as e:
            return {
                "text": f"Error fetching video: {str(e)}",
                "is_video": True,
                "error": str(e),
                "url": url
            }
