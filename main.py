import os
import random
import string
import json
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

TOKEN = os.environ.get("BOT_TOKEN")  # Set this in your environment on Render
bot = Bot(token=TOKEN)

# In-memory user data (use a DB for production)
user_data = {}

app = Flask(__name__)

# Generate CAPTCHA text
def generate_captcha_text(length=5):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Create a simple CAPTCHA image
def create_captcha_image(text):
    image = Image.new('RGB', (150, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 10), text, font=font, fill=(0, 0, 0))
    image.save("captcha.png")

# /start or /captcha command handler
def captcha(update, context):
    user_id = update.effective_user.id
    captcha_text = generate_captcha_text()
    create_captcha_image(captcha_text)

    # Save CAPTCHA text
    user_data[user_id] = {"captcha": captcha_text, "balance": user_data.get(user_id, {}).get("balance", 0)}

    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("captcha.png", 'rb'))
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply with the CAPTCHA text.")

# /balance command handler
def balance(update, context):
    user_id = update.effective_user.id
    balance = user_data.get(user_id, {}).get("balance", 0)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your balance: {balance}")

# Handle text (to check CAPTCHA answer)
def handle_text(update, context):
    user_id = update.effective_user.id
    message = update.message.text.strip()
    if user_id in user_data and "captcha" in user_data[user_id]:
        correct = user_data[user_id]["captcha"]
        if message.upper() == correct:
            user_data[user_id]["balance"] += 1
            context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Correct! +1 point")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Incorrect CAPTCHA")
        # Remove CAPTCHA after checking
        del user_data[user_id]["captcha"]

# Webhook setup
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot is running'

# Dispatcher
from telegram.ext import Updater
updater = Updater(token=TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", captcha))
dp.add_handler(CommandHandler("captcha", captcha))
dp.add_handler(CommandHandler("balance", balance))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

# For local testing:
# updater.start_polling()
# updater.idle()
