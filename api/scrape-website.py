import asyncio
import json
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler

# crawlee의 PlaywrightCrawler와 관련 타입을 임포트합니다.
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

async def crawl_page(url: str) -> dict:
    result = {}

    async def handler(context: PlaywrightCrawlingContext):
        context.log.info(f'Processing {context.request.url}')
        # 페이지 로드가 완료될 때까지 기다립니다.
        await context.page.wait_for_load_state("networkidle")
        # 페이지 제목과 body 내의 텍스트를 추출합니다.
        title = await context.page.title()
        content = await context.page.inner_text("body")
        result["link"] = context.request.url
        result["title"] = title if title else "No title"
        result["content"] = content if content else "No content"

    # 최대 요청 수를 1로 제한하여 단일 페이지 크롤링을 수행합니다.
    crawler = PlaywrightCrawler(max_requests_per_crawl=1)
    crawler.router.default_handler(handler)
    await crawler.run([url])
    return result

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 쿼리 스트링에서 'url' 파라미터를 추출합니다.
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        extracted_url = query_params.get("url", [None])[0]

        if not extracted_url or not extracted_url.startswith(('http://', 'https://')):
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_message = {"error": "Invalid or missing 'url' parameter in the input."}
            self.wfile.write(json.dumps(error_message).encode('utf-8'))
            return

        try:
            # 비동기 크롤링 함수를 실행하여 결과를 받아옵니다.
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
