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

    # close_ad_popup(driver)

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

def click_show_more(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "view-more")))
        click_button_by_class(driver, "view-more")
        # handle_popup(driver)
        time.sleep(2) # wait for content to load
    except TimeoutException:
        print("No more content")
        return False
    return True

def save_product_info(soup, base_url):
    product_info = []

    # Find all products in the list
    products = soup.find_all("li", class_="item ajaxed __cate_42")

    for product in products:
        # Extract and clean phone name
        product_title = product.find("h3").text.strip()
        # Get corresponding link
        relative_link = product.find("a", href=True)["href"]
        # Combine relative link with base URL
        product_link = urljoin(base_url, relative_link)
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
    main_url = r"https://www.thegioididong.com/dtdd"
    base_url = r"https://www.thegioididong.com/"
    columns = ["Title", "Link"]

    driver = init_driver(main_url) # initialize the driver

    while click_show_more(driver): # continue clicking the show more button until there is no more content
        pass

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    product_info = save_product_info(soup, base_url) # save the product's link and title to a list
    df = pd.DataFrame(product_info, columns=columns)

    if not os.path.exists("data"): # create a folder to store the data
        os.mkdir("data")
    
    df.to_csv("data/products_thegioididong.csv", mode='w', encoding="utf-8") # save the data to a csv file
    
    driver.quit()