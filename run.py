import os
import time

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from jsonlines import jsonlines
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class QuoteScraper:
    def __init__(self):
        load_dotenv()
        self.output_file = os.getenv("OUTPUT_FILE")
        self.input_url = os.getenv("INPUT_URL")
        self.proxy = os.getenv("PROXY")
        self.driver = None
        self.delay = 20  # base delay (sec) for loading quotes from script
        self.wait = None

    def setup_driver(self) -> None:
        """
        Defines webdriver with specified options to emulate scraping
        """
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        # since proxy doesn't work, it won't be included
        # options.add_argument(f"--proxy-server={self.proxy}")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, self.delay)

    def scrape_page(self) -> list[dict[str, list]]:
        """
        Collects quotes from a single page
        :return: list of dictionaries with quote-content
        """
        time.sleep(5)  # include some delay to imitate human browsing
        raw_quotes = self.driver.find_elements(By.CLASS_NAME, "quote")
        quotes = []
        for quote in raw_quotes:
            text = quote.find_element(By.CLASS_NAME, "text").get_attribute("innerText")
            author = quote.find_element(By.CLASS_NAME, "author").get_attribute(
                "innerText"
            )
            tags = [
                tag.get_attribute("innerText")
                for tag in quote.find_elements(By.CLASS_NAME, "tag")
            ]
            quotes.append({"text": text, "by": author, "tags": tags})
        return quotes

    def scrape_quotes(self) -> list[dict[str, list]]:
        """
        Collects quotes from the whole source url
        :return: list of dictionaries with quote-content
        """
        url = self.input_url
        all_quotes = []
        page_num = 1

        while True:
            self.driver.get(url)
            print(f"Currently scrapped: {url}")
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "quote"))
                )
                all_quotes.extend(self.scrape_page())
            except TimeoutException:
                break

            next_page = BeautifulSoup(self.driver.page_source, "html.parser").find(
                "li", {"class": "next"}
            )
            if not next_page:
                break
            else:
                page_num += 1
                url = f"{self.input_url}page/{page_num}/"

        return all_quotes

    def save_to_json(self, quotes):
        """saves data into json lines format"""
        with jsonlines.open(self.output_file, mode="w") as f:
            f.write_all(quotes)

    def run(self):
        self.setup_driver()
        quotes = self.scrape_quotes()
        self.save_to_json(quotes)
        self.driver.quit()


if __name__ == "__main__":
    scraper = QuoteScraper()
    scraper.run()
