from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
X_EMAIL = os.getenv('X_EMAIL')
X_USERNAME = os.getenv('X_USERNAME')
X_PASSWORD = os.getenv('X_PASSWORD')
X_URL = os.getenv('X_URL')
OS_TYPE = os.getenv('OS_TYPE')

def send_discord_notify(message):
    data = {
        'content': message
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print("ส่งแจ้งเตือนสำเร็จ")
    else:
        print("การแจ้งเตือนล้มเหลว:", response.text)

def init_and_login():
    print("OS Type:", OS_TYPE)
    if OS_TYPE == 'windows':
        s = Service('C:\\webdriver\\chromedriver.exe')
        driver = webdriver.Chrome(service=s)
    elif OS_TYPE == 'linux':
        s = Service('/usr/local/bin/chromedriver')
        driver = webdriver.Chrome(service=s)
    else:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        s = Service('/usr/local/bin/chromedriver-linux64/chromedriver')
        driver = webdriver.Chrome(service=s, options=chrome_options)

    driver.get('https://twitter.com/login')
    time.sleep(5)
    
    print("กำลัง Login...")
    try:
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        username_field.send_keys(X_USERNAME)
        username_field.send_keys(Keys.RETURN)
        time.sleep(2)

        try:
            print("เช็คอีเมลหรือโทรศัพท์")
            verification_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            verification_field.send_keys(X_EMAIL)
            verification_field.send_keys(Keys.RETURN)
            time.sleep(2)
        except Exception as e:
            print("ไม่พบการขอให้กรอกอีเมลหรือโทรศัพท์")

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(X_PASSWORD)
        password_field.send_keys(Keys.RETURN)
    except Exception as e:
        print(f"การ Login ล้มเหลว: {e}")
        driver.quit()
        return None

    print("Login สำเร็จ")
    time.sleep(5)
    driver.get(X_URL)
    return driver

def cleanup_old_tweets(sent_tweet_links, expiry_time=timedelta(minutes=5)):
    current_time = datetime.now()
    expired_links = [link for link, added_time in sent_tweet_links.items() if current_time - added_time > expiry_time]
    for link in expired_links:
        del sent_tweet_links[link]
    print(f"Cleaned up {len(expired_links)} expired tweet links.")

def get_latest_tweets(driver, sent_tweet_links):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-testid="tweetText"]'))
        )
        tweets = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        print("จำนวนทวีตที่พบ:", len(tweets))
        
        tweet_data = []
        for tweet in tweets:
            try:
                tweet_time_element = tweet.find_element(By.XPATH, './/time')
                tweet_time = tweet_time_element.get_attribute('datetime')
                
                tweet_time_utc = datetime.strptime(tweet_time, "%Y-%m-%dT%H:%M:%S.000Z")
                tweet_time_gmt7 = tweet_time_utc + timedelta(hours=7)
                
                current_time_gmt7 = datetime.now()
                
                time_diff = current_time_gmt7 - tweet_time_gmt7
                if time_diff.total_seconds() <= 120:
                    tweet_text = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                    
                    if "งานจะจัดวันที่" not in tweet_text:
                        try:
                            tweet_link_element = tweet.find_element(By.XPATH, './/a[contains(@href, "/status/")]')
                            tweet_link = tweet_link_element.get_attribute('href')
                        
                            if tweet_link not in sent_tweet_links:
                                tweet_data.append({
                                    'text': tweet_text,
                                    'link': tweet_link
                                })
                                sent_tweet_links[tweet_link] = current_time_gmt7
                        except Exception as e:
                            print(e)
                            continue
            except Exception as e:
                print(f"An error occurred while fetching tweet data: {e}")
                continue
        return tweet_data
    except Exception as e:
        print(f"ไม่พบข้อมูลทวีตหรือเกิดข้อผิดพลาด: {e}")
        return []

def main():
    sent_tweet_links = {}
    driver = init_and_login()
    if driver is None:
        return
    
    try:
        while True:
            latest_tweets = get_latest_tweets(driver, sent_tweet_links)
            if latest_tweets:
                for tweet in latest_tweets:
                    message = f"<=====โพสต์ใหม่=====>\n{tweet['text']}\nลิงก์: {tweet['link']}"
                    send_discord_notify(message)
            
            time.sleep(40)
            driver.refresh()
            cleanup_old_tweets(sent_tweet_links)
    except KeyboardInterrupt:
        print("โปรแกรมหยุดทำงาน")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
