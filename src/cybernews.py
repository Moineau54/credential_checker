from undetected_geckodriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm
from rich import print
from rich.console import Console
import time


class Cybernews:
    def __init__(self, driver, passwords, emails, numbers):
        self.driver = driver
        self.url_email_and_phone = "https://cybernews.com/personal-data-leak-check/"
        self.url_passwords = "https://cybernews.com/password-leak-check/"
        self.passwords = passwords
        self.emails = emails
        self.numbers = numbers
        self.console = Console()

    def dismiss_popups_and_banners(self):
        """
        Function to dismiss cookie banners and notification popups
        """
        current_time = time.strftime("%H:%M:%S")
        self.console.print(f"[blue][{current_time}][/blue]: [bold orange]Dismissing popups and banners[/bold orange]")

        # Wait a moment for page to load
        time.sleep(2)

        # List of selectors for different types of popups/banners
        popup_selectors = [
            # Cookie consent banners
            "button[data-cky-tag='reject-button']",  # Reject all cookies
            "button[data-cky-tag='accept-button']",  # Accept all cookies
            ".cky-btn-reject",  # Alternative reject button
            ".cky-btn-accept",  # Alternative accept button

            # OneSignal notification popups
            "#onesignal-slidedown-cancel-button",  # Cancel notifications
            ".onesignal-slidedown-cancel-button",

            # Generic close buttons
            "button[data-js-cookie-off-button]",  # Cookie off button
            ".subscribe__close",  # Newsletter popup close
            "[data-js-subscribe-close]",  # Subscribe close button

            # Additional cookie banner close buttons
            ".cky-btn-close",
            "[data-cky-tag='detail-close']",

            # Browser notification permission
            # Note: Browser permission popups can't be dismissed via Selenium
        ]

        dismissed_count = 0

        for selector in popup_selectors:
            try:
                # Try to find and click the element with a short timeout
                element = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )

                # Scroll element into view if needed
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)

                # Try to click the element
                element.click()
                dismissed_count += 1
                self.console.print(f"[green]✓ Dismissed popup with selector: {selector}[/green]")
                time.sleep(1)  # Wait a moment between clicks

            except (TimeoutException, NoSuchElementException):
                # Element not found or not clickable, continue to next
                continue
            except Exception as e:
                # Log other exceptions but continue
                self.console.print(f"[orange]Warning: Could not dismiss popup {selector}: {str(e)}[/orange]")
                continue

        # Try to handle browser notification permission popup programmatically
        try:
            # Execute JavaScript to deny notifications if the permission API is available
            self.driver.execute_script("""
                if ('Notification' in window && Notification.permission === 'default') {
                    // This won't work for permission prompts, but we can try
                    console.log('Notification permission is default');
                }
            """)
        except Exception:
            pass

        if dismissed_count > 0:
            self.console.print(f"[green]Successfully dismissed {dismissed_count} popup(s)[/green]")
        else:
            self.console.print(f"[blue]No popups found to dismiss[/blue]")

        # Wait a moment for any animations to complete
        time.sleep(2)

    def check_emails(self):
        pwned_emails = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(
            f"[blue][{current_time}][/blue]: [bold blue]checking emails on Cybernews Personal data checker[/bold blue]")

        self.driver.get(self.url_email_and_phone)

        # Dismiss popups and banners first
        self.dismiss_popups_and_banners()

        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.ID, "email-or-phone"))
            )

            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView();", element)

        finally:
            cybernews_cards = [
                ".personal-data-leak-checker-steps__status"
            ]
            for email in tqdm(self.emails):
                element.send_keys(Keys.CONTROL + "a")  # Select all text
                element.send_keys(Keys.BACKSPACE)
                element.send_keys(email)
                element.send_keys(Keys.ENTER)
                time.sleep(1)
                for card in cybernews_cards:
                    try:
                        cybernews_element = WebDriverWait(self.driver, 2).until(
                            EC.visibility_of_element_located(((By.CSS_SELECTOR, card)))
                        )
                        if "Your data has been leaked" in cybernews_element.get_attribute("innerHTML"):
                            pwned_emails.append(email)
                            break

                    except NoSuchElementException:
                        # Element not found in the DOM, continue to the next card
                        continue

                    except Exception as e:
                        # Handle any other unexpected exceptions
                        # print(f"An error occurred with card {card}: {str(e)}")
                        continue

                time.sleep(2)
        return pwned_emails

    def check_phone(self):
        pwned_phone = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(
            f"[blue][{current_time}][/blue]: [bold blue]checking phone numbers on Cybernews Personal data checker[/bold blue]")

        self.driver.get(self.url_email_and_phone)

        # Dismiss popups and banners first
        self.dismiss_popups_and_banners()

        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.ID, "email-or-phone"))
            )

            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView();", element)

        finally:
            cybernews_cards = [
                ".personal-data-leak-checker-steps__status"
            ]
            for number in tqdm(self.numbers):
                element.send_keys(Keys.CONTROL + "a")  # Select all text
                element.send_keys(Keys.BACKSPACE)
                element.send_keys(number)
                element.send_keys(Keys.ENTER)
                time.sleep(1)
                for card in cybernews_cards:
                    try:
                        cybernews_element = WebDriverWait(self.driver, 2).until(
                            EC.visibility_of_element_located(((By.CSS_SELECTOR, card)))
                        )
                        if "Your data has been leaked" in cybernews_element.get_attribute("innerHTML"):
                            pwned_phone.append(number)
                            break

                    except NoSuchElementException:
                        # Element not found in the DOM, continue to the next card
                        continue

                    except Exception as e:
                        # Handle any other unexpected exceptions
                        # print(f"An error occurred with card {card}: {str(e)}")
                        continue
                
                time.sleep(2)
        return pwned_phone

    def check_passwords(self):
        pwned_password = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(
            f"[blue][{current_time}][/blue]: [bold blue]checking passwords on Cybernews Password leak checker[/bold blue]")

        self.driver.get(self.url_passwords)

        # Dismiss popups and banners first
        self.dismiss_popups_and_banners()

        # Handle potential Cloudflare captcha
        if "Just a moment..." in self.driver.title:
            self.console.print("[orange]resolve captcha[/orange]")
            while "Just a moment..." in self.driver.title:
                time.sleep(1)

        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.ID, "checked-password"))
            )
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView();", element)

        finally:
            # Option 1: Using CSS_SELECTOR (current approach - most reliable)
            cybernews_cards = [
                ".personal-data-leak-checker-steps__header__title_leaked",
                ".personal-data-leak-checker-steps__status"
            ]

            for password in tqdm(self.passwords):
                element.send_keys(Keys.CONTROL + "a")  # Select all text
                element.send_keys(Keys.BACKSPACE)
                element.send_keys(password)
                element.send_keys(Keys.ENTER)
                time.sleep(1)

                # Option 1: Check specific elements (recommended)
                for card in cybernews_cards:
                    try:
                        cybernews_element = WebDriverWait(self.driver, 5).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, card))
                        )
                        if "Your data has been leaked" in cybernews_element.get_attribute("innerHTML"):
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
                
                time.sleep(2)
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
    # checker = Cybernews(driver, passwords, emails, numbers)

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