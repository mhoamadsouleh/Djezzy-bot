import telebot
import asyncio
import json
import os
from datetime import datetime
import aiohttp

# توكن البوت مباشرة داخل الكود
TOKEN = '7723535106:AAH_8dQhq7QwVWh5JZf2iTrW4pgrT7vIykQ'
bot = telebot.TeleBot(TOKEN)

data_file = 'djezzy_data.json'

def load_data():
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def hide_phone(msisdn):
    return msisdn[:4] + '***' + msisdn[-2:]

async def send_otp(msisdn):
    url = 'https://apim.djezzy.dz/oauth2/registration'
    payload = f'msisdn={msisdn}&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&scope=smsotp'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, headers=headers) as res:
                await res.json()
                return True
    except:
        return False

async def verify_otp(msisdn, otp):
    url = 'https://apim.djezzy.dz/oauth2/token'
    payload = f'otp={otp}&mobileNumber={msisdn}&scope=openid&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&client_secret=MVpXHW_ImuMsxKIwrJpoVVMHjRsa&grant_type=mobile'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, headers=headers) as res:
                return await res.json() if res.status == 200 else None
    except:
        return None

def can_activate_today(user):
    last = user.get('last_applied')
    if last:
        return datetime.fromisoformat(last).date() != datetime.now().date()
    return True

@bot.message_handler(commands=['start'])
def start_msg(msg):
    bot.send_message(msg.chat.id, 'أرسل رقمك Djezzy (يبدأ بـ 07):')
    bot.register_next_step_handler(msg, handle_number)

def handle_number(msg):
    chat_id = msg.chat.id
    phone = msg.text.strip()
    if phone.startswith('07') and len(phone) == 10:
        msisdn = '213' + phone[1:]
        bot.send_message(chat_id, 'جارٍ إرسال رمز OTP...')
        asyncio.run(send_otp(msisdn))
        bot.send_message(chat_id, 'أدخل الرمز المرسل إليك:')
        bot.register_next_step_handler(msg, lambda m: handle_otp(m, msisdn))
    else:
        bot.send_message(chat_id, '⚠️ أدخل رقم صحيح يبدأ بـ 07.')

def handle_otp(msg, msisdn):
    chat_id = msg.chat.id
    otp = msg.text.strip()
    result = asyncio.run(verify_otp(msisdn, otp))
    if result:
        data = load_data()
        user = data.get(str(chat_id), {})
        if not can_activate_today(user):
            bot.send_message(chat_id, '⚠️ تم التفعيل اليوم. حاول غدًا.')
            return
        data[str(chat_id)] = {
            'username': msg.from_user.username,
            'msisdn': msisdn,
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
            'last_applied': datetime.now().isoformat()
        }
        save_data(data)
        bot.send_message(chat_id, f"✅ تم التفعيل بنجاح!\nرقم: {hide_phone(msisdn)}\nتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        bot.send_message(chat_id, '❌ الرمز غير صحيح. حاول من جديد.')

bot.remove_webhook()          
bot.polling()
