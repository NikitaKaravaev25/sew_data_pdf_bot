import asyncio
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

async def prepear_webdriver():
    global driver, original_window
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    original_window =driver.window_handles[0]
    return driver

async def get_link(serial_number: str) -> Optional[str]:
    try:
        driver.switch_to.new_window('tab')

        url = f"https://www.seweurodrive.com/os/dud/?tab=productdata&country=us&language=en_us&search={serial_number}&doc_lang=en-DE"

        driver.get(url)
        await asyncio.sleep(3)
        for _ in range(26):
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.find(id="productdata-pdf-button")
            if text:
                return text.get('href')
            else:
                await asyncio.sleep(1)
    except Exception as e:
        return f'Exception: {e}'
    finally:
        driver.close()
        driver.switch_to.window(original_window)



