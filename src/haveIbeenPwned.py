from undetected_geckodriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from rich import print
from rich.console import Console
import time

class HaveIbeenPwned:
    def __init__(self, driver, passwords, emails):
        self.driver = driver
        self.url_email = "https://haveibeenpwned.com/"
        self.url_passwords = "https://haveibeenpwned.com/Passwords"
        self.passwords = passwords
        self.emails = emails
        self.console = Console()

    def check_passwords(self):
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
            for password in tqdm(self.passwords):
                #password = self.passwords[i]
                element.send_keys(Keys.CONTROL + "a")  # Select all text
                element.send_keys(Keys.BACKSPACE)
                element.send_keys(password)
                element.send_keys(Keys.ENTER)
                for card in pwn_card:
                    try:
                        pwn_element = WebDriverWait(self.driver, 2).until(
                            EC.visibility_of_element_located(((By.ID, card)))
                        )
                        if "Oh no — pwned!" in pwn_element.get_attribute("innerHTML"):
                            pwned_passwords.append(password)
                            break

                    except EC.NoSuchElementException:
                        # Element not found in the DOM, continue to the next card
                        continue

                    except Exception as e:
                        # Handle any other unexpected exceptions
                        #print(f"An error occurred with card {card}: {str(e)}")
                        continue
                time.sleep(2)

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
            for email in tqdm(self.emails):
                
                element.send_keys(Keys.CONTROL + "a")  # Select all text
                element.send_keys(Keys.BACKSPACE)
                time.sleep(1)
                element.send_keys(email)
                time.sleep(1)
                element.send_keys(Keys.ENTER)
                for card in pwn_card:
                    try:
                        pwn_element = WebDriverWait(self.driver, 2).until(
                            EC.visibility_of_element_located(((By.ID, card)))
                        )
                        if "Oh no — pwned!" in pwn_element.get_attribute("innerHTML"):
                            pwned_email.append(email)
                            break

                    except EC.NoSuchElementException:
                        # Element not found in the DOM, continue to the next card
                        continue

                    except Exception as e:
                        # Handle any other unexpected exceptions
                        #print(f"An error occurred with card {card}: {str(e)}")
                        continue
                time.sleep(2)

        return pwned_email