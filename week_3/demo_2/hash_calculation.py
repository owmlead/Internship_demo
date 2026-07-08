import hashlib
import os
from multiprocessing import Pool
from pathlib import Path
from loguru import logger


# 配置日志
os.makedirs("./log", exist_ok=True)
logger.add("log/log.log", rotation="500 MB", retention="10 days")


class HashCalculator:
    def __init__(self,path,num_process=4):
        self.path = path
        self.num_process = num_process

    @staticmethod
    def get_hash_single(path,start=0,size=None):
        sha256=hashlib.sha256()
        with open(path,'rb') as f:
            f.seek(start)
            if not size:
                for chunk in iter(lambda: f.read(8192),b''):
                    sha256.update(chunk)
            else:
                chunk = size
                while chunk > 0:
                    read_size = min(chunk, 8192)
                    data = f.read(read_size)
                    if not data:
                        break
                    sha256.update(data)
                    chunk -= len(data)
        return sha256.hexdigest()

    def get_hash_large_file(self):
        file_size=os.path.getsize(self.path)
        # chunk_size=file_size//self.num_process
        # with Pool(self.num_process) as pool:
        #     result=[]
        #     for i in range(self.num_process):
        #         start=i*chunk_size
        #         file_path_size=min(file_size-start,chunk_size)
        #         if file_path_size<=0:
        #             break
        #         result.append(pool.apply_async(self.get_hash_single,args=(self.path,start,file_path_size)))
        #     combined=b''.join([bytes.fromhex(res.get()) for res in result])
        # final_hash=hashlib.sha256(combined).hexdigest()
        # return final_hash
        return self.get_hash_single(self.path, 0, file_size)

    def get_hash_many_file(self):
        file_hash_dict = {}
        result=[]
        with Pool(self.num_process) as pool:
            path_iter = Path(self.path).glob("*")
            for file in path_iter:
                if file.is_file():
                    size=os.path.getsize(file)
                    result.append((os.path.basename(file),pool.apply_async(self.get_hash_single,args=(file,0,size))))
            for f,h in result:
                file_hash_dict[f]=h.get()
        return file_hash_dict


    def get_hash(self):
        if not os.path.exists(self.path):
            logger.error(f"{self.path}路径不存在")
        elif os.path.isdir(self.path):
            hash_files=self.get_hash_many_file()
            for f,h in hash_files.items():
                logger.info(f"文件{f}的hash是{h}")
                with open(os.path.join(self.path,f"{f}.hash"),'w',encoding="utf-8") as file:
                    file.write(h)
        elif os.path.isfile(self.path):
            h=self.get_hash_large_file()
            logger.info(f"文件{os.path.basename(self.path)}的hash是{h}")
            with open(self.path + f".hash", 'w',encoding="utf-8") as file:
                file.write(h)


if __name__ == "__main__":
    x=HashCalculator("E:/test")
    x.get_hash()