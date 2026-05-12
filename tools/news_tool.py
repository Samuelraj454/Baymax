from .base_tool import BaseTool, ToolResult
import httpx
import os
import xml.etree.ElementTree as ET
from loguru import logger

class NewsTool(BaseTool):
    name = "news"
    description = "Get top news headlines or search news."
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["top", "search"]},
            "query": {"type": "string"},
            "country": {"type": "string", "default": "in"},
            "count": {"type": "integer", "default": 5}
        },
        "required": ["action"]
    }

    def run(self, action: str, **kwargs) -> ToolResult:
        api_key = os.getenv("NEWS_API_KEY")
        
        if api_key:
            return self._fetch_news_api(action, api_key, **kwargs)
        else:
            return self._fetch_google_news_rss(kwargs.get("query", "top stories"))

    def _fetch_news_api(self, action, api_key, **kwargs):
        try:
            count = kwargs.get("count", 5)
            if action == "top":
                country = kwargs.get("country", "in")
                url = f"https://newsapi.org/v2/top-headlines?country={country}&apiKey={api_key}"
            else:
                query = kwargs.get("query")
                url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
                
            resp = httpx.get(url)
            resp.raise_for_status()
            articles = resp.json().get("articles", [])[:count]
            results = [{"title": a["title"], "source": a["source"]["name"], "url": a["url"]} for a in articles]
            return ToolResult(success=True, output=str(results))
        except Exception as e:
            return self._fetch_google_news_rss(kwargs.get("query", "top stories"))

    def _fetch_google_news_rss(self, query):
        try:
            url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
            resp = httpx.get(url)
            root = ET.fromstring(resp.text)
            results = []
            for item in root.findall('.//item')[:5]:
                results.append({
                    "title": item.find('title').text,
                    "url": item.find('link').text,
                    "date": item.find('pubDate').text
                })
            return ToolResult(success=True, output=str(results))
        except Exception as e:
            logger.error(f"News RSS Error: {e}")
            return ToolResult(success=False, output=None, error="Could not fetch news.")
