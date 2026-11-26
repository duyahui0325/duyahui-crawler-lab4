# -*- coding: utf-8 -*-
"""
实验4 公共工具模块
==================
把两个爬虫都要用到的功能集中在这里，避免代码重复：

1. create_driver()  —— 创建并配置 Edge 浏览器对象（Service + Options 写法）；
2. save_csv()       —— 把二维列表保存成 CSV 文件；
3. save_excel()     —— 把二维列表保存成带表头样式的 Excel 文件；
4. format_duration()—— 把秒数格式化成“X 分 Y 秒”，用来统计运行耗时。
"""

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

# ---------------------------------------------------------------------------
# 本机环境配置：换成自己电脑上的路径即可
# ---------------------------------------------------------------------------
EDGE_BINARY = r"C:\Program Files (x86)\Microsoft\EdgeCore\158.0.4370.33\msedge.exe"
EDGE_DRIVER = r"D:\msedgedriver64\msedgedriver.exe"

# 所有数据文件统一放在脚本同级的 data 目录下
DATA_DIR = Path(__file__).resolve().parent / "data"


def create_driver(headless=False):
    """创建 Edge WebDriver。

    - Service 指定 msedgedriver.exe 的路径（对应实验要求里的“驱动路径”）；
    - Options 里指定 Edge 浏览器的安装路径、启动时最大化窗口、中文语言；
    - 去掉“Microsoft Edge 正受到自动测试软件的控制”提示条，界面更干净。
    """
    options = Options()
    if Path(EDGE_BINARY).exists():          # 找不到就用系统默认的 Edge，保证可移植
        options.binary_location = EDGE_BINARY
    if headless:                            # 需要无界面运行时打开
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--lang=zh-CN")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(executable_path=EDGE_DRIVER)
    driver = webdriver.Edge(service=service, options=options)
    driver.set_page_load_timeout(60)        # 页面加载最多等 60 秒
    return driver


def save_csv(rows, header, filename):
    """把数据保存成 CSV 文件，返回文件路径。

    编码使用 utf-8-sig（带 BOM），这样用 Excel 直接双击打开时中文不会乱码。
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.writer(fp)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"CSV 已保存：{path}（{len(rows)} 行数据）")
    return path


def save_excel(rows, header, filename, sheet_name="Sheet1"):
    """把数据保存成 Excel 文件，返回文件路径。

    顺手做了一点格式化：表头加粗白字、深蓝底色、居中，并按内容自适应列宽。
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(header)
    for row in rows:
        sheet.append(row)

    # 表头样式
    head_font = Font(bold=True, color="FFFFFF", size=11)
    head_fill = PatternFill("solid", fgColor="1F4E79")
    for cell in sheet[1]:
        cell.font = head_font
        cell.fill = head_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # 列宽自适应：中文按 2 个字符宽度粗略估算
    for col_index, title in enumerate(header, start=1):
        width = _display_width(title)
        for row in rows:
            width = max(width, _display_width(row[col_index - 1]))
        sheet.column_dimensions[get_column_letter(col_index)].width = min(50, max(10, width + 4))

    sheet.freeze_panes = "A2"               # 冻结表头，方便查看
    workbook.save(path)
    print(f"Excel 已保存：{path}（{len(rows)} 行数据）")
    return path


def _display_width(text):
    """估算字符串在 Excel 中占用的宽度：中文等全角字符按 2 个字符计算。"""
    return sum(2 if ord(char) > 127 else 1 for char in str(text))


def format_duration(seconds):
    """把秒数格式化为易读的字符串。"""
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds} 秒"
    return f"{seconds // 60} 分 {seconds % 60} 秒"
