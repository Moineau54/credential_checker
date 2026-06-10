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
from bs4 import BeautifulSoup
import requests
import time
import random


class Cybernews:
    def __init__(self, driver, passwords, emails, numbers, flaresolverr_url: str = "http://localhost:8191/v1"):
        self.driver = driver
        self.url_email_and_phone = "https://cybernews.com/personal-data-leak-check/"
        self.url_passwords = "https://cybernews.com/password-leak-check/"
        self.passwords = passwords
        self.emails = emails
        self.numbers = numbers
        self.flaresolverr_url = flaresolverr_url
        self.console = Console()

    # ------------------------------------------------------------------ #
    #  FlareSolverr                                                        #
    # ------------------------------------------------------------------ #

    def _get_flaresolverr_cookies(self, url: str):
        """Use FlareSolverr to bypass Cloudflare and return cookies + UA."""
        self.console.print(f"[yellow]Requesting FlareSolverr bypass for {url}...[/yellow]")
        try:
            response = requests.post(self.flaresolverr_url, json={
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000
            }, timeout=70)
            data = response.json()

            if data.get("status") != "ok":
                self.console.print(f"[red]FlareSolverr failed: {data.get('message')}[/red]")
                return None, None

            cookies = data["solution"]["cookies"]
            user_agent = data["solution"]["userAgent"]
            self.console.print("[green]FlareSolverr bypass successful[/green]")
            return cookies, user_agent

        except Exception as e:
            self.console.print(f"[red]FlareSolverr error: {e}[/red]")
            return None, None

    def _apply_flaresolverr_cookies(self, url: str) -> bool:
        """Navigate to URL and inject FlareSolverr cookies into Selenium session."""
        cookies, user_agent = self._get_flaresolverr_cookies(url)
        if not cookies:
            return False

        # Override User-Agent via CDP (works with undetected-chromedriver)
        try:
            self.driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {"userAgent": user_agent}
            )
        except Exception:
            pass  # Geckodriver doesn't support CDP — skip silently

        # Navigate first so the domain is active for cookie injection
        self.driver.get(url)
        time.sleep(1)

        # Inject cookies
        for cookie in cookies:
            try:
                selenium_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie.get("domain", ""),
                    "path": cookie.get("path", "/"),
                    "secure": cookie.get("secure", False),
                }
                if cookie.get("expires") and cookie["expires"] != -1:
                    selenium_cookie["expiry"] = int(cookie["expires"])
                self.driver.add_cookie(selenium_cookie)
            except Exception as e:
                self.console.print(f"[orange]Cookie inject warning: {e}[/orange]")

        # Refresh to activate cookies
        self.driver.refresh()
        time.sleep(2)

        page = self.driver.page_source.lower()
        title = self.driver.title.lower()
        if "blocked" in page or "just a moment" in title or "sorry" in title:
            self.console.print("[red]Still blocked after FlareSolverr — falling back to direct navigation[/red]")
            return False

        self.console.print("[green]Cloudflare bypass applied successfully[/green]")
        return True

    def _navigate(self, url: str):
        """Navigate to URL, using FlareSolverr if Cloudflare blocks us."""
        self.driver.get(url)
        time.sleep(1)

        page = self.driver.page_source.lower()
        title = self.driver.title.lower()
        if "blocked" in page or "sorry, you have been blocked" in page or "just a moment" in title:
            self.console.print("[yellow]Cloudflare block detected — trying FlareSolverr...[/yellow]")
            success = self._apply_flaresolverr_cookies(url)
            if not success:
                self.console.print("[red]Could not bypass Cloudflare[/red]")
                return False
        return True

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def dismiss_popups_and_banners(self):
        """Dismiss cookie banners and notification popups."""
        current_time = time.strftime("%H:%M:%S")
        self.console.print(f"[blue][{current_time}][/blue]: [bold orange]Dismissing popups and banners[/bold orange]")

        time.sleep(0.1)

        popup_selectors = [
            "button[data-cky-tag='reject-button']",
            "button[data-cky-tag='accept-button']",
            ".cky-btn-reject",
            ".cky-btn-accept",
            "#onesignal-slidedown-cancel-button",
            ".onesignal-slidedown-cancel-button",
            "button[data-js-cookie-off-button]",
            ".subscribe__close",
            "[data-js-subscribe-close]",
            ".cky-btn-close",
            "[data-cky-tag='detail-close']",
        ]

        dismissed_count = 0
        for selector in popup_selectors:
            try:
                element = WebDriverWait(self.driver, 0.1).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.1)
                element.click()
                dismissed_count += 1
                self.console.print(f"[green]✓ Dismissed popup with selector: {selector}[/green]")
                time.sleep(0.1)
            except (TimeoutException, NoSuchElementException):
                continue
            except Exception as e:
                self.console.print(f"[orange]Warning: Could not dismiss popup {selector}: {str(e)}[/orange]")
                continue

        if dismissed_count > 0:
            self.console.print(f"[green]Successfully dismissed {dismissed_count} popup(s)[/green]")
        else:
            self.console.print("[blue]No popups found to dismiss[/blue]")

        time.sleep(0.1)

    def _random_delay(self, short=False):
        """Random delay. Occasionally takes a longer pause."""
        if short:
            time.sleep(random.uniform(0.05, 0.18))
            return
        delay = random.uniform(0.2, 2)
        if random.random() < 0.1:
            delay = random.uniform(0, 2)
            # self.console.print(f"[dim]taking a longer pause ({delay:.1f}s)...[/dim]")
        time.sleep(delay)

    def _type_humanlike(self, element, text):
        """Type text character by character with random delays.
        Shorter texts get slower, more human-like delays.
        Longer texts get faster delays to avoid excessive total time.
        """
        length = len(text)
        if length <= 8:
            min_delay, max_delay = 0.008, 0.25
        elif length <= 16:
            min_delay, max_delay = 0.004, 0.15
        elif length <= 32:
            min_delay, max_delay = 0.002, 0.08
        else:
            min_delay, max_delay = 0.001, 0.04

        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))

    def _clear_element(self, element):
        """Clear input field reliably."""
        try:
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.BACKSPACE)
        except Exception:
            try:
                element.clear()
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    #  Checkers                                                            #
    # ------------------------------------------------------------------ #

    def check_emails(self):
        pwned_emails = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(
            f"[blue][{current_time}][/blue]: [bold blue]checking emails on Cybernews Personal data checker[/bold blue]")

        if not self._navigate(self.url_email_and_phone):
            return pwned_emails
        self.dismiss_popups_and_banners()

        cybernews_cards = [".personal-data-leak-checker-steps__status"]

        for email in track(self.emails, description="checking emails on Cybernews emails leak checker"):
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.visibility_of_element_located((By.ID, "email-or-phone"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", element)
            except TimeoutException:
                self.console.print("[red]Could not find input element, skipping...[/red]")
                continue

            self._clear_element(element)
            self._type_humanlike(element, email)
            element.send_keys(Keys.ENTER)

            try:
                WebDriverWait(self.driver, 2).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, cybernews_cards[0]))
                )
            except TimeoutException:
                time.sleep(random.uniform(0.1, 2))

            for card in cybernews_cards:
                try:
                    cybernews_element = WebDriverWait(self.driver, 2).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, card))
                    )
                    if "Your data has been leaked" in cybernews_element.get_attribute("innerHTML"):
                        print(f"\033[31memail {email} has been pwned\033[0m")
                        pwned_emails.append(email)
                        break
                except (NoSuchElementException, TimeoutException):
                    continue
                except Exception:
                    continue

            self._random_delay()

        return pwned_emails

    def check_phone(self):
        pwned_phone = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(
            f"[blue][{current_time}][/blue]: [bold blue]checking phone numbers on Cybernews Personal data checker[/bold blue]")

        if not self._navigate(self.url_email_and_phone):
            return pwned_phone
        self.dismiss_popups_and_banners()

        cybernews_cards = [".personal-data-leak-checker-steps__status"]

        for number in track(self.numbers, description="checking phone numbers on Cybernews phone number leak checker"):
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.ID, "email-or-phone"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", element)
            except TimeoutException:
                self.console.print("[red]Could not find input element, skipping...[/red]")
                continue

            self._clear_element(element)
            self._type_humanlike(element, number)
            element.send_keys(Keys.ENTER)

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, cybernews_cards[0]))
                )
            except TimeoutException:
                time.sleep(random.uniform(3, 6))

            for card in cybernews_cards:
                try:
                    cybernews_element = WebDriverWait(self.driver, 2).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, card))
                    )
                    if "Your data has been leaked" in cybernews_element.get_attribute("innerHTML"):
                        print(f"\033[31mphone number {number} has been pwned\033[0m")
                        pwned_phone.append(number)
                        break
                except (NoSuchElementException, TimeoutException):
                    continue
                except Exception:
                    continue

            self._random_delay()

        return pwned_phone

    def check_passwords(self):
        pwned_password = []
        current_time = time.strftime("%H:%M:%S")
        self.console.print(
            f"[blue][{current_time}][/blue]: [bold blue]checking passwords on Cybernews password leak checker[/bold blue]")

        if not self._navigate(self.url_passwords):
            return pwned_password
        self.dismiss_popups_and_banners()

        if "Just a moment..." in self.driver.title:
            self.console.print("[orange]resolve captcha[/orange]")
            while "Just a moment..." in self.driver.title:
                time.sleep(0.1)

        cybernews_cards = ["personal-data-leak-checker-steps__header"]

        for password in track(self.passwords, description="checking passwords on Cybernews Password leak checker"):
            try:
                element = WebDriverWait(self.driver, 4).until(
                    EC.visibility_of_element_located((By.ID, "checked-password"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", element)
            except TimeoutException:
                self.console.print("[red]Could not find input element, skipping...[/red]")
                continue

            self._clear_element(element)
            self._type_humanlike(element, password)
            element.send_keys(Keys.ENTER)

            try:
                WebDriverWait(self.driver, 4).until(
                    EC.visibility_of_element_located(
                        (By.CLASS_NAME, "personal-data-leak-checker-steps__status")
                    )
                )
            except TimeoutException:
                time.sleep(random.uniform(0.1, 2))

            soup = BeautifulSoup(self.driver.page_source, "lxml")

            for card in cybernews_cards:
                try:
                    cybernews_element = soup.find("div", class_=card)
                    text = cybernews_element.text.strip()
                    if 'Oh no! Your password has been leaked' in text:
                        print(f"\033[31mpassword {password} has been pwned\033[0m")
                        if password not in pwned_password:
                            pwned_password.append(password)
                        break
                except Exception:
                    continue

            try:
                leak_element = WebDriverWait(self.driver, 1).until(
                    EC.visibility_of_element_located(
                        (By.CLASS_NAME, "personal-data-leak-checker-steps__header__title_leaked"))
                )
                if leak_element and password not in pwned_password:
                    pwned_password.append(password)
            except (NoSuchElementException, TimeoutException):
                pass

            if "Your data has been leaked" in self.driver.page_source and password not in pwned_password:
                print(f"\033[31mpassword {password} has been pwned\033[0m")
                pwned_password.append(password)

            self._random_delay()

        return pwned_password


# Example usage:
if __name__ == "__main__":
    emails = ["test@example.com"]
    passwords = ["password123"]
    numbers = ["+1234567890"]

    # driver = Firefox()
    # checker = Cybernews(driver, passwords, emails, numbers)
    # checker = Cybernews(driver, passwords, emails, numbers, flaresolverr_url="http://localhost:8191/v1")
    # pwned_emails = checker.check_emails()
    # pwned_passwords = checker.check_passwords()
    # pwned_phones = checker.check_phone()

    pass