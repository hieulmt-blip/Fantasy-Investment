import telebot
from telebot import types
import json
import os
from fastapi import FastAPI, Request

TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)
app = FastAPI()

sector_bank = {
    "Chứng khoán": "TCB",
    "BĐS": "TCB",
    "Doanh nghiệp": "VCB",
    "Tín dụng": "VPB",
    "SME": "MBB",
    "Xuất khẩu": "BID"
}

def load_data():
    with open("sectors.json","r") as f:
        return json.load(f)

def save_data(data):
    with open("sectors.json","w") as f:
        json.dump(data,f,indent=4)

@bot.message_handler(commands=['add'])
def add_stock(message):

    data = load_data()

    cmd = message.text.split()

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
        msg += f"🏦 Bank: {sector_bank.get(sector,'')}\n"

        if len(stocks)==0:
            msg += "- (trống)\n"

        for s in stocks:
            msg += f"- {s}\n"

        msg += "\n"

    bot.send_message(message.chat.id,msg)

@app.post("/webhook")
async def telegram_webhook(req: Request):

    json_data = await req.json()

    update = types.Update.de_json(json_data)

    bot.process_new_updates([update])

    return {"ok": True}
