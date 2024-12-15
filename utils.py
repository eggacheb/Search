# utils.py
import re
import logging
import requests
from bs4 import BeautifulSoup
import charset_normalizer

def clean_text(text):
    """
    清洗文本，移除控制字符和非打印字符。
    """
    # 移除控制字符
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    # 规范化空白字符
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def remove_duplicates(text_list, min_length=10):
    """
    移除文本列表中的重复内容和过短的内容。
    """
    seen = set()
    result = []
    for text in text_list:
        # 跳过过短的内容
        if len(text) < min_length:
            continue
        # 跳过重复内容
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result

def get_page_content(url, max_length=1000):
    """
    获取指定URL页面的所有文本内容，处理编码并过滤非HTML内容。
    限制返回内容的最大长度。
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

        # 检测编码
        detected = charset_normalizer.from_bytes(response.content).best()
        encoding = detected.encoding if detected and detected.encoding else 'utf-8'
        text = response.content.decode(encoding, errors='replace')

        soup = BeautifulSoup(text, 'html.parser')

        # 移除不需要的标签
        for tag in soup(['script', 'style', 'meta', 'link', 'noscript', 'header', 'footer', 'nav']):
            tag.decompose()

        # 提取主要内容
        article = soup.find('article')
        if article:
            content = extract_content_from_element(article, max_length)
        else:
            content = extract_content_from_element(soup.body if soup.body else soup, max_length)

        # 如果提取的内容太短，尝试其他方法
        if len(content) < 100:
            content = extract_content_from_element(soup, max_length)

        return clean_text(content)

    except Exception as e:
        logging.error(f"获取页面内容失败 ({url}): {e}")
        return "无法获取内容"

def extract_content_from_element(element, max_length=1000):
    """
    从HTML元素中提取文本内容，
    去除重复内容并限制最大长度。
    针对不同类型的网站采用不同的提取策略。
    """
    # 检查是否是360天气网
    element_str = str(element)
    if 'tianqi.so.com' in element_str:
        # 针对360天气网的特殊处理
        weather_info = []
        
        # 提取天气预报信息
        # 首先尝试获取7天天气预报
        days = element.select('.weather-list .item')
        if not days:
            # 如果没有找到,尝试其他可能的选择器
            days = element.select('.days-item')
            
        for day in days:
            try:
                # 尝试不同的选择器组合来获取信息
                date = day.select_one('.date') or day.select_one('.day')
                weather = day.select_one('.weather') or day.select_one('.wea')
                temp = day.select_one('.temp') or day.select_one('.temperature')
                wind = day.select_one('.wind') or day.select_one('.wind-direction')
                
                if date and weather and temp:
                    date_text = date.get_text().strip()
                    weather_text = weather.get_text().strip()
                    temp_text = temp.get_text().strip()
                    wind_text = wind.get_text().strip() if wind else "无风向"
                    
                    # 格式化信息
                    info = f"{date_text} {weather_text} 温度:{temp_text} 风力:{wind_text}"
                    weather_info.append(info)
            except Exception as e:
                logging.error(f"提取天气信息失败: {e}")
                continue
                
        if weather_info:
            # 只返回未来几天的天气预报
            return ' | '.join(weather_info[:7])
        
        # 如果上述方法都失败,尝试直接提取snippet中的信息
        snippet = element.get_text(separator=' ', strip=True)
        if '明天' in snippet and '℃' in snippet:
            return snippet

    # 如果不是天气网站或无法提取到天气信息,使用默认的提取方法
    content_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'section']
    contents = []
    for tag in element.find_all(content_tags):
        text = tag.get_text(separator=' ', strip=True)
        if text and not text.isspace():
            contents.append(text)
    
    contents = remove_duplicates(contents)
    text = ' '.join(contents)
    if len(text) > max_length:
        text = text[:max_length] + '...'
    
    return text