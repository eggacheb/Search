# search_engines.py
import logging
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from utils import get_page_content
import charset_normalizer

def get_google_search_results(query, num_results=5):
    """
    获取Google搜索结果，优先返回360天气网的结果。
    """
    # 如果是天气查询,优先搜索360天气网
    if "天气" in query:
        query = f"site:tianqi.so.com {query}"
    
    query_encoded = urllib.parse.quote_plus(query)
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

    # 如果是气查询,只返回360天气网的结果
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
    获取Bing搜索结果，并爬取每个结果页面的内容。
    """
    query_encoded = urllib.parse.quote_plus(query)
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
    获取百度搜索结果，并爬取每个结果页面的内容。
    """
    query_encoded = urllib.parse.quote_plus(query)
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