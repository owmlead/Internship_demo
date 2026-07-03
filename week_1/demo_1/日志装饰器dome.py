import os
import time


class FileContext:
    def __init__(self, file_url, model, encode):
        self.file_url = file_url
        self.model = model
        self.encode = encode
        self.file = None

    def __enter__(self):
        print(f"正在打开文件{self.file_url}")
        self.file = open(self.file_url, self.model, encoding=self.encode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"正在关闭文件 {self.file_url}")
        if self.file:
            self.file.close()
        return False


def countdown(n):
    while True:
        yield n
        n += 1


yy = countdown(1)


def logging_write(message):
    if not os.path.exists("./log"):
        os.mkdir('./log')
    with FileContext('./log/log.txt', 'a', encode="utf-8") as f:
        print(message)
        f.write(f"{next(yy)}:{message}")


def log_func(num_times):
    def info(function):
        def message(*args, **kwargs):
            # 函数执行前
            try:
                for _ in range(num_times):
                    result = function(*args, **kwargs)
                    logging_write(
                        f"info:{time.strftime(f"%Y-%m-%d %H:%M:%S", time.localtime())} {function.__name__}被调用了,结果为{result}\n")
                    # 函数执行后
                return result
            except Exception as e:
                logging_write(
                    f"ERROR:{time.strftime(f"%Y-%m-%d %H:%M:%S", time.localtime())} {function.__name__}出现了{e}错误\n")
            # raise

        return message

    return info


def log_class(cls):
    class wrapper:
        def __init__(self, *ages, **kwargs):
            logging_write(f"info:{time.strftime(f"%Y-%m-%d %H:%M:%S", time.localtime())} {cls.__name__}被创建了\n")
            self.wrapped = cls(*ages, **kwargs)

        def __getattr__(self, name):
            try:
                logging_write(
                    f"info:{time.strftime(f"%Y-%m-%d %H:%M:%S", time.localtime())} {cls.__name__}调用了{name}\n")
                return getattr(self.wrapped, name)
            except Exception as e:
                logging_write(f"ERROR:{time.strftime(f"%Y-%m-%d %H:%M:%S", time.localtime())} {name}出现了{e}错误\n")

    return wrapper


# 测试
if __name__ == '__main__':
    @log_class
    class count:
        def __init__(self):
            pass

        @log_func(1)
        def add(self, a, b):
            return a + b

        @log_func(1)
        def sub(self, a, b):
            return a - b

        @log_func(1)
        def mul(self, a, b):
            return a * b

        @log_func(1)
        def div(self, a, b):
            return a / b


    x = count()
    print(x.add(5, '0'))
    print(x.add(5, 5))
    print(x.sub(5, 4))
    print(x.sub(3, 3))
    print(x.mul(2, 0))
    print(x.mul(5, 'o'))
    print(x.div(5, 0))
    print(x.div(1, 2))
