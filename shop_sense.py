from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import concurrent.futures
import os  # Ensure os is imported for environment variables
import re  # Added for regex operations
from selenium.common.exceptions import TimeoutException
from colorlog import ColoredFormatter  # New import for colored logs
from colorama import init, Fore, Style
import pyfiglet
from selenium.webdriver.chrome.options import Options  # Ensure Options is imported
from selenium.webdriver.common.action_chains import ActionChains  # New import for advanced interactions

app = Flask(__name__)

# Configure colored logging
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.handlers = []  # Remove default handlers
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize colorama
init(autoreset=True)

# Display SHOPSENSE Banner with Enhanced Colors and Font
def display_banner():
    ascii_banner = pyfiglet.figlet_format("SHOPSENSE", font="standard")  # Changed font to 'standard'
    colored_banner = (
        Fore.CYAN + ascii_banner +  # Main banner in cyan
        Fore.MAGENTA + "The Product Price Comparison Tool\n" +  # Subtitle in magenta
        Style.RESET_ALL
    )
    print(colored_banner)

display_banner()

# Path to ChromeDriver executable
driver_path = r"C:\\Users\\HP\\OneDrive\\Desktop\\Btech\\[00]GITHUB----------------------\\[00]PROJECTS\\[00]SHOPSENSE\\chromedriver.exe"

# Normalize product name for consistent search across websites
def normalize_product_name(product_name):
    # Enhanced normalization: lowercase, remove special characters, and extra spaces
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', product_name.lower()).strip()
    normalized = re.sub(r'\s+', '+', normalized)
    return normalized

# ChromeOptions
def create_webdriver():
    CO = Options()
    CO.add_experimental_option('useAutomationExtension', False)
    CO.add_argument('--ignore-certificate-errors')
    CO.add_argument('--start-maximized')
    CO.add_argument('--headless')  # Run in headless mode
    # Set a custom user-agent to mimic a real browser
    CO.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/85.0.4183.102 Safari/537.36')
    service = Service(driver_path, log_path=os.devnull)  # Suppress WebDriver logs
    return webdriver.Chrome(service=service, options=CO)

def get_price_flipkart(product_name):
    wd = create_webdriver()
    wait = WebDriverWait(wd, 15)  # Increased wait time
    search_url = f"https://www.flipkart.com/search?q={product_name}"
    wd.get(search_url)
    logger.info(f"Searching for '{product_name}' on Flipkart")
    try:
        # Close the login popup if it appears
        try:
            close_button = wd.find_element(By.CSS_SELECTOR, 'button._2KpZ6l._2doB4z')
            close_button.click()
            logger.info("Closed Flipkart login popup.")
        except:
            logger.info("Flipkart login popup not present.")
        
        # Additional wait for product listings to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div._1AtVbE')))
        
        # Updated CSS selector for price
        price_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div._30jeq3._1_WHN1'))
        )
        price = price_element.text.replace('₹', '').replace(',', '').strip()
        logger.info(f"Flipkart Price: ₹{price}")
        return float(price), search_url
    except TimeoutException:
        logger.warning("Flipkart: Price not found.")
        wd.save_screenshot('flipkart_timeout.png')  # Capture screenshot
        return None, None
    except ValueError:
        logger.warning("Flipkart: Unable to parse the price.")
        wd.save_screenshot('flipkart_value_error.png')  # Capture screenshot
        return None, None
    except Exception as e:
        logger.error(f"Flipkart: Unexpected error - {e}")
        wd.save_screenshot('flipkart_exception.png')  # Capture screenshot
        return None, None
    finally:
        wd.quit()

def get_price_amazon(product_name):
    wd = create_webdriver()
    wait = WebDriverWait(wd, 20)
    search_url = f"https://www.amazon.in/s?k={product_name}"
    wd.get(search_url)
    logger.info(f"Searching for '{product_name}' on Amazon")
    try:
        price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.a-price-whole')))
        price = price_element.text.replace(',', '')
        logger.info(f"Amazon Price: ₹{price}")
        return float(price), search_url
    except TimeoutException:
        logger.warning("Amazon: Price not found.")
        return None, None
    except ValueError:
        logger.warning("Amazon: Unable to parse the price.")
        return None, None
    finally:
        wd.quit()

def get_price_ebay(product_name):
    wd = create_webdriver()
    wait = WebDriverWait(wd, 15)  # Increased wait time
    normalized_product = normalize_product_name(product_name)
    search_url = f"https://www.ebay.in/sch/i.html?_nkw={normalized_product}"
    wd.get(search_url)
    logger.info(f"Searching for '{product_name}' on eBay")
    try:
        # Wait for the product listings to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.srp-results')))
        price_elements = wd.find_elements(By.CSS_SELECTOR, 'span.s-item__price')
        
        for price_element in price_elements:
            raw_price = price_element.text.strip().replace('₹', '').replace(',', '').split(' ')[0]
            if raw_price.replace('.', '', 1).isdigit():
                price = float(raw_price)
                logger.info(f"eBay Price: ₹{price}")
                return price, search_url
        logger.warning("eBay: No valid price found.")
        wd.save_screenshot('ebay_no_price.png')  # Capture screenshot
        return None, None
    except TimeoutException:
        logger.warning("eBay: Price not found.")
        wd.save_screenshot('ebay_timeout.png')  # Capture screenshot
        return None, None
    except (ValueError, IndexError) as e:
        logger.warning(f"eBay: Unable to parse the price - {e}")
        wd.save_screenshot('ebay_parse_error.png')  # Capture screenshot
        return None, None
    except Exception as e:
        logger.error(f"eBay: Unexpected error - {e}")
        wd.save_screenshot('ebay_exception.png')  # Capture screenshot
        return None, None
    finally:
        wd.quit()

def get_price_xerve(product_name):
    wd = create_webdriver()
    wait = WebDriverWait(wd, 15)  # Increased wait time
    normalized_product = normalize_product_name(product_name)
    search_url = f"https://www.xerve.in/prices/s-mobiles?q={normalized_product}"
    wd.get(search_url)
    logger.info(f"Searching for '{product_name}' on Xerve")
    try:
        # Wait for the price element to load
        price_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span.product-price'))
        )
        price_text = price_element.text.strip().replace('₹', '').replace(',', '')
        price_match = re.findall(r'\d+\.?\d*', price_text)
        if price_match:
            price = float(price_match[0])
            logger.info(f"Xerve Price: ₹{price}")
            return price, search_url
        else:
            logger.warning("Xerve: No valid price found.")
            wd.save_screenshot('xerve_no_price.png')  # Capture screenshot
            return None, None
    except TimeoutException:
        logger.warning("Xerve: Price not found.")
        wd.save_screenshot('xerve_timeout.png')  # Capture screenshot
        return None, None
    except (ValueError, IndexError) as e:
        logger.warning(f"Xerve: Unable to parse the price - {e}")
        wd.save_screenshot('xerve_parse_error.png')  # Capture screenshot
        return None, None
    except Exception as e:
        logger.error(f"Xerve: Unexpected error - {e}")
        wd.save_screenshot('xerve_exception.png')  # Capture screenshot
        return None, None
    finally:
        wd.quit()

def send_notification(product, current_price, user_price, user_contact):
    if current_price < user_price:
        email_user = os.getenv('EMAIL_USER')
        email_pass = os.getenv('EMAIL_PASS')
        
        if not email_user or not email_pass:
            logger.error("Email credentials are not set. Please set EMAIL_USER and EMAIL_PASS environment variables.")
            return  # Exit the function if credentials are missing
        
        msg = MIMEMultipart()
        msg['From'] = email_user  # Use environment variable
        msg['To'] = user_contact
        msg['Subject'] = f'Price Drop Alert: {product}'
        
        body = f'The price of {product} has dropped to ₹{current_price}.'
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_user, email_pass)  # Use environment variables
            text = msg.as_string()
            server.sendmail(email_user, user_contact, text)
            server.quit()
            logger.info(f"Notification sent to {user_contact} for {product}.")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    product_name = request.form['product']
    normalized_product = normalize_product_name(product_name)  # Normalize product name
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            flipkart_future = executor.submit(get_price_flipkart, normalized_product)
            amazon_future = executor.submit(get_price_amazon, normalized_product)
            ebay_future = executor.submit(get_price_ebay, normalized_product)
            xerve_future = executor.submit(get_price_xerve, normalized_product)  # Added Xerve
            
            flipkart_price, flipkart_url = flipkart_future.result()
            amazon_price, amazon_url = amazon_future.result()
            ebay_price, ebay_url = ebay_future.result()
            xerve_price, xerve_url = xerve_future.result()  # Added Xerve results
        
        prices = [
            (flipkart_price, flipkart_url, 'Flipkart'),
            (amazon_price, amazon_url, 'Amazon'),
            (ebay_price, ebay_url, 'eBay'),
            (xerve_price, xerve_url, 'Xerve')
        ]
        prices = [p for p in prices if p[0] is not None]
        
        if not prices:
            logger.warning("No prices found for the product.")
            return render_template('results.html', product=product_name, error="No prices found for the product.")
        
        min_price, min_url, min_site = min(prices, key=lambda x: x[0])
        
        logger.info(f"Best price found on {min_site}: ₹{min_price}")
        
        return render_template(
            'results.html',
            product=product_name,
            flipkart_price=flipkart_price,
            amazon_price=amazon_price,
            ebay_price=ebay_price,
            xerve_price=xerve_price,
            flipkart_url=flipkart_url,
            amazon_url=amazon_url,
            ebay_url=ebay_url,
            xerve_url=xerve_url,
            min_url=min_url,
            min_site=min_site
        )
    except Exception as e:
        logger.error(f"Error during search operation: {e}")
        return render_template('results.html', product=product_name, error="An unexpected error occurred during the search.")

@app.route('/notify', methods=['POST'])
def notify():
    product_name = request.form['product']
    user_price = float(request.form['price'])
    user_contact = request.form['contact']
    flipkart_price = request.form.get('flipkart_price')
    amazon_price = request.form.get('amazon_price')
    ebay_price = request.form.get('ebay_price')  # Added eBay price retrieval
    xerve_price = request.form.get('xerve_price')  # Added Xerve price retrieval

    def try_send(price, site):
        if price is not None:
            try:
                price_val = float(price)
                if price_val < user_price:
                    send_notification(product_name, price_val, user_price, user_contact)
            except ValueError:
                logger.error(f"Invalid price value from {site}: {price}")

    try:
        try_send(flipkart_price, 'Flipkart')
        try_send(amazon_price, 'Amazon')
        try_send(ebay_price, 'eBay')
        try_send(xerve_price, 'Xerve')
    except Exception as e:
        logger.error(f"Error during notification process: {e}")
        return render_template('notify.html', product=product_name, user_price=user_price, user_contact=user_contact, error="An unexpected error occurred while setting up notifications.")

    logger.info(f"Notifications processed for '{product_name}' at desired price ₹{user_price} to {user_contact}.")
    return render_template('notify.html', product=product_name, user_price=user_price, user_contact=user_contact)

if __name__ == '__main__':
    app.run(debug=False)  # Changed debug to False for production