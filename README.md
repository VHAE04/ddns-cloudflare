# 🎯 Mục tiêu của script DDNS:

Script này tự động cập nhật địa chỉ IP công cộng của bạn lên các bản ghi DNS tại Cloudflare khi phát hiện IP thay đổi, và đồng thời gửi thông báo đến Telegram. Tính năng chính:

✅ Lấy địa chỉ IP công cộng hiện tại.

✅ So sánh với IP đã lưu lần trước.

✅ Nếu IP thay đổi:

Gửi yêu cầu cập nhật bản ghi DNS (A, *, www) trên Cloudflare thông qua API.

Gửi thông báo tới Telegram qua bot.

✅ Tự động chạy định kỳ (mỗi 60 giây – có thể điều chỉnh).



```python
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

```

file config.txt
CLOUDFLARE_RECORD_ID1 2 3 bạn thay lần lượt là domain , bản ghi * và bản ghi www\

```bash
CLOUDFLARE_TOKEN=krRbKr2DZNp-_xxx
CLOUDFLARE_ZONE_ID=7f81ad414eb8xxx
CLOUDFLARE_RECORD_ID=2f41c7fd7820xxx
CLOUDFLARE_RECORD_ID2=5c94f15ede2xxx
CLOUDFLARE_RECORD_ID3=7aefd1ef3xxx
DNS_NAME=bugineverything.com
TELEGRAM_BOT_TOKEN=7931912773:AAF7i_Z89HsA9hIdxxx
TELEGRAM_CHAT_ID=51527xxx
```

để lấy bạn CLOUDFLARE_RECORD_ID có thể dùng 

```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/YOUR_ZONE_ID/dns_records" -H "Authorization: Bearer YOUR_API_TOKEN" -H "Content-Type: application/json"
```

sau đó chạy lệnh sẽ gửi về telegram bạn mỗi khi ip thay đổi 

![image](https://github.com/user-attachments/assets/344db71b-3f25-49a0-8255-a63c327ac98b)



