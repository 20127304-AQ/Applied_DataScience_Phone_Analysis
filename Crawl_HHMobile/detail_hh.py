from bs4 import BeautifulSoup
import pandas as pd
import csv
import os
import time
import json

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
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "close")))
        click_button_by_class(driver, "close")
        print("Popup handled")
    except TimeoutException:
        return
    
def click_technical_detail(driver):
    try:
        # Wait for the link to be clickable
        technical_detail_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "product-specs-button"))
        )

        # Create an action chain for mouse actions
        action = ActionChains(driver)
        
        # Move to the element
        action.move_to_element(technical_detail_link).perform()

        # Click the link
        technical_detail_link.click()
        
        print("Clicked on technical detail link")
        
        # Wait for content to load, if needed
        time.sleep(2)
        
    except TimeoutException:
        print("No more content or link not found")
        return False
    except Exception as e:
        print("Error clicking the element:", e)
        return False
    return True


def find_next_button(driver):
    try:
        # Find the currently active page
        active_page = driver.find_element(By.XPATH, "//div[@class='pagcomment']/span[@class='active']")
        current_page = int(active_page.text)

        # Find the link to the next page
        next_page_xpath = f"//div[@class='pagcomment']/a[@title='trang {current_page + 1}']"
        
        # Check if the next page link exists
        next_page_link = driver.find_elements(By.XPATH, next_page_xpath)
        if next_page_link:
            return next_page_link[0]
        else:
            return None
    except TimeoutException:
        return None

def crawl_comments(driver):
    comments = []

    while True:
        # Wait for the comments section to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "review-content")))

        # Parse the HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find all comment items
        comment_items = soup.find_all('div', class_='item')

        # Iterate over each comment item
        for item in comment_items:
            comment = {}

            # Extract user information
            user_info = item.find('strong', class_='name')
            if user_info:
                comment['user_name'] = user_info.text.strip()

            # Extract comment content
            content_info = item.find('div', class_='content')
            if content_info:
                comment['content'] = content_info.text.strip()

            # Append the comment to the list
            comments.append(comment)

            # Check for replies to the current comment
            reply_items = item.find_all('div', class_='item')
            for reply_item in reply_items:
                reply = {}
                reply_user_info = reply_item.find('strong', class_='name')
                if reply_user_info:
                    reply['user_name'] = reply_user_info.text.strip()
                reply_content_info = reply_item.find('div', class_='content')
                if reply_content_info:
                    reply['content'] = reply_content_info.text.strip()
                comments.append(reply)

        # Check if there's a next page of comments
        pagination = soup.find('ol', class_='pagination')
        if pagination:
            next_page_link = pagination.find('a', string='2')  # Assuming the link for the next page is labeled as '2'
            if next_page_link:
                # Click on the next page link
                driver.execute_script("arguments[0].click();", next_page_link)
                WebDriverWait(driver, 10).until(EC.staleness_of(comment_items[0]))  # Wait for new comments to load
            else:
                break  # No more pages found, exit the loop
        else:
            break  # No pagination found, exit the loop

    return comments


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

def crawl_data(driver, check_header, name_data, url):
    try:
        # Initialize model_info dictionary
        model_info = {}

        price_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "current-product-price"))
        )
        price = price_element.find_element(By.TAG_NAME, "strong").text.strip()
        model_info['Giá tiền'] = price

        # Click the technical detail button
        if not click_technical_detail(driver):
            return

        # Wait for the technical detail page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "table-border")))

        # Get the page source after clicking technical detail
        page_source = driver.page_source

        # Use BeautifulSoup to parse the page source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find all table rows
        table_rows = soup.select('.table-border tr')

        # Iterate over table rows
        category = None
        for row in table_rows:
            th_element = row.find('th')
            if th_element:  # If it's a header row
                category = th_element.find('span', class_='f-16').text.strip()
                model_info[category] = {}
            else:  # If it's a data row
                td_elements = row.find_all('td')
                if len(td_elements) == 2:  # If it's a valid data row
                    title = td_elements[0].text.strip()
                    data = td_elements[1].text.strip()
                    model_info[category][title] = data

        temp = {}
        #Xử lý dữ liệu trước khi lưu
        temp['Tên điện thoại'] = name_data
        for x in model_info:
            if x == 'Camera sau' or x == 'Camera trước' or x == 'Giá tiền':
                temp[x] = model_info[x]
            else:
                temp.update(model_info[x])

        temp['Link'] = url

        # Chuẩn bị dữ liệu cho ghi
        fieldnames = ['Tên điện thoại','Kích thước màn hình','Chuẩn màn hình','Camera sau', 'Camera trước', 'Vi xử lý','Hệ điều hành','RAM','Bộ nhớ trong','Dung lượng pin','Số khe SIM','Độ phân giải','Giá tiền', 'Link']
        for x in fieldnames:
            if x not in temp.keys():
                temp[x] = ''
                if x == 'Chuẩn màn hình' and temp.get('Công nghệ màn hình') is not None:
                    temp[x] = temp['Công nghệ màn hình']
        rows_data = [{key: temp[key] for key in fieldnames}]

        # Ghi dữ liệu từ điển vào tệp CSV
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if check_header == 0:
                writer.writeheader()
                writer.writerows(rows_data)
                check_header = 1
            else:
                writer.writerows(rows_data)
        # print(model_info)

    except Exception as e:
        print("Error:", e)
    finally:
        # Close the webdriver
        driver.quit()

# Path to the CSV file
csv_file_path = 'data/products_hoangha.csv'
output_file = 'data/full_data_hoangha.csv'

# Open the CSV file and iterate through each row to extract links and crawl data
with open(csv_file_path, 'r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip the header row if present
    if os.path.exists(output_file):
        # If the file exists, delete it
        os.remove(output_file)
    print(f"Existing file '{output_file}' deleted.")
    check_header = 0
    for row in csv_reader:
        name_data = row[1]
        link = row[2]  # Assuming the 2nd column contains the link
        
        # Initialize the driver and navigate to the URL
        driver = init_driver(link)
        
        # Call the crawl_data function with the driver instance
        crawl_data(driver, check_header, name_data, link)
        check_header = 1
