import csv
import time
from typing import List, Dict

from colorama import Fore, Style, init
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def safe_text(parent, by, value) -> str:
    try:
        return parent.find_element(by, value).text.strip()
    except NoSuchElementException:
        return "N/A"


def build_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def search_hotels(query: str, city: str) -> List[Dict[str, str]]:
    driver = build_driver()
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.booking.com/")

        # Handle cookie banner when present
        try:
            cookie_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_btn.click()
        except TimeoutException:
            pass

        search_box = wait.until(EC.presence_of_element_located((By.NAME, "ss")))
        search_box.clear()
        search_box.send_keys(f"{query} {city}".strip())
        search_box.send_keys(Keys.ENTER)

        wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="property-card"]'))
        )

        time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid="property-card"]')
        results: List[Dict[str, str]] = []

        for card in cards:
            if len(results) >= 10:
                break

            name = safe_text(card, By.CSS_SELECTOR, '[data-testid="title"]')
            rating = safe_text(card, By.CSS_SELECTOR, '[data-testid="review-score"]')
            price = safe_text(card, By.CSS_SELECTOR, '[data-testid="price-and-discounted-price"]')

            results.append(
                {
                    "Name": name,
                    "Rating": rating if rating else "N/A",
                    "Price per night": price if price else "N/A",
                }
            )

        return results
    finally:
        driver.quit()


def save_to_csv(rows: List[Dict[str, str]], path: str) -> None:
    if not rows:
        return

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Name", "Rating", "Price per night"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    init(autoreset=True)

    query = input("What are you looking for? (e.g., Hotels): ").strip()
    city = input("In which city? (e.g., Muscat): ").strip()

    if not query or not city:
        print("Both inputs are required.")
        return

    hotels = search_hotels(query, city)

    for hotel in hotels:
        print(Fore.GREEN + f"Added: {hotel['Name']}" + Style.RESET_ALL)

    save_to_csv(hotels, "hotels_list.csv")


if __name__ == "__main__":
    main()
