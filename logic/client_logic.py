from selenium import webdriver
import time
from bs4 import BeautifulSoup


def get_link(serial_number):
    try:
        driver = webdriver.Chrome()
        url = f"https://www.seweurodrive.com/os/dud/?tab=productdata&country=us&language=en_us&search={serial_number}&doc_lang=en-DE"
        driver.get(url)
        time.sleep(10)
        html = driver.page_source
        soup = BeautifulSoup(html)
        text = soup.find(id="productdata-pdf-button")
        link = text.get('href')
        driver.quit()
        return link
    except:
        return "Error"
