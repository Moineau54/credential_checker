#!../.venv/bin/python3

from undetected_geckodriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from rich.progress import track
from rich.console import Console
import time
from selenium.common.exceptions import StaleElementReferenceException

class HaveIbeenPwned:
    def __init__(self, driver, passwords, emails):
        self.driver = driver
        self.url_email = "https://haveibeenpwned.com/"
        self.url_passwords = "https://haveibeenpwned.com/Passwords"
        self.passwords = passwords
        self.emails = emails
        self.console = Console()

    def captcha_solver(self):
        titles = [
            "just a moment"
        ]
        for title in titles:
            if self.driver.title.lower().__contains__(title):
                while self.driver.title == title:
                    time.sleep(1)
                    self.console.print(f"[orange bold]Captcha detected, please solve it[/orange bold]")
                time.sleep(1)
                break

    def safe_send_keys(self, element, keys):
        try:
            # Refetch element if it's stale
            element.send_keys(keys)
        except StaleElementReferenceException:
            print("Stale element detected, retrying...")
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".form-control"))
            )
            element.send_keys(keys)

    def check_passwords(self):
        console = Console()
        pwned_passwords = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(f"[blue][{current_time}][/blue]: [bold blue]checking passwords on HaveIbeenPwned[/bold blue]")
        self.driver.get(self.url_passwords)

        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".form-control"))
            )
        finally:
            pwn_card = [
                "pwned-result-good",
                "pwned-result-bad"
            ]
            for password in track(self.passwords, description="checking passwords on HaveIbeenPwned"):
                self.captcha_solver()
                try:
                    self.safe_send_keys(element, Keys.CONTROL + "a")  # Select all text
                    self.safe_send_keys(element, Keys.BACKSPACE)  # Clear field
                except Exception as e:
                    try:
                        element.clear()
                    except Exception as e:
                        print(e)
                self.safe_send_keys(element, password)  # Enter password
                self.safe_send_keys(element, Keys.ENTER)  # Submit
                self.captcha_solver()
                for card in pwn_card:
                    try:
                        pwn_element = WebDriverWait(self.driver, 2).until(
                            EC.visibility_of_element_located((By.ID, card))
                        )
                        if "Oh no — pwned!" in pwn_element.get_attribute("innerHTML"):
                            # console.print(f"[red] password {password} has been pwned[/red]")
                            print(f"\033[31mpassword {password} has been pwned\033[0m")
                            pwned_passwords.append(password)
                            break
                    except EC.NoSuchElementException:
                        continue
                    except Exception as e:
                        continue
                time.sleep(0.1)

        return pwned_passwords

    def check_emails(self):
        pwned_email = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(f"[blue][{current_time}][/blue]: [bold blue]checking emails on HaveIbeenPwned[/bold blue]")
        self.driver.get(self.url_email)
        try:
            # Wait for the email input element to be present and scroll into view
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".form-control"))
            )

            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView();", element)

            # Ensure the element is clickable
            WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".form-control"))
            )
        finally:
            pwn_card = [
                "pwned-result-good",
                "pwned-result-bad",
                "email-result-bad"
            ]
            for email in track(self.emails, description="checking emails on HaveIbeenPwned"):
                self.captcha_solver()
                try:
                    self.safe_send_keys(element, Keys.CONTROL + "a")  # Select all text
                    self.safe_send_keys(element, Keys.BACKSPACE)  # Clear field
                except Exception as e:
                    try:
                        element.clear()
                    except Exception as e:
                        print(e)
                time.sleep(1)
                self.captcha_solver()
                self.safe_send_keys(element, email)  # Enter email
                time.sleep(1)
                self.safe_send_keys(element, Keys.ENTER)  # Submit
                self.captcha_solver()
                for card in pwn_card:
                    try:
                        pwn_element = WebDriverWait(self.driver, 2).until(
                            EC.visibility_of_element_located((By.ID, card))
                        )
                        if "Oh no — pwned!" in pwn_element.get_attribute("innerHTML"):
                            print(f"\033[31memail {email} has been pwned\033[0m")
                            pwned_email.append(email)
                            break
                    except EC.NoSuchElementException:
                        continue
                    except Exception as e:
                        continue
                time.sleep(0.1)

        return pwned_email
