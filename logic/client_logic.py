import asyncio
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


async def get_link(serial_number: str) -> Optional[str]:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    url = f"https://www.seweurodrive.com/os/dud/?tab=productdata&country=us&language=en_us&search={serial_number}&doc_lang=en-DE"

    try:
        driver.get(url)
        await asyncio.sleep(10)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.find(id="productdata-pdf-button")
        link = text.get('href')
        return link
    except:
        return None
    finally:
        driver.quit()
