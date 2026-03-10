#!/usr/bin/env python3
"""
Instagram Unlimited Bulk SMS Sender - NO LIMIT
================================================
✅ Enter any number of phone numbers
✅ Send SMS to all with one click
✅ Real-time progress tracking
✅ Stop anytime with Ctrl+C
✅ Works with all countries (+233, +880, etc)
"""

import os
import sys
import time
import json
import random
import requests
import signal
from datetime import datetime
from colorama import Fore, Style, init
from fake_useragent import UserAgent

# Rich library import
try:
    from rich import print
    from rich.panel import Panel
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
except:
    os.system("pip install rich")
    from rich import print
    from rich.panel import Panel
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text

init(autoreset=True)

# Global flag for stopping
stop_flag = False

def signal_handler(sig, frame):
    """Handle Ctrl+C to stop gracefully"""
    global stop_flag
    print(f"\n{Fore.YELLOW}⚠️ Stopping... Please wait{Fore.RESET}")
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)

# Folder setup
folder_path = '/sdcard/Instagram_Unlimited'
try:
    os.makedirs(folder_path, exist_ok=True)
except:
    pass

os.system("clear")

# User Agent
ua = UserAgent()

def ugenX():
    """Random user agent"""
    return ua.random

def instagram_user_agent():
    """Instagram specific user agent"""
    insta_versions = ['269.0.0.18.75', '270.0.0.19.82', '271.0.0.20.95', '272.0.0.21.110']
    android_versions = ['27', '28', '29', '30', '31', '32', '33']
    devices = ['SM-G975F', 'Pixel 4', 'Redmi Note 8', 'OnePlus 7 Pro', 'Mi 9T Pro', 
               'Tecno Spark', 'Infinix Hot', 'Itel S23', 'Nokia 5.4', 'Samsung A12']
    
    return f'Instagram {random.choice(insta_versions)} Android ({random.choice(android_versions)}/{random.randint(8,10)}; {random.randint(380,420)}dpi; {random.randint(1080,1440)}x{random.randint(1920,2560)}; {random.choice(devices)}; {random.choice(["qcom","mt6765"])}; en_US; {random.randint(100000000,999999999)})'

def get_ip_info():
    """Get IP information"""
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        data = response.json()
        ip = requests.get('https://api.ipify.org/', timeout=5).text
        country = data.get("country", "Unknown")
        return ip, country
    except:
        return "Unknown", "Unknown"

# Get IP info
ip_address, country_name = get_ip_info()

def clean_phone(phone):
    """Clean phone number"""
    return phone.replace('+', '').replace(' ', '').replace('-', '')

def validate_phone(phone):
    """Basic phone validation"""
    if not phone.startswith('+'):
        phone = '+' + phone
    # Remove any spaces
    phone = phone.replace(' ', '')
    # Check if it has at least 10 digits after +
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) < 10:
        return False, None
    return True, phone

def send_sms_to_number(phone_number, index, total):
    """Send verification SMS to a single number"""
    
    clean_num = clean_phone(phone_number)
    
    # Multiple APIs to try
    apis = [
        {
            'name': 'Primary API',
            'url': 'https://i.instagram.com/api/v1/accounts/send_signup_sms_code/',
            'headers': {
                'User-Agent': instagram_user_agent(),
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-IG-App-ID': '936619743392459',
                'Accept-Language': 'en-US',
            },
            'data': {
                'phone_number': clean_num,
                'device_id': f'android-{random.randint(100000, 999999)}'
            }
        },
        {
            'name': 'Web API',
            'url': 'https://www.instagram.com/api/v1/accounts/send_signup_sms_code/',
            'headers': {
                'User-Agent': ugenX(),
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            'data': {
                'phone_number': '+' + clean_num
            }
        },
        {
            'name': 'Lookup API',
            'url': 'https://i.instagram.com/api/v1/users/lookup_phone/',
            'headers': {
                'User-Agent': instagram_user_agent(),
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            },
            'data': {
                'phone_number': clean_num,
                'country_code': clean_num[:3]
            }
        }
    ]
    
    # Try each API
    for api in apis:
        try:
            response = requests.post(
                api['url'], 
                headers=api['headers'], 
                data=api['data'], 
                timeout=10
            )
            
            if response.status_code in [200, 201, 202, 204]:
                return {
                    'success': True,
                    'api': api['name'],
                    'message': f'Sent via {api["name"]}'
                }
        except:
            continue
    
    return {
        'success': False,
        'api': 'None',
        'message': 'All APIs failed'
    }

def collect_numbers():
    """Collect phone numbers from user"""
    numbers = []
    
    print(f"\n{Fore.YELLOW}📝 Enter phone numbers (with country code):{Fore.RESET}")
    print(f"{Fore.CYAN}Example: +233xxxxxxxxx, +88017xxxxxxxxx{Fore.RESET}")
    print(f"{Fore.GREEN}Press ENTER without number to finish{Fore.RESET}\n")
    
    i = 1
    while True:
        num = input(f"{Fore.CYAN}Number {i}: {Fore.WHITE}").strip()
        
        if not num:
            if i == 1:
                print(f"{Fore.RED}❌ Please enter at least one number{Fore.RESET}")
                continue
            break
        
        valid, clean_num = validate_phone(num)
        if valid:
            numbers.append(clean_num)
            print(f"{Fore.GREEN}  ✅ Added: {clean_num}{Fore.RESET}")
            i += 1
        else:
            print(f"{Fore.RED}  ❌ Invalid number format{Fore.RESET}")
    
    return numbers

def main():
    """Main function"""
    global stop_flag
    
    # Clear screen
    os.system("clear")
    
    # Show banner
    print(Panel(
        f"""[bold magenta2]📱 INSTAGRAM UNLIMITED BULK SMS SENDER[/bold magenta2]
[cyan]├─ Your IP: {Fore.GREEN}{ip_address}[/cyan]
[cyan]├─ Country: {Fore.GREEN}{country_name}[/cyan]
[cyan]└─ No limit - Enter any number of phones[/cyan]""",
        style="bold magenta2"
    ))
    
    # Collect numbers
    numbers = collect_numbers()
    
    if not numbers:
        print(f"{Fore.RED}❌ No numbers entered!{Fore.RESET}")
        return
    
    total = len(numbers)
    
    # Show summary
    print(Panel(
        f"""{Fore.GREEN}📋 TOTAL NUMBERS: {total}{Fore.RESET}
{chr(10).join([f'  {i+1}. {num}' for i, num in enumerate(numbers[:5])])}{'...' if total > 5 else ''}""",
        style="bold magenta2"
    ))
    
    confirm = input(f"\n{Fore.YELLOW}Send SMS to all {total} numbers? (y/n): {Fore.WHITE}").strip().lower()
    if confirm != 'y':
        print(f"{Fore.RED}❌ Operation cancelled!")
        return
    
    # Reset stop flag
    stop_flag = False
    
    # Progress tracking
    results = []
    success_count = 0
    fail_count = 0
    
    print(f"\n{Fore.MAGENTA}{'='*70}{Fore.RESET}")
    print(f"{Fore.CYAN}📤 SENDING SMS TO {total} NUMBERS...{Fore.RESET}")
    print(f"{Fore.YELLOW}Press Ctrl+C to stop at any time{Fore.RESET}")
    print(f"{Fore.MAGENTA}{'='*70}{Fore.RESET}\n")
    
    # Create progress table
    table = Table(title="📊 Live Progress", style="bold magenta", show_header=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Phone Number", style="yellow", width=18)
    table.add_column("Status", style="green", width=40)
    table.add_column("Time", style="blue", width=8)
    
    console = Console()
    
    # Send SMS to each number
    for i, number in enumerate(numbers, 1):
        if stop_flag:
            print(f"\n{Fore.YELLOW}⚠️ Stopped by user after {i-1} numbers{Fore.RESET}")
            break
        
        # Send SMS
        result = send_sms_to_number(number, i, total)
        
        if result['success']:
            success_count += 1
            status = f"{Fore.GREEN}✅ {result['message']}{Fore.RESET}"
        else:
            fail_count += 1
            status = f"{Fore.RED}❌ {result['message']}{Fore.RESET}"
        
        results.append({
            'number': number,
            'success': result['success'],
            'message': result['message'],
            'time': datetime.now().strftime('%H:%M:%S')
        })
        
        # Add to table
        table.add_row(
            str(i),
            number,
            f"{'✅' if result['success'] else '❌'} {result['message'][:30]}",
            datetime.now().strftime('%H:%M:%S')
        )
        
        # Clear and redisplay table every 5 numbers or at the end
        if i % 5 == 0 or i == total or stop_flag:
            os.system('clear')
            print(Panel(
                f"""[bold magenta2]📱 PROGRESS: {i}/{total} - ✅ {success_count} | ❌ {fail_count}[/bold magenta2]""",
                style="bold magenta2"
            ))
            console.print(table)
            print(f"\n{Fore.CYAN}Press Ctrl+C to stop...{Fore.RESET}")
        
        # Random delay between requests (except last)
        if i < total and not stop_flag:
            delay = random.uniform(2, 4)
            print(f"\n{Fore.YELLOW}⏳ Waiting {delay:.1f} seconds...{Fore.RESET}")
            time.sleep(delay)
    
    # Show final results
    os.system('clear')
    print(Panel(
        f"""[bold magenta2]📱 FINAL RESULTS[/bold magenta2]
[cyan]├─ Total Processed: {len(results)}[/cyan]
[cyan]├─ {Fore.GREEN}✅ Successful: {success_count}[/cyan]
[cyan]└─ {Fore.RED}❌ Failed: {fail_count}[/cyan]""",
        style="bold magenta2"
    ))
    
    # Show final table
    final_table = Table(title="📋 Final Results", style="bold magenta")
    final_table.add_column("#", style="cyan", width=4)
    final_table.add_column("Phone Number", style="yellow")
    final_table.add_column("Status", style="green", width=30)
    final_table.add_column("Time", style="blue")
    
    for i, res in enumerate(results, 1):
        status_icon = "✅" if res['success'] else "❌"
        final_table.add_row(str(i), res['number'], f"{status_icon} {res['message']}", res['time'])
    
    console.print(final_table)
    
    # Save results to file
    filename = f"{folder_path}/unlimited_sms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Instagram Unlimited SMS Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*70}\n")
        f.write(f"IP: {ip_address}\n")
        f.write(f"Country: {country_name}\n")
        f.write(f"Total Numbers: {len(results)}\n")
        f.write(f"Success: {success_count}\n")
        f.write(f"Failed: {fail_count}\n")
        f.write(f"{'='*70}\n\n")
        
        for i, res in enumerate(results, 1):
            f.write(f"{i}. {res['number']} - {'SUCCESS' if res['success'] else 'FAILED'} - {res['message']} - {res['time']}\n")
        
        f.write(f"\n{'='*70}\n")
    
    print(f"\n{Fore.GREEN}✅ Results saved to: {filename}{Fore.RESET}")
    
    input(f"\n{Fore.YELLOW}Press Enter to continue...{Fore.RESET}")

def menu():
    """Main menu"""
    while True:
        os.system("clear")
        print(Panel(
            f"""
╔══════════════════════════════════════════════════════════════╗
║     📱 INSTAGRAM UNLIMITED SMS SENDER - NO LIMIT            ║
║     ✅ Enter any number of phones (2, 3, 10, 100...)        ║
║     ✅ Works with all countries (+233, +880, etc)           ║
║     ✅ Stop anytime with Ctrl+C                              ║
║     ✅ Real-time progress tracking                          ║
║     ✅ Auto-save results                                     ║
╚══════════════════════════════════════════════════════════════╝
[IP: {ip_address} | Country: {country_name}]""",
            style="bold magenta2"
        ))
        
        print(Panel(
            f"""{Fore.YELLOW}[{Fore.CYAN}1{Fore.YELLOW}]{Fore.GREEN} 📱 SEND SMS TO MULTIPLE NUMBERS
{Fore.YELLOW}[{Fore.CYAN}2{Fore.YELLOW}]{Fore.GREEN} 📁 VIEW SAVED RESULTS
{Fore.YELLOW}[{Fore.CYAN}3{Fore.YELLOW}]{Fore.GREEN} 📊 QUICK STATS
{Fore.YELLOW}[{Fore.CYAN}0{Fore.YELLOW}]{Fore.RED} 🚪 EXIT""",
            style="bold magenta2"
        ))
        
        choice = input(f"{Fore.MAGENTA}└──> ").strip()
        
        if choice in ["1", "01"]:
            main()
        elif choice in ["2", "02"]:
            os.system(f"ls -la {folder_path}")
            print(Panel(f"{Fore.GREEN}📁 Results saved in: {folder_path}", style="bold magenta2"))
            input(f"{Fore.YELLOW}Press Enter to continue...")
        elif choice in ["3", "03"]:
            try:
                files = os.listdir(folder_path)
                print(Panel(f"{Fore.GREEN}📊 Total sessions: {len(files)}", style="bold magenta2"))
            except:
                print(Panel(f"{Fore.YELLOW}No data yet", style="bold magenta2"))
            input(f"{Fore.YELLOW}Press Enter to continue...")
        elif choice in ["0", "00"]:
            print(f"{Fore.GREEN}👋 Goodbye!")
            sys.exit()
        else:
            print(Panel(f"{Fore.RED}❌ OPTION NOT FOUND IN MENU", style="bold magenta2"))
            time.sleep(1)

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Program stopped by user")
    except Exception as e:
        print(Panel(f"{Fore.RED}❌ CRITICAL ERROR: {str(e)}", style="bold magenta2"))