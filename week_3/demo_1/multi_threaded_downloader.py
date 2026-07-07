import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from loguru import logger
import requests


class DownLoader:
    """管理下载操作类"""

    def __init__(self, url, save_path, num_thread=4):
        self.lock = threading.Lock()
        self.url = url
        self.save_path = save_path
        self.num_thread = num_thread
        self.chunk_size=1024*1024
        try:
            response = requests.head(url, timeout=10)
            response.raise_for_status()
            self.total_size = int(response.headers.get('content-length', 0))
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            raise
        if self.total_size <= 0:
            logger.warning("无法获取文件大小，将使用单线程下载（无法断点续传）")

    def download(self):
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

    def _single_thread(self, local_size=0, start=0, end=0, path=None, shared_pbar=None):
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

    def _multi_thread(self, local_size):

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

    def _download_part(self, path, start, end, pbar):
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
    test_save_path = "E:/test/test.e"
    test_num_thread = 4
    downloader = DownLoader(test_url, test_save_path, test_num_thread)
    downloader.download()
