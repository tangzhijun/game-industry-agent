import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json
from datetime import datetime

# 加载环境变量
load_dotenv()
API_KEY = os.getenv("DASHSCOPE_API_KEY")
NEWS_URLS = os.getenv("NEWS_URLS").split(",")

# 1. 爬虫：抓取网页正文
def crawl(url):
    try:
        res=requests.get(url, timeout=10)
        res.raise_for_status()
        soup=BeautifulSoup(res.text, "html.parser")
        # 通用正文提取（可按网站微调）
        text = "\n".join([p.text for p in soup.find_all("p")])
        return text[:3000]  # 限制长度避免超限
    except Exception as e:
        print(f"爬取失败 {url}: {e}")
        return ""

# 2. 调用通义千问做摘要
def summarize(text):
    if not text:
        return "无内容"
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data={
        "model": "qwen-turbo",
        "input": {"messages": [{"role": "user", "content": f"请用3句话总结以下游戏行业新闻，提炼关键信息：\n{text}"}]},
        "parameters": {"result_format": "text"}
    }
    try:
        res=requests.post(url, headers=headers, json=data)
        return res.json()["output"]["text"]
    except Exception as e:
        print(f"摘要失败: {e}")
        return "摘要生成失败"

# 3. 主流程：爬→总结→保存
def run():
    results = []
    for url in NEWS_URLS:
        print(f"正在爬取: {url}")
        text=crawl(url)
        summary=summarize(text)
        results.append({"url": url, "summary": summary, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
    
    # 保存到markdown（可直接在GitHub查看）
    md = f"# 游戏行业日报 {datetime.now().strftime('%Y-%m-%d')}\n\n"
    for item in results:
        md += f"## [{item['url']}]({item['url']})\n{item['summary']}\n\n"
    
    with open("daily_report.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("✅ 日报生成完成：daily_report.md")

if __name__ == "__main__":
    run()
