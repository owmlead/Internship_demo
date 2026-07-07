"""批量文件重命名工具 — 使用正则表达式匹配并重命名文件。

基于 Click 构建命令行界面，使用 loguru 进行结构化日志记录。
支持三种互斥的重命名模式：替换、添加前缀、添加后缀。
"""

import os
import re
from pathlib import Path

import click
from loguru import logger
from pydantic import ValidationError, validate_call

logger.add("log/log.log", rotation="500 MB", retention="10 days")


def _count_operations(replace: str | None, prefix: str | None, suffix: str | None) -> int:
    """返回当前激活的重命名操作数量（非 None 且非空）。"""
    return sum(1 for v in (replace, prefix, suffix) if v)


@click.command()
@click.option("--directory", "-d", default=".", help="目标目录，默认为当前目录")
@click.option("--pattern", "-p", default=".*", help="使用正则表达式匹配文件名")
@click.option("--replace", "-r", default=None, help="将文件名中的旧字符串替换")
@click.option("--prefix", default=None, help="添加前缀")
@click.option("--suffix", default=None, help="添加后缀（在扩展名之前）")
@click.option("--recursive", is_flag=True, help="是否递归处理子目录")
@click.option("--force", is_flag=True, help="强制覆盖已存在的文件")
@validate_call
def rename_files(
    directory: str,
    pattern: str,
    replace: str | None,
    prefix: str | None,
    suffix: str | None,
    recursive: bool,
    force: bool,
) -> None:
    """使用正则表达式批量重命名文件。

    必须且只能选择 --replace、--prefix、--suffix 中的一项。
    """
    # 编译正则表达式
    try:
        re_pattern = re.compile(pattern)
    except re.error as e:
        logger.error(f"{e}, 正则表达式错误")
        return

    # 验证目标目录
    if not os.path.isdir(directory):
        click.echo("目录不存在")
        return

    # 收集匹配的文件
    file_path_list: list[Path] = []
    path_iter = Path(directory).rglob("*") if recursive else Path(directory).glob("*")
    for file in path_iter:
        if file.is_file() and re_pattern.search(file.name):
            file_path_list.append(file)

    # 确保仅选择了一项操作
    op_count = _count_operations(replace, prefix, suffix)
    if op_count > 1:
        click.echo("只能选择一项重命名操作")
        return
    if op_count == 0:
        click.echo("修改方式未选择，未修改")
        return

    # 对每个文件执行重命名
    for file in file_path_list:
        new_file_name = file.name
        file_dir = os.path.dirname(file)

        if replace is not None:
            new_file_name = re_pattern.sub(replace, file.name)
        elif prefix:
            new_file_name = prefix + file.name
        elif suffix:
            new_file_name = file.stem + suffix + file.suffix

        if new_file_name == file.name:
            continue

        target_path = os.path.join(file_dir, new_file_name)
        if os.path.exists(target_path):
            if os.path.isdir(target_path):
                continue
            if not force and not click.confirm(f"{new_file_name} 已经存在. 是否覆盖:"):
                continue

        try:
            os.replace(file, target_path)
            logger.success(
                f"{os.path.join(file_dir, file.name)} 已成功重命名为 '{new_file_name}'"
            )
        except Exception as e:
            logger.error(e)
            click.echo(f"{file.name} 重命名操作失败")


if __name__ == "__main__":
    try:
        rename_files()
    except ValidationError as e:
        logger.error(e)
