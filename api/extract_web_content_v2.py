from urllib.parse import urlparse, parse_qs
import json
import requests
import trafilatura
from requests_html import HTMLSession
from http.server import BaseHTTPRequestHandler
import nest_asyncio

# 현재 스레드에 이벤트 루프 적용
nest_asyncio.apply()

def fetch_dynamic_content(url):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return {"error": str(e)}

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        extracted_url = query_params.get("url", [None])[0]

        if not extracted_url or not extracted_url.startswith(('http://', 'https://')):
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Invalid or missing 'url' parameter in the input."
            }, ensure_ascii=False).encode('utf-8'))
            return

        try:
            dynamic_content = fetch_dynamic_content(extracted_url)
            if isinstance(dynamic_content, dict) and "error" in dynamic_content:
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(dynamic_content, ensure_ascii=False).encode('utf-8'))
                return

            # Trafilatura로 본문 및 메타데이터 추출 (JSON 형식)
            result_str = trafilatura.extract(dynamic_content, output_format='json', with_metadata=True)
            if result_str is None:
                title = "No title"
                content_text = "No content"
            else:
                result = json.loads(result_str)
                title = result.get('title', "No title")
                content_text = result.get('text', "No content")

            # requests_html를 사용해 동적 페이지 렌더링 및 댓글 추출 (CSS 셀렉터 사용)
            session = HTMLSession()
            r = session.get(extracted_url)
            # render 시, "--user-data-dir=/tmp" 옵션을 전달하여 쓰기 가능한 경로를 지정
            r.html.render(timeout=20, args=['--user-data-dir=/tmp'])
            # "div.cmt_list" 내부의 "div.cmt_item" 요소를 CSS 셀렉터로 찾음
            comment_elements = r.html.find("div.cmt_list div.cmt_item")
            comments = [elem.text for elem in comment_elements]

            data = {
                'link': extracted_url,
                'title': title,
                'content': content_text,
                'comments': comments
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8'))
