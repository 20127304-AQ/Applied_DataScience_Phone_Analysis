from bs4 import BeautifulSoup
import pandas as pd
import os
import time

from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

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
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "close")))
        click_button_by_class(driver, "close")
        print("Popup handled")
    except TimeoutException:
        return

def close_ad_popup(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "fpopup")))
        click_button_by_class(driver, "close")
        print("Ad popup closed")
    except TimeoutException:
        print("No ad popup found")
        return

def click_show_more(driver):
    try:
        while True:
            show_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn.btn-light')))
            driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
            show_more_button.click()
            time.sleep(2) # wait for content to load
    except TimeoutException:
        print("No more content")

def save_product_info(soup, base_url):
    product_info = []

    products = soup.find_all("div", class_="cdt-product__info")

    for product in products:
        # Get product's link
        relative_link = product.find("a", href=True)["href"]
        product_link = urljoin(base_url, relative_link)
        # Get product's title
        product_title = product.find("a", class_="cdt-product__name").text.strip()
        product_info.append([product_title, product_link])

    return product_info

def save_link_to_product(driver, base_url):
    product_info = []

    while True:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_info.extend(save_product_info(soup, base_url))
        
        if not click_show_more(driver): # If there are no more products to load, break the loop
            break

    return product_info

if __name__=="__main__":
    main_url = r"https://fptshop.com.vn/dien-thoai"
    base_url = r"https://fptshop.com.vn"
    columns = ["Title", "Link"]

    driver = init_driver(main_url) # initialize the driver

    while click_show_more(driver): # continue clicking the show more button until there is no more content
        pass

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    product_info = save_product_info(soup, base_url) # save the product's link and title to a list
    df = pd.DataFrame(product_info, columns=columns)

    if not os.path.exists("data"): # create a folder to store the data
        os.mkdir("data")
    
    df.to_csv("data/products_fpt.csv", mode='w', encoding="utf-8") # save the data to a csv file
    
    driver.quit()