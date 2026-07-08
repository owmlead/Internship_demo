import asyncio
import csv
import re
import aiohttp
from lxml import html
import random

# 定义URL
URL = "https://www.themoviedb.org"
PHAT = "./test/test.csv"

HEADER = {
}


class CrawLer:
    def __init__(self, url, save_path, page_start=1, page_end=2):
        self.url = url
        self.save_path = save_path
        self.page_start = page_start
        self.page_end = page_end

    async def fetch_url(self, session, url, semaphore):
        async with semaphore:
            try:
                await asyncio.sleep(random.uniform(0.5, 2))
                async with session.get(url, timeout=10) as response:
                    html_text = await response.text()
                    return await self.get_data(html_text)
            except Exception as e:
                return {"error": str(e)}

    async def start(self):
        connector = aiohttp.TCPConnector(limit_per_host=100)
        semaphore = asyncio.Semaphore(3)
        async with aiohttp.ClientSession(headers=HEADER,connector=connector) as session:
            detail_urls = []
            for page in range(self.page_start, self.page_end + 1):
                urls = await self.get_movie_page_num(page, session)
                detail_urls.extend(urls)

            if not detail_urls:
                print("未获取到任何电影链接")
                return

            tasks = [asyncio.create_task(self.fetch_url(session, url, semaphore)) for url in detail_urls]
            results = await asyncio.gather(*tasks)

            valid_results = [r for r in results if r is not None]
            if valid_results:
                self.up_data(valid_results)
            else:
                print("没有成功获取到任何电影数据")

    @staticmethod
    async def get_data(html_text):
        document = html.fromstring(html_text)
        movie_name = document.xpath("//*[@id='original_header']/div[2]/section/div[1]/h2/a/text()")
        name = re.search(r".+", movie_name).group() if movie_name else ""
        movie_date = document.xpath("//*[@id='original_header']/div[2]/section/div[1]/div/span[2]/text()")
        date = re.search(r"\d{4}-\d{2}-\d{2}", movie_date).group() if movie_date else ""
        movie_type = document.xpath("//*[@id='original_header']/div[2]/section/div[1]/div/span[3]/a/text()")
        type_list = re.findall(r"\w{2}", movie_type)
        types = []
        for t in type_list:
            types.append(t)
        types = ','.join(types)
        movie_time = document.xpath("//*[@id='original_header']/div[2]/section/div[1]/div/span[4]/text()")
        time = str(
            int(re.search(r"\d*h", movie_time).group()[:-1] if re.search(r"\d*h",
                                                                         str(movie_time)) else 0) * 60 + int(
                re.search(r"\d*m", movie_time).group()[:-1] if re.search(r"\d*m", str(movie_time)) else 0))
        movie_grade = document.xpath("//*[@id='consensus_pill']/div/div[1]/div/div/@data-percent")
        grade = re.search(r"\d{1,2}", movie_grade).group() if movie_grade else ""
        movie_slogan = document.xpath("//*[@id='original_header']/div[2]/section/div[3]/h3[1]/text()")
        slogan = re.sub(r'^.{2}|.{2}$', "", re.search(r".*", movie_slogan).group()) if movie_slogan else ""
        movie_summary = document.xpath("//*[@id='original_header']/div[2]/section/div[3]/div/p/text()")
        summary = re.sub(r'^.{2}|.{2}$', "", re.search(r".*", movie_summary).group()) if movie_summary else ""
        movie_director = document.xpath("//*[@id='original_header']/div[2]/section/div[3]/ol/li[1]/p[1]/a/text()")
        director = re.sub(r'^.{2}|.{2}$', "", re.search(r".*", movie_director).group()) if movie_director else ""
        movie_screenwriter = document.xpath(
            "//*[@id='original_header']/div[2]/section/div[3]/ol/li[2]/p[1]/a/text()")
        screenwriter = re.sub(r'^.{2}|.{2}$', "",
                              re.search(r".*", movie_screenwriter).group()) if movie_screenwriter else ""
        movie = (
            {"名字": name, "日期": date, "类型": types, "时长": time, "评分": grade, "评语": slogan,
             "简介": summary, "导演": director, "制片人": screenwriter})
        print(movie)
        return movie

    # 上传数据到文件
    def up_data(self, movie_data):
        if not movie_data:
            return
        with open(self.save_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=movie_data[0].keys())
            writer.writeheader()
            writer.writerows(movie_data)

    # 读取文件数据
    def read_data(self):
        with open(self.save_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    # 获取电影url数据
    async def get_movie_page_num(self, page, session):
        # 发送请求，获取数据
        url=f"{URL}/movie?page={page}"
        await asyncio.sleep(random.uniform(1, 3))
        async with session.get(url, timeout=60) as response:
            # 输出数据
            html_text = await response.text()
            document = html.fromstring(html_text)
            # 电影URL
            movie_url_list = document.xpath(
                f"//*[@id='page_{page}']//div[@class='relative w-full']/a[@data-media-type='movie']/@href")
            return  movie_url_list



if __name__ == '__main__':
    x = CrawLer(URL, PHAT, 1, 2)
    asyncio.run(x.start())
