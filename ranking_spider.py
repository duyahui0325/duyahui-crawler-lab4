# -*- coding: utf-8 -*-
"""
任务二：模拟鼠标翻页，爬取“软科中国大学排名 2025”
====================================================
目标网页：https://www.shanghairanking.cn/rankings/bcur/2025
网页特点：表格数据是浏览器执行 JavaScript 后异步渲染出来的，直接用 requests
          拿到的 HTML 里没有排名行，所以必须用 Selenium 驱动真实浏览器。

实现步骤：
    1. 启动 Edge 并打开排名页面；
    2. 用 WebDriverWait 显式等待表格的 tbody 中出现数据行；
    3. 解析当前页的 30 行数据（排名、学校名、英文名、标签、省市、类型、总分、办学层次）；
    4. 用 ActionChains 把鼠标移动到“下一页”按钮上并点击，配合“页码变化”等待，
       循环翻完 20 页；
    5. 589 条数据同时保存成 CSV 和 Excel，并打印总耗时。
"""

import time
from datetime import datetime

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from spider_utils import create_driver, format_duration, save_csv, save_excel

URL = "https://www.shanghairanking.cn/rankings/bcur/2025"
HEADER = ["排名", "学校名称", "英文名称", "学校标签", "省市", "办学类型", "总分", "办学层次"]
MAX_PAGE = 20          # 2025 年共 20 页，作为兜底，防止死循环
WAIT = 20              # 等待单个元素出现的最长秒数


def text_of(element, css):
    """取 element 下第一个匹配 css 的子元素的文本，找不到时返回空字符串。"""
    found = element.find_elements(By.CSS_SELECTOR, css)
    return found[0].text.strip() if found else ""


def parse_row(tr):
    """解析表格中的一行 <tr>，返回一条记录的列表；不是数据行时返回 None。"""
    tds = tr.find_elements(By.TAG_NAME, "td")
    if len(tds) < 6:
        return None
    # 排名单元格里是 <div class="ranking">1</div>，取不到时退回单元格文本
    rank = text_of(tds[0], ".ranking") or tds[0].text.strip()
    score = tds[4].text.strip()
    level = tds[5].text.strip()
    return [
        int(rank) if rank.isdigit() else rank,      # 排名
        text_of(tds[1], ".name-cn"),                # 学校中文名
        text_of(tds[1], ".name-en"),                # 学校英文名
        text_of(tds[1], "p.tags"),                  # 学校标签，如“双一流/985/211”
        tds[2].text.strip(),                        # 省市
        tds[3].text.strip(),                        # 办学类型
        float(score) if score else "",              # 总分
        float(level) if level else "",              # 办学层次
    ]


def parse_current_page(driver):
    """解析当前页的所有数据行。"""
    rows = []
    for tr in driver.find_elements(By.CSS_SELECTOR, "table tbody tr"):
        row = parse_row(tr)
        if row is not None:
            rows.append(row)
    return rows


def current_page_no(driver):
    """读取分页条上当前高亮的页码。"""
    active = driver.find_element(By.CSS_SELECTOR, ".ant-pagination-item-active")
    return int(active.text.strip())


def click_next_page(driver):
    """模拟鼠标移动到“下一页”按钮并点击；已经是最后一页时返回 False。"""
    next_btn = driver.find_element(By.CSS_SELECTOR, ".ant-pagination-next")
    if "ant-pagination-disabled" in (next_btn.get_attribute("class") or ""):
        return False

    old_page = current_page_no(driver)
    # 按钮在页面下方，先滚动到可视区域，再用 ActionChains 模拟真实鼠标
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
    time.sleep(0.3)
    ActionChains(driver).move_to_element(next_btn).pause(0.2).click().perform()

    # 等待：页码变化说明翻页成功，且新一页的表格已经渲染出来
    WebDriverWait(driver, WAIT).until(lambda d: current_page_no(d) != old_page)
    WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    time.sleep(0.8)                    # 给表格渲染留一点余量
    return True


def main():
    start = datetime.now()
    print("=" * 64)
    print("软科中国大学排名 2025 爬取开始：", start.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 64)

    driver = create_driver()
    all_rows = []
    try:
        driver.get(URL)
        # 动态网页必须等待：等 tbody 里出现第一个数据行再开始解析
        WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        time.sleep(2)                  # 等首屏渲染和图片加载稳定

        page = 1
        while True:
            time.sleep(0.5)
            rows = parse_current_page(driver)
            all_rows.extend(rows)
            print(f"第 {page:>2} 页：{len(rows):>2} 条，累计 {len(all_rows):>3} 条")
            if page >= MAX_PAGE or not click_next_page(driver):
                break
            page += 1
    finally:
        driver.quit()                  # 无论成功失败都要关闭浏览器，避免驱动进程残留

    save_csv(all_rows, HEADER, "shanghai_ranking_2025.csv")
    save_excel(all_rows, HEADER, "shanghai_ranking_2025.xlsx", sheet_name="2025中国大学排名")

    end = datetime.now()
    print("-" * 64)
    print(f"共采集 {len(all_rows)} 条数据，总耗时 {format_duration((end - start).total_seconds())}")
    print("结束时间：", end.strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
