"""异步网页爬虫 — 演示 asyncio + aiohttp 实现并发 HTTP 请求。

用法:
  python async_crawler.py

对比同步与异步获取的性能差异。
"""

import asyncio
import time

import aiohttp

# 待抓取的 URL 列表
URLS = [
    "https://www.deepseek.com/",
    "https://www.github.com",
    "https://www.zhihu.com",
    "https://www.bilibili.com",
]

REQUEST_TIMEOUT = 10  # 请求超时时间（秒）


async def fetch_url(session: aiohttp.ClientSession, url: str) -> tuple[str, int | None]:
    """抓取单个 URL，返回 (url, status_code)。"""
    try:
        async with session.head(url, timeout=REQUEST_TIMEOUT) as response:
            return url, response.status
    except Exception as e:
        print(f"  [{url}] 错误: {e}")
        return url, None


async def fetch_all(urls: list[str]) -> list[tuple[str, int | None]]:
    """并发抓取所有 URL。"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)


def main() -> None:
    """运行异步抓取，打印结果和耗时。"""
    print(f"正在并发抓取 {len(URLS)} 个 URL ...\n")
    start = time.perf_counter()
    results = asyncio.run(fetch_all(URLS))
    elapsed = time.perf_counter() - start

    for url, status in results:
        if status:
            print(f"  {url}  →  {status}")
        else:
            print(f"  {url}  →  失败")

    print(f"\n完成，耗时 {elapsed:.2f}s")


if __name__ == "__main__":
    main()
