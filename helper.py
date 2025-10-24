import json
import os

CONFIG_FILE = "config.json"


def load_config(self):
    """Tải cookie, api_key, và access_token từ file config.json nếu có"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                self.cookie = config_data.get("cookie", "")
                self.api_key = config_data.get("api_key", "")
                self.access_token = config_data.get("access_token", "")  # <-- THÊM DÒNG NÀY
        except Exception as e:
            print(f"Lỗi khi tải config: {e}")
            # (Có thể xóa file config lỗi nếu cần)
            # os.remove(CONFIG_FILE)


def get_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                return config_data
        except Exception as e:
            print(f"Lỗi khi tải config: {e}")
    return None
