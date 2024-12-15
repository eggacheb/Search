# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import os
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor

from search_engines import (
    get_google_search_results,
    get_bing_search_results,
    get_baidu_search_results
)

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="OnlineGPT Search API",
    description="A web API for searching information from multiple search engines",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    queries: List[str]
    num_results: Optional[int] = 5
    engine: Optional[str] = "Google"
    custom_question: Optional[str] = None

class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str
    content: str

@app.get("/")
async def root():
    return {"message": "Welcome to OnlineGPT Search API"}

@app.post("/search")
async def search(request: SearchRequest):
    try:
        # 设置搜索超时时间为55秒(留5秒缓冲)
        timeout = 55
        
        async def search_with_timeout():
            all_results = []
            for query in request.queries:
                if request.engine == 'Google':
                    results = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        get_google_search_results,
                        query, 
                        request.num_results
                    )
                elif request.engine == 'Bing':
                    results = await asyncio.get_event_loop().run_in_executor(
                        None,
                        get_bing_search_results,
                        query,
                        request.num_results
                    )
                elif request.engine == '百度':
                    results = await asyncio.get_event_loop().run_in_executor(
                        None,
                        get_baidu_search_results,
                        query,
                        request.num_results
                    )
                else:
                    raise HTTPException(status_code=400, detail="Unsupported search engine")
                
                all_results.extend(results)
            return all_results

        # 使用asyncio.wait_for来设置超时
        results = await asyncio.wait_for(search_with_timeout(), timeout=timeout)

        return {
            "status": "success",
            "query": request.queries,
            "engine": request.engine,
            "custom_question": request.custom_question,
            "results": results
        }
    except asyncio.TimeoutError:
        logging.error("Search timeout")
        raise HTTPException(status_code=504, detail="Search timeout")
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)