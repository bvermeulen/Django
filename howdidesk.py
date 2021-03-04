import os
import time
import webview
from threading import Thread

def start_webview():
    window = webview.create_window(
        'Howdimain', url='http://127.0.0.1:8000', confirm_close=True, width=900, height=600)
    webview.start()
    window.closed = os._exit(0)

def start_django():
    local_host = '127.0.0.1'
    port =  '8000'
    os.system(f'python manage.py runserver {local_host}:{port}')
    time.sleep(5)

if __name__ == '__main__':
    Thread(target=start_django).start()
    start_webview()
