# -*- coding: utf-8 -*-
"""
任务三：Selenium 自动登录网站，并把登录后的信息爬取下来
==========================================================
演示站点：https://www.saucedemo.com/
    这是 Sauce Labs 官方提供的在线练习站，用户名、密码公开写在登录页上
    （standard_user / secret_sauce），每次登录的数据都一样，不会涉及个人隐私，
    特别适合练习“登录 + 页面跳转 + 数据抓取 + 存储”的完整流程。

实现步骤：
    1. 打开登录页，用 By.ID 定位用户名、密码输入框和登录按钮；
    2. send_keys() 输入账号密码，click() 提交；
    3. 显式等待 URL 跳到 inventory.html，确认登录成功，保存一张登录成功截图；
    4. 解析商品列表里 6 件商品的名称、描述、价格；
    5. 保存成 CSV 和 Excel。
"""

import re
import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from spider_utils import DATA_DIR, create_driver, format_duration, save_csv, save_excel

LOGIN_URL = "https://www.saucedemo.com/"
USERNAME = "standard_user"
PASSWORD = "secret_sauce"
WAIT = 20
HEADER = ["商品名称", "商品描述", "价格(美元)"]


def login(driver):
    """输入账号密码并提交，返回登录成功后的页面标题。"""
    driver.get(LOGIN_URL)
    # 等登录框可见，避免元素还没渲染出来就去定位
    WebDriverWait(driver, WAIT).until(EC.visibility_of_element_located((By.ID, "user-name")))

    driver.find_element(By.ID, "user-name").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "login-button").click()

    # 登录成功的标志：页面 URL 从根路径跳到 inventory.html
    WebDriverWait(driver, WAIT).until(EC.url_contains("inventory.html"))
    return driver.title


def parse_products(driver):
    """解析商品列表，每个商品返回 [名称, 描述, 价格]。"""
    products = []
    for item in driver.find_elements(By.CSS_SELECTOR, ".inventory_item"):
        name = item.find_element(By.CSS_SELECTOR, ".inventory_item_name").text.strip()
        desc = item.find_element(By.CSS_SELECTOR, ".inventory_item_desc").text.strip()
        price_text = item.find_element(By.CSS_SELECTOR, ".inventory_item_price").text.strip()
        price = float(re.sub(r"[^\d.]", "", price_text))       # 去掉 "$" 只保留数字
        products.append([name, desc, price])
    return products


def main():
    start = datetime.now()
    print("=" * 64)
    print("自动登录爬取开始：", start.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 64)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    driver = create_driver()
    try:
        title = login(driver)
        print(f"登录成功！页面标题：{title}")
        print(f"当前地址：{driver.current_url}")

        time.sleep(1)                       # 等商品图片加载完，截图更好看
        shot_path = DATA_DIR / "login_success.png"
        driver.save_screenshot(str(shot_path))
        print(f"登录成功截图已保存：{shot_path}")

        products = parse_products(driver)
        for index, (name, desc, price) in enumerate(products, start=1):
            print(f"  {index}. {name} | {desc[:34]}… | ${price}")
    finally:
        driver.quit()

    save_csv(products, HEADER, "saucedemo_products.csv")
    save_excel(products, HEADER, "saucedemo_products.xlsx", sheet_name="商品列表")

    end = datetime.now()
    print("-" * 64)
    print(f"共采集 {len(products)} 件商品，总耗时 {format_duration((end - start).total_seconds())}")


if __name__ == "__main__":
    main()
