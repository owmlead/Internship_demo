"""日志装饰器演示 — 演示函数/类装饰器配合文件日志记录。

提供:
  - FileContext: 安全文件打开/关闭的上下文管理器
  - logging_write: 将带时间戳的消息写入日志文件
  - log_func: 记录每次函数调用的装饰器
  - log_class: 记录类实例化和属性访问的装饰器
"""

import os
import time
from typing import Any, Callable, Type, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def _current_timestamp() -> str:
    """返回当前时间的格式化字符串。"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


class FileContext:
    """安全文件处理的上下文管理器。

    即使发生异常，也会在退出时自动关闭文件。
    """

    def __init__(self, file_path: str, mode: str, encoding: str = "utf-8"):
        self.file_path = file_path
        self.mode = mode
        self.encoding = encoding
        self.file = None

    def __enter__(self):
        print(f"正在打开文件 {self.file_path}")
        self.file = open(self.file_path, self.mode, encoding=self.encoding)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"正在关闭文件 {self.file_path}")
        if self.file:
            self.file.close()
        return False


def _counter(start: int = 1):
    """从 *start* 开始的无限计数器生成器。"""
    n = start
    while True:
        yield n
        n += 1


_line_counter = _counter(1)


def logging_write(message: str) -> None:
    """将带时间戳和编号的消息追加到日志文件。"""
    if not os.path.exists("./log"):
        os.mkdir("./log")
    with FileContext("./log/log.log", "a", encoding="utf-8") as f:
        print(message)
        f.write(f"{next(_line_counter)}:{message}")


def log_func(num_times: int = 1):
    """装饰器：对被装饰函数的每次调用记录 *num_times* 次日志。

    成功时日志包含返回值；失败时记录异常并重新抛出。
    """

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            last_result = None
            for _ in range(num_times):
                try:
                    last_result = func(*args, **kwargs)
                    logging_write(
                        f"info:{_current_timestamp()} "
                        f"{func.__name__} 被调用了, 结果为 {last_result}\n"
                    )
                except Exception as e:
                    logging_write(
                        f"ERROR:{_current_timestamp()} "
                        f"{func.__name__} 出现了 {e} 错误\n"
                    )
                    raise
            return last_result

        return wrapper

    return decorator


def log_class(cls: Type):
    """装饰器：记录类实例化和每次属性访问。"""

    class Wrapper:
        def __init__(self, *args, **kwargs):
            logging_write(
                f"info:{_current_timestamp()} {cls.__name__} 被创建了\n"
            )
            self._wrapped = cls(*args, **kwargs)

        def __getattr__(self, name: str):
            try:
                logging_write(
                    f"info:{_current_timestamp()} "
                    f"{cls.__name__} 调用了 {name}\n"
                )
                return getattr(self._wrapped, name)
            except Exception as e:
                logging_write(
                    f"ERROR:{_current_timestamp()} "
                    f"{name} 出现了 {e} 错误\n"
                )
                raise

    return Wrapper


@log_class
class Calculator:
    """通过装饰器实现日志记录的简易计算器。"""

    def __init__(self):
        pass

    @log_func(1)
    def add(self, a: float, b: float) -> float:
        return a + b

    @log_func(1)
    def sub(self, a: float, b: float) -> float:
        return a - b

    @log_func(1)
    def mul(self, a: float, b: float) -> float:
        return a * b

    @log_func(1)
    def div(self, a: float, b: float) -> float:
        return a / b


if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 0))
    print(calc.add(5, 5))
    print(calc.sub(5, 4))
    print(calc.sub(3, 3))
    print(calc.mul(2, 0))
    try:
        print(calc.mul(5, "o"))
    except TypeError:
        print("mul with string raised TypeError (expected)")
    try:
        print(calc.div(5, 0))
    except ZeroDivisionError:
        print("div by zero raised ZeroDivisionError (expected)")
    print(calc.div(1, 2))
