#!.venv/bin/python3

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from undetected_geckodriver import Firefox
import undetected as uc


from selenium.webdriver.firefox.options import Options
import json
import os
import sys
import argparse
from rich.console import Console
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException


from src.haveIbeenPwned import HaveIbeenPwned
from src.cybernews import Cybernews


def printing(console, pwned_passwords, pwned_numbers, pwned_emails):
    if len(pwned_emails) > 0:
        console.print("\n[bold red]pwned emails:[/bold red]")
        for pwn_email in pwned_emails:
            console.print(f"    [yellow]{pwn_email}[/yellow]")

    if len(pwned_passwords) > 0:
        console.print("\n[bold red]pwned passwords:[/bold red]")
        for pwn_password in pwned_passwords:
            console.print(f"    [yellow]{pwn_password}[/yellow]")

    if len(pwned_numbers) > 0:
        console.print("\n[bold red]pwned phone numbers:[/bold red]")
        for pwn_numbers in pwned_numbers:
            console.print(f"    [yellow]{pwn_numbers}[/yellow]")

def arguments():
    parser = argparse.ArgumentParser(
        prog='credential_checker',
        description='Checks credentials on various pwned sites.',
        epilog='Author: test'
    )

    # Headless argument (for running without opening a browser)
    parser.add_argument(
        '--without_head',
        action='store_true',
        help='Run the browser in headless mode (without UI).',
        default=False
    )

    # Single credential to check (e.g., an email, password, or telephone number)
    parser.add_argument(
        '--credential',
        type=str,
        help='Provide a single credential (email, password, or telephone number) to check.'
    )

    # Specify the type of credential (email, password, or tel)
    parser.add_argument(
        '--credential_type',
        choices=['email', 'password', 'tel'],
        help='Specify the type of credential: "email", "password", or "tel".'
    )

    # Custom file for credentials (in JSON format)
    parser.add_argument(
        '--file',
        type=str,
        default='credentials.json',
        help='Specify a custom JSON file with credentials. Default is "credentials.json".'
    )

    # Specify whether to check only "HaveIbeenPwned" (shortened to hIbP)
    parser.add_argument(
        '--hIbP',
        action='store_true',
        help='Check only "HaveIbeenPwned" for the provided credentials.'
    )

    # Specify whether to check only "CyberNews"
    parser.add_argument(
        '--cybernews',
        action='store_true',
        help='Check only "CyberNews" for the provided credentials.'
    )

    # Option to check all sites (default is to check all)
    parser.add_argument(
        '--all',
        action='store_true',
        help='Check all pwned sites (default action).'
    )

    # Browser type (chrome or firefox)
    parser.add_argument(
        '--browser',
        choices=['chrome', 'firefox'],
        default='chrome',
        help='Specify the browser to use: "chrome" or "firefox". Default is chrome.'
    )

    # Parse arguments
    args = parser.parse_args()

    # If both --hIbP and --cybernews are not specified, default to checking all
    if not (args.hIbP or args.cybernews):
        args.all = True  # Default to checking all sites
        args.hIbP = True
        args.cybernews = True

    if args.credential_type and not args.credential:
        parser.error("--credential must be specified when using --credential_type.")
        sys.exit()

    # Ensure that --credential and --credential_type are used together
    if args.credential and not args.credential_type:
        parser.error("--credential_type must be specified when using --credential.")
        sys.exit()

    return args

def initialize_browser(args):
    if args.without_head:
        headless_option = "--headless"
    else:
        headless_option = ""

    if args.browser == 'chrome':
        driver = uc.Chrome(version_main=139, headless=headless_option)
    elif args.browser == 'firefox':
        firefox_options = Options()
        if headless_option:
            firefox_options.add_argument("--headless")
        driver = Firefox(options=firefox_options)
    
    return driver

def safe_element_interaction(driver, element_locator, action, *args):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(element_locator)
        )
        if action == "send_keys":
            element.send_keys(*args)
        elif action == "click":
            element.click()
    except StaleElementReferenceException:
        print("Element reference became stale, re-fetching...")
        safe_element_interaction(driver, element_locator, action, *args)

def main():
    args = arguments()
    console = Console()

    if "credentials.json" not in os.listdir():
        default_content = {
            "browser": {
                "profile": "",
                "binary": ""
            },
            "emails": [],
            "telnumber": [],
            "passwords": []
        }
        # Open the file for writing and dump the default content into it
        with open("credentials.json", "w") as f:
            json.dump(default_content, f, indent=4)

        print("enter credentials, firefox profile and executable path in credentials.json")
        sys.exit()

    passwords = []
    emails = []
    telephone_numbers = []

    if not args.credential:
        args.credential_type = "email password tel"
        with open("credentials.json") as f:
            content = json.load(f)  # Use json.load to read data from the file

        if len(content["telnumbers"]) == 0 and len(content["emails"]) == 0 and len(content["passwords"]) == 0:
            console.print("[bold red]no credentials of any kind in crendentials.json.\nplease enter a crendential in credentials.json[/bold red]")
            sys.exit()
        else:
            if len(content["telnumbers"]) > 0:
                for number in content["telnumbers"]:
                    telephone_numbers.append(number)
            else:
                console.print("[orange]no telephone numbers in credentials.json[/orange]")

            if len(content["emails"]) > 0:
                for email in content["emails"]:
                    emails.append(email)
            else:
                console.print("[orange]no emails in credentials.json[/orange]")

            if len(content["passwords"]) > 0:
                for password in content["passwords"]:
                    passwords.append(password)
            else:
                console.print("[orange]no passwords in credentials.json[/orange]")

    elif args.credential_type.__contains__("email"):
        emails.append(args.credential)
    elif args.credential_type.__contains__("password"):
        passwords.append(args.credential)
    elif args.credential_type.__contains__("tel"):
        telephone_numbers.append(args.credential)

    # Initialize the browser based on user input
    driver = initialize_browser(args)

    pwned_passwords = []
    pwned_emails = []
    pwned_numbers = []

    if args.hIbP or args.all:
        haveIbeenPwned = HaveIbeenPwned(driver=driver, passwords=passwords, emails=emails)
        if args.credential_type.__contains__("password"):
            haveIbeenPwned_passwords = haveIbeenPwned.check_passwords()
            if haveIbeenPwned_passwords != None and len(haveIbeenPwned_passwords) != 0:
                for hIbP_password in haveIbeenPwned_passwords:
                    if hIbP_password not in pwned_passwords:
                        pwned_passwords.append(hIbP_password)

        if args.credential_type.__contains__("email"):
            haveIbeenPwned_emails = haveIbeenPwned.check_emails()
            if haveIbeenPwned_emails != None and len(haveIbeenPwned_emails) != 0:
                for hIbP_email in haveIbeenPwned_emails:
                    if hIbP_email not in pwned_emails:
                        pwned_emails.append(hIbP_email)

        if args.credential_type.__contains__("tel"):
            pass  # Implement if needed

    if args.cybernews or args.all:
        cybernews = Cybernews(driver=driver, passwords=passwords, numbers=telephone_numbers, emails=emails)
        if args.credential_type.__contains__("password"):
            cybernews_passwords = cybernews.check_passwords()
            if cybernews_passwords != None and len(cybernews_passwords) != 0:
                for Cybernews_password in cybernews_passwords:
                    if Cybernews_password not in pwned_passwords:
                        pwned_passwords.append(Cybernews_password)

        if args.credential_type.__contains__("email"):
            cybernews_emails = cybernews.check_emails()
            if cybernews_emails != None and len(cybernews_emails) != 0:
                for cybernews_email in cybernews_emails:
                    if cybernews_email not in pwned_emails:
                        pwned_emails.append(cybernews_email)

        if args.credential_type.__contains__("tel"):
            cybernews_telephone_numbers = cybernews.check_phone()
            if cybernews_telephone_numbers != None and len(cybernews_telephone_numbers):
                for cybernews_number in cybernews_telephone_numbers:
                    if cybernews_number not in pwned_numbers:
                        pwned_numbers.append(cybernews_number)

    printing(console, pwned_passwords=pwned_passwords, pwned_numbers=pwned_numbers, pwned_emails=pwned_emails)

    driver.close()

if __name__ == "__main__":
    main()
