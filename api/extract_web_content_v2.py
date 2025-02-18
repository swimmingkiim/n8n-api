import os
# Vercel과 같이 /home이 읽기 전용인 환경에서는 /tmp 내에 저장하도록 설정합니다.
pyppeteer_home = "/tmp/pyppeteer"
if not os.path.exists(pyppeteer_home):
    os.makedirs(pyppeteer_home)
os.environ["PYPPETEER_HOME"] = pyppeteer_home

from urllib.parse import urlparse, parse_qs
import json
import requests
import trafilatura
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
            error_msg = {"error": "Invalid or missing 'url' parameter in the input."}
            self.wfile.write(json.dumps(error_msg, ensure_ascii=False).encode('utf-8'))
            return

        try:
            dynamic_content = fetch_dynamic_content(extracted_url)
            if isinstance(dynamic_content, dict) and "error" in dynamic_content:
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(dynamic_content, ensure_ascii=False).encode('utf-8'))
                return

            # Trafilatura를 사용하여 본문 및 메타데이터 추출 (JSON 형식)
            result_str = trafilatura.extract(dynamic_content, output_format='json', with_metadata=True)
            if result_str is None:
                title = "No title"
                content_text = "No content"
            else:
                result = json.loads(result_str)
                title = result.get('title', "No title")
                content_text = result.get('text', "No content")

            data = {
                'link': extracted_url,
                'title': title,
                'content': content_text
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
