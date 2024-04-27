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
from selenium.common.exceptions import NoSuchElementException, TimeoutException

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

def click_technical_detail(driver):
    try:
        # Wait for the link to be clickable
        technical_detail_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-detail"))
        )
        
        # Scroll to the element
        driver.execute_script("arguments[0].scrollIntoView(true);", technical_detail_link)
        
        # Click the link
        technical_detail_link.click()
        
        print("Clicked on technical detail link")
        
        # Optionally handle any popups here if necessary
        
        # Wait for content to load, if needed
        time.sleep(2)
        
    except TimeoutException:
        print("No more content or link not found")
        return False
    except Exception as e:
        print("Error clicking the element:", e)
        return False
    return True

def click_next_page(driver):
    try:
        # Find the next page button by its xpath
        next_page_button = driver.find_element(By.XPATH, "//div[@class='pagcomment']//a[contains(text(), '›')]")

        # Scroll to the element
        driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)

        # Click the button to go to the next page
        next_page_button.click()

        print("Clicked on the next page button")
    except NoSuchElementException:
        print("Next page button not found")
        return False  # Return False to indicate failure to click the button
    except Exception as e:
        print("Error clicking the next page button:", e)
        return False  # Return False to indicate failure to click the button

    return True  # Return True to indicate successful click

def click_view_all_reviews(driver):
    try:
        # Find the "Xem tất cả đánh giá" button by its class name
        view_all_button = driver.find_element(By.CLASS_NAME, "btn-view-all")

        # Click the button to view all reviews
        view_all_button.click()

        print("Clicked on 'Xem tất cả đánh giá' button")
    except NoSuchElementException:
        print("Button 'Xem tất cả đánh giá' not found")
        # If the button is not found, start crawling the page immediately
        return

def crawl_comments(html_content, name_data):
    comments = []

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all comment items
    comment_items = soup.select('.comment-list .par')

    for item in comment_items:
        comment = {}
        comment['phone_name'] = name_data

        # Extract user name
        user_name = item.find(class_='cmt-top-name').text.strip()
        comment['user_name'] = user_name

        # Extract comment content
        content = item.find(class_='cmt-txt').text.strip()
        comment['content'] = content

        # Extract star rating
        star_count = len(item.select('.cmt-top-star .iconcmt-starbuy'))
        comment['star_rating'] = star_count

        comments.append(comment)

    return comments

def clean_model_info(model_info):
    cleaned_model_info = {}
    for category, details in model_info.items():
        # Check if details is a string
        if isinstance(details, str):
            # Remove unwanted '\n' characters and unnecessary whitespaces from the string
            cleaned_value = details.replace('\n', '').strip()
            cleaned_model_info[category] = cleaned_value
        else:
            # If details is a dictionary, remove unwanted '\n' characters and unnecessary whitespaces from the values
            cleaned_details = {}
            for key, value in details.items():
                cleaned_value = value.replace('\n', '').strip()
                cleaned_details[key] = cleaned_value
            cleaned_model_info[category] = cleaned_details
    return cleaned_model_info


def crawl_data(url, check_header, name_data):
    # Initialize the Selenium webdriver
    driver = init_driver(url)

    try:
        # COMMENT CRAWLING
        click_view_all_reviews(driver)
        time.sleep(2)
        
        # Write CSV header only if it's the first iteration
        if check_header == 0:
            with open('comments_tgdd.csv', 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['phone_name', 'user_name', 'content', 'star_rating']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()  # Write CSV header

        # Crawl comments from all pages
        page_num = 1
        while True:
            # Crawl comments from the current page
            comments = crawl_comments(driver.page_source, name_data)
            print(comments)

            # Write comments to CSV file
            with open('comments_tgdd.csv', 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['phone_name', 'user_name', 'content', 'star_rating']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for comment in comments:
                    writer.writerow(comment)

            page_num += 1  # Increment page number

            # Click on the next page link
            if not click_next_page(driver):
                break  # Exit the loop if there's no next page link or failed to click the button

            # Wait for the page to load after clicking the link
            time.sleep(2)  # Adjust the waiting time as needed

        # TECHNICAL CRAWLING
        # Click the technical detail button
        if not click_technical_detail(driver):
            return
        
        # Wait for the sub-technical detail page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tab-specification-gallery-0")))

        # Click on the sub-technical detail tab
        spec_tab = driver.find_element(By.ID, "tab-specification-gallery-0")
        spec_tab.click()

        # Wait for the technical detail page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "parameter-all")))

        # Get the page source after clicking technical detail
        page_source = driver.page_source

        # Use BeautifulSoup to parse the page source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract model information
        model_info = {}

        price_element = soup.find(class_='box-price-present')
        if price_element:
            price = price_element.text.strip()
            model_info['Giá tiền'] = price

        # Find all parameter items
        parameter_items = soup.find_all(class_="parameter-item")

        # Iterate through each parameter item
        for item in parameter_items:
            title = item.find(class_="parameter-ttl").text.strip()
            model_info[title] = {}

            # Find all list items under this parameter item
            list_items = item.find_all("li")
            for li in list_items:
                left_text = li.find(class_="ctLeft").text.strip()
                right_text = li.find(class_="ctRight").text.strip()
                model_info[title][left_text] = right_text

        # Remove \n from dictionary model_info
        model_info = clean_model_info(model_info)
        
        temp = {}
        #Xử lý dữ liệu trước khi lưu
        temp['Tên điện thoại'] = name_data
        for x in model_info:
            if x == 'Camera sau' or x == 'Camera trước' or x == 'Giá tiền':
                temp[x] = model_info[x]
            else:
                temp.update(model_info[x])

        temp['Link'] = url

        # Preparation for data
        fieldnames = ['Tên điện thoại', 'Màn hình rộng:','Chuẩn màn hình:','Camera sau','Camera trước','Hệ điều hành:','Chip xử lý (CPU):', 'RAM:','Dung lượng lưu trữ:','Dung lượng pin:','SIM:','Độ phân giải:', 'Giá tiền', 'Link']
        for x in fieldnames:
            if x not in temp.keys():
                temp[x] = ''
                if x == 'Chuẩn màn hình:' and temp.get('Công nghệ màn hình:') is not None:
                    temp[x] = temp['Công nghệ màn hình:']
        rows_data = [{key: temp[key] for key in fieldnames}]

        # Write data to .csv
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if check_header == 0:
                writer.writeheader()
                writer.writerows(rows_data)
                check_header = 1
            else:
                writer.writerows(rows_data)

    finally:
        # Close the webdriver
        driver.quit()

# Path to the CSV file
csv_file_path = 'data/products_thegioididong.csv'
output_file = 'data/full_data_tgdd.csv'

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
