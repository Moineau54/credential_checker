#!../.venv/bin/python3

import hashlib
import time
import requests
from urllib.parse import quote

from undetected_geckodriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from rich.progress import track


FLARESOLVERR_URL = "http://localhost:8191/v1"
HIBP_BASE        = "https://haveibeenpwned.com/api/v3"
PWNED_PASS_BASE  = "https://api.pwnedpasswords.com"

# ANSI colour helpers
def _red(s):    return f"\033[31m{s}\033[0m"
def _green(s):  return f"\033[32m{s}\033[0m"
def _yellow(s): return f"\033[33m{s}\033[0m"
def _blue(s):   return f"\033[34m{s}\033[0m"
def _bold(s):   return f"\033[1m{s}\033[0m"
def _dim(s):    return f"\033[2m{s}\033[0m"


class HaveIbeenPwned:
    def __init__(self, driver: Firefox, passwords: list, emails: list,
                 api_key: str = None, flaresolverr: bool = False):
        self.driver        = driver
        self.passwords     = passwords
        self.emails        = emails
        self.api_key       = api_key
        self.flaresolverr  = flaresolverr

        self.url_email     = "https://haveibeenpwned.com/"
        self.url_passwords = "https://haveibeenpwned.com/Passwords"

        self._api_headers  = {
            "hibp-api-key": self.api_key or "",
            "User-Agent":   "hibp-python-checker",
        }
        self._fs_session: str | None = None

    # ------------------------------------------------------------------ #
    #  FlareSolverr helpers                                                #
    # ------------------------------------------------------------------ #

    def _fs_create_session(self) -> str:
        resp = requests.post(FLARESOLVERR_URL, json={"cmd": "sessions.create"}, timeout=30)
        resp.raise_for_status()
        sid = resp.json()["session"]
        print(_dim(f"FlareSolverr session: {sid}"))
        return sid

    def _fs_get(self, url: str) -> dict:
        if self._fs_session is None:
            self._fs_session = self._fs_create_session()
        payload = {
            "cmd":        "request.get",
            "url":        url,
            "session":    self._fs_session,
            "maxTimeout": 60000,
        }
        resp = requests.post(FLARESOLVERR_URL, json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json()

    def _fs_destroy_session(self):
        if self._fs_session:
            requests.post(FLARESOLVERR_URL, json={
                "cmd":     "sessions.destroy",
                "session": self._fs_session,
            }, timeout=10)
            self._fs_session = None

    # ------------------------------------------------------------------ #
    #  API: Pwned Passwords (free, k-anonymity, no key needed)             #
    # ------------------------------------------------------------------ #

    def _api_check_password(self, password: str) -> int:
        sha1   = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]
        url    = f"{PWNED_PASS_BASE}/range/{prefix}"

        try:
            resp = requests.get(url, headers={"User-Agent": "hibp-python-checker"}, timeout=10)
            if resp.status_code == 403 and self.flaresolverr:
                print(_yellow("Pwned Passwords: 403, trying FlareSolverr…"))
                fs_resp = self._fs_get(url)
                body    = fs_resp.get("solution", {}).get("response", "")
            elif resp.status_code == 429:
                retry = int(resp.headers.get("retry-after", 2))
                print(_yellow(f"Rate limited, waiting {retry}s…"))
                time.sleep(retry)
                resp = requests.get(url, headers={"User-Agent": "hibp-python-checker"}, timeout=10)
                resp.raise_for_status()
                body = resp.text
            else:
                resp.raise_for_status()
                body = resp.text
        except requests.RequestException as e:
            print(_red(f"Password API error: {e}"))
            return -1  # signal: use web fallback

        for line in body.splitlines():
            if ":" not in line:
                continue
            h, count = line.split(":", 1)
            if h.strip() == suffix:
                return int(count.strip())
        return 0

    # ------------------------------------------------------------------ #
    #  API: Breach search by email (requires paid API key)                 #
    # ------------------------------------------------------------------ #

    def _api_check_email(self, email: str) -> list:
        if not self.api_key:
            return None  # no key → fallback

        url = f"{HIBP_BASE}/breachedAccount/{quote(email)}"
        try:
            resp = requests.get(url, headers=self._api_headers,
                                params={"truncateResponse": "true"}, timeout=10)

            if resp.status_code == 404:
                return []
            if resp.status_code == 401:
                print(_red("Invalid API key."))
                return None
            if resp.status_code == 403:
                if self.flaresolverr:
                    print(_yellow("Email API: 403, trying FlareSolverr…"))
                return None
            if resp.status_code == 429:
                retry = int(resp.headers.get("retry-after", 2))
                print(_yellow(f"Rate limited ({email}), waiting {retry}s…"))
                time.sleep(retry)
                resp = requests.get(url, headers=self._api_headers,
                                    params={"truncateResponse": "true"}, timeout=10)
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()

            resp.raise_for_status()
            return [b["Name"] for b in resp.json()]

        except requests.RequestException as e:
            print(_red(f"Email API error: {e}"))
            return None  # fallback

    # ------------------------------------------------------------------ #
    #  Selenium helpers                                                    #
    # ------------------------------------------------------------------ #

    def _ts(self) -> str:
        return time.strftime("%H:%M:%S")

    def captcha_solver(self):
        titles = ["just a moment"]
        for title in titles:
            if title in self.driver.title.lower():
                print(_yellow("\033[1mCaptcha detected, please solve it\033[0m"))
                while title in self.driver.title.lower():
                    time.sleep(1)
                time.sleep(1)
                break

    def _flaresolverr_load(self, url: str):
        print(_yellow(f"Cloudflare detected, routing through FlareSolverr: {url}"))
        self._fs_get(url)
        self.driver.get(url)
        time.sleep(2)

    def _is_cloudflare_blocked(self) -> bool:
        title = self.driver.title.lower()
        return "just a moment" in title or "cloudflare" in title or "attention required" in title

    def safe_send_keys(self, element, keys):
        try:
            element.send_keys(keys)
        except StaleElementReferenceException:
            print(_dim("Stale element, retrying…"))
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".form-control"))
            )
            element.send_keys(keys)

    def _get_form_element(self, url: str):
        self.driver.get(url)
        if self._is_cloudflare_blocked():
            if self.flaresolverr:
                self._flaresolverr_load(url)
            else:
                self.captcha_solver()
        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".form-control"))
        )

    def _clear_and_type(self, element, text: str):
        try:
            self.safe_send_keys(element, Keys.CONTROL + "a")
            self.safe_send_keys(element, Keys.BACKSPACE)
        except Exception:
            try:
                element.clear()
            except Exception:
                pass
        self.safe_send_keys(element, text)

    # ------------------------------------------------------------------ #
    #  Web fallback: passwords                                             #
    # ------------------------------------------------------------------ #

    def _web_check_password(self, element, password: str) -> bool:
        self.captcha_solver()
        self._clear_and_type(element, password)
        self.safe_send_keys(element, Keys.ENTER)
        self.captcha_solver()

        if self._is_cloudflare_blocked() and self.flaresolverr:
            self._flaresolverr_load(self.url_passwords)

        for card_id in ("pwned-result-good", "pwned-result-bad"):
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.visibility_of_element_located((By.ID, card_id))
                )
                if "Oh no — pwned!" in el.get_attribute("innerHTML"):
                    return True
                return False
            except Exception:
                continue
        return False

    # ------------------------------------------------------------------ #
    #  Web fallback: emails                                                #
    # ------------------------------------------------------------------ #

    def _web_check_email(self, element, email: str) -> bool:
        self.captcha_solver()
        self._clear_and_type(element, email)
        time.sleep(1)
        self.safe_send_keys(element, Keys.ENTER)
        self.captcha_solver()

        if self._is_cloudflare_blocked() and self.flaresolverr:
            self._flaresolverr_load(self.url_email)

        for card_id in ("pwned-result-good", "pwned-result-bad", "email-result-bad"):
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.visibility_of_element_located((By.ID, card_id))
                )
                if "Oh no — pwned!" in el.get_attribute("innerHTML"):
                    return True
                return False
            except Exception:
                continue
        return False

    # ------------------------------------------------------------------ #
    #  Public: check_passwords                                             #
    # ------------------------------------------------------------------ #

    def check_passwords(self) -> list:
        print(_blue(f"[{self._ts()}]: ") + _bold(_blue("Checking passwords (API + web fallback)")))
        pwned_passwords = []
        web_element     = None

        for password in track(self.passwords, description="Checking passwords"):
            count = self._api_check_password(password)

            if count == -1:
                print(_dim("API failed for password, using web fallback"))
                if web_element is None:
                    web_element = self._get_form_element(self.url_passwords)
                if self._web_check_password(web_element, password):
                    print(_red(f"password '{password}' has been pwned (web)"))
                    pwned_passwords.append(password)
            elif count > 0:
                print(_red(f"password '{password}' has been pwned {count:,}× (API)"))
                pwned_passwords.append(password)
            # else:
            #     print(_green(f"password '{password}' not found"))

            time.sleep(0.1)

        return pwned_passwords

    # ------------------------------------------------------------------ #
    #  Public: check_emails                                                #
    # ------------------------------------------------------------------ #

    def check_emails(self) -> list:
        print(_blue(f"[{self._ts()}]: ") + _bold(_blue("Checking emails (API + web fallback)")))
        pwned_emails = []
        web_element  = None

        for email in track(self.emails, description="Checking emails"):
            result = self._api_check_email(email)

            if result is None:
                # print(_dim(f"Using web fallback for {email}"))
                if web_element is None:
                    web_element = self._get_form_element(self.url_email)
                    self.driver.execute_script("arguments[0].scrollIntoView();", web_element)
                    WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".form-control"))
                    )
                if self._web_check_email(web_element, email):
                    leak_cards = [
                        ".mb-0.me-auto.fw-semibold.text-white"
                    ]
                    leaks = ""
                    for leak_card in leak_cards:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, leak_card)
                        if elements:
                            
                            for element in elements:
                                if leaks == "":
                                    leaks = element.text
                                else:
                                    leaks = f"{leaks}, {element.text}"
                    
                    if leaks == "":
                        print(_red(f"email {email} has been pwned (web)"))
                    else:
                        print(_red(f"email {email} has been pwned (web)\n\tleaks:  {leaks}"))
                    pwned_emails.append(email)

            elif len(result) > 0:
                breaches = ", ".join(result)
                print(_red(f"email {email} found in {len(result)} breach(es): {breaches} (API)"))
                pwned_emails.append(email)

            # else:
            #     print(_green(f"email {email} not found in any breach"))

            time.sleep(0.5)

        return pwned_emails

    def __del__(self):
        self._fs_destroy_session()