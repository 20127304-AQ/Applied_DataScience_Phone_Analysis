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

    handle_popup(driver)  # Check and handle popup if it appears immediately
    handle_popup_ads_2(driver)
    
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
        popup = driver.find_element(By.CSS_SELECTOR, "a.close-modal")
        if popup.is_displayed():
            popup.click()
            print("Popup handled")
    except TimeoutException:
        print("Popup not found or not displayed")
        return
    
def handle_popup_ads_1(driver):
    try:
        # Wait for the popup to appear
        popup = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ins-element-close-button"))
        )
        if popup.is_displayed():
            popup.click()
            print("Popup handled")
    except TimeoutException:
        print("Popup not found or not displayed within the timeout period")
        return
    
def handle_popup_ads_2(driver):
    try:
        # Wait for the popup to appear
        popup = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.closeAdsFooter"))
        )
        if popup.is_displayed():
            popup.click()
            print("Popup handled")
    except TimeoutException:
        print("Popup not found or not displayed within the timeout period")
        return

def click_show_more(driver):
    try:
        handle_popup_ads_1(driver)
        more_product_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "more-product"))
        )
        # Check if there are more products
        if "Không còn sản phẩm nào" in more_product_button.text:
            print("No more products available")
            return False
        else:
            more_product_button.click()
            time.sleep(2) # wait for content to load
            return True
    except TimeoutException:
        print("No more content")
        return False

# def save_product_info(soup, base_url):
#     product_info = []

#     # Find all products in the list
#     products = soup.find_all("div", class_="item")

#     for product in products:
#         # Extract phone name
#         product_title = product.find("a", class_="title").text.strip()

#         # Get corresponding link
#         relative_link = product.find("a", href=True)["href"]
#         # Combine relative link with base URL
#         product_link = urljoin(base_url, relative_link)

#         product_info.append([product_title, product_link])

#     return product_info

def save_product_info(soup, base_url):
    product_info = []

    # Find all products in the list
    products = soup.find_all("div", class_="item")

    for product in products:
        # Extract phone name if available
        product_title_element = product.find("a", class_="title")
        if product_title_element:
            product_title = product_title_element.text.strip()
        else:
            product_title = "N/A"

        # Get corresponding link if available
        product_link_element = product.find("a", href=True)
        if product_link_element:
            relative_link = product_link_element["href"]
            # Combine relative link with base URL
            product_link = urljoin(base_url, relative_link)
        else:
            product_link = "N/A"

        product_info.append([product_title, product_link])
    product_info = [info for info in product_info if info.count("N/A") == 0]
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
    main_url = r"https://hoanghamobile.com/dien-thoai-di-dong"
    base_url = r"https://hoanghamobile.com/"
    columns = ["Title", "Link"]

    driver = init_driver(main_url) # initialize the driver

    while click_show_more(driver): # continue clicking the show more button until there is no more content
        pass

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    product_info = save_product_info(soup, base_url) # save the product's link and title to a list
    df = pd.DataFrame(product_info, columns=columns)

    if not os.path.exists("data"): # create a folder to store the data
        os.mkdir("data")
    
    df.to_csv("data/products_hoangha.csv", mode='w', encoding="utf-8") # save the data to a csv file
    
    driver.quit()