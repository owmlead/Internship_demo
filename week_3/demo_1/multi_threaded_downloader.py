import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from loguru import logger
import requests


#配置日志
os.makedirs("./log", exist_ok=True)
logger.add("log/log.log", rotation="500 MB", retention="10 days")

class DownLoader:
    """管理下载操作类"""

    def __init__(self, url:str, save_path:str, num_thread:int=4)->None:
        """
        初始化变量
        :param url: 下载地址
        :param save_path: 保存路径
        :param num_thread: 线程数
        """
        self.lock = threading.Lock() #锁,防止多个进程同时修改进度条
        self.url = url               #下载地址
        self.save_path = save_path   #保存路径
        self.num_thread = num_thread #进程数
        self.chunk_size = 1024*1024    #文件一次写入大小
        try:
            response = requests.head(url, timeout=10)
            response.raise_for_status()
            self.total_size = int(response.headers.get('content-length', 0))
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            raise
        if self.total_size <= 0:
            logger.warning("无法获取文件大小，将使用单线程下载（无法断点续传）")

    def download(self)->None:
        """
        启动下载器
        :return:None
        """
        if os.path.exists(self.save_path):
            local_size = os.path.getsize(self.save_path)
            if local_size >= self.total_size:
                logger.info(f"文件已存在")
                return
        else:
            local_size = 0
        if self.num_thread <= 1 or self.total_size <= 1024 * 1024:
            self._single_thread(local_size)
        else:
            self._multi_thread(local_size)

    def _single_thread(self, local_size:int=0, start:int=0, end:int=0, path:str|None=None, shared_pbar:tqdm|None=None)->None:
        """
        单线程下载/分快下载
        :param local_size: 本地大小
        :param start: 开始位置
        :param end: 结束位置
        :param path: 文件保存路径
        :param shared_pbar: 全局进度条
        :return:None
        """
        header = {"Range": f"bytes={local_size + start}-{end if end else ''}"}
        try:
            response = requests.get(self.url, stream=True, headers=header)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"下载请求失败:{e}")
            raise
        mode = "ab" if local_size + start else "wb"
        with open(path if path else self.save_path, mode) as file:
            if not shared_pbar:
                with tqdm(total=self.total_size, initial=local_size, unit="B", unit_scale=True) as pbar:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        file.write(chunk)
                        pbar.update(len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    file.write(chunk)
                    with self.lock:
                        shared_pbar.update(len(chunk))

    def _multi_thread(self, local_size:int)->None:
        """
        多线程下载
        :param local_size: 本地大小
        :return: None
        """
        part_size = int((self.total_size - local_size) / self.num_thread)
        if part_size == 0:
            self._single_thread(local_size)
            return
        part_file_paths = []
        with ThreadPoolExecutor(max_workers=self.num_thread) as executor, tqdm(total=self.total_size,
                                                                               initial=local_size, unit="B",
                                                                               unit_scale=True) as pbar:
            futures = []
            for i in range(self.num_thread):
                part_file_path = f"{self.save_path}.part{i}"
                part_file_paths.append(part_file_path)
                start = local_size + i * part_size
                end = start + part_size - 1 if i < self.num_thread - 1 else self.total_size - 1
                futures.append(executor.submit(self._download_part, part_file_path, start, end, pbar))
            for f in futures:
                f.result()
        logger.info("合并分块中...")
        mode = "ab" if local_size > 0 else "wb"
        with open(self.save_path, mode) as out, tqdm(total=self.total_size, unit='B', unit_scale=True,
                                                     desc="合并") as pbar:
            for part_file in part_file_paths:
                with open(part_file, "rb") as inf:
                    while True:
                        data = inf.read(1024 * 1024)
                        if not data:
                            break
                        out.write(data)
                        pbar.update(len(data))
                os.remove(part_file)
        logger.success("下载完成")

    def _download_part(self, path:str, start:int, end:int, pbar:tqdm)->None:
        """
        分块下载线程
        :param path: 保存地址
        :param start: 开始位置
        :param end: 结束位置
        :param pbar: 全局进度条
        :return: None
        """
        expected_size = end - start + 1
        local_size = 0
        max_retries = 3
        retry_delay = 2  # 秒
        for attempt in range(1, max_retries + 1):
            try:
                if os.path.exists(path):
                    local_size = os.path.getsize(path)
                    if local_size >= expected_size:
                        logger.info(f"分块 {start}-{end} 已完成")
                        return

                self._single_thread(local_size, start, end, path, pbar)

            except Exception as e:
                logger.warning(f"分块 {start}-{end} 下载失败 (尝试 {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    logger.error(f"分块 {start}-{end} 重试 {max_retries} 次后仍失败")
                    raise  # 抛出异常，终止整个下载
                # 等待后重试
                time.sleep(retry_delay)




if __name__ == "__main__":
    test_url = "https://samplefile.com/samples/download/document/csv/csv_sample_file_25MB.csv/?utm_source=samplefile&utm_medium=large_detail&utm_campaign=file_download"
    test_save_path = "E:/test/test.ccc"
    test_num_thread = 4
    downloader = DownLoader(test_url, test_save_path, test_num_thread)
    downloader.download()
