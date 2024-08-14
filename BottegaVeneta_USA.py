import psutil
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup Chrome options
options = Options()
# options.add_argument("--headless")  # Run headless Chrome if you want to hide the browser
options.add_argument("--blink-settings=imagesEnabled=false")  # Disabling the pictures from each item

# Initialize the WebDriver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

offset = 1000

def scroll_load(driver, url, category):
    previous_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight - {offset});")
        time.sleep(2)
        
        # Parse products while scrolling
        new_products = parse_products(driver, category)
        if new_products:
            all_products.extend(new_products)
            logging.info(f"Found {len(new_products)} new products in {category} category.")
            print(f"Found {len(new_products)} new products in {category} category.")
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

def handle_cookie_consent(driver):
    try:
        print("Waiting for the cookie consent pop-up...")
        cookie_consent_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#onetrust-accept-btn-handler"))
        )
        print("Clicking the cookie consent button...")
        cookie_consent_button.click()
        print("Cookie consent accepted.")
    except (TimeoutException, NoSuchElementException):
        print("No cookie consent pop-up found.")

country = 'United State'
scrape_date = datetime.now().strftime('%Y-%m-%d')
all_products = []
unique_ids = set()

# Function for scrapping the items
def parse_products(driver, category):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = soup.find_all('a', class_='c-product__link c-product__focus')
    products = soup.find_all('h2', class_='c-product__name')
    prices = soup.find_all('p', class_='c-price__value--current')

    new_products = []
    for product, price, link in zip(products, prices, links):
        try:
            product_name = product.get_text(strip=True)
            product_price = price.get_text(strip=True)
            product_link = link['href']
            product_id = product_link.split('-')[-1].replace('.html','')

            if product_id not in unique_ids:
                unique_ids.add(product_id)
                new_products.append({
                    'Category': category,
                    'Name': product_name,
                    'Cost': product_price,
                    'ID': product_id,
                    'Country': country,
                    'Scrape Date': scrape_date
                })  
                
        except Exception as e:
            logging.error(f"An error occurred while processing the items: {e}")
    
    return new_products

def save_results(filename):
    global all_products
    output_df = pd.DataFrame(all_products)
    output_df.to_csv(filename, index=False)
    logging.info(f"Saved results to {filename}..")

# List of URLs to navigate and scroll
urls = [
    "https://www.bottegaveneta.com/en-us/search?q=home",
    "https://www.bottegaveneta.com/en-us/search?q=men",
    "https://www.bottegaveneta.com/en-us/search?q=women"
]

try:
    for url in urls:
        category = url.split('=')[-1].capitalize()
        # Navigate to the URL
        print(f"Navigating to {url}...")
        driver.get(url)
        
        # Handle the cookie consent pop-up if present
        handle_cookie_consent(driver)
        
        # Scroll down the page to load all items
        scroll_load(driver, url, category)

    #logging.info(f'All products found: {all_products}')
    #print(f'All products found: {all_products}')
    save_results('Bottega_Veneta_USA.csv')

except Exception as e:
    print('An error occurred, try again...')
    print(f"Error: {e}")
finally:
    driver.quit()
