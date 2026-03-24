"""
BeClass 廍子國小 114學年度第2學期課後社團 自動報名模組
使用 undetected-chromedriver（本機）或 selenium headless（雲端 Railway）
模擬真實瀏覽器操作，繞過 Cloudflare 機器人防護。
"""
import os
import time
import logging

logger = logging.getLogger(__name__)

BECLASS_URL = "https://www.beclass.com/rid=3052575698eccf04320a"

# ── 判斷是否在雲端環境（Railway 會設定 RAILWAY_ENVIRONMENT 或 CHROME_BIN）──
IS_CLOUD = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('CHROME_BIN'))

# 社團清單（對應 BeClass 頁面上的 checkbox id：tb_extra_ID_1_{index}）
BECLASS_CLUBS = [
    # ── 星期一 ──
    {"index": 0,  "name": "桌球社A",                       "day": "星期一", "time": "16:10-17:00", "note": "限高年級"},
    {"index": 1,  "name": "MLS魔幻科學(操控者科技初階)",   "day": "星期一", "time": "16:10-17:00", "note": ""},
    {"index": 2,  "name": "MLS魔幻科學(地球尋寶隊進階)",   "day": "星期一", "time": "17:05-17:55", "note": ""},
    {"index": 3,  "name": "生物研究社(初級)",               "day": "星期一", "time": "16:10-17:00", "note": "限高年級"},
    {"index": 4,  "name": "籃球社(初階1)",                  "day": "星期一", "time": "16:10-17:00", "note": ""},
    {"index": 5,  "name": "籃球社(進階1)",                  "day": "星期一", "time": "17:05-17:55", "note": ""},
    {"index": 6,  "name": "水果鳥美術社(A班)",             "day": "星期一", "time": "16:10-17:55", "note": ""},
    {"index": 7,  "name": "樂樂足壘社(初階1)",              "day": "星期一", "time": "16:10-17:00", "note": ""},
    {"index": 8,  "name": "樂樂足壘社(進階1)",              "day": "星期一", "time": "16:10-17:00", "note": ""},
    {"index": 9,  "name": "樂樂足壘社(初階2)",              "day": "星期一", "time": "17:05-17:55", "note": ""},
    {"index": 10, "name": "樂樂足壘社(進階2)",              "day": "星期一", "time": "17:05-17:55", "note": ""},
    {"index": 11, "name": "3D列印玩創社",                   "day": "星期一", "time": "16:10-17:00", "note": ""},
    {"index": 12, "name": "Roblox遊戲創作大師班",           "day": "星期一", "time": "16:10-17:55", "note": ""},
    {"index": 13, "name": "扯鈴社1",                        "day": "星期一", "time": "16:10-17:55", "note": ""},
    {"index": 14, "name": "烏克麗麗(A班)",                  "day": "星期一", "time": "16:10-17:00", "note": ""},
    {"index": 15, "name": "烏克麗麗(B班)",                  "day": "星期一", "time": "17:05-17:55", "note": ""},
    # ── 星期二 ──
    {"index": 16, "name": "桌球社B",                        "day": "星期二", "time": "16:10-17:00", "note": "限高年級"},
    {"index": 17, "name": "黏土拼貼創意DIY",                "day": "星期二", "time": "16:10-17:00", "note": ""},
    {"index": 18, "name": "直排輪(初階)",                   "day": "星期二", "time": "16:10-17:00", "note": ""},
    {"index": 19, "name": "乾燥花藝創意社",                 "day": "星期二", "time": "16:10-17:00", "note": ""},
    {"index": 20, "name": "韻律體操社(初階)",               "day": "星期二", "time": "16:10-17:00", "note": ""},
    {"index": 21, "name": "韻律體操社(進階)",               "day": "星期二", "time": "17:05-17:55", "note": ""},
    {"index": 22, "name": "AI智能自走車",                   "day": "星期二", "time": "16:10-17:00", "note": ""},
    {"index": 23, "name": "超級魔法師(A班)",                "day": "星期二", "time": "16:10-17:00", "note": ""},
    {"index": 24, "name": "超級魔法師(B班)",                "day": "星期二", "time": "17:05-17:55", "note": ""},
    {"index": 25, "name": "迷你網球(A班)",                  "day": "星期二", "time": "16:10-17:00", "note": ""},
    {"index": 26, "name": "無人機足球",                     "day": "星期二", "time": "17:05-17:55", "note": ""},
    {"index": 27, "name": "扯鈴社2",                        "day": "星期二", "time": "16:10-17:55", "note": ""},
    {"index": 28, "name": "菲菲笛",                         "day": "星期二", "time": "17:05-17:55", "note": ""},
    # ── 星期三 ──
    {"index": 29, "name": "手作小點心",                     "day": "星期三", "time": "16:10-17:55", "note": ""},
    {"index": 30, "name": "籃球社(進階2)",                  "day": "星期三", "time": "17:05-17:55", "note": ""},
    {"index": 31, "name": "水果鳥美術社(B班)",             "day": "星期三", "time": "16:10-17:55", "note": ""},
    {"index": 32, "name": "樂樂足壘社(初階3)",              "day": "星期三", "time": "16:10-17:00", "note": ""},
    {"index": 33, "name": "樂樂足壘社(進階3)",              "day": "星期三", "time": "16:10-17:00", "note": ""},
    {"index": 34, "name": "小小調茶師-創意飲品",            "day": "星期三", "time": "16:10-17:55", "note": ""},
    {"index": 35, "name": "排球社(全校)",                   "day": "星期三", "time": "16:10-17:00", "note": ""},
    {"index": 36, "name": "輕鬆學陶笛(初階A)",              "day": "星期三", "time": "16:10-17:00", "note": ""},
    {"index": 37, "name": "輕鬆學陶笛(初階B)",              "day": "星期三", "time": "17:05-17:55", "note": ""},
    # ── 星期四 ──
    {"index": 49, "name": "壓克力畫話 初階班",              "day": "星期四", "time": "16:10-17:00", "note": ""},
    {"index": 50, "name": "壓克力畫話 進階班",              "day": "星期四", "time": "17:05-17:55", "note": ""},
    {"index": 51, "name": "生物研究社(進階)",               "day": "星期四", "time": "16:10-17:00", "note": "限高年級"},
    {"index": 52, "name": "彩繪擴香石社",                   "day": "星期四", "time": "17:05-17:55", "note": ""},
    {"index": 53, "name": "兒童瑜伽社",                     "day": "星期四", "time": "16:10-17:00", "note": ""},
    {"index": 54, "name": "不插電學程式設計",               "day": "星期四", "time": "17:05-17:55", "note": ""},
    {"index": 55, "name": "療癒手作-創課種子社",            "day": "星期四", "time": "16:10-17:00", "note": ""},
    {"index": 56, "name": "AI機器人程式+遊戲設計社",        "day": "星期四", "time": "16:10-17:00", "note": ""},
    {"index": 57, "name": "園藝社：「莓」好森活",           "day": "星期四", "time": "16:10-17:55", "note": ""},
    {"index": 58, "name": "扯鈴社3",                        "day": "星期四", "time": "16:10-17:55", "note": ""},
    {"index": 59, "name": "匹克球社",                       "day": "星期四", "time": "16:10-17:55", "note": ""},
    # ── 星期五 ──
    {"index": 38, "name": "黏土創作暨手作DIY 初階(A班)",   "day": "星期五", "time": "15:15-16:05", "note": ""},
    {"index": 39, "name": "黏土創作暨手作DIY 進階(B班)",   "day": "星期五", "time": "16:10-17:00", "note": ""},
    {"index": 40, "name": "國標律動社",                     "day": "星期五", "time": "15:15-16:05", "note": ""},
    {"index": 41, "name": "圍棋社（初階）",                 "day": "星期五", "time": "15:15-16:05", "note": ""},
    {"index": 42, "name": "圍棋社（進階）",                 "day": "星期五", "time": "16:10-17:00", "note": ""},
    {"index": 43, "name": "直排輪(進階)",                   "day": "星期五", "time": "15:15-16:05", "note": ""},
    {"index": 44, "name": "籃球社(初階3)",                  "day": "星期五", "time": "15:15-16:05", "note": ""},
    {"index": 45, "name": "籃球社(進階3)",                  "day": "星期五", "time": "16:10-17:00", "note": ""},
    {"index": 46, "name": "Buziwood影片實驗室",             "day": "星期五", "time": "15:15-17:00", "note": ""},
    {"index": 47, "name": "迷你網球(B班)",                  "day": "星期五", "time": "16:10-17:00", "note": ""},
    {"index": 48, "name": "扯鈴社4",                        "day": "星期五", "time": "15:15-17:00", "note": ""},
]


def submit_beclass(record: dict) -> dict:
    """
    使用 undetected-chromedriver（本機）或 headless Chromium（雲端）
    自動填寫並送出 BeClass 報名表。

    Args:
        record: 報名記錄字典，包含 student_name, id_number, gender,
                parent_email, phone, class_seat, club_indexes (list[int])

    Returns:
        {'success': bool, 'message': str}
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    driver = None
    try:
        if IS_CLOUD:
            # ── 雲端：使用系統 Chromium（headless）──
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options

            chrome_bin      = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
            chromedriver_bin = os.environ.get('CHROMEDRIVER_BIN', '/usr/bin/chromedriver')

            options = Options()
            options.binary_location = chrome_bin
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1280,900')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)

            service = Service(executable_path=chromedriver_bin)
            driver  = webdriver.Chrome(service=service, options=options)
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            logger.info("🌐 [雲端] 啟動 Chromium headless...")
        else:
            # ── 本機：使用 undetected-chromedriver（繞過 Cloudflare）──
            try:
                import undetected_chromedriver as uc
            except ImportError:
                return {'success': False, 'message': '缺少 undetected-chromedriver 套件，請執行 pip install undetected-chromedriver'}

            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = uc.Chrome(options=options)
            logger.info("🌐 [本機] 啟動 undetected Chrome...")

        wait = WebDriverWait(driver, 30)
        driver.get(BECLASS_URL)
        time.sleep(3)  # 等待 Cloudflare 驗證

        # ── 等待表單出現 ──
        wait.until(EC.presence_of_element_located((By.ID, 'username')))
        logger.info("✅ 表單已載入")

        # ── 填寫姓名 ──
        name_field = driver.find_element(By.ID, 'username')
        name_field.clear()
        name_field.send_keys(record['student_name'])

        # ── 填寫身分證（第2個 class=textbox required 的 input） ──
        text_inputs = driver.find_elements(By.CSS_SELECTOR, 'input.textbox.required')
        # text_inputs[0] = 姓名(id=username), [1] = 身分證, [2] = email, [3] = 電話
        if len(text_inputs) >= 2:
            text_inputs[1].clear()
            text_inputs[1].send_keys(record['id_number'])

        # ── 選擇性別 ──
        gender_value = '男' if record['gender'] == 'male' else '女'
        gender_radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
        for radio in gender_radios:
            try:
                if radio.get_attribute('value') == gender_value:
                    driver.execute_script("arguments[0].click();", radio)
                    break
            except Exception:
                pass

        # ── 填寫 Email ──
        email_fields = driver.find_elements(By.CSS_SELECTOR, 'input.validate-email')
        if email_fields:
            email_fields[0].clear()
            email_fields[0].send_keys(record['parent_email'])

        # ── 填寫手機 ──
        phone_fields = driver.find_elements(By.CSS_SELECTOR, 'input.validate-integer')
        if phone_fields:
            phone_fields[0].clear()
            phone_fields[0].send_keys(record['phone'])

        # ── 填寫班級座號（格式：年班座，如10101） ──
        seat_fields = driver.find_elements(By.CSS_SELECTOR, 'input[placeholder*="10101"]')
        if seat_fields:
            seat_fields[0].clear()
            seat_fields[0].send_keys(record['class_seat'])

        # ── 勾選社團（最多2個） ──
        club_indexes = record.get('club_indexes', [])[:2]  # 最多2個
        for idx in club_indexes:
            cb_id = f'tb_extra_ID_1_{idx}'
            try:
                checkbox = driver.find_element(By.ID, cb_id)
                if not checkbox.is_selected():
                    driver.execute_script("arguments[0].click();", checkbox)
                logger.info(f"✅ 已勾選社團 index={idx}")
            except Exception as e:
                logger.warning(f"找不到社團 checkbox {cb_id}: {e}")

        time.sleep(1)

        # ── 點擊送出按鈕 ──
        submit_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"]')
        if not submit_buttons:
            # BeClass 通常有 class=submit_btn 的按鈕
            submit_buttons = driver.find_elements(By.CSS_SELECTOR, '.submit_btn, .btn_submit, input[value*="確認"], input[value*="送出"], input[value*="報名"]')

        if submit_buttons:
            driver.execute_script("arguments[0].click();", submit_buttons[0])
            logger.info("📤 已點擊送出按鈕，等待回應...")
            time.sleep(5)
        else:
            # 嘗試直接觸發表單 submit
            driver.execute_script("document.querySelector('form').submit();")
            time.sleep(5)

        # ── 判斷結果（依頁面內容） ──
        page_text = driver.page_source
        success_keywords = ['報名成功', '已完成報名', '謝謝您', 'success', '完成']
        fail_keywords    = ['報名截止', '已截止', '錯誤', 'error', '失敗', 'fail', '身分證已存在', '重複']

        for kw in success_keywords:
            if kw.lower() in page_text.lower():
                logger.info(f"✅ 報名成功！關鍵字：{kw}")
                return {'success': True, 'message': f'報名成功（頁面包含：{kw}）'}

        for kw in fail_keywords:
            if kw.lower() in page_text.lower():
                logger.error(f"❌ 報名失敗，關鍵字：{kw}")
                return {'success': False, 'message': f'報名失敗（頁面包含：{kw}）'}

        # 若無法判斷，截圖存檔供人工確認
        screenshot_path = f"data/screenshot_{record.get('id', 'unknown')}.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"⚠️ 無法判斷結果，截圖已存至 {screenshot_path}")
        return {'success': True, 'message': f'已送出，請人工確認截圖：{screenshot_path}'}

    except Exception as e:
        logger.error(f"❌ BeClass 自動報名發生錯誤：{e}", exc_info=True)
        return {'success': False, 'message': str(e)}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
