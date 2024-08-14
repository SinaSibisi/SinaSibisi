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
options.add_argument("--headless")  # Run headless Chrome if you want to hide the browser
options.add_argument("--blink-settings=imagesEnabled=false")

# Initialize the WebDriver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

# Global variables
all_products = []
unique_ids = set()
item_count = 0
country = "United States"
scrape_date = datetime.now().strftime('%Y-%m-%d')

# Function to monitor memory usage
def monitor_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    return memory_info.rss / (1024 * 1024)  # Memory usage in MB

def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )
#Function to scroll and load more items which is dependent on the size of the window.
def scroll_to_load_items(driver, category):
    previous_product_count = 0
    while True:
         scroll_height = driver.execute_script("return document.body.scrollHeight")
         initial_increment = scroll_height // 10  # Divide the scroll into smaller increments
         current_position = 0

         while current_position < scroll_height:
             increment = initial_increment
             driver.execute_script(f"window.scrollBy(0, {increment});")
             current_position += increment
             time.sleep(5)  # Increase delay to allow new items to load

            # Parse products while scrolling
             new_products = parse_products(category)
             if new_products:
                 all_products.extend(new_products)
                 logging.info(f"Found {len(new_products)} new products in {category} category.")
        
         new_scroll_height = driver.execute_script("return document.body.scrollHeight")
         if new_scroll_height == scroll_height:  # Check if no new items are loaded
             break

         # Check if new products were added after scrolling
         if len(all_products) == previous_product_count:
             break
         previous_product_count = len(all_products)

#Scraping the products in the HTML
def parse_products(category):
    global item_count
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = soup.find_all('a', class_='cta-link-primary redesigned-product-card__link')
    products = soup.find_all('div', class_='product-card-title product-card-content__title')
    prices = soup.find_all('span', class_='product-card-price__current-price')

    new_products = []
    for product, price, link in zip(products, prices, links):
        try:
            product_name = product.get_text(strip=True)
            product_price = price.get_text(strip=True)
            product_link = link['href']
            product_id = product_link.split('-')[-1]

            if product_id not in unique_ids:
                unique_ids.add(product_id)
                new_products.append({
                    'Name': product_name,
                    'Cost': product_price,
                    'ID': product_id,
                    'Category': category,  # Using category as the search term
                    'Country': country,    # Adding country information
                    'Scrape Date': scrape_date # Adding scrape date
                })
                item_count += 1

        except Exception as e:
            logging.error(f"An error occurred while processing the items: {e}")
    
    return new_products

def scroll_to_top_and_search_again(driver, search_term):
    try:
        # Scroll back to the top
        print("Scrolling back to the top...")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(4)

        # Wait for the "Search again" button to be clickable and click it
        print("Waiting for the 'Search again' button to be clickable...")
        search_again_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='search-again']"))
        )
        print("Clicking the 'Search again' button...")
        search_again_button.click()

        # Wait for the search input to be visible
        print("Waiting for the search input to be visible...")
        search_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='search'][aria-label='Search']"))
        )

        # Input the search term and simulate pressing Enter
        print(f"Searching for '{search_term}'...")
        search_input.clear()
        search_input.send_keys(search_term)
        search_input.send_keys(Keys.RETURN)

        # Wait for the search results page to load
        print("Waiting for the search results page to load...")
        wait_for_page_load(driver)
        time.sleep(6)

        # Scroll to load all items
        scroll_to_load_items(driver, search_term)
        print(f"All items for '{search_term}' have been loaded.")
    except TimeoutException as e:
        print(f"TimeoutException occurred: {e}")
    except ElementClickInterceptedException as e:
        print(f"ElementClickInterceptedException occurred: {e}")
    except NoSuchElementException as e:
        print(f"NoSuchElementException occurred: {e}")
    except Exception as e:
        print(f"An error occurred during the search: {e}")

def search_items(driver, search_term):
    try:
        # Wait for the search button to be clickable and click it
        print("Waiting for the search button to be clickable...")
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='button-search']"))
        )
        print("Clicking the search button...")
        search_button.click()

        # Wait for the search input to be visible
        print("Waiting for the search input to be visible...")
        search_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='search'][aria-label='Search']"))
        )

        # Input the search term and simulate pressing Enter
        print(f"Searching for '{search_term}'...")
        search_input.clear()
        search_input.send_keys(search_term)
        search_input.send_keys(Keys.RETURN)

        # Wait for the search results page to load
        print("Waiting for the search results page to load...")
        wait_for_page_load(driver)
        time.sleep(6)

        # Scroll to load all items
        scroll_to_load_items(driver, search_term)
        print(f"All items for '{search_term}' have been loaded.")
    except TimeoutException as e:
        print(f"TimeoutException occurred: {e}")
    except ElementClickInterceptedException as e:
        print(f"ElementClickInterceptedException occurred: {e}")
    except NoSuchElementException as e:
        print(f"NoSuchElementException occurred: {e}")
    except Exception as e:
        print(f"An error occurred during the search: {e}")

def save_intermediate_results(filename):
    global all_products
    output_df = pd.DataFrame(all_products)
    output_df.to_csv(filename, index=False)
    all_products.clear()
    unique_ids.clear()
    logging.info(f"Saved intermediate results to {filename} and cleared memory.")

try:
    # Navigating to the Burberry website
    print("Navigating to the Burberry website...")
    driver.get("https://www.burberry.com")

    # Handle the cookie consent pop-up if present
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

    # Wait for the country picker button to be clickable and click it
    print("Waiting for the country picker button...")
    country_picker_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='country-picker-button']"))
    )
    print("Clicking the country picker button...")
    country_picker_button.click()

    # Wait for the country picker modal to be visible
    print("Waiting for the country picker modal...")
    country_picker_modal_selector = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#country-picker-modal-selector"))
    )

    # Select United States from the dropdown
    print("Selecting United States from the dropdown...")
    country_picker_modal_selector = driver.find_element(By.CSS_SELECTOR, "#country-picker-modal-selector")
    for option in country_picker_modal_selector.find_elements(By.TAG_NAME, 'option'):
        if option.text == 'United States ($)':
            option.click()
            break
    # Click the update shipping location button
    print("Clicking the update shipping location button...")
    update_shipping_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'].css-1dv9zd0.e6yz8z0"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", update_shipping_button)
    driver.execute_script("arguments[0].click();", update_shipping_button)

    # Wait for the page to load after changing the location
    print("Waiting for the page to load after changing the location...")
    wait_for_page_load(driver)
    print("Country has been changed to United States.")
    time.sleep(5)

    # Search for "Children"
    search_items(driver, "Children")
    save_intermediate_results('burberry_products_children_US.csv')

    # Search for "Men"
    scroll_to_top_and_search_again(driver, "Men")
    save_intermediate_results('burberry_products_men_US.csv')

    # Search for "Women"
    scroll_to_top_and_search_again(driver, "Women")
    save_intermediate_results('burberry_products_women_US.csv')

    # Combine all intermediate CSV files into a single DataFrame
    children_df = pd.read_csv('burberry_products_children_US.csv')
    men_df = pd.read_csv('burberry_products_men_US.csv')
    women_df = pd.read_csv('burberry_products_women_US.csv')
    combined_df = pd.concat([children_df, men_df, women_df], ignore_index=True)
    combined_df.to_csv('burberry_products_combined_US.csv', index=False)

    logging.info("Combined all category results into 'burberry_products_combined.csv'")

except Exception as e:
    print('Did not access the website correctly, try again....')
    print(f"Error: {e}")

finally:
    # Ensure the WebDriver is closed properly
    driver.quit()
