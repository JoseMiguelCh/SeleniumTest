import os
import smtplib
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from dotenv import load_dotenv

load_dotenv()

result_op = False
browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(browser, 2)

# wait for page to load
browser.implicitly_wait(5)

browser.get(os.getenv("URL"))
try:
    email = wait.until(EC.presence_of_element_located((By.ID, "usernameId_new")))
    email.send_keys(os.getenv("EMAIL"))
    password = wait.until(EC.presence_of_element_located((By.ID, "passwordId_new")))
    password.send_keys(os.getenv("PASSWORD"))

    browser.find_element(By.CLASS_NAME, "formLoginButton_new").click()

    todos_list = browser.find_element(By.CLASS_NAME, "todosItemList")
    todos = todos_list.find_element(By.TAG_NAME, "a")
    todos.click()

    time_sheet = wait.until(EC.presence_of_element_located((By.ID, "time_sheet_week_1")))
    rows = time_sheet.find_elements(By.TAG_NAME, "tr")
    row_input = None
    row_total = None

    for row in rows:
        if row.get_attribute("class") == "hoursWorked":
            row_input = row
        if row.get_attribute("class") == "hoursTotal":
            row_total = row
        if row_input and row_total:
            break

    for entry in row_input.find_elements(By.TAG_NAME, "td"):
        if "nonWorkingDay" not in entry.get_attribute("class"):
            try:
                input = entry.find_element(By.TAG_NAME, "input")
                input.send_keys(os.getenv("HOURS_PER_DAY"))
            except:
                pass

    time_sheet.click()  
    total_hours = row_total.find_element(By.CLASS_NAME, "rowTotal").get_attribute("innerHTML")

    textareas = browser.find_elements(By.TAG_NAME, "textarea")
    for comment in textareas:
        if "comments" in comment.get_attribute("name"):
            comment.send_keys(os.getenv("COMMENT"))

    if total_hours == "40h 0m":
        submit = wait.until(EC.presence_of_element_located((By.ID, "fgTSSubmit")))
        submit.click()
        #wait.until(EC.presence_of_element_located((By.ID, "update")))
        #submit = browser.find_element(By.ID, "update")
        #submit.click()
        result_op = True
    else:
        print("Total hours is not 40", total_hours)
except:
    pass

finally:
    message = f"Subject: {'Succesfull' if result_op else 'Failed'} filled Arroyo time sheet"

    with smtplib.SMTP(os.getenv("EMAIL_HOST"), os.getenv("EMAIL_PORT")) as server:
        server.starttls()
        server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
        server.sendmail(os.getenv("EMAIL_ADDRESS"), os.getenv("RECIPIENT_EMAIL_ADDRESS"), message)

    browser.quit()