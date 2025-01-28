from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('example url: https://n8n-api-delta.vercel.app/api/extract_web_content?url=https://www.fxstreet.com/cryptocurrencies/news/why-chinas-deepseek-is-causing-bitcoin-and-crypto-market-to-plunge-202501272010'.encode('utf-8'))
        return