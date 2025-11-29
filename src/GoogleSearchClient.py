# -*- coding: utf-8 -*-
"""
Google Search Client
基于 Google Custom Search API 的搜索客户端

使用方法:
    from GoogleSearchClient import GoogleSearchClient
    
    client = GoogleSearchClient(
        api_key="YOUR_API_KEY",
        cse_id="YOUR_CSE_ID",
        proxy="http://127.0.0.1:7890"  # 可选
    )
    
    result = client.web_search("Python 教程", top_k=10)
    for ref in result["references"]:
        print(ref["title"], ref["url"])
"""

import requests
from typing import Optional, Dict, List, Any


class GoogleSearchClient:
    """
    Google Custom Search API 客户端
    
    Attributes:
        api_key: Google API 密钥
        cse_id: 自定义搜索引擎 ID
        base_url: Google Custom Search API 端点
        proxies: 代理配置
    """
    
    def __init__(self, api_key: str, cse_id: str, proxy: Optional[str] = None):
        """
        初始化 Google 搜索客户端
        
        Args:
            api_key: Google API 密钥
            cse_id: 自定义搜索引擎 ID (Custom Search Engine ID)
            proxy: 代理 URL，例如 "http://127.0.0.1:7890"
        """
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        # 代理配置：防止 proxy 为空字符串时报错
        self.proxies = {
            "http": proxy,
            "https": proxy
        } if proxy and proxy.strip() else None

    def web_search(
        self, 
        query: str, 
        top_k: int = 10,
        language: Optional[str] = None,
        safe: str = "off",
        timeout: int = 15,
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        执行 Google 搜索并返回适配后的数据结构
        
        Args:
            query: 搜索关键词
            top_k: 返回结果数量，最大为 10（Google API 限制）
            language: 搜索语言，例如 "zh-CN", "en"
            safe: 安全搜索级别，"off", "medium", "high"
            timeout: 请求超时时间（秒）
            **kwargs: 其他传递给 API 的参数
            
        Returns:
            包含 "references" 键的字典，每个 reference 包含:
            - url: 链接地址
            - title: 标题
            - content: 内容摘要
            
        Example:
            >>> client = GoogleSearchClient(api_key, cse_id)
            >>> result = client.web_search("Python 教程", top_k=5)
            >>> for ref in result["references"]:
            ...     print(ref["title"])
        """
        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': query,
            'num': min(top_k, 10),  # Google API 最大一次返回 10 条
            'safe': safe
        }
        
        # 添加语言参数
        if language:
            params['lr'] = f'lang_{language}'
        
        # 合并额外参数
        params.update(kwargs)
        
        try:
            response = requests.get(
                self.base_url, 
                params=params, 
                proxies=self.proxies,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            
            references = []
            if "items" in data:
                for item in data["items"]:
                    # 拼接 snippet 和 metatags 增强内容
                    content = item.get("snippet", "")
                    try:
                        pagemap = item.get("pagemap", {})
                        metatags = pagemap.get("metatags", [{}])[0]
                        desc = metatags.get("og:description") or metatags.get("description")
                        if desc and isinstance(desc, str) and desc not in content:
                            content += " " + desc
                    except:
                        pass

                    references.append({
                        "url": item.get("link"),
                        "title": item.get("title"),
                        "content": content
                    })
            
            return {"references": references}
            
        except requests.exceptions.Timeout:
            print(f"Google API Timeout: 请求超时 ({timeout}s)")
            return {"references": []}
        except requests.exceptions.RequestException as e:
            print(f"Google API Request Error: {e}")
            return {"references": []}
        except Exception as e:
            print(f"Google API Error: {e}")
            return {"references": []}
    
    def search_with_pagination(
        self,
        query: str,
        total_results: int = 20,
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        支持分页的搜索，可获取超过 10 条结果
        
        Args:
            query: 搜索关键词
            total_results: 期望获取的总结果数
            **kwargs: 传递给 web_search 的其他参数
            
        Returns:
            包含 "references" 键的字典
            
        Note:
            Google API 每次最多返回 10 条，此方法会自动分页获取
        """
        all_references = []
        start_index = 1
        
        while len(all_references) < total_results:
            remaining = total_results - len(all_references)
            num = min(remaining, 10)
            
            params = {
                'key': self.api_key,
                'cx': self.cse_id,
                'q': query,
                'num': num,
                'start': start_index,
                'safe': kwargs.get('safe', 'off')
            }
            
            if 'language' in kwargs:
                params['lr'] = f'lang_{kwargs["language"]}'
            
            try:
                response = requests.get(
                    self.base_url,
                    params=params,
                    proxies=self.proxies,
                    timeout=kwargs.get('timeout', 15)
                )
                response.raise_for_status()
                data = response.json()
                
                if "items" not in data:
                    break
                    
                for item in data["items"]:
                    content = item.get("snippet", "")
                    try:
                        pagemap = item.get("pagemap", {})
                        metatags = pagemap.get("metatags", [{}])[0]
                        desc = metatags.get("og:description") or metatags.get("description")
                        if desc and isinstance(desc, str) and desc not in content:
                            content += " " + desc
                    except:
                        pass
                    
                    all_references.append({
                        "url": item.get("link"),
                        "title": item.get("title"),
                        "content": content
                    })
                
                # 检查是否还有更多结果
                next_page = data.get("queries", {}).get("nextPage")
                if not next_page:
                    break
                    
                start_index += num
                
            except Exception as e:
                print(f"Google API Pagination Error: {e}")
                break
        
        return {"references": all_references}


# ================= 使用示例 =================
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 从环境变量获取配置，或直接填入
    API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_API_KEY")
    CSE_ID = os.getenv("GOOGLE_CSE_ID", "YOUR_CSE_ID")
    PROXY = os.getenv("HTTP_PROXY")  # 可选
    
    # 创建客户端
    client = GoogleSearchClient(
        api_key=API_KEY,
        cse_id=CSE_ID,
        proxy=PROXY
    )
    
    # 基本搜索
    print("=== 基本搜索测试 ===")
    result = client.web_search("Python 教程", top_k=5)
    
    if result["references"]:
        for i, ref in enumerate(result["references"], 1):
            print(f"\n{i}. {ref['title']}")
            print(f"   URL: {ref['url']}")
            print(f"   摘要: {ref['content'][:100]}...")
    else:
        print("未找到搜索结果")
    
    # 分页搜索（获取更多结果）
    print("\n\n=== 分页搜索测试 ===")
    result_paginated = client.search_with_pagination("机器学习", total_results=15)
    print(f"获取到 {len(result_paginated['references'])} 条结果")

