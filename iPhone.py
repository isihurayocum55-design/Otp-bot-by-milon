#!/usr/bin/env python3
"""
Instagram & Facebook Auto OTP Sender - StexSMS Integration (FAST MODE)
=======================================================================
✅ Enhanced login reliability for iSH (iPhone shell) environment
✅ Auto retries with exponential backoff
✅ Token validation after login
✅ Graceful fallback if colorama missing
=======================================================================
"""

import os
import sys
import time
import json
import random
import requests
import re
from datetime import datetime

# Try to import colorama, but fallback to plain text if not available
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    # Dummy color classes
    class Fore:
        RESET = ''; BLACK = ''; RED = ''; GREEN = ''; YELLOW = ''; BLUE = ''; MAGENTA = ''; CYAN = ''; WHITE = ''
    class Style:
        RESET_ALL = ''; BRIGHT = ''
    HAS_COLORAMA = False

# =============================================
# CONFIGURATION
# =============================================
NUMBERS_PER_RANGE = 15
INSTAGRAM_OTPS_PER_NUMBER = 2
FACEBOOK_OTPS_PER_NUMBER = 10
DELAY_BETWEEN_OTP = 1
FACEBOOK_DELAY_BETWEEN_OTP = 4
DELAY_BETWEEN_NUMBERS = 2
MAX_RETRIES = 3
AUTO_RESTART_DELAY = 5
MAX_CYCLES = 999999

# =============================================
# LOGIN RETRY DECORATOR / HELPER
# =============================================
def retry_on_failure(max_retries=3, delay=1, backoff=2):
    """Decorator to retry a function on failure."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                try:
                    result = func(*args, **kwargs)
                    if result:
                        return result
                except Exception as e:
                    print(f"{Fore.YELLOW}Attempt {retries+1}/{max_retries} failed: {e}{Fore.RESET}")
                retries += 1
                if retries < max_retries:
                    print(f"{Fore.YELLOW}Retrying in {current_delay}s...{Fore.RESET}")
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator

# =============================================
# STEXSMS CLIENT (ENHANCED)
# =============================================
class StexSMSClient:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.cookies_dict = {}
        self.cookies_string = ""
        self.headers = {}
        self.logged_in = False

    @retry_on_failure(max_retries=3, delay=2, backoff=2)
    def login(self, email, password):
        """Login to StexSMS with automatic retries."""
        print(f"\n{Fore.YELLOW}📡 Logging in to StexSMS...{Fore.RESET}")

        login_url = "https://stexsms.com/mapi/v1/mauth/login"
        headers = {
            "sec-ch-ua-platform": "\"Android\"",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; TECNO KE6j Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.159 Mobile Safari/537.36",
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://stexsms.com",
            "x-requested-with": "mark.via.gp",
            "referer": "https://stexsms.com/mauth/login",
        }
        login_data = {"email": email, "password": password}
        initial_cookies = {"twk_idm_key": "hzIEEDc3xRCxApDeILYAZ", "TawkConnectionTime": "0"}

        try:
            resp = self.session.post(login_url, json=login_data, headers=headers, cookies=initial_cookies, timeout=30)
            if resp.status_code != 200:
                print(f"{Fore.RED}HTTP {resp.status_code}{Fore.RESET}")
                return False

            data = resp.json()
            # Check success
            if not (data.get('meta', {}).get('status') == 'success' or data.get('status') == 'success'):
                error = data.get('message', 'Unknown error')
                print(f"{Fore.RED}Login failed: {error}{Fore.RESET}")
                return False

            # Extract token
            self.token = data.get('data', {}).get('token') or data.get('token')
            if not self.token:
                # Try to get token from cookies (sometimes set automatically)
                self.token = self.session.cookies.get('mauthtoken')
            if not self.token:
                print(f"{Fore.RED}No token in response or cookies{Fore.RESET}")
                return False

            # Save cookies
            self.cookies_dict = self.session.cookies.get_dict()
            # Ensure token is in cookies
            if 'mauthtoken' not in self.cookies_dict:
                self.cookies_dict['mauthtoken'] = self.token
            self.cookies_string = ', '.join([f"{k}={v}" for k, v in self.cookies_dict.items()])

            # Prepare headers for future requests
            self.headers = {
                "sec-ch-ua-platform": "\"Android\"",
                "user-agent": "Mozilla/5.0 (Linux; Android 10; TECNO KE6j Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.159 Mobile Safari/537.36",
                "accept": "application/json, text/plain, */*",
                "mauthtoken": self.token,
                "x-requested-with": "mark.via.gp",
                "referer": "https://stexsms.com/mdashboard/console",
            }

            # Validate login by fetching console info
            if not self._validate_token():
                print(f"{Fore.RED}Token validation failed{Fore.RESET}")
                return False

            self.logged_in = True
            print(f"{Fore.GREEN}✅ Login successful!{Fore.RESET}")
            return True

        except Exception as e:
            print(f"{Fore.RED}Login error: {e}{Fore.RESET}")
            return False

    def _validate_token(self):
        """Check if token works by making a lightweight request."""
        try:
            resp = self.session.get("https://stexsms.com/mapi/v1/mdashboard/console/info",
                                    headers=self.headers, cookies=self.cookies_dict, timeout=10)
            if resp.status_code == 200 and 'data' in resp.json():
                return True
        except:
            pass
        return False

    def get_console_info(self):
        if not self.logged_in:
            return None
        try:
            resp = self.session.get("https://stexsms.com/mapi/v1/mdashboard/console/info",
                                    headers=self.headers, cookies=self.cookies_dict, timeout=30)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return None

    def get_facebook_numbers_from_console(self):
        data = self.get_console_info()
        if not data:
            return []
        numbers = []
        try:
            for log in data.get('data', {}).get('logs', []):
                if 'facebook' in log.get('app_name', '').lower():
                    num = log.get('number')
                    if num and num not in numbers:
                        numbers.append(num)
        except:
            pass
        return numbers

    def get_first_range_from_facebook(self):
        nums = self.get_facebook_numbers_from_console()
        if not nums:
            return None
        first = nums[0]
        return first[:-3] + 'XXX' if len(first) >= 3 else first

    def get_number_from_range(self, range_pattern):
        if not self.logged_in:
            return None
        url = "https://stexsms.com/mapi/v1/mdashboard/getnum/number"
        headers = self.headers.copy()
        headers['referer'] = f"https://stexsms.com/mdashboard/getnum?range={range_pattern}"
        headers['content-type'] = 'application/json'
        data = {"range": range_pattern, "is_national": False, "remove_plus": False}
        try:
            resp = self.session.post(url, json=data, headers=headers, cookies=self.cookies_dict, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                # Try different possible keys
                num = result.get('data', {}).get('number') or result.get('data', {}).get('full_number') or result.get('data', {}).get('copy') or result.get('number')
                return num
        except:
            pass
        return None

    def get_numbers_from_range(self, range_pattern, count=NUMBERS_PER_RANGE):
        numbers = []
        print(f"{Fore.YELLOW}📡 Getting {count} numbers from {range_pattern}...{Fore.RESET}")
        for i in range(count):
            print(f"   {Fore.CYAN}Fetching {i+1}/{count}...{Fore.RESET}", end='\r')
            num = self.get_number_from_range(range_pattern)
            if num:
                numbers.append(num)
                print(f"   {Fore.GREEN}✅ Got: {num}{' ' * 20}")
            else:
                print(f"   {Fore.RED}❌ Failed{' ' * 30}")
            if i < count - 1:
                time.sleep(0.3)
        unique = list(set(numbers))
        print(f"{Fore.GREEN}✅ Got {len(unique)} unique numbers{Fore.RESET}")
        return unique[:count]

# =============================================
# OTP FUNCTIONS (Instagram, Facebook)
# =============================================
def instagram_user_agent():
    versions = ['269.0.0.18.75', '270.0.0.19.82', '271.0.0.20.95', '272.0.0.21.110']
    android = ['27', '28', '29', '30', '31', '32', '33']
    devices = ['SM-G975F', 'Pixel 4', 'Redmi Note 8', 'OnePlus 7 Pro', 'Mi 9T Pro']
    return f'Instagram {random.choice(versions)} Android ({random.choice(android)}/{random.randint(8,10)}; {random.randint(380,420)}dpi; {random.randint(1080,1440)}x{random.randint(1920,2560)}; {random.choice(devices)}; qcom; en_US; {random.randint(100000000,999999999)})'

def send_instagram_otp(phone_number):
    clean = re.sub(r'[^0-9]', '', phone_number)
    url = "https://i.instagram.com/api/v1/accounts/send_signup_sms_code/"
    headers = {
        'User-Agent': instagram_user_agent(),
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-IG-App-ID': '936619743392459',
        'Accept-Language': 'en-US',
    }
    data = {'phone_number': clean, 'device_id': f'android-{random.randint(100000, 999999)}'}
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=8)
        if resp.status_code == 200:
            return True, "✅"
        elif resp.status_code == 400:
            return True if 'already' in resp.text.lower() else False, "⚠️" if 'already' in resp.text.lower() else "❌"
        elif resp.status_code == 429:
            return False, "⏳"
        return False, "❌"
    except:
        return False, "❌"

def clean_phone(phone):
    return re.sub(r'[^0-9]', '', phone)

def get_country_code(phone):
    if phone.startswith('1') and len(phone) == 11:
        return '1'
    elif phone.startswith('880') and len(phone) >= 11:
        return '880'
    elif phone.startswith('91') and len(phone) >= 10:
        return '91'
    elif phone.startswith('92') and len(phone) >= 10:
        return '92'
    elif phone.startswith('966') and len(phone) >= 9:
        return '966'
    elif phone.startswith('971') and len(phone) >= 9:
        return '971'
    elif phone.startswith('20') and len(phone) >= 10:
        return '20'
    elif phone.startswith('234') and len(phone) >= 10:
        return '234'
    elif phone.startswith('254') and len(phone) >= 9:
        return '254'
    elif phone.startswith('261') and len(phone) >= 9:
        return '261'
    else:
        return phone[:3] if len(phone) >= 3 else phone

def send_facebook_otp_v1(phone):
    clean = clean_phone(phone)
    cc = get_country_code(clean)
    url = "https://www.facebook.com/api/graphql/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.facebook.com",
        "Referer": "https://www.facebook.com/login/identify/",
        "X-FB-LSD": f"AVr{random.randint(1000,9999)}-{random.randint(1000,9999)}"
    }
    data = {
        "doc_id": "5093723633840143",
        "variables": json.dumps({"phone": clean, "country_code": cc, "source": "forgot_password", "is_prefetch": False})
    }
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        return resp.status_code == 200 and ('success' in resp.text.lower() or 'code_sent' in resp.text.lower())
    except:
        return False

def send_facebook_otp_v2(phone):
    clean = clean_phone(phone)
    url = "https://www.facebook.com/ajax/login/help/identify/send_code.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.facebook.com",
        "Referer": "https://www.facebook.com/login/identify/",
    }
    data = {"phone": clean, "country_code": get_country_code(clean), "source": "forgot_password", "__a": "1"}
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        return resp.status_code == 200 and '"success":true' in resp.text
    except:
        return False

def send_facebook_otp_v3(phone):
    clean = clean_phone(phone)
    url = "https://m.facebook.com/ajax/login/help/identify/send_code.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://m.facebook.com",
        "Referer": "https://m.facebook.com/login/identify/",
    }
    data = {"phone": clean, "country_code": get_country_code(clean), "source": "forgot_password", "__a": "1"}
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        return resp.status_code == 200 and '"success":true' in resp.text
    except:
        return False

def send_facebook_otp_v4(phone):
    clean = clean_phone(phone)
    url = "https://www.facebook.com/recover/initiate/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.facebook.com",
        "Referer": "https://www.facebook.com/login/identify/",
    }
    data = {"identifier": clean, "source": "forgot_password"}
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10, allow_redirects=False)
        return resp.status_code == 200 and ('checkpoint' in resp.url or 'recover' in resp.url)
    except:
        return False

def send_facebook_otp(phone):
    methods = [send_facebook_otp_v1, send_facebook_otp_v2, send_facebook_otp_v3, send_facebook_otp_v4]
    for method in methods:
        try:
            if method(phone):
                return True, "✅"
        except:
            continue
    return False, "❌"

# =============================================
# MODES (Instagram Auto Restart, Facebook)
# =============================================
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    print(f"""
{Fore.MAGENTA}╔══════════════════════════════════════════════════════════════╗
║     📱 INSTAGRAM & FACEBOOK AUTO OTP                          ║
║     ✅ Enhanced login for iSH (iPhone shell)                  ║
║     ✅ Auto login to StexSMS with retries                     ║
║     ✅ Fetch Facebook ranges                                  ║
║     ✅ Get 15 numbers per range                               ║
║     ✅ Instagram: 2 OTPs per number (FAST)                    ║
║     ✅ Instagram: AUTO RESTART after 15 accounts              ║
║     ✅ Facebook: 10 OTPs per number (4s apart)                ║
╚══════════════════════════════════════════════════════════════╝{Fore.RESET}
    """)

def instagram_mode_with_autorestart(client, email):
    cycle = 0
    while cycle < MAX_CYCLES:
        cycle += 1
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}📱 INSTAGRAM MODE - AUTO RESTART{Fore.RESET}")
        print(f"{Fore.GREEN}Logged in as: {email}{Fore.RESET}")
        print(f"{Fore.YELLOW}Cycle #{cycle}{Fore.RESET}\n")

        # Get range
        range_pat = client.get_first_range_from_facebook()
        if not range_pat:
            print(f"{Fore.RED}Failed to get range{Fore.RESET}")
            time.sleep(AUTO_RESTART_DELAY)
            continue
        print(f"{Fore.GREEN}Range: {range_pat}{Fore.RESET}\n")

        # Get numbers
        numbers = client.get_numbers_from_range(range_pat, NUMBERS_PER_RANGE)
        if not numbers:
            print(f"{Fore.RED}No numbers{Fore.RESET}")
            time.sleep(AUTO_RESTART_DELAY)
            continue

        print(f"\n{Fore.YELLOW}Sending {INSTAGRAM_OTPS_PER_NUMBER} OTPs per number...{Fore.RESET}\n")
        total_success = total_failed = total_otps = 0
        start = time.time()

        for idx, num in enumerate(numbers, 1):
            print(f"{Fore.CYAN}[{idx}/{len(numbers)}] {num}:{Fore.RESET} ", end='')
            successes = 0
            for _ in range(INSTAGRAM_OTPS_PER_NUMBER):
                ok, icon = send_instagram_otp(num)
                total_otps += 1
                if ok:
                    successes += 1
                    total_success += 1
                else:
                    total_failed += 1
                print(icon, end='')
                if _ < INSTAGRAM_OTPS_PER_NUMBER - 1:
                    time.sleep(DELAY_BETWEEN_OTP)
            print(f"  (✅{successes} ❌{INSTAGRAM_OTPS_PER_NUMBER-successes})")
            if idx < len(numbers):
                time.sleep(DELAY_BETWEEN_NUMBERS)

        elapsed = time.time() - start
        print(f"\n{Fore.GREEN}{'='*60}{Fore.RESET}")
        print(f"{Fore.GREEN}CYCLE #{cycle} COMPLETE{Fore.RESET}")
        print(f"Numbers: {len(numbers)} | OTPs: {total_otps}")
        print(f"✅ {total_success} | ❌ {total_failed} | ⏱️ {elapsed:.1f}s | ⚡ {total_otps/elapsed:.1f} OTPs/s")
        if total_otps:
            print(f"📊 Success rate: {total_success/total_otps*100:.1f}%")

        print(f"\n{Fore.YELLOW}🔄 Auto restart in {AUTO_RESTART_DELAY}s (Ctrl+C to stop){Fore.RESET}")
        try:
            for i in range(AUTO_RESTART_DELAY, 0, -1):
                print(f"\r⏳ Restarting in {i} seconds...", end='')
                time.sleep(1)
            print()
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Stopped by user{Fore.RESET}")
            again = input(f"{Fore.YELLOW}Continue auto restart? (y/n): ").strip().lower()
            if again != 'y':
                break

def facebook_mode(client):
    clear_screen()
    print_banner()
    print(f"{Fore.CYAN}📘 FACEBOOK MODE - 10 OTPs per number (4s apart){Fore.RESET}\n")
    range_pat = client.get_first_range_from_facebook()
    if not range_pat:
        print(f"{Fore.RED}Failed to get range{Fore.RESET}")
        input("Press Enter...")
        return
    print(f"{Fore.GREEN}Range: {range_pat}{Fore.RESET}\n")
    numbers = client.get_numbers_from_range(range_pat, NUMBERS_PER_RANGE)
    if not numbers:
        print(f"{Fore.RED}No numbers{Fore.RESET}")
        input("Press Enter...")
        return

    total_success = total_failed = total_otps = 0
    start = time.time()
    for idx, num in enumerate(numbers, 1):
        print(f"\n{Fore.CYAN}[{idx}/{len(numbers)}] {num}{Fore.RESET}")
        print(f"{Fore.CYAN}{'─'*50}{Fore.RESET}")
        success_count = 0
        for attempt in range(1, FACEBOOK_OTPS_PER_NUMBER + 1):
            print(f"  Attempt {attempt:2d}/{FACEBOOK_OTPS_PER_NUMBER}: ", end='')
            ok, icon = send_facebook_otp(num)
            total_otps += 1
            if ok:
                success_count += 1
                total_success += 1
                print(f"{Fore.GREEN}{icon} Success{Fore.RESET}")
            else:
                total_failed += 1
                print(f"{Fore.RED}{icon} Failed{Fore.RESET}")
            print(f"     Running: ✅{success_count} ❌{attempt-success_count} | Total: ✅{total_success} ❌{total_failed}")
            if attempt < FACEBOOK_OTPS_PER_NUMBER:
                print(f"     {Fore.YELLOW}⏳ Waiting {FACEBOOK_DELAY_BETWEEN_OTP}s...{Fore.RESET}")
                time.sleep(FACEBOOK_DELAY_BETWEEN_OTP)
        print(f"\n  📊 Number summary: ✅{success_count}/{FACEBOOK_OTPS_PER_NUMBER}")
        if idx < len(numbers):
            print(f"\n{Fore.YELLOW}⏳ Next number in {DELAY_BETWEEN_NUMBERS}s...{Fore.RESET}")
            time.sleep(DELAY_BETWEEN_NUMBERS)

    elapsed = time.time() - start
    print(f"\n{Fore.GREEN}{'='*60}{Fore.RESET}")
    print(f"{Fore.GREEN}FACEBOOK FINAL STATISTICS{Fore.RESET}")
    print(f"Numbers: {len(numbers)} | OTPs: {total_otps}")
    print(f"✅ {total_success} | ❌ {total_failed} | ⏱️ {elapsed:.1f}s | ⚡ {total_otps/elapsed:.1f} OTPs/s")
    if total_otps:
        print(f"📊 Success rate: {total_success/total_otps*100:.1f}%")
    input("\nPress Enter...")

# =============================================
# MAIN
# =============================================
def main():
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}🔐 STEXSMS LOGIN{Fore.RESET}")
        email = input(f"{Fore.CYAN}Email: {Fore.WHITE}").strip()
        password = input(f"{Fore.CYAN}Password: {Fore.WHITE}").strip()
        if not email or not password:
            print(f"{Fore.RED}Email and password required{Fore.RESET}")
            time.sleep(1)
            continue

        client = StexSMSClient()
        if not client.login(email, password):
            print(f"{Fore.RED}Login failed after retries{Fore.RESET}")
            retry = input(f"{Fore.YELLOW}Try again? (y/n): ").strip().lower()
            if retry != 'y':
                break
            continue

        # Main menu after successful login
        while True:
            clear_screen()
            print_banner()
            print(f"{Fore.GREEN}✅ Logged in as: {email}{Fore.RESET}\n")
            print(f"{Fore.CYAN}📌 SELECT OPTION:{Fore.RESET}")
            print(f"  [1] 📱 Instagram (2 OTPs/num - AUTO RESTART)")
            print(f"  [2] 📘 Facebook (10 OTPs/num - 4s apart)")
            print(f"  [3] 🔄 Switch Account")
            print(f"  [0] 🚪 Exit")
            choice = input(f"\n{Fore.MAGENTA}└─> {Fore.WHITE}").strip()

            if choice == '1':
                instagram_mode_with_autorestart(client, email)
            elif choice == '2':
                facebook_mode(client)
            elif choice == '3':
                print(f"{Fore.YELLOW}Switching account...{Fore.RESET}")
                break
            elif choice == '0':
                print(f"{Fore.GREEN}Goodbye!{Fore.RESET}")
                sys.exit()
            else:
                print(f"{Fore.RED}Invalid option{Fore.RESET}")
                time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Program stopped by user{Fore.RESET}")
    except Exception as e:
        print(f"\n{Fore.RED}Critical error: {e}{Fore.RESET}")