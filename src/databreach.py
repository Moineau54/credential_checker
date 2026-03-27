#!../.venv/bin/python3

from undetected_geckodriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm
from rich.progress import track
from rich.console import Console
import time


class Databreach:
    def __init__(self, driver, emails, numbers):
        self.driver = driver
        self.url_email_and_phone = "https://databreach.com/"
        self.url_passwords = "https://databreach.com/"
        self.emails = emails
        self.numbers = numbers
        self.console = Console()

    def check_emails(self):
        pwned_emails = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(
            f"[blue][{current_time}][/blue]: [bold blue]checking emails on Databreach Personal data checker[/bold blue]")

        self.driver.get(self.url_email_and_phone)

        # Dismiss popups and banners first
        # self.dismiss_popups_and_banners()

        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.ID, "search"))
            )

            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView();", element)

        finally:
            cybernews_cards = [
                ".mt-10.text-center"
            ]
            for email in track(self.emails, description="checking emails on Databreach emails leak checker"):
                try:
                    element.clear()  # Select all text
                    # element.send_keys(Keys.BACKSPACE)
                except Exception as e:
                    try:
                        element.clear()
                    except Exception as e:
                        print(e)
                element.send_keys(email)
                element.send_keys(Keys.ENTER)
                time.sleep(0.1)
                for card in cybernews_cards:
                    try:
                        cybernews_element = WebDriverWait(self.driver, 2).until(
                            EC.visibility_of_element_located(((By.CSS_SELECTOR, card)))
                        )
                        if "Your data was leaked" in cybernews_element.get_attribute("innerHTML"):
                            print(f"\033[31memail {email} has been pwned\033[0m")
                            pwned_emails.append(email)
                            break

                    except NoSuchElementException:
                        # Element not found in the DOM, continue to the next card
                        continue

                    except Exception as e:
                        # Handle any other unexpected exceptions
                        # print(f"An error occurred with card {card}: {str(e)}")
                        continue

                time.sleep(0.1)
        return pwned_emails

    def check_phone(self):
        pwned_phone = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(
            f"[blue][{current_time}][/blue]: [bold blue]checking phone numbers on Databreach Personal data checker[/bold blue]")

        self.driver.get(self.url_email_and_phone)

        # Dismiss popups and banners first
        # self.dismiss_popups_and_banners()

        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.ID, "search"))
            )

            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView();", element)

        finally:
            cybernews_cards = [
                ".w-full.bg-card-accent.md:rounded-b-3xl"
            ]
            for number in track(self.numbers, description="checking phone numbers on Databreach phone number leak checker"):
                try:
                    element.send_keys(Keys.CONTROL + "a")  # Select all text
                    element.send_keys(Keys.BACKSPACE)
                except Exception as e:
                    try:
                        element.clear()
                    except Exception as e:
                        print(e)
                element.send_keys(number)
                element.send_keys(Keys.ENTER)
                time.sleep(0.1)
                for card in cybernews_cards:
                    try:
                        cybernews_element = WebDriverWait(self.driver, 2).until(
                            EC.visibility_of_element_located(((By.CSS_SELECTOR, card)))
                        )
                        if "Your data has been leaked" in cybernews_element.get_attribute("innerHTML"):
                            print(f"\033[31mphone number {number} has been pwned\033[0m")
                            pwned_phone.append(number)
                            break

                    except NoSuchElementException:
                        # Element not found in the DOM, continue to the next card
                        continue

                    except Exception as e:
                        # Handle any other unexpected exceptions
                        # print(f"An error occurred with card {card}: {str(e)}")
                        continue
                
                time.sleep(0.1)
        return pwned_phone

        pwned_password = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(
            f"[blue][{current_time}][/blue]: [bold blue]checking passwords on Databreach password leak checker[/bold blue]")

        self.driver.get(self.url_passwords)

        # Dismiss popups and banners first
        # self.dismiss_popups_and_banners()

        # Handle potential Cloudflare captcha
        if "Just a moment..." in self.driver.title:
            self.console.print("[orange]resolve captcha[/orange]")
            while "Just a moment..." in self.driver.title:
                time.sleep(0.1)

        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".relative.h-12.w-full"))
            )
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView();", element)

        finally:
            # Option 1: Using CSS_SELECTOR (current approach - most reliable)
            cybernews_cards = [
                ".personal-data-leak-checker-steps__header__title_leaked",
                ".w-full.bg-card-accent.md:rounded-b-3xl"
            ]

            for password in track(self.passwords, description="checking passwords on Databreach Password leak checker"):
                try:
                    element.send_keys(Keys.CONTROL + "a")  # Select all text
                    element.send_keys(Keys.BACKSPACE)
                except Exception as e:
                    try:
                        element.clear()
                    except Exception as e:
                        print(e)
                element.send_keys(password)
                element.send_keys(Keys.ENTER)
                time.sleep(0.1)

                # Option 1: Check specific elements (recommended)
                for card in cybernews_cards:
                    try:
                        cybernews_element = WebDriverWait(self.driver, 5).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, card))
                        )
                        if "Your data has been leaked" in cybernews_element.get_attribute("innerHTML"):
                            print(f"\033[31mpassword {password} has been pwned\033[0m")
                            pwned_password.append(password)
                            break  # Found leak, no need to check other cards

                    except (NoSuchElementException, TimeoutException):
                        # Element not found, continue to the next card
                        continue
                    except Exception as e:
                        # Handle any other unexpected exceptions
                        continue

                # Option 2: Alternative using CLASS_NAME (if you prefer)
                # Note: Only works with single class names
                try:
                    # Remove dot and use only the main class name
                    leak_element = WebDriverWait(self.driver, 3).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME, "personal-data-leak-checker-steps__header__title_leaked"))
                    )
                    if leak_element:
                        pwned_password.append(password)
                except (NoSuchElementException, TimeoutException):
                    pass

                # Option 3: Check entire page source (less precise but works)
                if "Your data has been leaked" in self.driver.page_source and password not in pwned_password:
                    pwned_password.append(password)
                
                time.sleep(0.1)
        return pwned_password


# Example usage:
if __name__ == "__main__":
    # Example data
    emails = ["test@example.com"]
    passwords = ["password123"]
    numbers = ["+1234567890"]

    # Initialize driver (you'll need to set this up)
    # driver = Firefox()

    # Initialize checker
    # checker = Databreach(driver, passwords, emails, numbers)

    # Check emails (popups will be automatically dismissed)
    # pwned_emails = checker.check_emails()
    # print(f"Pwned emails: {pwned_emails}")

    # Check passwords (popups will be automatically dismissed)
    # pwned_passwords = checker.check_passwords()
    # print(f"Pwned passwords: {pwned_passwords}")

    # Check phone numbers (popups will be automatically dismissed)
    # pwned_phones = checker.check_phone()
    # print(f"Pwned phones: {pwned_phones}")

    pass