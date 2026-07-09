import asyncio
import csv
import os

import aiohttp
from lxml import html
import random


# 设置代理信息
proxyHost = "www.16yun.cn"
proxyPort = "5445"
proxyUser = "16QMSOML"
proxyPass = "280651"
proxy_url = f"https://{proxyUser}:{proxyPass}@{proxyHost}:{proxyPort}"


# 定义URL
URL = "https://quotes.toscrape.com/page/"
PHAT = "./test/test.csv"



def header_x():
    # 随机获取一个headers
    user_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
                   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER',
                   'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0'
                   ]

    headers = {
        "User-Agent": random.choice(user_agents)
    }
    return headers



class CrawLer:
    """
    爬虫类
    """
    def __init__(self, url, save_path, page_start=1, page_end=2):
        """
        初始化爬虫
        :param url: 要爬的地址
        :param save_path: 存储的路径
        :param page_start: 开始的页数
        :param page_end: 结束的页数
        """
        self.url = url
        self.save_path = save_path
        self.page_start = page_start
        self.page_end = page_end

    async def fetch_url(self, session, url, semaphore)->list:
        """
        爬取单个页面,交给get_data方法处理,如何反回数据列表
        :param session: 分配到的会话线程
        :param url: 爬取的URL
        :param semaphore: 信号量
        :return: 数据列表
        """
        async with semaphore:
            try:
                await asyncio.sleep(random.uniform(5, 8))
                async with session.get(url, timeout=10) as response:
                    html_text = await response.text()
                    return await self.get_data(html_text)
            except Exception as e:
                print(f"error: {str(e)}")
                return []

    async def start(self)->None:
        """
        启动人口
        :return: None
        """
        resolver = aiohttp.resolver.ThreadedResolver()
        connector = aiohttp.TCPConnector(limit_per_host=3, resolver=resolver)
        semaphore = asyncio.Semaphore(3)
        async with aiohttp.ClientSession(connector=connector,headers=header_x()) as session:
            detail_urls = []
            for page in range(self.page_start, self.page_end + 1):
                await asyncio.sleep(random.uniform(3, 5))
                urls = await self.get_page_num(page, session)
                detail_urls.extend([urls])

            if not detail_urls:
                print("未获取到任何电影链接")
                return

            tasks = [asyncio.create_task(self.fetch_url(session, url, semaphore)) for url in detail_urls]
            results = await asyncio.gather(*tasks)

            flat_data = []
            valid_results = [r for r in results if r is not None]
            for page_data in valid_results:
                flat_data.extend(page_data)
            if flat_data:
                self.up_data(flat_data)
            else:
                print("没有成功获取到任何电影数据")

    @staticmethod
    async def get_data(html_text)->list:
        """
        进行数据清洗
        :param html_text: 爬取的页面
        :return: 数据列表
        """
        document = html.fromstring(html_text)
        # name = document.xpath("//*[@id='wrapper']/h1/span/text()")
        #
        # writer = document.xpath("//*[@id='info']/span[1]/span/a/text()")
        #
        # translator = document.xpath("//*[@id='info']/span[2]/a/text()")
        #
        # publishing_house = document.xpath("//*[@id='info']/span[3]/a/text()")
        #
        # production_company = document.xpath("//*[@id='info']/span[4]/a/text()")
        #
        # date = document.xpath("//*[@id='info']/span[5]/a/text()")
        #
        # isbn = document.xpath("//*[@id='info']/span[6]/a/text()")
        #
        # page_count = document.xpath("//*[@id='info']/span[7]/a/text()")
        #
        # book_binding = document.xpath("//*[@id='info']/span[8]/a/text()")
        #
        # price = document.xpath("//*[@id='info']/span[9]/a/text()")
        #
        # book_series = document.xpath("//*[@id='info']/span[10]/a/text()")
        # book = (
        #     {
        #         "名字": name,
        #         "作者": writer,
        #         "译者": translator,
        #         "出版社": publishing_house,
        #         "出品方": production_company,
        #         "出版年": date,
        #         "ISBN": isbn,
        #         "页数": page_count,
        #         "装帧": book_binding,
        #         "定价": price,
        #         "丛书": book_series
        #     }
        # )
        quote=[]
        for i in range(1,11):
            content = document.xpath(f"//div[@class='col-md-8']/div[{i}]/span[1]/text()")[0]
            if content:
                # 去除首尾的中文引号、英文引号
                content = content.strip('“”\'"')
                # 压缩多个空白为单个空格
                content = ' '.join(content.split())
            else:
                content = ""
            author = document.xpath(f"//div[@class='col-md-8']/div[{i}]/span[2]/small/text()")[0]
            author = author.strip() if author else ""
            tags = document.xpath(f"//div[@class='col-md-8']/div[{i}]/div/a/text()")
            if tags:
                # 去除每个标签首尾空格，并用逗号连接
                tags = ', '.join([tag.strip() for tag in tags])
            else:
                tags = ""
            quote.append({
                "内容": content,
                "作者": author,
                "标签": tags
            })
        return quote

    # 上传数据到文件
    def up_data(self, movie_data):
        """
        上传数据到文件
        :param movie_data: 需要上传数据
        :return: None
        """
        if not movie_data:
            return
        if not os.path.exists(os.path.dirname(self.save_path)):
            os.makedirs(os.path.dirname(self.save_path))
        with open(self.save_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=movie_data[0].keys())
            writer.writeheader()
            writer.writerows(movie_data)

    # 读取文件数据
    def read_data(self):
        """
        读取文件数据
        :return: 读取到的数据列表
        """
        with open(self.save_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    # 获取电影url数据
    async def get_page_num(self, page, session):
        """
        处理分页数据
        :param page: 页数
        :param session: 会话
        :return: 页数连接
        """
        # 发送请求，获取数据
        url = f"{URL}{page}/"
        # await asyncio.sleep(random.uniform(1, 3))
        # async with session.get(url, timeout=10) as response:
        #     # 输出数据
        #     html_text = await response.text()
        #     document = html.fromstring(html_text)
        #     # URL
        #     url_list = document.xpath(
        #         f"//*[@id='content']/div[2]/div[1]/ul//a[@class='fleft']/@href")

        return url


if __name__ == '__main__':
    x = CrawLer(URL, PHAT, 1, 10)
    asyncio.run(x.start())
