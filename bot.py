import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from telegram import ReplyKeyboardMarkup, KeyboardButton
keyboard = [["Black", "Brown"], ["Tan", "Blue"]]
markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

contact_button = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
contact_markup = ReplyKeyboardMarkup(contact_button, resize_keyboard=True)

user_data = {}


# TOKEN = os.getenv("BOT_TOKEN")
# ADMIN_ID = int(os.getenv("ADMIN_ID"))
TOKEN = "8724767851:AAET6QJk_JPx_C_5oeLHyHelBhKRoyq6LnE"

ADMIN_ID = 1713887351



def is_valid_input(text):
    return text is not None and text.strip() != ""


async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_data[user_id] = {"step":"order_id"}

    await update.message.reply_text("Please enter your Order ID:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    text = update.message.text

    if user_id in user_data and user_data[user_id]["step"] == "stopped":
        return

    if user_id not in user_data:
        user_data[user_id] = {"step": "order_id"}
        await update.message.reply_text("Please enter your Order ID:")
        return

    step = user_data[user_id]["step"]

    # STEP 1: ORDER ID
    if step == "order_id":

        # Validation: must be numeric and cant be empty
        if not is_valid_input(text):
            await update.message.reply_text("❌ Order ID cannot be empty.")
            return
    
        if not text.isdigit():
            await update.message.reply_text("❌ Order ID must be numeric.")
            return

        # Load existing orders
        existing_orders = load_orders()

        # Check duplicate Order ID
        for order in existing_orders:
            if order["order_id"] == text:
                await update.message.reply_text("❌ This Order ID already exists. Please enter a different one.")
                return

        user_data[user_id]["order_id"] = text
        user_data[user_id]["step"] = "name"

        await update.message.reply_text("Enter the name to be embossed (Keep it short):")

    # STEP 2: NAME
    elif step == "name":

        if not is_valid_input(text):
            await update.message.reply_text("❌ Name cannot be empty.")
            return
        
        user_data[user_id]["name"] = text
        user_data[user_id]["step"] = "color"

        await update.message.reply_text("🎨 Choose wallet color:", reply_markup=markup)

    # STEP 3: COLOR
    elif step == "color":

        if not is_valid_input(text):
            await update.message.reply_text("❌ Color cannot be empty.")
            return
        
        user_data[user_id]["color"] = text
        user_data[user_id]["step"] = "charm"

        await update.message.reply_text("Enter the charm number:")

    # STEP 4: CHARM
    elif step == "charm":

        if not is_valid_input(text):
            await update.message.reply_text("Charm number cannot be empty.")
            return
        if not text.isdigit():
            await update.message.reply_text("Charm No. must be numeric.")
            return

        user_data[user_id]["charm"] = text.strip()
        user_data[user_id]["step"] = "phone"

        await update.message.reply_text(
        "📞 Please share your phone number:",
        reply_markup=contact_markup)

    elif step == "confirm_new_order":


        if text.lower() == "yes":
            user_data[user_id] = {"step": "order_id"}
            await update.message.reply_text("🧾 Please enter your Order ID:")

        elif text.lower() == "no":
            user_data[user_id] = {"step": "stopped"}
            await update.message.reply_text("👍 Okay! If you need anything later, type /start")

        else:
            await update.message.reply_text("❓ Please type 'yes' or 'no'")
        # Stop replying if user chose NO
        


     
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    contact = update.message.contact

    if user_id not in user_data or user_data[user_id]["step"] != "phone":
        return

    phone = contact.phone_number

    # Clean phone (+91 etc.)
    if phone.startswith("+91"):
        phone = phone[3:]

    if not phone.isdigit() or len(phone) <= 10:
        await update.message.reply_text("❌ Invalid phone number.")
        return

    user_data[user_id]["phone"] = phone

    # Save data
    data = user_data[user_id].copy()
    data.pop("step", None)
    data["user_id"] = user_id

    confirmation = f"""✅ Order Confirmed!

🧾 Order ID: {data['order_id']}
✍️ Name: {data['name']}
🎨 Color: {data['color']}
🔢 Charm No: {data['charm']}
📞 Phone: {data['phone']}"""

    await update.message.reply_text(confirmation)

    await context.bot.send_message(
    chat_id=ADMIN_ID,
    text=f"""
📦 *New Order Received*

🧾 *Order ID:* `{data['order_id']}`
👤 *Name:* {data['name']}
🎨 *Color:* {data['color']}
🔢 *Charm:* {data['charm']}
📞 *Phone:* `{data['phone']}`
""",
    parse_mode="Markdown"
)

    # Move to next step
    user_data[user_id] = {"step": "confirm_new_order"}

    await update.message.reply_text("Do you want to place a new order? (yes/no)")        

def load_orders():
    try:
        with open("order.json", "r") as file:
            return json.load(file)
    except:
        return []
    
    
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)) 
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    print("Bot is running.... ")
    print("ADMIN_ID:", ADMIN_ID)
    app.run_polling()

if __name__ == "__main__":
    main()           

    