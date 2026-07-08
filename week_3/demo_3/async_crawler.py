import asyncio
import csv
import os
import re
import time

import aiohttp
import requests
from lxml import html

# 定义URL
URL = "https://www.themoviedb.org"


HEADER={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.themoviedb.org/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


class crawler:
    def __init__(self,urls):
        self.urls =urls


    async def start(self):
        connector = aiohttp.TCPConnector(limit_per_host=100)
        async with aiohttp.ClientSession(connector=connector) as session:
            semaphore = asyncio.Semaphore(10)





    # 获取电影url数据
    def get_movie_list(self,page):
        # 发送请求，获取数据
        response = session.get(url + f"/movie?page={page}", timeout=60)
        # 输出数据
        document = html.fromstring(response.text)
        # 电影URL
        movie_url_list = document.xpath(
            f"//*[@id='page_{page}']//div[@class='relative w-full']/a[@data-media-type='movie']/@href")
        return movie_url_list

    # 获取电影信息数据
    def get_movie_data(self,movie_url_list):
        movie_data = []
        for movie_url in movie_url_list:
            time.sleep(5)
            response = requests.get(url + movie_url, timeout=60)
            document = html.fromstring(response.text)
            movie_name = document.xpath("//*[@id='original_header']/div[2]/section/div[1]/h2/a/text()")
            movie_date = document.xpath("//*[@id='original_header']/div[2]/section/div[1]/div/span[2]/text()")
            movie_type = document.xpath("//*[@id='original_header']/div[2]/section/div[1]/div/span[3]/a/text()")
            movie_time = document.xpath("//*[@id='original_header']/div[2]/section/div[1]/div/span[4]/text()")
            movie_grade = document.xpath("//*[@id='consensus_pill']/div/div[1]/div/div/@data-percent")
            movie_slogan = document.xpath("//*[@id='original_header']/div[2]/section/div[3]/h3[1]/text()")
            movie_summary = document.xpath("//*[@id='original_header']/div[2]/section/div[3]/div/p/text()")
            movie_director = document.xpath("//*[@id='original_header']/div[2]/section/div[3]/ol/li[1]/p[1]/a/text()")
            movie_screenwriter = document.xpath(
                "//*[@id='original_header']/div[2]/section/div[3]/ol/li[2]/p[1]/a/text()")
            movie = {"name": movie_name, "date": movie_date, "type": movie_type, "time": movie_time,
                     "grade": movie_grade,
                     "slogan": movie_slogan, "summary": movie_summary, "director": movie_director,
                     "screenwriter": movie_screenwriter}
            print(movie)
            movie_data.append(movie)
        return movie_data

    # 数据清理
    def data_clean(movie_data):
        movie_data_clean = []
        for data in movie_data:
            name = re.search(r".+", data["name"]).group()
            date = re.search(r"\d{4}-\d{2}-\d{2}", data["date"]).group()
            type_list = re.findall(r"\w{2}", data["type"])
            type = []
            for t in type_list:
                type.append(t)
            type = ','.join(type)
            time = str(
                int(re.search(r"\d*h", data["time"]).group()[:-1] if re.search(r"\d*h",
                                                                               str((data["time"]))) else 0) * 60 + int(
                    re.search(r"\d*m", data["time"]).group()[:-1] if re.search(r"\d*m", str((data["time"]))) else 0))
            grade = re.search(r"\d{1,2}", data["grade"]).group()
            slogan = re.sub(r'^.{2}|.{2}$', "", re.search(r".*", data["slogan"]).group())
            summary = re.sub(r'^.{2}|.{2}$', "", re.search(r".*", data["summary"]).group())
            director = re.sub(r'^.{2}|.{2}$', "", re.search(r".*", data["director"]).group())
            screenwriter = re.sub(r'^.{2}|.{2}$', "", re.search(r".*", data["screenwriter"]).group())
            movie_data_clean.append(
                {"名字": name, "日期": date, "类型": type, "时长": time, "评分": grade, "评语": slogan,
                 "简介": summary, "导演": director, "制片人": screenwriter})
        return movie_data_clean

    # 上传数据到文件
    def updata(movie_data):
        if not os.path.exists("./movie_data"):
            os.mkdir("./movie_data")
        with open("./movie_data/movie_data.CSV", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=movie_data[0].keys())
            writer.writeheader()
            for data in movie_data:
                writer.writerow(data)

    # 读取文件数据
    def read_movie_data():
        with open("./movie_data/movie_data.CSV", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    # 分页控制
    def page_num(first, last):
        movie_url_list = []
        for i in range(first, last + 1):
            movie_url_list = movie_url_list + get_movie_list(i)
        return movie_url_list


if __name__ == '__main__':
    updata(get_movie_data(page_num(1, 3)))
    data_clean(read_movie_data())
