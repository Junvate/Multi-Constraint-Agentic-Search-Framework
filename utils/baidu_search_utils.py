"""
百度AI搜索工具类
基于百度千帆平台的Web搜索API
"""
import requests
import json
from typing import List, Dict, Optional


class BaiduSearchClient:
    """百度AI搜索客户端"""
    
    def __init__(self, api_key: str):
        """
        初始化百度搜索客户端
        
        Args:
            api_key: AppBuilder API Key
        """
        self.api_key = api_key
        self.base_url = "https://qianfan.baidubce.com"
        self.search_endpoint = "/v2/ai_search/web_search"
        
    def web_search(
        self,
        query: str,
        top_k: int = 10,
        edition: str = "standard",
        search_recency_filter: Optional[str] = None,
        site_filter: Optional[List[str]] = None,
        block_websites: Optional[List[str]] = None
    ) -> Dict:
        """
        执行百度Web搜索
        
        Args:
            query: 搜索查询词
            top_k: 返回结果数量，最大50
            edition: 搜索版本，可选 "standard"(完整版) 或 "lite"(标准版，时延更好)
            search_recency_filter: 时效性过滤，可选 "week", "month", "semiyear", "year"
            site_filter: 指定站点列表，仅在这些站点中搜索
            block_websites: 需要屏蔽的站点列表
            
        Returns:
            搜索结果字典，包含 references 列表
        """
        url = f"{self.base_url}{self.search_endpoint}"
        
        headers = {
            "X-Appbuilder-Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体
        payload = {
            "messages": [
                {
                    "content": query,
                    "role": "user"
                }
            ],
            "edition": edition,
            "search_source": "baidu_search_v2",
            "resource_type_filter": [
                {"type": "web", "top_k": min(top_k, 50)}
            ]
        }
        
        # 添加可选参数
        if search_recency_filter:
            payload["search_recency_filter"] = search_recency_filter
            
        if site_filter:
            payload["search_filter"] = {
                "match": {
                    "site": site_filter
                }
            }
            
        if block_websites:
            payload["block_websites"] = block_websites
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"搜索请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"错误详情: {json.dumps(error_detail, ensure_ascii=False, indent=2)}")
                except:
                    print(f"响应内容: {e.response.text}")
            return {"references": [], "error": str(e)}
    
    def format_search_results(
        self, 
        search_result: Dict, 
        max_results: int = 3,
        include_url: bool = True
    ) -> str:
        """
        格式化搜索结果为文本
        
        Args:
            search_result: 搜索结果字典
            max_results: 最多使用的结果数量
            include_url: 是否包含URL
            
        Returns:
            格式化后的文本字符串
        """
        if "references" not in search_result or not search_result["references"]:
            return "无相关搜索结果"
        
        references = search_result["references"][:max_results]
        formatted_parts = []
        
        for i, ref in enumerate(references, 1):
            title = ref.get("title", "无标题")
            content = ref.get("content", "无内容")
            url = ref.get("url", "")
            date = ref.get("date", "")
            
            # 清理内容中的特殊字符
            content = content.replace("\u0004", "").replace("\u0005", "")
            
            part = f"[结果 {i}] {title}"
            if date:
                part += f" ({date})"
            part += f"\n{content}"
            if include_url and url:
                part += f"\n来源: {url}"
            
            formatted_parts.append(part)
        
        return "\n\n".join(formatted_parts)
    
    def get_top_results(self, search_result: Dict, top_n: int = 3) -> List[Dict]:
        """
        获取前N个搜索结果
        
        Args:
            search_result: 搜索结果字典
            top_n: 返回结果数量
            
        Returns:
            结果列表
        """
        if "references" not in search_result:
            return []
        
        return search_result["references"][:top_n]


# 使用示例
if __name__ == "__main__":
    # 测试代码
    API_KEY = "your-appbuilder-api-key"  # 替换为你的API Key
    
    client = BaiduSearchClient(api_key=API_KEY)
    
    # 执行搜索
    result = client.web_search(
        query="百度千帆平台",
        top_k=5,
        edition="standard"
    )
    
    # 打印原始结果
    print("原始结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 格式化输出
    print("\n格式化结果:")
    formatted = client.format_search_results(result, max_results=3)
    print(formatted)

