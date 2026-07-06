"""表达式求值器 — 支持运算符优先级的简易计算器。

支持 +, -, *, /, ^（乘方）, %, 以及括号。
使用调度场算法解析并计算中缀表达式。
"""

import os

from loguru import logger

# 配置日志
os.makedirs("./log", exist_ok=True)
logger.add("./log/log.log", rotation="1 MB", retention=5, level="ERROR")


# ---------------------------------------------------------------------------
# 基本算术运算
# ---------------------------------------------------------------------------


def add(a: float, b: float) -> float:
    return a + b


def sub(a: float, b: float) -> float:
    return b - a


def mul(a: float, b: float) -> float:
    return a * b


def div(a: float, b: float) -> float:
    if a == 0:
        raise ZeroDivisionError("除数不能为0")
    return b / a


def exp(a: float, b: float) -> float:
    return b ** a


def mod(a: float, b: float) -> float:
    if a == 0:
        raise ZeroDivisionError("取余运算的除数不能为0")
    return b % a


# ---------------------------------------------------------------------------
# 运算符调度
# ---------------------------------------------------------------------------


class Operator:
    """可调用对象，分发到对应的算术函数。"""

    _operations = {
        "+": add,
        "-": sub,
        "*": mul,
        "/": div,
        "^": exp,
        "%": mod,
    }

    def __init__(self, op: str):
        self._op = op

    def __call__(self, a: float, b: float) -> float:
        return self._operations[self._op](a, b)


def _calculate(a: float, b: float, op: str) -> float:
    """对操作数 *a* 和 *b* 应用运算符 *op*。"""
    return Operator(op)(a, b)


# ---------------------------------------------------------------------------
# 表达式解析器 / 求值器（调度场算法）
# ---------------------------------------------------------------------------


def evaluate(expression: str) -> float:
    """解析并计算算术表达式。

    返回数值结果，输入不合法时抛出 ValueError 或 SyntaxError。

    支持: ``+`` ``-`` ``*`` ``/`` ``^`` ``%`` ``(`` ``)`` 以及小数。
    """
    allowed_chars = set("0123456789.+-*/^%()")  # 合法输入字符集
    precedence = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3, "%": 2}  # 运算符优先级

    op_stack: list[str] = []        # 运算符栈
    val_stack: list[float] = []     # 数字栈
    num_buffer: list[str] = []      # 缓冲数字字符
    last_char = ""                  # 上一个字符

    for ch in expression:
        if ch == " ":
            continue

        # 检测非法字符
        if ch not in allowed_chars:
            raise ValueError(f"非法字符 '{ch}'")

        # 负号处理：开头、左括号后、运算符后的 '-' 视为负号
        if ch == "-" and (last_char == "" or last_char == "(" or last_char in "+-*/^%"):
            val_stack.append(0)
            op_stack.append(ch)
            last_char = ch
            continue

        # 将数字 / 小数点累积到 num_buffer
        if ("0" <= ch <= "9") or ch == ".":
            num_buffer.append(ch)
        else:
            if num_buffer:
                val_stack.append(float("".join(num_buffer)))
                num_buffer.clear()

            if ch == "(":
                op_stack.append(ch)
            elif ch == ")":
                # 弹出直到匹配的 '('
                while True:
                    if not op_stack:
                        raise SyntaxError("括号不匹配")
                    op = op_stack.pop()
                    if op == "(":
                        break
                    val_stack.append(_calculate(val_stack.pop(), val_stack.pop(), op))
            else:
                # 不允许连续运算符（负号除外）
                if last_char in "+-*/^%" and ch != "-":
                    raise SyntaxError(f"不允许连续运算符：{last_char}{ch}")

                # 从栈中弹出优先级更高或相等的运算符并计算
                while (
                    op_stack
                    and op_stack[-1] != "("
                    and precedence[ch] <= precedence[op_stack[-1]]
                ):
                    val_stack.append(
                        _calculate(val_stack.pop(), val_stack.pop(), op_stack.pop())
                    )
                op_stack.append(ch)

        last_char = ch

    # 处理可能遗留的数字
    if num_buffer:
        val_stack.append(float("".join(num_buffer)))
        num_buffer.clear()

    # 防止多余括号
    if "(" in op_stack:
        raise SyntaxError("括号不匹配：缺少右括号")

    # 清空运算符栈
    while op_stack:
        if len(val_stack) < 2:
            raise SyntaxError("表达式不完整（运算符缺少操作数）")
        val_stack.append(
            _calculate(val_stack.pop(), val_stack.pop(), op_stack.pop())
        )

    # 最终结果只有一个
    if len(val_stack) != 1:
        raise SyntaxError("表达式不完整")
    return val_stack.pop()


# ---------------------------------------------------------------------------
# 交互式 REPL
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    while True:
        try:
            expr = input("> ")
            if expr == "exit":
                break
            print(evaluate(expr))
        except Exception as e:
            logger.error(f"计算表达式 '{expr}' 时发生错误: {e}")
            print(f"计算错误：{e}")
