# ================================
# IMPORT
# ================================
import os
import json
import requests
import telebot
from telebot import types
from fastapi import FastAPI, Request


# ================================
# CONFIG / ENV
# ================================
TOKEN = os.getenv("BOT_TOKEN")
DNSE_TOKEN = os.getenv("DNSE_TOKEN")

bot = telebot.TeleBot(TOKEN)
app = FastAPI()


# ================================
# DATA
# ================================
sector_bank = {
    "Chứng khoán": "SSI",
    "BĐS": "TCB",
    "Doanh nghiệp": "VCB",
    "Tín dụng": "VPB",
    "SME": "MBB",
    "Tiêu dùng": "HDB"
}

DATA_FILE = "sectors.json"


# ================================
# UTIL FUNCTIONS
# ================================
def load_data():

    if not os.path.exists(DATA_FILE):

        data = {
            "Chứng khoán": [],
            "BĐS": [],
            "Doanh nghiệp": [],
            "Tín dụng": [],
            "SME": [],
            "Tiêu dùng": []
        }

        save_data(data)
        return data

    with open(DATA_FILE,"r") as f:
        return json.load(f)


def save_data(data):

    with open(DATA_FILE,"w") as f:
        json.dump(data,f,indent=4)


# ================================
# DNSE API
# ================================
def get_dnse_portfolio():

    url = "https://api.lightspeed.dnse.com.vn/positions"

    headers = {
        "Authorization": f"Bearer {DNSE_TOKEN}"
    }

    try:

        res = requests.get(url,headers=headers)
        return res.json()

    except:

        return None


# ================================
# TELEGRAM HANDLERS
# ================================

@bot.message_handler(commands=['add'])
def add_stock(message):

    data = load_data()

    cmd = message.text.split()

    if len(cmd) < 3:
        bot.reply_to(
            message,
            "❌ Cú pháp: /add SYMBOL NGANH\nVí dụ: /add SSI Chứng_khoán"
        )
        return

    symbol = cmd[1].upper()
    sector = cmd[2].replace("_"," ")

    if sector not in data:
        bot.reply_to(message,"❌ ngành không tồn tại")
        return

    if symbol not in data[sector]:
        data[sector].append(symbol)

    save_data(data)

    bot.reply_to(message,f"✅ thêm {symbol} vào {sector}")


@bot.message_handler(commands=['portfolio'])
def portfolio(message):

    data = load_data()

    msg = "📊 PORTFOLIO THEO NGÀNH\n\n"

    for sector,stocks in data.items():

        msg += f"🏷 {sector}\n"
        msg += f"🏛 Đại diện: {sector_bank.get(sector,'')}\n"

        if len(stocks)==0:
            msg += "- (trống)\n"

        for s in stocks:
            msg += f"- {s}\n"

        msg += "\n"

    bot.send_message(message.chat.id,msg)


@bot.message_handler(commands=['sync'])
def sync_dnse(message):

    portfolio = get_dnse_portfolio()

    if portfolio is None:
        bot.reply_to(message,"❌ không lấy được dữ liệu DNSE")
        return

    msg = "📊 DANH MỤC DNSE\n\n"

    try:

        for stock in portfolio["data"]:

            symbol = stock["symbol"]
            qty = stock["quantity"]

            msg += f"{symbol} : {qty}\n"

    except:

        msg = "❌ dữ liệu DNSE sai format"

    bot.send_message(message.chat.id,msg)


# ================================
# FASTAPI WEBHOOK
# ================================
@app.post("/webhook")
async def telegram_webhook(req: Request):

    json_data = await req.json()

    update = types.Update.de_json(json_data)

    bot.process_new_updates([update])

    return {"ok": True}
