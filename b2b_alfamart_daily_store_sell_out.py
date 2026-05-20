# ========== CUSTOMIZE THESE ==========
import os
TOTP_SECRET_KEY = os.environ.get("TOTP_SECRET_KEY", "YOUR_FALLBACK_KEY")
# ====================================

import time
import pyotp
import pytz
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ---------- AUTO DATE CALCULATION (Jakarta Time) ----------
jakarta_tz = pytz.timezone('Asia/Jakarta')
today = datetime.now(jakarta_tz)

end_date = today - timedelta(days=2)
start_date = datetime(today.year, today.month, 1, tzinfo=jakarta_tz)

if end_date < start_date:
    if today.month == 1:
        start_date = datetime(today.year - 1, 12, 1, tzinfo=jakarta_tz)
    else:
        start_date = datetime(today.year, today.month - 1, 1, tzinfo=jakarta_tz)

START_DATE = start_date.strftime("%d-%m-%Y")
END_DATE   = end_date.strftime("%d-%m-%Y")
print(f"Auto date range (Jakarta time): {START_DATE} → {END_DATE}")

# ---------- START BROWSER ----------
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
# Headless mode is not needed because we need to interact with the page
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    # ---------- LOGIN ----------
    driver.get("https://b2b.alfamart.co.id/login.php")
    time.sleep(2)
    driver.find_element(By.NAME, "uname").send_keys("O-0108_10")
    driver.find_element(By.NAME, "upass").send_keys("Scarlett2024!")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Login']").click()

    # ---------- 2FA ----------
    time.sleep(3)
    totp = pyotp.TOTP(TOTP_SECRET_KEY)
    current_otp = totp.now()
    print(f"Generated OTP: {current_otp}")
    driver.find_element(By.NAME, "code").send_keys(current_otp)
    driver.find_element(By.XPATH, "//button[text()='Verify']").click()

    # ---------- CLOSE POPUP ----------
    time.sleep(3)
    try:
        wait = WebDriverWait(driver, 5)
        overlay = wait.until(EC.presence_of_element_located((By.ID, "promoOverlay")))
        if overlay.is_displayed():
            driver.find_element(By.CLASS_NAME, "close-btn").click()
            print("Promo popup closed.")
    except:
        print("No popup.")
    time.sleep(3)

    # ---------- OPEN Dashboard & Modular (Laporan menu) ----------
    wait = WebDriverWait(driver, 20)
    # Ensure the Laporan menu is present
    laporan_menu = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Laporan')]")))
    actions = ActionChains(driver)
    actions.move_to_element(laporan_menu).perform()
    print("Hovered over Laporan menu.")
    time.sleep(2)

    # Wait for Dashboard & Modular link to be clickable
    dashboard_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='get_laporan_new_premium.php']")))
    driver.execute_script("arguments[0].scrollIntoView(true);", dashboard_link)
    time.sleep(0.5)
    try:
        dashboard_link.click()
        print("Clicked Dashboard & Modular link.")
    except:
        driver.execute_script("arguments[0].click();", dashboard_link)
        print("JavaScript click executed.")

    # ---------- SWITCH TO NEW TAB ----------
    time.sleep(3)
    original_tab = driver.current_window_handle
    new_tab = None
    for tab in driver.window_handles:
        if tab != original_tab:
            new_tab = tab
            break
    if new_tab is None:
        raise Exception("New tab did not open!")
    driver.switch_to.window(new_tab)
    print("Switched to new tab.")
    time.sleep(3)

    # ---------- CLICK "Report Modular" ----------
    # Wait for the switch buttons to load
    wait = WebDriverWait(driver, 15)
    modular_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='performancesales-modular']")))
    driver.execute_script("arguments[0].scrollIntoView(true);", modular_link)
    time.sleep(1)
    modular_link.click()
    print("Clicked 'Report Modular'.")
    time.sleep(4)  # Allow the report type selector to load

    # ---------- SELECT "Performance by Item by Store by Day" ----------
    # Wait for the jenis performance dropdown to be present
    wait = WebDriverWait(driver, 15)
    jenis_dropdown = wait.until(EC.presence_of_element_located((By.ID, "jenis_performace")))
    jenis_performance = Select(jenis_dropdown)
    jenis_performance.select_by_value("4")
    print("Selected 'Performance by Item by Store by Day'.")
    time.sleep(3)  # Let the filter form change

    # ---------- SET DATE RANGE ----------
    start_input = driver.find_element(By.ID, "periode_awal")
    driver.execute_script("arguments[0].removeAttribute('readonly')", start_input)
    start_input.clear()
    start_input.send_keys(START_DATE)
    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", start_input)

    end_input = driver.find_element(By.ID, "periode_akhir")
    driver.execute_script("arguments[0].removeAttribute('readonly')", end_input)
    end_input.clear()
    end_input.send_keys(END_DATE)
    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", end_input)
    print(f"Periode set: {START_DATE} to {END_DATE}")

    # ---------- LOOP THROUGH CATEGORIES + UNITS ----------
    categories = [
        ("3222", "BEAUTY LIQUID SOAP"),
        ("3251", "BODY LOTION"),
        ("3253", "BODY SCRUB"),
        ("3252", "BODY SERUM"),
        ("3246", "FACE MASK"),
        ("3243", "FACIAL CLEANSER TONIC"),
        ("3241", "FACIAL WASH SOAP"),
        ("3245", "MOISTURIZER"),
        ("8012", "PROMOTION GOODS MEMBER"),
        ("3249", "SERUM ESSENCE"),
        ("3240", "SUNSCREEN"),
        ("3232", "WOMEN PARFUME & EDT")
    ]
    units = [("v", "Value"), ("q", "Qty")]

    for cat_value, cat_name in categories:
        print(f"\n{'='*60}")
        print(f"📂 Category: {cat_name}")
        print('='*60)

        # Wait for category dropdown to be ready
        cat_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "category-filter-report-modular-3"))
        )
        category_select = Select(cat_dropdown)
        category_select.select_by_value(cat_value)
        print(f"Category set to: {cat_name}")
        time.sleep(1)

        for unit_value, unit_name in units:
            print(f"   📥 Download for Unit: {unit_name}")
            unit_select = Select(driver.find_element(By.ID, "unit-filter-report-modular-3"))
            unit_select.select_by_value(unit_value)
            time.sleep(1)

            download_btn = driver.find_element(By.ID, "download-xls")
            download_btn.click()
            print(f"   ⏳ Clicked download for {cat_name} | {unit_name}")

            # Handle alert (success or rate limit)
            try:
                time.sleep(1)
                alert = driver.switch_to.alert
                alert_text = alert.text
                print(f"   ⚠️ Alert: {alert_text}")
                alert.accept()
            except:
                print(f"   ✅ No alert – download triggered.")
            time.sleep(5)

        time.sleep(3)

    print("\n🎉 All done! Check your email for the reports.")
    time.sleep(10)  # Give time for any final alerts

except Exception as e:
    print(f"An error occurred: {e}")
    # Save a screenshot for debugging
    try:
        driver.save_screenshot("error_screenshot.png")
        print("Screenshot saved as error_screenshot.png")
    except:
        pass
    time.sleep(30)

finally:
    driver.quit()
