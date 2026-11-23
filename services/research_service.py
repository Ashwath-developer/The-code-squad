import os
import requests

class ResearchService:
    def current_guidance(self, query="fire emergency safety official guidance"):
        key = os.getenv("SEARCH_API_KEY")
        if not key:
            return {"status": "unavailable", "source": "none", "message": "Live search API key not configured; using no external claims.", "results": []}
        try:
            response = requests.get("https://www.googleapis.com/customsearch/v1",
                params={"key": key, "cx": os.getenv("SEARCH_ENGINE_ID", ""), "q": query}, timeout=10)
            response.raise_for_status()
            items = response.json().get("items", [])[:3]
            return {"status": "success", "source": "Google Custom Search",
                    "results": [{"title": i.get("title", ""), "url": i.get("link", ""), "snippet": i.get("snippet", "")} for i in items]}
        except requests.RequestException as exc:
            return {"status": "degraded", "source": "search API", "message": str(exc)[:300], "results": []}
