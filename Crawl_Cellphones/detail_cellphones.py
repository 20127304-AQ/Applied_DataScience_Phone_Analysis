import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def init_driver(url):
    service = Service(executable_path="chromedriver.exe")

    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(
        service=service,
        options=options)
    
    driver.get(url)
    driver.maximize_window()

    return driver

def move_to_element(driver, element):
    action = ActionChains(driver)
    element = driver.find_element(By.CLASS_NAME, element)
    action.move_to_element(element)
    action.perform()

def save_link_to_product(driver, link, name):
    # brand name
    brand_name = name.split(" ")[0]

    # for oppo reno 11 f only (special page)
    if link == "https://cellphones.com.vn/dien-thoai-oppo-reno-11-f.html":
        move_to_element(driver, 'cps-container')
        time.sleep(5)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # original price 
        span_tag = soup.find('span', {'class': 'text-price'})
        original_price = span_tag.strong.get_text().replace("đ", "").replace(".", "").strip()

        # product info
        ul_element = soup.find('ul', {'class': 'technical-content'})
        li_elements = ul_element.find_all('li')

        data_info = {}
        
        for li in li_elements: 
            p_tag = li.find('p')
            div_tag = li.find('div')

            key = p_tag.get_text()
            value = div_tag.get_text()

            data_info[key] = value
        
        result = [name, brand_name, original_price, None, None, None, data_info, link]
        driver.close()
        return result
    
    # scroll down to get the needed information
    attempt = 1
    max_attempts = 3

    while attempt <= max_attempts:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@class="box-more-promotion my-3"]'))
            )
            driver.execute_script("arguments[0].scrollIntoView();", element)

            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@class="block-same-product"]'))
            )
            driver.execute_script("arguments[0].scrollIntoView();", element)

            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@class="technical-content"]'))
            )
            driver.execute_script("arguments[0].scrollIntoView();", element)

            break
        except:
            print("Refreshing ")
            attempt += 1
            driver.refresh()

    # Get the page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # original price (tpt---sale-price) // product__price--show
    try:
        original_price = soup.find_all('p', {"class": 'tpt---sale-price'})
        if len(original_price) > 0:
            original_price = soup.find_all('p', {"class": 'tpt---sale-price'})[1].get_text()\
                .replace("đ", "").replace(".", "").strip()
        else:
            original_price = soup.find('p', {"class": 'product__price--show'}).get_text()\
                .replace("đ", "").replace(".", "").strip()
    except:
        original_price = None

    # discount price (tpt---price) // product__price--through
    try:
        discount_price = soup.find_all('p', {"class": 'tpt---price'})
        if len(discount_price) > 0:
            discount_price = soup.find_all('p', {"class": 'tpt---price'})[0].get_text()\
                .replace("đ", "").replace(".", "").strip()
        else:
            discount_price = soup.find('p', {"class": 'product__price--through'}).get_text()\
                .replace("đ", "").replace(".", "").strip()
    except:
        discount_price = None
        
    # star_rating
    try:
        star_rating = soup.find('p', {"class": 'title is-4 m-0 p-0'}).get_text()
    except AttributeError:
        star_rating = None

    # rewview_count
    try:
        review_count = soup.find('p', {"class": 'boxReview-score__count'})
        review_count = review_count.find('strong').get_text()
    except AttributeError:
        review_count = None

    # product info
    ul_element = soup.find('ul', {'class': 'technical-content'})
    li_elements = ul_element.find_all('li')

    data_info = {}

    for li in li_elements: 
        p_tag = li.find('p')
        div_tag = li.find('div')

        key = p_tag.get_text(strip=True)
        value = div_tag.get_text(strip=True)

        data_info[key] = value

    result = [name, brand_name, discount_price, original_price,  
              star_rating, review_count, data_info, link]
    
    driver.close()
    return result

def main():
    product_info_header = [
        "product_name", "brand_name", "original_price", "discount_price", 
        "rating", "review_count", "specs_info", "link"
    ]
    df_products = pd.DataFrame(columns=product_info_header)
    df_products.to_csv("data/product_info_new.csv", header=True, index=False)

    df = pd.read_csv("data/your_data.csv")  # Change "your_data.csv" to your file name
    count = 0
    data = []

    for index, row in df.iterrows():
        link, name = row["Link"], row["Title"]
        driver = init_driver(link)
        
        new_product = save_link_to_product(driver, link, name)
        data.append(new_product)

        print(f"Done row {count}/{len(df)}")

        count += 1
        if count % 2 == 0:
            df_new_products = pd.DataFrame(data, columns=product_info_header)
            df_new_products = pd.concat([df_products, df_new_products], ignore_index=True)
            df_new_products.to_csv("data/product_info_new.csv", mode='a', encoding="utf-8", header=False, index=False)
            # reset the data batch
            data = []

if __name__ == "__main__":
    main()
