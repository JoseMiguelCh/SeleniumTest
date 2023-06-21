import logging
import os
import smtplib
import holidays

from datetime import date, timedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def login(browser, email, password):
    """
    Logs into the website with the given credentials.

    Args:
        browser (webdriver): The webdriver instance.
        email (str): The user's email address.
        password (str): The user's password.

    Returns:
        bool: True if login was successful, False otherwise.
    """
    browser.get(os.getenv("URL"))
    email_input = wait.until(
        EC.presence_of_element_located((By.ID, "usernameId_new")))
    email_input.send_keys(email)
    password_input = wait.until(
        EC.presence_of_element_located((By.ID, "passwordId_new")))
    password_input.send_keys(password)
    login_button = browser.find_element(By.CLASS_NAME, "formLoginButton_new")
    login_button.click()

    try:
        todos_link = browser.find_element(By.CSS_SELECTOR, ".todosItemList a")
        todos_link.click()
    except NoSuchElementException as e:
        logging.warning(f"Could not find todos link: {e}")
        return False

    return True

def fill_time_sheet(browser, hours_per_day, comment, country):
    """
    Fills out the time sheet with the given hours and comment.

    Args:
        browser (webdriver): The webdriver instance.
        hours_per_day (str): The number of hours worked per day.
        comment (str): The comment to add to the time sheet.
    """
    time_sheet_input = wait.until(
        EC.presence_of_element_located((By.ID, "time_sheet_week_1")))

    # Fill out hours worked and comments
    row_inputs = time_sheet_input.find_elements(By.CSS_SELECTOR, ".hoursWorked input")
    comment_input = browser.find_elements(By.CSS_SELECTOR, "textarea[name*='comments']")[0]
    day_of_week = date.today() - timedelta(days=date.today().weekday()) # Monday of current week
    country_holidays = holidays.country_holidays(country, years=date.today().year)
    holidays_count = 0

    for entry in row_inputs:
        if "nonWorkingDay" not in entry.get_attribute("class") and "hour" in entry.get_attribute("class"):
            if day_of_week not in country_holidays:
                entry.send_keys(hours_per_day)
            else:
                holidays_count += 1
                logging.info(f"{day_of_week} is a holiday.")
            day_of_week += timedelta(days=1)
    
    comment_input.send_keys(comment)
    return holidays_count

def submit_time_sheet(browser, total_hours):
    """
    Submits the time sheet and confirms submission.
        total_hours is the number of hours to submit per week
    Returns:
        bool: True if submission was successful, False otherwise.
    """
    total_hours_input = int(browser.find_element(By.CSS_SELECTOR, ".rowTotal").get_attribute("innerHTML").split("h")[0])
    if total_hours == total_hours_input:
        submit = wait.until(EC.presence_of_element_located((By.ID, "fgTSSubmit")))
        submit.click()
        confirm_button = wait.until(EC.presence_of_element_located((By.ID, "update")))
        # confirm_button.click() # Uncomment to submit time sheet
    else:
        logging.warning(
            f"The number of hours worked this week is %d", total_hours)

    # Check if submission successful
    try:
        success_message = browser.find_element(By.CLASS_NAME, "successMessage")
        if "submitted successfully" in success_message.text.lower():
            return True
    except NoSuchElementException as e:
        logging.warning(f"Could not find success message: {e}")
    return False

def notify_result(result: bool) -> None:
    """
    Sends an email notification with the result of the operation.
    """
    # Send email notification
    message = f"Subject: {'Successful' if result else 'Failed'} filled Arroyo time sheet"
    with smtplib.SMTP(os.getenv("EMAIL_HOST"), os.getenv("EMAIL_PORT")) as server:
        server.starttls()
        server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
        server.sendmail(os.getenv("EMAIL_ADDRESS"), os.getenv(
            "RECIPIENT_EMAIL_ADDRESS"), message)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Load environment variables
    load_dotenv()

    # Set up webdriver
    browser = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(browser, 2)
    browser.implicitly_wait(5)

    # Save results
    result_op = False

    try:
        if login(browser, os.getenv("EMAIL"), os.getenv("PASSWORD")):
            holidays = fill_time_sheet(browser, os.getenv("HOURS_PER_DAY"), os.getenv("COMMENT"), os.getenv("COUNTRY"))
            result_op = submit_time_sheet(browser, int(os.getenv("HOURS_PER_WEEK")) - holidays * int(os.getenv("HOURS_PER_DAY")))
            if result_op:
                logging.info("Successfully submitted time sheet.")
            else:
                logging.error("Failed to submit time sheet.")
    except Exception as e:
        logging.error(f"Encountered exception: {e}")
    finally:
        notify_result(result_op)
        browser.quit()
