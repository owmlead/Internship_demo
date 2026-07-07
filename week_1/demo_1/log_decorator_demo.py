"""日志装饰器演示 — 演示函数/类装饰器配合文件日志记录。

提供:
  - FileContext: 安全文件打开/关闭的上下文管理器
  - logging_write: 将带时间戳的消息写入日志文件
  - log_func: 记录每次函数调用的装饰器
  - log_class: 记录类实例化和属性访问的装饰器
"""

import os
import time




def _current_timestamp() -> str:
    """
    返回当前时间的格式化字符串。
    :return: 格式化时间字符串。
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


class FileContext:
    """安全文件处理的上下文管理器。

    即使发生异常，也会在退出时自动关闭文件。
    """

    def __init__(self, file_path: str, mode: str, encoding: str = "utf-8"):
        """
        初始化上下文管理器
        :param file_path: 文件路径
        :param mode: 文件打开方式(例如 'r':读取,'w':写入)
        :param encoding: 文件已什么编码格式打开(例如 'utf-8')
        """
        self.file_path = file_path
        self.mode = mode
        self.encoding = encoding
        self.file = None

    def __enter__(self):
        """
        上下文管理器进入接口
        :return: file对象
        """
        print(f"正在打开文件 {self.file_path}")
        self.file = open(self.file_path, self.mode, encoding=self.encoding)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器退出接口
        :param exc_type: 异常类型
        :param exc_val: 异常变量
        :param exc_tb: 异常回溯对象
        :return: False
        """
        print(f"正在关闭文件 {self.file_path}")
        if self.file:
            self.file.close()
        return False


def _counter(start: int = 1):
    """
    从start开始的无限计数器生成器。
    :param start: 开始的数,默认为1
    :return: start+next()调用次数
    """
    n = start
    while True:
        yield n
        n += 1

_line_counter = _counter(1)  # 初始化生成器

def logging_write(message: str) -> None:
    """
    将带时间戳和编号的消息追加到日志文件。
    :param message: 日志信息
    :return: None
    """
    if not os.path.exists("./log"):
        os.mkdir("./log")
    with FileContext("./log/log.log", "a", encoding="utf-8") as f:
        print(message)
        f.write(f"{next(_line_counter)}:{message}")


def log_func(num_times: int = 1):
    """
    装饰器：对被装饰函数的每次调用记录被装饰函数次数日志。
    成功时日志包含返回值；失败时记录异常并重新抛出。
    :param num_times: 调用多少次被装饰函数
    :return: 内部函数decorator
    """
    def decorator(func):
        """
        装饰器：包装函数
        :param func: 被装饰函数
        :return: 内部函数wrapper
        """
        def wrapper(*args, **kwargs):
            """
            装饰器: 实际执行函数
            :param args: 位置传参
            :param kwargs: 关键字传参
            :return: 被装饰函数执行结果
            """
            last_result = None #被装饰函数执行结果初始化
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


def log_class(cls):
    """
    装饰器：装饰类,记录类实例化和每次属性访问。
    :param cls: 被装饰类
    :return: 内部类Wrapper
    """
    class Wrapper:
        """
        内部类用来装饰被装饰类
        """
        def __init__(self, *args, **kwargs):
            """
            初始化被装饰类变量
            :param args: 位置参数
            :param kwargs: 关键字参数
            """
            logging_write(
                f"info:{_current_timestamp()} {cls.__name__} 被创建了\n"
            )
            self._wrapped = cls(*args, **kwargs)

        def __getattr__(self, name: str):
            """
            装饰类调用接口
            :param name: 调用函数名
            :return: 调用函数结果
            """
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
    """
    通过装饰器实现日志记录的简易计算器。
    """

    def __init__(self):
        """
        初始化
        """
        pass

    @log_func(1)
    def add(self, a: float, b: float) -> float:
        """
        加法
        :param a: 被加数
        :param b: 加数
        :return: 和
        """
        return a + b

    @log_func(1)
    def sub(self, a: float, b: float) -> float:
        """
        减法
        :param a: 被减数
        :param b: 减数
        :return: 差
        """
        return a - b

    @log_func(1)
    def mul(self, a: float, b: float) -> float:
        """
        乘法
        :param a: 被乘数
        :param b: 乘数
        :return: 积
        """
        return a * b

    @log_func(1)
    def div(self, a: float, b: float) -> float:
        """
        除法
        :param a: 被除数
        :param b: 除数
        :return: 商
        """
        return a / b


if __name__ == "__main__":
    """
    测试
    """
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
