# CRAWL COMMENTS OR CRAWL TECHNICAL DETAILS IN ONCE. RUNNING THEM SIMULTANEOUSLY MIGHT LEAD TO UNWANTED ERRORS.
# JUST COMMENT THE PART YOU DO NOT NEED IN 'crawl_data' function
from bs4 import BeautifulSoup
import pandas as pd
import csv
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

def click_technical_detail(driver):
    try:
        # Wait for the link to be clickable
        technical_detail_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "re-link.js--open-modal"))
        )
        
        # Scroll to the element
        driver.execute_script("arguments[0].scrollIntoView(true);", technical_detail_link)
        
        # Click the link
        technical_detail_link.click()
        
        # Optionally handle any popups here if necessary
        
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
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@class='pagination pagination-space']//a[contains(@class, 'pagination-link')]/i[@class='cm-ic-angle-right']"))
        )
        return next_button
    except TimeoutException:
        return None

def crawl_comments(driver, name_data):
    comments = []
    check = False
    while True:
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "user-wrapper")))
        except TimeoutException:
            print("Element with class 'user-wrapper' not found. Continuing without it.")
            break

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        user_blocks = soup.find_all('div', class_='user-block')
        for block in user_blocks:
            comment = {}
            comment['used_to_buy'] = 'no'
            comment['phone_name'] = name_data
            user_name = block.find('div', class_='avatar-name').text.strip()
            if "Đã mua tại FPTShop" in user_name:
                user_name = user_name.split("Đã mua tại FPTShop")[0].strip()
                comment['used_to_buy'] = 'yes'
            comment['user_name'] = user_name
            comment['content'] = block.find('div', class_='avatar-para').text.strip()
            
            # Count the number of stars
            star_elements = block.select('.list-star .cm-ic-star.cm-ic-color-warning')
            comment['star_count'] = len(star_elements)
            if comment['star_count'] != 0:
                comments.append(comment)

        next_button = find_next_button(driver)
        if next_button is None or 'disabled' in next_button.get_attribute('class'):
            break
        else:
            next_button.click()
            time.sleep(2)
    return comments


def crawl_data(url, check_header, name_data):
    # Initialize the Selenium webdriver
    driver = init_driver(url)

    try:
        # CRAWL COMMENT
        comments = crawl_comments(driver, name_data)
        print(comments)
        with open('final_comments_fpt.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['phone_name', 'user_name', 'used_to_buy', 'content', 'star_count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header only if the file is empty
            if csvfile.tell() == 0:
                writer.writeheader()

            # Write comments
            writer.writerows(comments)

        # CRAWL TECHINCAL DETAIL
        # Click the technical detail button
        if not click_technical_detail(driver):
            return

        # Wait for the technical detail page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "c-modal__content")))

        # Get the page source after clicking technical detail
        page_source = driver.page_source

        # Use BeautifulSoup to parse the page source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract model information
        model_info = {}

        price_element = soup.find('div', class_='st-price-main')
        if price_element:
            price = price_element.text.strip()
            model_info['Giá tiền'] = price

        rows = soup.find_all('div', class_='c-modal__row')
        for row in rows:
            title_element = row.find('div', class_='st-table-title')
            if title_element:
                title = title_element.text.strip()
                if title not in model_info:
                    model_info[title] = {}

                # Find all key-value pairs in the table
                tables = row.find_all('table', class_='st-table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        key = cols[0].text.strip()
                        value = cols[1].text.strip()
                        model_info[title][key] = value

        temp = {}
        #Xử lý dữ liệu trước khi lưu
        temp['Tên điện thoại'] = name_data
        for x in model_info:
            if x == 'Camera sau' or x == 'Selfie' or x == 'Giá tiền':
                temp[x] = model_info[x]
            else:
                temp.update(model_info[x])

        temp['Link'] = url

        # Chuẩn bị dữ liệu cho ghi
        fieldnames = ['Tên điện thoại','Kích thước màn hình','Chuẩn màn hình','Camera sau','Selfie','Phiên bản CPU','RAM','Bộ nhớ trong','Dung lượng pin','Số khe SIM','Version','Độ phân giải','Tần số quét', 'Giá tiền', 'Link']
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


    finally:
        # Close the webdriver
        driver.quit()

# Path to the CSV file
csv_file_path = 'data/products_fpt.csv'
output_file = 'data/full_data_fpt.csv'

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
        crawl_data(link, check_header, name_data)
        check_header = 1