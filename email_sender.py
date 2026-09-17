import os
import sys
import time
import re
import urllib.parse
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
import socket

DEFAULT_CSV_FILE = "email_contacts.csv"
DEFAULT_SUBJECT_FILE = "email_subject.txt"
DEFAULT_TEMPLATE_FILE = "email_template.txt"
DEFAULT_ATTACHMENT_FILE = "email_attachment.txt"
DEFAULT_POSTER_PATH = r"C:\Users\amitm\OneDrive\Desktop\poster.jpeg"

def load_global_subject():
    """Loads campaign subject from email_subject.txt if available."""
    if os.path.exists(DEFAULT_SUBJECT_FILE):
        try:
            with open(DEFAULT_SUBJECT_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass
    return "Invitation for VIBRANT 2K26 Fest"

def load_global_body_template():
    """Loads campaign body template with {Name} placeholder from email_template.txt."""
    if os.path.exists(DEFAULT_TEMPLATE_FILE):
        try:
            with open(DEFAULT_TEMPLATE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass
    return "Hello {Name},\n\nWe are pleased to invite you to VIBRANT 2K26!"

def load_global_attachment():
    """Finds default attachment path from file, desktop, or directory."""
    if os.path.exists(DEFAULT_ATTACHMENT_FILE):
        try:
            with open(DEFAULT_ATTACHMENT_FILE, "r", encoding="utf-8") as f:
                p = f.read().strip()
                if p and os.path.exists(p):
                    return os.path.abspath(p)
        except Exception:
            pass
    if os.path.exists(DEFAULT_POSTER_PATH):
        return os.path.abspath(DEFAULT_POSTER_PATH)
    if os.path.exists("poster.jpeg"):
        return os.path.abspath("poster.jpeg")
    if os.path.exists("attachment.png"):
        return os.path.abspath("attachment.png")
    return None

def detect_active_gmail_account(driver):
    """Finds the active Gmail tab and extracts the account path (/u/0, /u/1, etc.) and email address."""
    gmail_handles = []
    chosen_handle = None
    for h in driver.window_handles:
        try:
            driver.switch_to.window(h)
            if "mail.google.com" in driver.current_url.lower():
                gmail_handles.append(h)
                # Check if this tab is currently the visible/active one
                try:
                    is_visible = driver.execute_script("return document.visibilityState === 'visible';")
                    if is_visible:
                        chosen_handle = h
                except Exception:
                    pass
        except Exception:
            pass

    if not gmail_handles:
        return "/u/0", None, (driver.window_handles[0] if driver.window_handles else None)

    if not chosen_handle:
        chosen_handle = gmail_handles[-1]

    driver.switch_to.window(chosen_handle)
    url = driver.current_url

    # Check for /u/1, /u/2, /u/3 etc.
    account_prefix = "/u/0"
    match = re.search(r'/mail/(u/\d+)', url)
    if match:
        account_prefix = "/" + match.group(1)

    # Try detecting email from Google Account avatar
    sender_email = None
    try:
        avatars = driver.find_elements(By.XPATH, '//a[contains(@aria-label, "Google Account") or contains(@aria-label, "@")]')
        for a in avatars:
            label = a.get_attribute("aria-label") or ""
            m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', label)
            if m:
                sender_email = m.group(0)
                break
    except Exception:
        pass

    return account_prefix, sender_email, chosen_handle

def format_body_text(text):
    """Converts HTML or formatted text into clean, professional email body with live clickable URLs."""
    if not text:
        return ""
    # Replace <br> and <br/> with newline
    s = re.sub(r'<br\s*/?>', '\n', str(text), flags=re.IGNORECASE)
    # Replace </p> with double newline
    s = re.sub(r'</p>', '\n\n', s, flags=re.IGNORECASE)
    # Convert <a href="URL">TEXT</a> to TEXT (URL)
    s = re.sub(r'<a\s+[^>]*?href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', r'\2 (\1)', s, flags=re.IGNORECASE)
    # Strip any remaining HTML tags
    s = re.sub(r'<[^>]+>', '', s)
    # Normalize multiple newlines
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def find_browser_executable():
    """Finds Brave Browser first, then Google Chrome."""
    candidates = [
        # Brave Browser (User profile and System paths)
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        # Google Chrome fallback
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

DEBUG_PORT = 9555

def is_port_open(port=DEBUG_PORT):
    """Checks if browser debugging port is active and not hijacked by Edge."""
    import urllib.request
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1)
        data = req.read().decode('utf-8')
        if "Edg/" in data:
            return False
        return True
    except Exception:
        return False

def find_user_profile_dir(browser_name="Brave"):
    """Finds the user's real default browser profile so they don't have to log in."""
    if browser_name == "Brave":
        p = os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data")
        if os.path.exists(p):
            return p
    else:
        p = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
        if os.path.exists(p):
            return p
    return None

def is_browser_running(browser_name="Brave"):
    """Checks if the browser is currently running."""
    try:
        import psutil
        p_name = "brave" if browser_name == "Brave" else "chrome"
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and p_name in proc.info['name'].lower():
                return True
    except Exception:
        pass
    return False

def close_browser_processes(browser_name="Brave"):
    """Safely closes existing browser instances so the profile can be accessed."""
    p_name = "brave.exe" if browser_name == "Brave" else "chrome.exe"
    try:
        subprocess.run(["taskkill", "/F", "/IM", p_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
    except Exception:
        pass
    try:
        import psutil
        base = "brave" if browser_name == "Brave" else "chrome"
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and base in proc.info['name'].lower():
                try:
                    proc.kill()
                except Exception:
                    pass
        time.sleep(1)
    except Exception:
        pass

def get_contacts(csv_file):
    """Loads contacts from CSV, skipping commented rows."""
    target_csv = csv_file
    if not os.path.exists(target_csv):
        if os.path.exists("contacts.csv"):
            print(f"Notice: '{csv_file}' not found. Falling back to 'contacts.csv'...")
            target_csv = "contacts.csv"
        else:
            print(f"Error: Neither '{csv_file}' nor 'contacts.csv' was found.")
            return None

    try:
        df = pd.read_csv(target_csv, comment='#', encoding='utf-8')
        return df, target_csv
    except Exception as e:
        print(f"Error reading {target_csv}: {e}")
        return None

def send_in_current_inbox(driver, email, subject, message, attachment_path=None):
    """Composes and sends an email directly inside the user's currently active Gmail inbox tab."""
    clean_body = format_body_text(message)

    # 1. Discard/close any old open compose windows so we have a clean slate
    try:
        old_dialogs = driver.find_elements(By.XPATH, '//div[@role="dialog" and (.//input[@name="subjectbox"] or contains(@aria-label, "Message Body"))]')
        for old in old_dialogs:
            discard_btns = old.find_elements(By.XPATH, './/div[@role="button" and (contains(@aria-label, "Discard") or contains(@data-tooltip, "Discard") or @aria-label="Close")]')
            for btn in discard_btns:
                try:
                    btn.click()
                    time.sleep(0.5)
                except Exception:
                    pass
    except Exception:
        pass

    # 2. Click Compose button in the active inbox
    compose_selectors = [
        '//div[@gh="cm"]',
        '//div[@role="button" and (contains(., "Compose") or @aria-label="Compose")]',
        '//div[contains(@class, "T-I-KE")]',
        '//div[text()="Compose"]'
    ]
    compose_clicked = False
    for sel in compose_selectors:
        try:
            elems = driver.find_elements(By.XPATH, sel)
            for el in elems:
                if el.is_displayed():
                    driver.execute_script("arguments[0].click();", el)
                    compose_clicked = True
                    break
            if compose_clicked:
                break
        except Exception:
            pass

    if not compose_clicked:
        action = webdriver.ActionChains(driver)
        action.send_keys('c').perform()

    # Wait for the Compose dialog to appear
    compose_box = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((
            By.XPATH,
            '//div[@role="dialog" and (.//input[@name="subjectbox"] or contains(@aria-label, "Message Body") or contains(@aria-label, "New Message"))]'
        ))
    )
    time.sleep(0.5)

    # Ensure compose dialog is not minimized / collapsed
    max_btns = compose_box.find_elements(
        By.XPATH,
        './/button[@aria-label="Maximize" or @data-tooltip="Maximize" or contains(@class, "Hk")]'
    )
    for mb in max_btns:
        if mb.is_displayed():
            driver.execute_script("arguments[0].click();", mb)
            time.sleep(0.5)

    # 3. Locate and focus the Recipient (To) field inside the active compose dialog
    to_input = None
    to_selectors = [
        './/input[contains(@aria-label, "To") or contains(@aria-label, "to")]',
        './/input[@name="to"]',
        './/input[@peoplekit-id]',
        './/div[@name="to"]//input',
        './/textarea[@name="to"]'
    ]
    for sel in to_selectors:
        found = compose_box.find_elements(By.XPATH, sel)
        for f in found:
            if f.is_displayed():
                to_input = f
                break
        if to_input:
            break

    # If the input isn't immediately interactable, click the "To" container to activate it
    if not to_input or not to_input.is_displayed():
        containers = compose_box.find_elements(
            By.XPATH,
            './/div[@name="to"] | .//span[text()="To" or text()="Recipients"] | .//div[contains(@aria-label, "To recipients")] | .//td[contains(., "To")]'
        )
        for c in containers:
            try:
                driver.execute_script("arguments[0].click();", c)
                time.sleep(0.5)
                break
            except Exception:
                pass
        for sel in to_selectors:
            found = compose_box.find_elements(By.XPATH, sel)
            for f in found:
                if f.is_displayed():
                    to_input = f
                    break
            if to_input:
                break

    # Type recipient email
    if to_input:
        try:
            driver.execute_script("arguments[0].focus();", to_input)
            time.sleep(0.3)
            to_input.send_keys(email)
            to_input.send_keys(Keys.ENTER)
        except Exception:
            actions = webdriver.ActionChains(driver)
            actions.move_to_element(to_input).click().send_keys(email).send_keys(Keys.ENTER).perform()
    else:
        actions = webdriver.ActionChains(driver)
        actions.send_keys(email).send_keys(Keys.ENTER).perform()

    time.sleep(0.5)

    # 4. Find Subject field
    subject_field = compose_box.find_element(By.XPATH, './/input[@name="subjectbox"]')
    driver.execute_script("arguments[0].focus();", subject_field)
    try:
        subject_field.click()
    except Exception:
        pass
    subject_field.send_keys(subject)
    time.sleep(0.5)

    # 5. Find Body textbox and insert formatted text
    body_field = compose_box.find_element(
        By.XPATH,
        './/div[@role="textbox" and (contains(@aria-label, "Message Body") or contains(@aria-label, "Message body"))]'
    )
    driver.execute_script("arguments[0].focus();", body_field)
    try:
        body_field.click()
    except Exception:
        pass

    try:
        driver.execute_script("""
            const el = arguments[0];
            el.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, arguments[1]);
            el.dispatchEvent(new Event('input', { bubbles: true }));
        """, body_field, clean_body)
    except Exception:
        body_field.send_keys(clean_body)

    time.sleep(1)

    # 6. Handle local attachment if provided
    if attachment_path and os.path.exists(attachment_path):
        abs_path = os.path.abspath(attachment_path)
        try:
            file_inputs = compose_box.find_elements(By.XPATH, './/input[@type="file"]')
            if not file_inputs:
                file_inputs = driver.find_elements(By.XPATH, '//input[@type="file"]')
            if file_inputs:
                file_inputs[0].send_keys(abs_path)
                print(f" [Attaching {os.path.basename(abs_path)}...]", end=" ", flush=True)
                # Wait for upload progress to finish (up to 15s)
                for _ in range(15):
                    time.sleep(1)
                    progress = compose_box.find_elements(By.XPATH, './/div[@role="progressbar"]')
                    if not progress:
                        break
                time.sleep(2)
        except Exception as e:
            print(f"(Attachment note: {e})", end=" ")

    time.sleep(1)

    # 7. Click Send button or press Ctrl + Enter
    send_clicked = False
    send_buttons = compose_box.find_elements(
        By.XPATH,
        './/div[@role="button" and (contains(@aria-label, "Send") or text()="Send" or contains(@data-tooltip, "Send"))]'
    )
    for btn in send_buttons:
        try:
            if btn.is_displayed():
                btn.click()
                send_clicked = True
                break
        except Exception:
            pass

    if not send_clicked:
        action = webdriver.ActionChains(driver)
        action.key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()

    # Wait for compose box to send and close
    try:
        WebDriverWait(driver, 10).until(EC.staleness_of(compose_box))
    except Exception:
        time.sleep(3)

    return True

def send_bulk_emails(csv_file=DEFAULT_CSV_FILE):
    """Main workflow: Automates Chrome/Brave to send emails via Gmail Web without needing passwords."""
    result = get_contacts(csv_file)
    if not result:
        return
    df, actual_csv = result

    # Find column names
    cols = {str(c).strip().lower(): c for c in df.columns}
    email_col = next((cols[k] for k in ['email', 'email address', 'mail', 'e-mail'] if k in cols), None)

    if not email_col:
        print(f"Error: No 'Email' column found in {actual_csv}.")
        print(f"Available columns: {list(df.columns)}")
        return

    name_col = cols.get('name')
    subject_col = cols.get('subject')
    body_col = next((cols[k] for k in ['body', 'message', 'text', 'content'] if k in cols), None)
    attachment_col = next((cols[k] for k in ['attachment', 'image', 'file', 'photo'] if k in cols), None)

    # Native Browser executable detection (Brave first, then Chrome)
    browser_exe = find_browser_executable()
    browser_name = "Brave" if browser_exe and "brave.exe" in browser_exe.lower() else "Chrome"
    
    # Use user's real browser profile where Gmail is already logged in!
    real_profile = find_user_profile_dir(browser_name)
    profile_dir = real_profile if real_profile else os.path.join(os.path.dirname(os.path.abspath(__file__)), "brave_profile_mail")

    # If the browser is currently running without debugging port, close it so we can attach to the real profile
    if not is_port_open(DEBUG_PORT) and is_browser_running(browser_name):
        print(f"\n" + "=" * 60)
        print(f"💡 TO USE YOUR ALREADY LOGGED-IN GMAIL IN {browser_name.upper()}:")
        print(f"   Windows requires all open {browser_name} windows to be closed")
        print(f"   once so we can load your active logged-in session.")
        print("=" * 60)
        ans = input(f"Press [Enter] after closing {browser_name} (or type 'kill' to auto-close): ").strip().lower()
        if ans == 'kill':
            close_browser_processes(browser_name)
        else:
            time.sleep(1)

    print(f"\n[1/3] 🌐 Launching {browser_name} with your logged-in Gmail profile...")
    
    driver = None
    # 1. If port is already open, test connecting
    if is_port_open(DEBUG_PORT):
        try:
            options = webdriver.ChromeOptions()
            if browser_exe:
                options.binary_location = browser_exe
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        except Exception:
            # If connection failed, browser might be in bad state. Clean it up.
            print(f"Notice: Stale session detected on port {DEBUG_PORT}. Resetting browser...")
            close_browser_processes(browser_name)
            time.sleep(2)
            driver = None

    # 2. If not connected, launch browser with debugging port
    if not driver:
        if is_browser_running(browser_name) and not is_port_open(DEBUG_PORT):
            close_browser_processes(browser_name)
            time.sleep(1)

        if browser_exe:
            cmd = [
                browser_exe,
                f"--remote-debugging-port={DEBUG_PORT}",
                f"--user-data-dir={profile_dir}",
                "https://mail.google.com"
            ]
            subprocess.Popen(cmd)
            for _ in range(15):
                time.sleep(1)
                if is_port_open(DEBUG_PORT):
                    break

        options = webdriver.ChromeOptions()
        if browser_exe:
            options.binary_location = browser_exe
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Open Gmail
    print(f"\n[2/3] 📬 {browser_name} is open with Gmail Web!")
    print("=" * 65)
    print("💡 YOU CAN NOW SWITCH TO ANY GMAIL ACCOUNT IN BRAVE:")
    print("   👉 If you have multiple accounts, click your profile icon")
    print("      in Gmail and switch to whichever account you want.")
    print("   👉 Make sure the desired account is open in the active tab.")
    print("=" * 65)
    
    while True:
        cmd_input = input("\n👉 Type 'send' (or press Enter) when ready to start sending: ").strip().lower()
        if cmd_input in ['send', 's', 'start', 'y', 'yes', '']:
            break
        elif cmd_input in ['q', 'quit', 'exit']:
            print("Cancelled by user.")
            driver.quit()
            return
        else:
            print("Type 'send' and hit Enter to start, or 'quit' to exit.")

    # Detect the active Gmail account and handle from the user's currently open tab
    account_prefix, sender_email, target_handle = detect_active_gmail_account(driver)
    sender_display = f"<{sender_email}> " if sender_email else ""
    print(f"\n✅ Active Sender Account Detected: {sender_display}(Account {account_prefix})")
    print(f"🚀 Dispatching all emails from this account!\n")

    total = len(df)
    print(f"[3/3] Iterating {total} email contact(s)...")

    global_subject = load_global_subject()
    global_body = load_global_body_template()
    global_attachment = load_global_attachment()

    print(f"📧 Campaign Subject: '{global_subject}'")
    if global_attachment:
        print(f"📎 Campaign Attachment: {os.path.basename(global_attachment)}")
    print()

    success_count = 0
    fail_count = 0

    for index, row in df.iterrows():
        # Always verify and switch to the user's chosen Gmail tab
        try:
            if target_handle in driver.window_handles:
                driver.switch_to.window(target_handle)
            elif driver.window_handles:
                driver.switch_to.window(driver.window_handles[-1])
            else:
                print("❌ Browser was closed. Exiting.")
                break
        except Exception:
            pass

        name = str(row[name_col]).strip() if name_col and not pd.isna(row[name_col]) else "Valued Contact"
        email = str(row[email_col]).strip()

        if not email or email.lower() == "nan" or "@" not in email:
            print(f"⚠️ [{index+1}/{total}] Skipping invalid email for {name}: '{email}'")
            fail_count += 1
            continue

        # Subject: row override if present, otherwise global subject
        if subject_col and not pd.isna(row[subject_col]) and str(row[subject_col]).strip():
            subject = str(row[subject_col]).strip().replace("{Name}", name)
        else:
            subject = global_subject.replace("{Name}", name)

        # Body / Message: row override if present, otherwise global body template
        if body_col and not pd.isna(row[body_col]) and str(row[body_col]).strip():
            message = str(row[body_col]).strip().replace("{Name}", name)
        else:
            message = global_body.replace("{Name}", name)

        # Attachment / Image path: row override if present, otherwise global attachment
        attachment_path = None
        if attachment_col and not pd.isna(row[attachment_col]) and str(row[attachment_col]).strip():
            raw_att = str(row[attachment_col]).strip()
            if os.path.exists(raw_att):
                attachment_path = raw_att
            else:
                rel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), raw_att)
                if os.path.exists(rel_path):
                    attachment_path = rel_path
        if not attachment_path:
            attachment_path = global_attachment

        print(f"  ↳ [{index+1}/{total}] Sending email to {name} ({email})...", end=" ", flush=True)

        sent = False
        try:
            sent = send_in_current_inbox(driver, email, subject, message, attachment_path)
        except Exception as e:
            print(f"❌ [FAILED]: {e}")
            fail_count += 1
            continue

        if sent:
            print("[OK]")
            success_count += 1

        # Safe rate-pacing delay between emails
        time.sleep(3)

    print("\n" + "=" * 50)
    print("🎉 All emails processed!")
    print(f"   Successfully Sent: {success_count}")
    print(f"   Failed/Skipped:    {fail_count}")
    print("=" * 50)

    time.sleep(3)
    driver.quit()

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV_FILE
    send_bulk_emails(csv_file)
