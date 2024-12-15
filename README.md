# OnlineGPT Search API

这是一个强大的搜索API服务，支持从多个搜索引擎获取信息。它是从OnlineGPT桌面应用改造而来的Web API服务，专门设计用于与GPT等大型语言模型集成。

## 功能特点

- 支持多个搜索引擎 (Google、Bing、百度)
- 自动提取网页内容
- RESTful API接口
- 支持自定义搜索数量
- 支持批量关键词搜索
- 异步处理请求
- 自动编码检测和处理

## API文档

### 搜索接口

**POST** `/search`

请求体:
```json
{
    "queries": ["搜索关键词1", "搜索关键词2"],
    "num_results": 5,
    "engine": "Google",
    "custom_question": "可选的自定义问题"
}
```

参数说明:
- `queries`: 搜索关键词列表
- `num_results`: 每个关键词返回的结果数量 (默认5)
- `engine`: 搜索引擎选择 ("Google", "Bing", "百度")
- `custom_question`: 可选的自定义问题

响应示例:
```json
{
    "status": "success",
    "query": ["搜索关键词1", "搜索关键词2"],
    "engine": "Google",
    "custom_question": "自定义问题",
    "results": [
        {
            "title": "页面标题",
            "link": "页面URL",
            "snippet": "搜索结果摘要",
            "content": "页面内容"
        }
    ]
}
```

## 部署说明

### Vercel部署

1. Fork本仓库
2. 在Vercel中导入项目
3. 部署完成后即可使用

### 本地开发

1. 克隆仓库:
```bash
git clone https://github.com/yourusername/onlinegpt-api.git
cd onlinegpt-api
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 运行服务:
```bash
uvicorn main:app --reload
```

4. 访问API文档:
```
http://localhost:8000/docs
```

## 使用示例

### Python
```python
import requests

api_url = "https://your-api-url.vercel.app/search"
data = {
    "queries": ["Python programming", "AI development"],
    "num_results": 5,
    "engine": "Google"
}

response = requests.post(api_url, json=data)
results = response.json()
```

### curl
```bash
curl -X POST "https://your-api-url.vercel.app/search" \
     -H "Content-Type: application/json" \
     -d '{"queries":["Python programming"],"num_results":5,"engine":"Google"}'
```

## 注意事项

1. 请遵守搜索引擎的使用条款
2. 建议添加适当的请求限制
3. 在生产环境中请设置适当的CORS策略
4. 建议添加缓存机制以提高性能
5. 注意处理并发请求

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---
