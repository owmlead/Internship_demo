"""并发URL状态检查器 — 多线程并发检查多个URL的HTTP状态码。

使用 threading 并发发送 HEAD 请求。
"""

import threading

import requests

# 待检查的 URL 列表
URLS = [
    "https://www.deepseek.com/",
    "https://www.github.com",
    "https://www.zhihu.com",
    "https://www.bilibili.com",
]

REQUEST_TIMEOUT = 10  # 请求超时时间（秒）


class HttpChecker:
    """并发检查多个 URL 的 HTTP 状态码。"""

    def __init__(self, url_list: list[str]):
        self.url_list = url_list
        self._threads: list[threading.Thread] = []

    @staticmethod
    def url_status(url: str) -> None:
        """获取并打印 *url* 的 HTTP 状态码。"""
        try:
            r = requests.head(url, timeout=REQUEST_TIMEOUT)
            print(f"{url}  状态码: {r.status_code}")
        except requests.RequestException as e:
            print(f"{url}  错误: {e}")

    def start(self) -> None:
        """为每个 URL 启动一个线程，然后等待全部完成。"""
        self._threads = []
        for url in self.url_list:
            t = threading.Thread(target=self.url_status, args=(url,))
            t.start()
            self._threads.append(t)

        for t in self._threads:
            t.join()


if __name__ == "__main__":
    checker = HttpChecker(URLS)
    checker.start()
