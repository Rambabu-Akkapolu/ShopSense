from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import pyttsx3
import time

# Path to ChromeDriver executable
driver_path = r"C:\Users\HP\OneDrive\Desktop\PROJECT\chromedriver_win32.exe"
# Product URLs
source1 = "https://www.flipkart.com/apple-iphone-14-plus-blue-128-gb/p/itmac8385391b02b?pid=MOBGHWFHUYWGB5F2&lid=LSTMOBGHWFHUYWGB5F2PCWBUL&marketplace=FLIPKART&q=iphone+14+plus&store=tyy%2F4io&srno=s_1_5&otracker=AS_QueryStore_OrganicAutoSuggest_1_9_na_na_na&otracker1=AS_QueryStore_OrganicAutoSuggest_1_9_na_na_na&fm=SEARCH&iid=a0c270a1-a004-47e3-8e5f-ab782e3e8d9c.MOBGHWFHUYWGB5F2.SEARCH&ppt=pp&ppn=pp&ssid=ex46nw35v40000001669401953183&qH=70897fd4f67467a5"
source2 = "https://www.amazon.in/Apple-iPhone-Plus-128GB-Product/dp/B0BDK2FSZ5/?tag=webtrendingams-21&ascsubtag=||1671115900|37873|553|detail-box-vary2|407649676"
source3 = "https://www.91mobiles.com/apple-iphone-14-plus-price-in-india"

# Product Name 
product = "iPhone 14 Plus"

# ChromeOptions
CO = webdriver.ChromeOptions()
CO.add_experimental_option('useAutomationExtension', False)
CO.add_argument('--ignore-certificate-errors')
CO.add_argument('--start-maximized')

# ChromeDriver Service
service = Service(driver_path)

# WebDriver Initialization
wd = webdriver.Chrome(service=service, options=CO)

# Explicit Wait
wait = WebDriverWait(wd, 10)

# Flipkart
print("Connecting to Flipkart...")
wd.get(source1)
flipkart_price_path = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="_30jeq3 _16Jk6d"]')))
flipkart_price = flipkart_price_path.text
print("Successfully retrieved the price from Flipkart")

# Amazon
print("Connecting to Amazon...")
wd.get(source2)
amazon_price_path = wait.until(EC.presence_of_element_located((By.XPATH, '//span[@id="priceblock_ourprice"]')))
amazon_price = amazon_price_path.text
print("Successfully retrieved the price from Amazon")

# 91mobiles
print("Connecting to 91mobiles...")
wd.get(source3)
mobiles91_price_path = wait.until(EC.presence_of_element_located((By.XPATH, '//span[@itemprop="price"]')))
mobiles91_price = mobiles91_price_path.text
print("Successfully retrieved the price from 91mobiles")

# Displaying Product Prices
print("#" * 40)
print("Price for [{}] on all websites, Prices are in INR \n".format(product))
print("Price available at Flipkart is: ₹" + flipkart_price)
print("Price available at Amazon is: ₹" + amazon_price)
print("Price available at 91mobiles is: ₹" + mobiles91_price)

# Reading out the prices
speaker = pyttsx3.init()
voices = speaker.getProperty('voices')
speaker.setProperty('voice', voices[0].id)
speaker.say("Price for [{}] on 3 websites, Prices are in INR".format(product))
speaker.say("Price available at Flipkart is: " + flipkart_price)
speaker.say("Price available at Amazon is: " + amazon_price)
speaker.say("Price available at 91mobiles is: " + mobiles91_price)
speaker.runAndWait()

# Compare The Product Prices
print("\nPrice for [{}] on all 3 websites, Prices are in INR\n".format(product))
P_info = {'WEBSITES': ['Flipkart', 'Amazon', '91mobiles'],
          'PRICES': [flipkart_price[1:], amazon_price[2:], mobiles91_price[1:]],
          'LINKS': [source1, source2, source3]}
info = pd.DataFrame(P_info)
print(info)

# Quit WebDriver
wd.quit()
