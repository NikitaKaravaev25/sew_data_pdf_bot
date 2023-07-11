import asyncio
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


async def get_link(serial_number: str) -> Optional[str]:
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        url = f"https://www.seweurodrive.com/os/dud/?tab=productdata&country=us&language=en_us&search={serial_number}&doc_lang=en-DE"

        driver.get(url)
        await asyncio.sleep(5)
        for _ in range(20):
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.find(id="productdata-pdf-button")
            if text:
                return text.get('href')
            else:
                await asyncio.sleep(2)
    except Exception as e:
        return f'Exception: {e}'
    finally:
        driver.quit()
