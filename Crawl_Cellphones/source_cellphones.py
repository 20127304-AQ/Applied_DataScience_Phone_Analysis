from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime as dt

from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def init_driver(url):
    service = Service(executable_path="chromedriver.exe")

    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(
        service=service,
        options=options)
    
    driver.get(url)
    driver.maximize_window()

    return driver

def click_button_by_class(driver, element):
    button = driver.find_element(By.CLASS_NAME, element)
    button.click()

def move_to_element(driver, element):
    action = ActionChains(driver)
    element = driver.find_element(By.CLASS_NAME, element)
    action.move_to_element(element)
    action.perform()

def handle_popup(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cancel-button-top"))
        )
        click_button_by_class(driver, "cancel-button-top")
        print("Popup handled")
    except:
        return
    
def handle_popup_83(driver):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '(//button[@aria-label="close"])[position()=2]'))
        )
        element.click()
        print("Popup 83 handled")
    except:
        return False
    return True

def click_show_more(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "btn-show-more"))
        )
        click_button_by_class(driver, "btn-show-more")
        move_to_element(driver, "btn-show-more")
        handle_popup(driver)
    except:
        print("No more content")
        return False
    return True

def save_link_to_product(driver, base_url):
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    products = soup.find_all("div", class_="product-info", limit=None)
    product_info = []
    for product in products:
        relative_link = product.find("a", class_="product__link button__link").get("href")
        product_link = urljoin(base_url, relative_link)
        product_title = product.find("div", class_="product__name").find('h3').text
        product_info.append([product_title, product_link])

    return product_info

if __name__ == "__main__":
    main_url = r"https://cellphones.com.vn/mobile.html"
    base_url = r"https://cellphones.com.vn/"
    columns = ["Title", "Link"]
    current_day = dt.now().day
    current_month = dt.now().month

    driver = init_driver(main_url)

    while handle_popup_83(driver):
        pass
    
    while click_show_more(driver):
        pass

    product_info = save_link_to_product(driver, base_url)
    df = pd.DataFrame(product_info, columns=columns)

    data_path = f"data/products_cellphones_{current_day}_{current_month}.csv"
    
    if not os.path.exists("data"):
        os.mkdir("data")
    df.to_csv(data_path, mode='w', encoding="utf-8")
    
    driver.quit()
