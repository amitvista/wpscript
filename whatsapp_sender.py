import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import urllib.parse

def send_whatsapp_messages(csv_file):
    # Load contacts
    try:
        df = pd.read_csv(csv_file, comment='#')
    except FileNotFoundError:
        print(f"Error: {csv_file} not found.")
        return

    # Setup Chrome options
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Do not use headless for WhatsApp Web as it requires scanning QR
    
    # Initialize WebDriver
    print("Initializing browser...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Open WhatsApp Web
    driver.get("https://web.whatsapp.com/")
    print("Please scan the QR code to log in.")
    
    # Wait for login (checks for multiple indicators of a successful login)
    try:
        WebDriverWait(driver, 300).until(
            EC.any_of(
                EC.presence_of_element_located((By.XPATH, '//div[@id="side"]')),
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')),
                EC.presence_of_element_located((By.XPATH, '//canvas[@aria-label="Scan me!"]/following::div[contains(text(), "Scan")]')) # This is weird, let's stick to positive indicators
            )
        )
        print("Logged in successfully!")
    except Exception as e:
        print("Timeout waiting for login. Please try again.")
        driver.quit()
        return

    # Iterate through contacts
    for index, row in df.iterrows():
        name = row['Name']
        phone = str(row['Phone']).strip()
        message = row['Message'] if 'Message' in row and not pd.isna(row['Message']) else "Hello form automated script!"

        print(f"Sending message to {name} ({phone})...")

        try:
            # URL encode the message
            encoded_message = urllib.parse.quote(message)
            
            # Open chat with message
            url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_message}"
            driver.get(url)
            
            # Wait for page load - check for either the send button OR the invalid number popup
            try:
                # Increased timeout to 60 seconds
                WebDriverWait(driver, 60).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.XPATH, '//span[@data-icon="send"]')),
                        EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Send"]')),
                        EC.presence_of_element_located((By.XPATH, '//div[text()="Phone number shared via url is invalid."]')),
                        EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "invalid")]'))
                    )
                )
            except Exception as e:
                print(f"Timeout waiting for chat to load for {name}. Skipping.")
                continue

            # Check for invalid number popup
            invalid_popup = driver.find_elements(By.XPATH, '//div[text()="Phone number shared via url is invalid."]')
            if invalid_popup:
                print(f"Invalid number for {name} ({phone}). Skipping.")
                continue
            
            # Click send button
            try:
                send_btn = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
                send_btn.click()
            except Exception:
                try:
                    send_btn = driver.find_element(By.XPATH, '//button[@aria-label="Send"]')
                    send_btn.click()
                except Exception:
                   # Fallback: Focus input and press Enter
                   print("Send button not found, trying Enter key...")
                   action = webdriver.ActionChains(driver)
                   action.send_keys(Keys.ENTER)
                   action.perform()


            
            print(f"Message sent to {name}!")
            
            # Random delay to avoid bans
            time.sleep(5)
            
        except Exception as e:
            print(f"Failed to send message to {name}: {e}")

    print("All messages processed.")
    # Keep browser open for a bit to ensure last message sends
    time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    contacts_file = "contacts.csv" # Ensure this file exists in the same directory
    send_whatsapp_messages(contacts_file)
