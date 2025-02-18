from urllib.parse import urlparse, parse_qs
import json
import requests
import trafilatura
from bs4 import BeautifulSoup

from http.server import BaseHTTPRequestHandler

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

            # Trafilatura로 메타데이터 포함 추출 (JSON 형식으로 반환)
            result_str = trafilatura.extract(dynamic_content, output_format='json', with_metadata=True)

            if result_str is None:
                title = "No title"
                content_text = "No content"
            else:
                result = json.loads(result_str)
                title = result.get('title', "No title")
                content_text = result.get('text', "No content")

            # BeautifulSoup를 사용해 댓글 추출 (div.cmt_list 내부의 div.cmt_item)
            soup = BeautifulSoup(dynamic_content, 'html.parser')
            comment_container = soup.find('div', class_='cmt_list')
            if comment_container:
                comment_items = comment_container.find_all('div', class_='cmt_item')
                comments = [item.get_text(strip=True) for item in comment_items]
            else:
                comments = []

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
