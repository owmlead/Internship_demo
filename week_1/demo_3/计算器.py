import os

from loguru import logger

#配置日志
os.makedirs("./log", exist_ok=True)
logger.add("./log/log.log", rotation="1 MB", retention=5, level="ERROR")

def add(a, b):
    return a + b
def sub(a, b):
    return b - a
def mul(a, b):
    return a * b
def div(a, b):
    if a == 0:
        raise ZeroDivisionError("除数不能为0")
    return b / a
def exp(a, b):
    return b ** a
def mod(a, b):
    if a == 0:
        raise ZeroDivisionError("取余运算的除数不能为0")
    return b % a
class oper:
    x = {'+': add, '-': sub, '*': mul, '/': div, '^': exp, '%': mod}
    def __init__(self, opt):
        self.c = opt
    def __call__(self, a, b):
        return self.x[self.c](a, b)
def col(a, b, c):
    x = oper(c)
    return x(a, b)
def jsq(s):
    """计算表达式，正常返回结果，出错则抛出异常"""
    allow = set("0123456789.+-*/^%()")  # 合法输入字符集
    level = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3, '%': 2}  # 运算符优先级
    operation = []  # 运算符栈
    count = []  # 数字栈
    join = []  # 缓冲数字字符
    last_bol = ''  # 上一个字符
    for i in s:
        if i == ' ':
            continue
        # 检测非法字符
        if i not in allow:
            raise ValueError(f"非法字符 '{i}'")
        # 负号处理
        if i == '-' and (last_bol == '' or last_bol == '(' or last_bol in '+-*/^%'):
            count.append(0)
            operation.append(i)
            last_bol = i
            continue
        # 将str转换为浮点数
        if ("0" <= i <= "9") or i == ".":
            join.append(i)
        else:
            if len(join):
                count.append(float(''.join(join)))
                join.clear()
            # 处理括号
            if i == '(':
                operation.append(i)
            elif i == ')':
                while True:
                    # 括号不匹配
                    if not operation:
                        raise SyntaxError("括号不匹配")
                    k = operation.pop()
                    if k == '(':
                        break
                    count.append(col(count.pop(), count.pop(), k))
            else:
                # 输入连续的运算符
                if last_bol in '+-*/^%' and i != '-':
                    raise SyntaxError(f"不允许连续运算符：{last_bol}{i}")
                # 进行运算
                while operation and operation[-1] != '(' and level[i] <= level[operation[-1]]:
                    count.append(col(count.pop(), count.pop(), operation.pop()))
                operation.append(i)
        last_bol = i
    # 处理可能遗留数字
    if len(join):
        count.append(float(''.join(join)))
        join.clear()
    # 防止多余括号
    if '(' in operation:
        raise SyntaxError("括号不匹配：缺少右括号")
    # 清空运算符栈
    while len(operation):
        # 出现多余运算符
        if len(count) < 2:
            raise SyntaxError("表达式不完整（运算符缺少操作数）")
        count.append(col(count.pop(), count.pop(), operation.pop()))
    # 最终结果只有一个
    if len(count) != 1:
        raise SyntaxError("表达式不完整")
    return count.pop()
if __name__ == "__main__":
    while True:
        try:
            expr=input()
            if expr=="exit":
                break
            print(jsq(expr))
        except Exception as e:
            logger.error(f"计算表达式 '{expr}' 时发生错误: {e}")
            print(f"计算错误：{e}")
