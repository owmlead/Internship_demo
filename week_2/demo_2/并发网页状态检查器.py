import requests
import threading

urls = [
    'https://www.deepseek.com/',
    'https://www.github.com',
    'https://www.zhihu.com',
    'https://www.bilibili.com'
]


class HttpTest:
    def __init__(self, url_list):
        self.url_list = url_list
    @staticmethod
    def url_status( url):
        r = requests.head(url)
        print(f"{url}  的状态码:{r.status_code}")

    def start(self):
        for url in self.url_list:
            t = threading.Thread(target=self.url_status, args=(url,))
            t.start()


if __name__ == '__main__':
    x = HttpTest(urls)
    x.start()
