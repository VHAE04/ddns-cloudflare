import requests
import json
import os
import time
from pathlib import Path

# ==== Đọc file cấu hình ==== #
def load_config(file_path="config.txt"):
    config = {}
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file cấu hình: {file_path}")
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

# ==== Cấu hình từ file ==== #
config = load_config()

CLOUDFLARE_TOKEN = config["CLOUDFLARE_TOKEN"]
CLOUDFLARE_ZONE_ID = config["CLOUDFLARE_ZONE_ID"]
CLOUDFLARE_RECORD_ID = config["CLOUDFLARE_RECORD_ID"]
CLOUDFLARE_RECORD_ID2 = config["CLOUDFLARE_RECORD_ID2"]
CLOUDFLARE_RECORD_ID3 = config["CLOUDFLARE_RECORD_ID3"]
DNS_NAME = config["DNS_NAME"]

TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]

IP_FILE = Path("last_ip.txt")

# ==== Lấy IP Public ==== #
def get_public_ip():
    try:
        return requests.get("https://api.ipify.org").text.strip()
    except Exception as e:
        return None

# ==== Gửi thông báo Telegram ==== #
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

# ==== Cập nhật Cloudflare ==== #
def update_cloudflare_dns(ip):
    url = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records/{CLOUDFLARE_RECORD_ID}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "A",
        "name": DNS_NAME,
        "content": ip,
        "ttl": 1,
        "proxied": True
    }
    response = requests.put(url, headers=headers, data=json.dumps(data))
    url = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records/{CLOUDFLARE_RECORD_ID2}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "A",
        "name": "*",
        "content": ip,
        "ttl": 1,
        "proxied": True
    }
    response2 = requests.put(url, headers=headers, data=json.dumps(data))
    url = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records/{CLOUDFLARE_RECORD_ID3}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "A",
        "name": "www",
        "content": ip,
        "ttl": 1,
        "proxied": True
    }
    response3 = requests.put(url, headers=headers, data=json.dumps(data))
    return response.ok

# ==== Main Logic ==== #
def main():
    current_ip = get_public_ip()
    if not current_ip:
        print("Không lấy được IP.")
        return

    old_ip = IP_FILE.read_text().strip() if IP_FILE.exists() else ""
    if current_ip == old_ip:
        print("IP chưa thay đổi.")
        return

    success = update_cloudflare_dns(current_ip)
    if success:
        IP_FILE.write_text(current_ip)
        msg = f"✅ IP đã thay đổi và cập nhật thành công:\n{DNS_NAME} → {current_ip}"
        print(msg)
        send_telegram_message(msg)
    else:
        msg = f"❌ Lỗi khi cập nhật DNS Cloudflare với IP {current_ip}"
        print(msg)
        send_telegram_message(msg)

# ==== Vòng lặp chạy mỗi 5 phút ==== #
if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            error_msg = f"⚠️ Lỗi trong script cập nhật DNS:\n{str(e)}"
            print(error_msg)
            send_telegram_message(error_msg)
        time.sleep(60)  # Chờ 5 phút
