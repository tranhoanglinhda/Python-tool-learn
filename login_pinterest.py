from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv, find_dotenv
import os
import time


dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path, override=True)
else:
    load_dotenv()


def _write_env_var(path: str, key: str, value: str) -> None:
    """Write or update a single KEY=VALUE in the dotenv file at path.
    If path does not exist, it will be created.
    """
    try:
        if not path:
            path = os.path.join(os.getcwd(), ".env")
        # Read existing lines if file exists
        lines = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        key_prefix = f"{key}="
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith(key_prefix):
                lines[i] = f"{key}={value}\n"
                found = True
                break

        if not found:
            lines.append(f"{key}={value}\n")

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception:
        # Best-effort: do not crash the script for file write errors
        pass


def upload_image(driver, wait, image_path: str) -> None:
    """Upload image using the provided full XPath; fallback to input[type=file]."""
    try:
        short_wait = WebDriverWait(driver, 10)  # shorter timeout for individual elements
        long_wait = WebDriverWait(driver, 15)   # longer timeout for tricky elements like description
        
        print(f"Navigating to pin-creation page to upload: {image_path}")
        driver.get('https://www.pinterest.com/pin-creation-tool/')
        time.sleep(1)  # let page initialize (reduced from 2s)
        
        # find and send file
        xpath_input = '/html/body/div[1]/div[1]/div/div[3]/div/div/div/div[2]/div[2]/div/div/div[2]/div/div/div[1]/div/div[1]/div/input'
        try:
            file_input = short_wait.until(EC.presence_of_element_located((By.XPATH, xpath_input)))
            print("✅ Found file input by XPath")
        except TimeoutException:
            print("⚠️ XPath not found, trying CSS selector")
            file_input = short_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))

        file_input.send_keys(image_path)
        print("✅ File path sent to input")
        time.sleep(3)  # let upload process start
        
        # wait for upload to complete (thumbnail appearing)
        print("⏳ Waiting for upload to complete...")
        try:
            short_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='pin-draft']")))
            print("✅ Upload complete - thumbnail present")
        except TimeoutException:
            print("⚠️ Thumbnail not found in 10 sec - page might have changed")
            driver.save_screenshot("upload_debug.png")
            time.sleep(2)  # wait anyway
        
        # fill title if provided
        title_text = os.getenv("PIN_TITLE", "")
        if title_text:
            try:
                title_xpath = '/html/body/div[1]/div[1]/div/div[3]/div/div/div/div[2]/div[2]/div/div/div[2]/div/div/div[2]/div/div/div/div[1]/div/div/div/input'
                title_el = short_wait.until(EC.element_to_be_clickable((By.XPATH, title_xpath)))
                title_el.click()
                time.sleep(0.5)
                title_el.clear()
                title_el.send_keys(title_text)
                print(f"✅ Title set: {title_text}")
            except TimeoutException:
                print(f"❌ Title input not found (check XPath)")
            except Exception as e:
                print(f"❌ Failed to set title: {e}")
        
        # fill description if provided
        desc_text = os.getenv("PIN_DESCRIPTION", "")
        if desc_text:
            desc_xpath = '/html/body/div[1]/div[1]/div/div[3]/div/div/div/div[2]/div[2]/div/div/div[2]/div/div/div[2]/div/div/div/div[2]/div/div[2]/div/div/div/div[1]/div/div[2]/div/div/div[1]/div/div/div/div/div'
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    desc_el = long_wait.until(EC.presence_of_element_located((By.XPATH, desc_xpath)))
                    # scroll into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", desc_el)
                    time.sleep(0.8)
                    # click to focus
                    desc_el.click()
                    time.sleep(0.8)
                    # use JavaScript to set text directly (more reliable for contenteditable)
                    driver.execute_script("""
                    arguments[0].textContent = arguments[1];
                    arguments[0].innerText = arguments[1];
                    var event = new Event('input', { bubbles: true });
                    arguments[0].dispatchEvent(event);
                    """, desc_el, desc_text)
                    time.sleep(0.5)
                    print(f"✅ Description set: {desc_text}")
                    break
                except TimeoutException:
                    print(f"❌ Description input not found (attempt {retry_count+1}/{max_retries})")
                    if retry_count == max_retries - 1:
                        break
                    retry_count += 1
                    time.sleep(1)
                except Exception as e:
                    print(f"❌ Failed to set description (attempt {retry_count+1}/{max_retries}): {e}")
                    if retry_count == max_retries - 1:
                        break
                    retry_count += 1
                    time.sleep(1)
        
        # click publish
        try:
            publish_xpath = '/html/body/div[1]/div[1]/div/div[3]/div/div/div/div[2]/div[2]/div/div/div[1]/div[2]/div[2]/div/button/div/div'
            publish_btn = short_wait.until(EC.element_to_be_clickable((By.XPATH, publish_xpath)))
            publish_btn.click()
            print("✅ Publish button clicked!")
        except TimeoutException:
            print("❌ Publish button not found (check XPath)")
            driver.save_screenshot("publish_button_missing.png")
        except Exception as e:
            print(f"❌ Failed to click publish: {e}")
    
    except Exception as e:
        print(f"❌ Unexpected error in upload_image: {e}")
        driver.save_screenshot("upload_error_debug.png")
        raise

def main():
    email = os.getenv("PINTEREST_EMAIL")
    password = os.getenv("PINTEREST_PASSWORD")
    if not email or not password:
        print("Please set PINTEREST_EMAIL and PINTEREST_PASSWORD in a .env file (see .env.example)")
        return

    keep_open = os.getenv("KEEP_OPEN", "true").lower() in ("1", "true", "yes")

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")

    # Use a persistent Chrome profile directory so login persists between runs.
    # If CHROME_PROFILE_DIR is not set in .env, create a default and write it back to .env after first run.
    profile_dir = os.getenv("CHROME_PROFILE_DIR")
    wrote_profile_to_env = False
    if not profile_dir:
        profile_dir = os.path.abspath(os.path.join(os.getcwd(), "chrome_profile"))
        wrote_profile_to_env = True

    if profile_dir:
        profile_dir = os.path.abspath(os.path.expanduser(profile_dir))
        try:
            os.makedirs(profile_dir, exist_ok=True)
        except Exception:
            pass
        options.add_argument(f"--user-data-dir={profile_dir}")
        print(f"Using Chrome profile directory: {profile_dir}")
        print("Ensure no other Chrome instance is running with that profile before starting the script.")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 5)  # reduced from 20s for faster navigation

    try:
        driver.get("https://www.pinterest.com")

        xpath_login = "/html/body/div[1]/div[1]/header/div[1]/nav/div[2]/div[2]/button/div/div"
        try:
            login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_login)))
            login_btn.click()
        except Exception:
            # continue anyway - page may show login fields directly
            pass

        # Try to find login fields; if they're not present we assume we're already logged in
        try:
            email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
            password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
            email_input.send_keys(email)
            password_input.send_keys(password)

            submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
            submit.click()
        except TimeoutException:
            print("Login form not found — continuing with existing session or different layout.")

        # After login (or if already logged in), attempt upload
        image_path = os.getenv("PIN_IMAGE_PATH", os.path.abspath("image.png"))
        if os.path.exists(image_path):
            try:
                upload_image(driver, wait, image_path)
            except Exception as e:
                print(f"image upload failed: {e}")
        else:
            print(f"image file not found at {image_path}, skipping upload")

        # If we created a default profile_dir and there's a .env file (or we'll create one), save it so future runs reuse it
        if wrote_profile_to_env:
            target_env = dotenv_path if dotenv_path else os.path.join(os.getcwd(), ".env")
            _write_env_var(target_env, "CHROME_PROFILE_DIR", profile_dir)
            print(f"Saved CHROME_PROFILE_DIR to {target_env}")
    finally:
        try:
            if not keep_open:
                driver.quit()
            else:
                print("Keeping browser open (KEEP_OPEN=true). Close manually when finished.")
        except Exception:
            pass


if __name__ == "__main__":
    main()
