import json
import urllib.parse
import urllib.request
from typing import Optional
from dataclasses import dataclass

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import BaseTool


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class LangChainDuckDuckGoSearcher(BaseTool):
    name: str = "duckduckgo_search"
    description: str = "Search the web using DuckDuckGo"

    def _run(self, query: str, max_results: int = 10) -> list[SearchResult]:
        search = DuckDuckGoSearchRun()
        raw = search.run(f"{query} (site:github.com OR site:towardsdatascience.com OR site:medium.com OR site:stackoverflow.com OR site:python.org OR site:reddit.com OR site:arxiv.org OR site:wikipedia.org OR site:docs.python.org OR site:realpython.com OR site:dev.to OR site:analyticsvidhya.com OR site:kaggle.com)")
        results = []
        for line in raw.split("\n"):
            if line.strip():
                results.append(SearchResult(
                    title=line.strip()[:80],
                    url="",
                    snippet=line.strip()
                ))
        return results[:max_results]


class TavilySearcher(BaseTool):
    name: str = "tavily_search"
    description: str = "Search the web using Tavily API"

    def _run(self, query: str, max_results: int = 10) -> list[SearchResult]:
        try:
            search = TavilySearchResults(max_results=max_results)
            raw = search.invoke({"query": query})
            results = []
            for item in raw:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", "")
                ))
            return results
        except Exception as e:
            print(f"[WARN] Tavily search failed: {e}")
            return []


class BaiduSearcher(BaseTool):
    name: str = "baidu_search"
    description: str = "Search the web using Baidu (Chinese search engine)"

    def _run(self, query: str, max_results: int = 10) -> list[SearchResult]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}&rn={max_results}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[WARN] Baidu search failed: {e}")
            return []

        import re
        results = []
        blocks = re.findall(
            r'<div[^>]*class="[^"]*result[^"]*"[^>]*>.*?<h3[^>]*>.*?<a[^>]*href="(.*?)"[^>]*>(.*?)</a>.*?<span[^>]*class="[^"]*content-right_[^"]*"[^>]*>(.*?)</span>',
            html, re.DOTALL
        )
        for url, title, snippet in blocks[:max_results]:
            title_clean = re.sub(r"<[^>]+>", "", title).strip()
            snippet_clean = re.sub(r"<[^>]+>", "", snippet).strip()
            results.append(SearchResult(
                title=title_clean,
                url=url,
                snippet=snippet_clean
            ))

        if not results:
            titles = re.findall(r'<h3[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.DOTALL)[:max_results]
            for t in titles:
                t_clean = re.sub(r"<[^>]+>", "", t).strip()
                results.append(SearchResult(title=t_clean, url="", snippet=""))

        return results


def search_web(query: str, max_results: int = 10, engine: str = "duckduckgo") -> list[SearchResult]:
    if engine == "tavily":
        searcher = TavilySearcher()
    elif engine == "baidu":
        searcher = BaiduSearcher()
    else:
        searcher = LangChainDuckDuckGoSearcher()
    return searcher._run(query, max_results)
