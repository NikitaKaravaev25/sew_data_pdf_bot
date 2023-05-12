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
        await asyncio.sleep(5)
        for _ in range(12):
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            try:
                text = soup.find(id="productdata-pdf-button")
                return text.get('href')
            except:
                await asyncio.sleep(2)
    except:
        return None
    finally:
        driver.quit()
