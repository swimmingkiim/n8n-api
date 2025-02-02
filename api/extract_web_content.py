from urllib.parse import urlparse, parse_qs
import json
import requests
from goose3 import Goose

from http.server import BaseHTTPRequestHandler

def fetch_dynamic_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid or missing 'url' parameter in the input."}).encode('utf-8'))
            return

        try:
            dynamic_content = fetch_dynamic_content(extracted_url)

            if isinstance(dynamic_content, dict) and "error" in dynamic_content:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(dynamic_content).encode('utf-8'))
                return

            g = Goose()
            article = g.extract(raw_html=dynamic_content)
            title = article.title
            content_text = article.cleaned_text

            data = {
                'link': extracted_url,
                'title': title if title else "No title",
                'content': content_text if content_text else "No content"
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))