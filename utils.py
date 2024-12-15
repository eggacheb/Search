# utils.py
import re
import logging
import requests
from bs4 import BeautifulSoup
import charset_normalizer

def clean_text(text):
    """
    清洗文本，保留有意义的格式。
    """
    if not text:
        return ""
        
    # 移除控制字符
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    
    # 统一空白字符
    text = re.sub(r'\s+', ' ', text)
    
    # 清理多余的换行
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # 清理HTML实体
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    
    # 清理特殊Unicode字符
    text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u205f-\u206f]', '', text)
    
    return text.strip()

def get_page_content(url):
    """
    获取指定URL页面的核心内容，处理编码并保留重要的文本格式。
    智能提取主要内容区域，过滤无关内容。
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 检查内容类型
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
            return "非HTML内容，无法提取"

        # 检测编码
        detected = charset_normalizer.from_bytes(response.content).best()
        encoding = detected.encoding if detected and detected.encoding else 'utf-8'
        text = response.content.decode(encoding, errors='replace')

        # 使用Beautiful Soup解析HTML
        soup = BeautifulSoup(text, 'html.parser')

        # 移除干扰元素
        noise_tags = [
            'script', 'style', 'meta', 'link', 'noscript', 'iframe',
            'header', 'footer', 'nav', 'aside', 'form', 'button',
            '[class*="menu"]', '[class*="sidebar"]', '[class*="banner"]',
            '[class*="advertisement"]', '[class*="copyright"]', '[class*="social"]'
        ]
        for tag in soup.select(','.join(noise_tags)):
            tag.decompose()

        # 提取主要内容
        content_parts = []
        
        # 1. 尝试找到主要内容区域
        main_selectors = [
            'article', 'main', '[role="main"]', '.main-content', '#content', '#main',
            '.article', '.post', '.entry', '.blog-post', '.content-main'
        ]
        
        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            main_content = soup.body if soup.body else soup

        # 2. 提取标题
        title = None
        title_tags = main_content.find_all(['h1', 'h2'], limit=2)
        for tag in title_tags:
            if len(tag.get_text(strip=True)) > 10:
                title = tag.get_text(strip=True)
                break

        if title:
            content_parts.append(title)

        # 3. 提取正文内容
        content_tags = main_content.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
        
        for tag in content_tags:
            text = tag.get_text(strip=True)
            # 过滤无效内容
            if not text or len(text) < 20:
                continue
            if any(x in text.lower() for x in ['copyright', '版权所有', '关注我们', '扫描二维码']):
                continue
            if re.match(r'^[【\[\(（].*[】\]\)）]$', text):  # 跳过纯标签文本
                continue
                
            # 处理标题标签
            if tag.name.startswith('h'):
                content_parts.append(f"\n{text}\n")
            # 处理列表项
            elif tag.name == 'li':
                content_parts.append(f"- {text}")
            # 处理普通段落
            else:
                content_parts.append(text)

        # 4. 如果提取的内容太少，尝试其他方法
        if len('\n'.join(content_parts)) < 200:
            # 寻找长文本块
            for tag in main_content.find_all(['div', 'section']):
                text = tag.get_text(strip=True)
                if len(text) > 200 and not any(x in text.lower() for x in ['copyright', '版权所有']):
                    content_parts.append(text)
                    break

        # 5. 组合并清理最终内容
        final_text = '\n\n'.join(content_parts)
        final_text = clean_text(final_text)
        
        # 6. 内容有效性检查
        if not final_text or len(final_text) < 100:
            return "无法提取有效内容"
            
        return final_text

    except requests.exceptions.RequestException as e:
        logging.error(f"网页请求失败 ({url}): {e}")
        return "网页请求失败"
    except Exception as e:
        logging.error(f"内容提取失败 ({url}): {e}")
        return "内容提取失败"
