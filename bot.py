import os
import json
import asyncio
import requests
import uvicorn
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import hmac
import hashlib
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DNSE_TOKEN = os.getenv("DNSE_TOKEN")

tg_app = ApplicationBuilder().token(BOT_TOKEN).build()

DATA_FILE = "sectors.json"

sector_bank = {
    "Chứng khoán": "SSI",
    "BĐS": "TCB",
    "Doanh nghiệp": "VCB",
    "Tín dụng": "VPB",
    "SME": "MBB",
    "Tiêu dùng": "HDB"
}
def dnse_signature(payload):

    secret = os.getenv("DNSE_SECRET").encode()

    return hmac.new(
        secret,
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
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



def get_dnse_portfolio():

    api_key = os.getenv("DNSE_API_KEY")
    secret = os.getenv("DNSE_SECRET")
    account = os.getenv("DNSE_ACCOUNT")

    timestamp = str(int(time.time()*1000))

    payload = f"accountNo={account}&timestamp={timestamp}"

    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    url = f"https://api.dnse.com.vn/v2/positions?{payload}&signature={signature}"

    headers = {
        "X-API-KEY": api_key
    }

    try:

        res = requests.get(url, headers=headers)

        print("DNSE STATUS:", res.status_code)
        print("DNSE RESPONSE:", res.text)

        if res.status_code != 200:
            return None

        return res.json()

    except Exception as e:

        print("DNSE ERROR:", e)
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📊 DNSE Portfolio Bot Ready"
    )


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    portfolio = get_dnse_portfolio()

    if portfolio is None:

        await update.message.reply_text(
            "❌ không đọc được DNSE"
        )
        return

    msg = "📊 PORTFOLIO DNSE\n\n"

    try:

        for stock in portfolio["data"]:

            symbol = stock["symbol"]
            qty = stock["quantity"]

            msg += f"{symbol} : {qty}\n"

    except:

        msg = "❌ DNSE format lỗi"

    await update.message.reply_text(msg)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_data()

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ /add SYMBOL SECTOR\nVD: /add SSI Chứng_khoán"
        )
        return

    symbol = context.args[0].upper()
    sector = context.args[1].replace("_"," ")

    if sector not in data:

        await update.message.reply_text("❌ ngành không tồn tại")
        return

    if symbol not in data[sector]:

        data[sector].append(symbol)

    save_data(data)

    await update.message.reply_text(
        f"✅ thêm {symbol} vào {sector}"
    )


async def sync(update: Update, context: ContextTypes.DEFAULT_TYPE):

    portfolio = get_dnse_portfolio()

    if portfolio is None:

        await update.message.reply_text(
            "❌ không đọc được DNSE"
        )
        return

    msg = "📊 DANH MỤC DNSE\n\n"

    try:

        for stock in portfolio["data"]:

            symbol = stock["symbol"]
            qty = stock["quantity"]

            msg += f"{symbol} : {qty}\n"

    except:

        msg = "❌ DNSE format lỗi"

    await update.message.reply_text(msg)

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("portfolio", portfolio))
tg_app.add_handler(CommandHandler("add", add))
tg_app.add_handler(CommandHandler("sync", sync))

fastapi_app = FastAPI()

@fastapi_app.on_event("startup")
async def startup():

    await tg_app.initialize()
    await tg_app.start()

    await tg_app.bot.set_webhook(
        f"{WEBHOOK_URL}/webhook"
    )

    print("✅ Bot ready")


@fastapi_app.post("/webhook")
async def telegram_webhook(req: Request):

    data = await req.json()

    update = Update.de_json(data, tg_app.bot)

    await tg_app.process_update(update)

    return {"ok": True}

if __name__ == "__main__":

    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT",10000))
    )
