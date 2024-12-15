# search_engines.py
import logging
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from utils import get_page_content
import charset_normalizer
import re

def process_search_query(query):
    """
    处理搜索查询，识别并应用高级搜索技巧。
    """
    # 提取精确匹配的短语（使用双引号）
    exact_phrases = re.findall(r'"([^"]+)"', query)
    
    # 提取排除关键词（使用减号）
    exclude_terms = re.findall(r'-(\w+)', query)
    
    # 提取站内搜索（site:）
    site_search = re.findall(r'site:(\S+)', query)
    
    # 提取文件类型搜索（filetype:）
    filetype = re.findall(r'filetype:(\w+)', query)
    
    # 提取数值范围搜索（使用..）
    ranges = re.findall(r'(\d+)\.\.(\d+)', query)
    
    # 提取定义查询（define:）
    define_terms = re.findall(r'define:(\w+)', query)
    
    # 提取相关搜索（related:）
    related_sites = re.findall(r'related:(\S+)', query)
    
    # 提取标题搜索（intitle:）
    title_terms = re.findall(r'intitle:(\S+)', query)
    
    # 提取URL搜索（inurl:）
    url_terms = re.findall(r'inurl:(\S+)', query)
    
    # 提取时间限制
    time_limits = re.findall(r'time:(last\d+\w+)', query)
    
    return {
        'exact_phrases': exact_phrases,
        'exclude_terms': exclude_terms,
        'site_search': site_search,
        'filetype': filetype,
        'ranges': ranges,
        'define_terms': define_terms,
        'related_sites': related_sites,
        'title_terms': title_terms,
        'url_terms': url_terms,
        'time_limits': time_limits
    }

def build_advanced_query(query, engine='Google'):
    """
    根据搜索引擎构建高级搜索查询。
    """
    search_params = process_search_query(query)
    advanced_query = query

    if engine == 'Google':
        # 添加精确匹配
        for phrase in search_params['exact_phrases']:
            advanced_query = advanced_query.replace(f'"{phrase}"', f'"{phrase}"')
        
        # 添加排除词
        for term in search_params['exclude_terms']:
            advanced_query = advanced_query.replace(f'-{term}', f'-{term}')
        
        # 添加站内搜索
        if search_params['site_search']:
            advanced_query += f" site:{search_params['site_search'][0]}"
        
        # 添加文件类型
        if search_params['filetype']:
            advanced_query += f" filetype:{search_params['filetype'][0]}"
            
    elif engine == 'Bing':
        # Bing特定的查询构建逻辑
        for phrase in search_params['exact_phrases']:
            advanced_query = advanced_query.replace(f'"{phrase}"', f'"{phrase}"')
            
        if search_params['time_limits']:
            advanced_query += f" time:{search_params['time_limits'][0]}"
            
    elif engine == '百度':
        # 百度特定的查询构建逻辑
        for phrase in search_params['exact_phrases']:
            advanced_query = advanced_query.replace(f'"{phrase}"', f'"{phrase}"')
            
        if search_params['site_search']:
            advanced_query += f" site:{search_params['site_search'][0]}"

    return advanced_query

def get_google_search_results(query, num_results=5):
    """
    获取Google搜索结果，支持高级搜索语法。
    """
    # 处理高级搜索查询
    advanced_query = build_advanced_query(query, 'Google')
    query_encoded = urllib.parse.quote_plus(advanced_query)
    
    # 如果是天气查询,优先搜索360天气网
    if "天气" in query:
        query_encoded = urllib.parse.quote_plus(f"site:tianqi.so.com {query}")
    
    url = f"https://www.google.com/search?q={query_encoded}&num={num_results}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    logging.info(f"发送请求到Google URL: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        detected = charset_normalizer.from_bytes(response.content).best()
        encoding = detected.encoding if detected and detected.encoding else 'utf-8'
        text = response.content.decode(encoding, errors='replace')
    except Exception as e:
        logging.error(f"Google搜索请求失败: {e}")
        raise Exception(f"Google搜索请求失败: {e}")

    soup = BeautifulSoup(text, 'html.parser')
    results = []

    for g in soup.find_all('div', class_='tF2Cxc'):
        title_tag = g.find('h3')
        title = title_tag.get_text(separator=' ', strip=True) if title_tag else "No title"

        link_tag = g.find('a')
        link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else "No link"

        snippet = ""
        possible_snippet_classes = ['VwiC3b', 'IsZvec', 'aCOpRe']
        for cls in possible_snippet_classes:
            snippet_tag = g.find('div', class_=cls)
            if snippet_tag:
                snippet = snippet_tag.get_text(separator=' ', strip=True)
                break

        if not snippet:
            snippet_tag = g.find('span', class_='aCOpRe')
            if snippet_tag:
                snippet = snippet_tag.get_text(separator=' ', strip=True)
        if not snippet:
            snippet = "No content"

        results.append({
            'title': title,
            'link': link,
            'snippet': snippet,
            'content': "正在获取内容...",
            'engine': 'Google'
        })

        if len(results) >= num_results:
            break

    # 如果是天气查询,只返回360天气网的结果
    if "天气" in query:
        results = [r for r in results if 'tianqi.so.com' in r['link']]
        if results:
            results = [results[0]]  # 只保留第一个结果

    # 并行获取页面内容
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_result = {
            executor.submit(get_page_content, result['link']): result 
            for result in results
        }

        for future in as_completed(future_to_result):
            result = future_to_result[future]
            try:
                content = future.result()
                result['content'] = content
            except Exception as e:
                logging.error(f"获取页面内容失败 ({result['link']}): {e}")
                result['content'] = "无法获取内容"

    return results

def get_bing_search_results(query, num_results=5):
    """
    获取Bing搜索结果，支持高级搜索语法。
    """
    # 处理高级搜索查询
    advanced_query = build_advanced_query(query, 'Bing')
    query_encoded = urllib.parse.quote_plus(advanced_query)
    
    url = f"https://www.bing.com/search?q={query_encoded}&count={num_results}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    logging.info(f"发送请求到Bing URL: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        detected = charset_normalizer.from_bytes(response.content).best()
        encoding = detected.encoding if detected and detected.encoding else 'utf-8'
        text = response.content.decode(encoding, errors='replace')
    except Exception as e:
        logging.error(f"Bing搜索请求失败: {e}")
        raise Exception(f"Bing搜索请求失败: {e}")

    soup = BeautifulSoup(text, 'html.parser')
    results = []

    for li in soup.find_all('li', class_='b_algo'):
        h2 = li.find('h2')
        if h2 and h2.find('a'):
            a_tag = h2.find('a')
            title = a_tag.get_text(separator=' ', strip=True)
            link = a_tag['href']
        else:
            continue

        snippet_tag = li.find('p')
        snippet = snippet_tag.get_text(separator=' ', strip=True) if snippet_tag else "No content"

        results.append({
            'title': title,
            'link': link,
            'snippet': snippet,
            'content': "正在获取内容...",
            'engine': 'Bing'
        })

        if len(results) >= num_results:
            break

    # 并行获取页面内容
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_result = {
            executor.submit(get_page_content, result['link']): result 
            for result in results
        }

        for future in as_completed(future_to_result):
            result = future_to_result[future]
            try:
                content = future.result()
                result['content'] = content
            except Exception as e:
                logging.error(f"获取页面内容失败 ({result['link']}): {e}")
                result['content'] = "无法获取内容"

    return results

def get_baidu_search_results(query, num_results=5):
    """
    获取百度搜索结果，支持高级搜索语法。
    """
    # 处理高级搜索查询
    advanced_query = build_advanced_query(query, '百度')
    query_encoded = urllib.parse.quote_plus(advanced_query)
    
    url = f"https://www.baidu.com/s?wd={query_encoded}&rn={num_results}&ie=utf-8"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    logging.info(f"发送请求到百度 URL: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        detected = charset_normalizer.from_bytes(response.content).best()
        encoding = detected.encoding if detected and detected.encoding else 'utf-8'
        text = response.content.decode(encoding, errors='replace')
    except Exception as e:
        logging.error(f"百度搜索请求失败: {e}")
        raise Exception(f"百度搜索请求失败: {e}")

    soup = BeautifulSoup(text, 'html.parser')
    results = []

    for div in soup.find_all('div', class_='result'):
        h3 = div.find('h3')
        if h3 and h3.find('a'):
            a_tag = h3.find('a')
            title = a_tag.get_text(separator=' ', strip=True)
            link = a_tag['href']
        else:
            continue

        snippet_tag = div.find('div', class_='c-abstract')
        if not snippet_tag:
            snippet_tag = div.find('div', class_='c-span18 c-span-last')
        snippet = snippet_tag.get_text(separator=' ', strip=True) if snippet_tag else "No content"

        results.append({
            'title': title,
            'link': link,
            'snippet': snippet,
            'content': "正在获取内容...",
            'engine': '百度'
        })

        if len(results) >= num_results:
            break

    # 并行获取页面内容
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_result = {
            executor.submit(get_page_content, result['link']): result 
            for result in results
        }

        for future in as_completed(future_to_result):
            result = future_to_result[future]
            try:
                content = future.result()
                result['content'] = content
            except Exception as e:
                logging.error(f"获取页面内容失败 ({result['link']}): {e}")
                result['content'] = "无法获取内容"

    return results
