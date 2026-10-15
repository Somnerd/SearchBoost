#!/usr/bin/env python3
"""
SearchBoost MCP Bridge for Hermes Agent
Exposes SearchBoost cognitive search, SearXNG metasearch, and vector knowledge base as MCP tools.
"""

import os
import sys
import json
import asyncio
import httpx
from typing import Optional
from mcp.server.mcpserver import MCPServer

app = MCPServer("SearchBoost")

API_BASE_URL = os.environ.get("SEARCHBOOST_API_URL", "http://localhost:3001/api")
SEARXNG_URL = os.environ.get("SEARCHBOOST_SEARXNG_URL", "http://localhost:8888")
USERNAME = os.environ.get("SEARCHBOOST_USER", "hermes_agent")
PASSWORD = os.environ.get("SEARCHBOOST_PASSWORD", "")

_cached_token: Optional[str] = None

async def get_auth_token(client: httpx.AsyncClient) -> str:
    global _cached_token
    if _cached_token:
        return _cached_token

    # Attempt login
    try:
        resp = await client.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=5.0
        )
        if resp.status_code == 200:
            token = resp.cookies.get("sb_token")
            if token:
                _cached_token = token
                return token
    except Exception:
        pass

    # If login failed, attempt registration first
    try:
        await client.post(
            f"{API_BASE_URL}/auth/register",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=5.0
        )
        resp = await client.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=5.0
        )
        token = resp.cookies.get("sb_token")
        if token:
            _cached_token = token
            return token
    except Exception as e:
        sys.stderr.write(f"[SearchBoost MCP] Auth error: {e}\n")

    return ""

async def fallback_searxng_search(client: httpx.AsyncClient, query: str) -> str:
    """Direct fallback to SearXNG metasearch engine."""
    try:
        resp = await client.get(
            f"{SEARXNG_URL}/search",
            params={"q": query, "format": "json"},
            timeout=10.0
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return f"SearchBoost metasearch returned 0 direct hits for '{query}'."
            formatted = []
            for r in results[:6]:
                title = r.get("title", "Untitled")
                content = r.get("content", "")
                url = r.get("url", "")
                formatted.append(f"### [{title}]({url})\n{content}\n")
            return "\n---\n".join(formatted)
    except Exception as e:
        return f"SearXNG search error: {e}"
    return "No search results available."

@app.tool()
async def searchboost_search(query: str, search_depth: str = "deep") -> str:
    """Execute cognitive search across SearXNG metasearch and knowledge vector memory via SearchBoost.
    
    Args:
        query: The search question or keywords.
        search_depth: 'deep' for comprehensive multi-source reasoning or 'fast' for quick grounding.
    """
    research_mode = search_depth.lower() != "fast"
    async with httpx.AsyncClient() as client:
        token = await get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {}

        # 1. Enqueue job to SearchBoost API
        try:
            enqueue_resp = await client.post(
                f"{API_BASE_URL}/search/enqueue",
                headers=headers,
                json={
                    "query": query,
                    "thread_id": "hermes-session",
                    "options": {"research_mode": research_mode, "web_search": True}
                },
                timeout=8.0
            )

            if enqueue_resp.status_code == 200:
                job_id = enqueue_resp.json().get("id") or enqueue_resp.json().get("job_id")
                if job_id:
                    # Poll for completion (up to 25 seconds)
                    for _ in range(25):
                        await asyncio.sleep(1.0)
                        res_resp = await client.get(
                            f"{API_BASE_URL}/search/result/{job_id}",
                            headers=headers,
                            timeout=5.0
                        )
                        if res_resp.status_code == 200:
                            res_data = res_resp.json()
                            status = res_data.get("status")
                            if status == "complete":
                                result_text = res_data.get("result", "")
                                if result_text and "no results found" not in result_text.lower():
                                    return str(result_text)
                                # If synthesis reported no results, fall back to direct SearXNG raw results
                                raw = await fallback_searxng_search(client, query)
                                return f"{result_text}\n\n**Direct Metasearch Sources:**\n{raw}"
                            elif status == "failed":
                                break
        except Exception as e:
            sys.stderr.write(f"[SearchBoost MCP] Pipeline exception: {e}\n")

        # Fallback to direct SearXNG metasearch if worker queue is unavailable or timed out
        return await fallback_searxng_search(client, query)

@app.tool()
async def searchboost_list_docs() -> str:
    """List indexed documents and files currently in the SearchBoost vector knowledge base."""
    async with httpx.AsyncClient() as client:
        token = await get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            resp = await client.get(f"{API_BASE_URL}/search/docs", headers=headers, timeout=5.0)
            if resp.status_code == 200:
                docs = resp.json()
                if not docs:
                    return "No documents currently indexed in SearchBoost knowledge base."
                return json.dumps(docs, indent=2)
            return f"Failed to list docs: HTTP {resp.status_code}"
        except Exception as e:
            return f"Error listing SearchBoost documents: {e}"

if __name__ == "__main__":
    app.run()
