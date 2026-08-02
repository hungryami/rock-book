import http.server
import socketserver
import webbrowser
import threading


PORT = 8000


class MyHandler(http.server.SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        # 关闭刷屏日志
        pass



def start_server():

    with socketserver.TCPServer(
        ("", PORT),
        MyHandler
    ) as httpd:

        print(f"""
==============================
 洛克王国图鉴启动成功

 地址:
 http://localhost:{PORT}/rock_book/

 Ctrl+C 关闭
==============================
        """)

        httpd.serve_forever()



if __name__ == "__main__":

    # 自动打开浏览器
    url = f"http://localhost:{PORT}/rock_book/index.html"

    threading.Timer(
        1,
        lambda:webbrowser.open(url)
    ).start()


    start_server()