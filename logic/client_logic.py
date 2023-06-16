from typing import Optional

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import Chrome
from bs4 import BeautifulSoup


async def get_link(serial_number: str) -> Optional[str]:
    options = Options()
    options.add_argument("--headless")
    driver = Chrome(options=options)

    url = f"https://www.seweurodrive.com/os/dud/?tab=productdata&country=us&language=en_us&search={serial_number}&doc_lang=en-DE"

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#productdata-pdf-button")))
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.select_one("#productdata-pdf-button")
        return text.get('href')
    except:
        return None
    finally:
        driver.quit()
