import os
import subprocess
import asyncio
import json
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

def install_browser():
    """
    필요한 브라우저(예: Chromium)를 설치합니다.
    이 명령은 콜드 스타트 시마다 실행되며, 이미 설치되어 있으면
    추가 시간이 크게 들지 않습니다.
    """
    try:
        # 필요한 브라우저만 설치합니다. (예: chromium)
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        print("Error installing browser:", e)

async def crawl_page(url: str) -> dict:
    result = {}

    async def handler(context: PlaywrightCrawlingContext):
        context.log.info(f'Processing {context.request.url}')
        await context.page.wait_for_load_state("networkidle")
        title = await context.page.title()
        content = await context.page.inner_text("body")
        result["link"] = context.request.url
        result["title"] = title if title else "No title"
        result["content"] = content if content else "No content"

    crawler = PlaywrightCrawler(max_requests_per_crawl=1)
    crawler.router.default_handler(handler)
    await crawler.run([url])
    return result

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 런타임 초기화 시 필요한 브라우저를 설치합니다.
        install_browser()

        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        extracted_url = query_params.get("url", [None])[0]

        if not extracted_url or not extracted_url.startswith(('http://', 'https://')):
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid or missing 'url' parameter in the input."}).encode('utf-8'))
            return

        try:
            result = asyncio.run(crawl_page(extracted_url))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
