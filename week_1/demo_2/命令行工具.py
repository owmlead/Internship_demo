import os
import re
import click
from pydantic import validate_call, ValidationError
from loguru import logger
from pathlib import Path

logger.add("log/log_cil.txt", rotation="500 MB", retention="10 days")


@click.command()
@click.option('--directory', '-d', default='.', help='目标目录，默认为当前目录')
@click.option('--pattern', '-p', default='.*', help='使用正则表达式匹配文件名）')
@click.option('--replace', '-r', help='将文件名中的旧字符串替换为空（删除）')
@click.option('--prefix', help='添加前缀')
@click.option('--suffix', help='添加后缀（在扩展名之前）')
@click.option('--recursive', is_flag=True, help='是否递归处理子目录')
@click.option('--force', is_flag=True, help='强制覆盖已存在的文件')
@validate_call
def files_rename(directory: str, pattern: str,replace, prefix, suffix, recursive: bool,
                 force: bool ):
    """
       批量重命名文件工具。使用glob通配符进行匹配
    """

    if  replace=='':
        click.echo(f"无需修改")
        return
    else:
        if not bool(replace):
            replace = ''

    try:
        re_pattern =re.compile(pattern)
        re_replace =re.compile(replace)
    except re.error as e:
        logger.error(f"e,正则表达式错误")
        return

    file_path_list = []
    if not os.path.exists(directory):
        click.echo(f"目录不存在")
        return

    if recursive:
        files_path_list = Path(directory).rglob("*")
        for file in files_path_list:
            if file.is_file() and re_pattern.search(file.name):
                file_path_list.append(file)
    else:
        files_path_list = Path(directory).glob("*")
        for file in files_path_list:
            if file.is_file() and re_pattern.search(file.name):
                file_path_list.append(file)

    if not bool(replace) + bool(prefix) + bool(suffix) <= 1:
        click.echo(f"只能选择一项重命名操作")
        return
    if bool(replace) + bool(prefix) + bool(suffix) == 0:
        click.echo(f"修改方式未选择,未修改")
        return

    for file in file_path_list:
        new_file_name = file.name
        file_dir = os.path.dirname(file)
        if bool(replace):
            new_file_name = re_replace.sub( '', file.name)
        if bool(prefix):
            new_file_name = prefix + file.name
        if bool(suffix):
            new_file_name = file.stem + suffix + file.suffix
        if new_file_name == file.name:
            continue
        if os.path.isfile(os.path.join(file_dir,new_file_name)):
            if not force:
                if not click.confirm(f"{new_file_name}已经存在.是否覆盖:"):
                    continue
        try:
            os.replace(file, os.path.join(file_dir, new_file_name))
            logger.success(f"{os.path.join(file_dir,file.name)}已成功重命名为 '{new_file_name}'")
        except Exception as e:
            logger.error(e)
            click.echo(f"{file.name}重命名操作失败")
    return


if __name__ == '__main__':
    try:
        files_rename()
    except ValidationError as e:
        logger.error(e)

# @validate_call
# def newnamefile(url: str, name: str) -> None:
#     if not os.path.exists(url):
#         logger.error(f"{url}地址错误,文件不存在")
#         click.echo(f"{url}地址错误,文件不存在")
#     else:
#         # url_head=re.sub(r"[\\/][^\\/]+$","",url)
#         url_head = os.path.dirname(url)
#         target_path = os.path.join(url_head, name)
#         if not os.path.exists(url_head):
#             os.makedirs(url_head, exist_ok=True)
#         if os.path.exists(target_path):
#             if click.confirm(f"{target_path}已经存在.是否覆盖:"):
#                 os.replace(url, target_path)
#                 logger.success(f"{url}已覆盖为 '{target_path}'")
#                 click.echo(f"已覆盖为 '{target_path}'")
#             else:
#                 logger.info("操作已取消。")
#                 click.echo("操作已取消。")
#                 return
#         else:
#             os.replace(url, target_path)
#             logger.success(f"{url}已成功重命名为 '{target_path}'")
#             click.echo(f"已成功重命名为 '{target_path}'")


# if __name__ == '__main__':
#     try:
#         # newnamefile()
#         files_rename()
#     except ValidationError as e:
#         logger.error(e)

# print(os.path.dirname('E:/Clash.Verge/Clash.Verge_2.5.1_x64-setup.exe'))
# print(re.search(r'^(.*)[\\/]','E:/Clash.Verge/Clash.Verge_2.5.1_x64-setup.exe').group())
# print(re.sub(r"[\\/][^\\/]+$","",'E:/Clash.Verge/Clash.Verge_2.5.1_x64-setup.exe'))
