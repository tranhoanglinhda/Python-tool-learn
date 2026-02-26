from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv, find_dotenv
import os


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
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.pinterest.com")

        xpath_login = "/html/body/div[1]/div[1]/header/div[1]/nav/div[2]/div[2]/button/div/div"
        try:
            login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_login)))
            login_btn.click()
        except Exception:
            # continue anyway - page may show login fields directly
            pass

        email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
        password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
        email_input.send_keys(email)
        password_input.send_keys(password)

        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
        submit.click()

        if keep_open:
            print("Login attempted — browser will remain open. Press Enter here to close and exit.")
            input()

        # If we created a default profile_dir and there's a .env file (or we'll create one), save it so future runs reuse it
        if wrote_profile_to_env:
            target_env = dotenv_path if dotenv_path else os.path.join(os.getcwd(), ".env")
            _write_env_var(target_env, "CHROME_PROFILE_DIR", profile_dir)
            print(f"Saved CHROME_PROFILE_DIR to {target_env}")

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
