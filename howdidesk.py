import os
import webview

def start_webview():
    window = webview.create_window(
        'Howdimain', url='https://www.howdiweb.nl', confirm_close=True, width=1000, height=600)
    webview.start()
    window.closed = os._exit(0)

if __name__ == '__main__':
    start_webview()
