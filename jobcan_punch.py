"""
Jobcan 自动打卡脚本
使用方法:
    python jobcan_punch.py in    # 上班打刻
    python jobcan_punch.py out   # 下班退勤

前置条件:
    1. 已安装 selenium、cryptography:
       python -m pip install selenium cryptography
    2. 已运行过一次性手动登录，并在独立Chrome profile (C:\\jobcan_profile)
       中允许了该网站的GPS定位权限。
    3. 已运行过 save_password.py，在 C:\\jobcan_profile 下生成了
       key.bin 和 pwd.bin 两个加密密码文件。
    4. 任务计划程序里登录方式设为"不管用户是否登录都运行"时，
       务必启用下面的 --headless=new 无头模式。
"""

import sys
import time
from cryptography.fernet import Fernet
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===================== 基本配置（按需修改） =====================
PROFILE_DIR = r"C:\jobcan_profile"
LOGIN_URL = "https://ssl.jobcan.jp/login/mb-employee-global?redirect_to=%2Fm%2Fwork%2Faccessrecord%3F_m%3Dadit"

COMPANY_ID = "solisline"
EMAIL = "hanlei@solisline.com"

KEY_FILE = r"C:\jobcan_profile\key.bin"
PWD_FILE = r"C:\jobcan_profile\pwd.bin"

LOG_FILE = r"C:\Users\LENOVO\Downloads\jobcan_punch_log.txt"
SUCCESS_SHOT = r"C:\Users\LENOVO\Downloads\debug_success.png"
ERROR_SHOT = r"C:\Users\LENOVO\Downloads\debug_error.png"
ERROR_HTML = r"C:\Users\LENOVO\Downloads\debug_page_source.html"
# =================================================================

action = sys.argv[1] if len(sys.argv) > 1 else "in"
button_id = "adit_item_6" if action == "in" else "adit_item_7"


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_password():
    with open(KEY_FILE, "rb") as f:
        key = f.read()
    with open(PWD_FILE, "rb") as f:
        encrypted = f.read()
    return Fernet(key).decrypt(encrypted).decode()


driver = None

try:
    PASSWORD = load_password()
    if not PASSWORD:
        raise ValueError("密码为空，请检查 key.bin / pwd.bin 是否正确生成")

    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    prefs = {"profile.default_content_setting_values.geolocation": 1}
    options.add_experimental_option("prefs", prefs)
    # "不管用户是否登录都运行"模式下没有可见桌面，必须用无头模式
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,1696")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    driver.get(LOGIN_URL)

    # ===== 登录 =====
    client_id_field = wait.until(EC.presence_of_element_located((By.NAME, "client_id")))
    client_id_field.clear()
    client_id_field.send_keys(COMPANY_ID)

    email_field = driver.find_element(By.NAME, "email")
    email_field.clear()
    email_field.send_keys(EMAIL)

    password_field = driver.find_element(By.NAME, "password")
    password_field.clear()
    password_field.send_keys(PASSWORD)

    driver.find_element(By.CSS_SELECTOR, "button[onclick='setCookie()']").click()

    # ===== 点击 打刻/退勤 按钮 =====
    wait.until(EC.element_to_be_clickable((By.ID, button_id))).click()

    # ===== GPS定位环节：可能需要手动点击链接，也可能已自动完成并跳转 =====
    try:
        gfs_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[onclick=\"getGFS()\"]"))
        )
        gfs_link.click()
        log("已点击GPS定位链接")
    except Exception:
        log("未找到GPS定位链接，可能已自动跳转，继续流程")

    # ===== 最终确认页面，点击"はい" =====
    yes_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "yes"))
    )
    log(f"到达确认页面，当前URL: {driver.current_url}")

    try:
        yes_button.click()
    except Exception:
        driver.execute_script("arguments[0].click();", yes_button)

    time.sleep(2)
    log(f"打卡完成: {action} (button_id={button_id})")
    driver.save_screenshot(SUCCESS_SHOT)

except Exception as e:
    log(f"失败: {type(e).__name__}: {repr(e)}")
    try:
        if driver:
            log(f"失败时当前URL: {driver.current_url}")
            driver.save_screenshot(ERROR_SHOT)
            with open(ERROR_HTML, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
    except Exception:
        pass

finally:
    if driver:
        driver.quit()