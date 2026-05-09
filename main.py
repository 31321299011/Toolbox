import json
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------- কনফিগ ----------
TOKEN = "8787041046:AAF8g2MD6fB-hhQ16oAdXl9XN5FQ7u4C0j8"
ADMIN_ID = 8194390770
BUTTONS_FILE = "buttons.json"

# ---------- কালার → ইমোজি ম্যাপিং ----------
COLOR_MAP = {
    "red": ("#FF0000", "🟥"),
    "orange": ("#FFA500", "🟧"),
    "yellow": ("#FFFF00", "🟨"),
    "green": ("#00FF00", "🟩"),
    "blue": ("#0000FF", "🟦"),
    "purple": ("#800080", "🟪"),
    "brown": ("#A52A2A", "🟫"),
    "black": ("#000000", "⬛"),
    "white": ("#FFFFFF", "⬜"),
    "pink": ("#FFC0CB", "🩷"),
}

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2))

def get_color_emoji(hex_color: str) -> str:
    """হেক্স কালার থেকে নিকটতম রঙের স্কয়ার ইমোজি বের করে"""
    if not hex_color:
        return "🔹"  # default
    try:
        rgb = hex_to_rgb(hex_color)
    except:
        return "🔹"
    closest = min(COLOR_MAP.values(), key=lambda x: color_distance(hex_to_rgb(x[0]), rgb))
    return closest[1]

# ---------- JSON হেল্পার ----------
def load_buttons():
    if os.path.exists(BUTTONS_FILE):
        with open(BUTTONS_FILE, "r") as f:
            return json.load(f)
    return []

def save_buttons(buttons):
    with open(BUTTONS_FILE, "w") as f:
        json.dump(buttons, f, indent=2)

# ---------- কমান্ড ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = load_buttons()
    keyboard = []
    for btn in buttons:
        name = btn["name"]
        color = btn.get("color")
        emoji = get_color_emoji(color) if color else "🔹"
        text = f"{emoji} {name}"
        keyboard.append([InlineKeyboardButton(text=text, url=btn["url"])])

    markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    msg = (
        "⚡ <b>TOOL IO BOX</b> ⚡\n"
        "┌────────────────┐\n"
        "│ ▶️  টুল বক্সে স্বাগতম!  │\n"
        "└────────────────┘\n"
        "নিচের বাটনে ক্লিক করে সরাসরি যাও 👇"
    )

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)

async def set_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ তুমি অ্যাডমিন না, যাও ভাগ!")
        return

    # ফরম্যাট: /set - নাম - লিংক - #কালার(optional)
    text = update.message.text.strip()
    # রেজেক্স দিয়ে পার্স করা: /set - নাম - লিংক - #কালার? (কালার অপশনাল)
    # সহজ ভাবে স্প্লিট দিয়ে করব
    parts = text.split(" - ", 3)
    if len(parts) < 3:
        await update.message.reply_text(
            "❗ <b>নিয়ম:</b>\n<code>/set - নাম - লিংক - #কালার(optional)</code>\n"
            "উদাহরণ: <code>/set - Google - https://google.com - #FF0000</code>",
            parse_mode=ParseMode.HTML
        )
        return

    name = parts[1].strip()
    url = parts[2].strip()
    color = parts[3].strip() if len(parts) == 4 else None

    if not name or not url:
        await update.message.reply_text("❌ নাম আর লিংক দিতেই হবে!")
        return
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ লিংক http:// বা https:// দিয়ে শুরু হওয়া লাগবে!")
        return
    if color and not color.startswith("#"):
        await update.message.reply_text("❌ কালার কোড # চিহ্ন দিয়ে শুরু হবে (যেমন #FF00FF)")
        return

    buttons = load_buttons()
    buttons.append({"name": name, "url": url, "color": color})
    save_buttons(buttons)

    emoji = get_color_emoji(color) if color else "🔹"
    await update.message.reply_text(
        f"✅ বাটন যোগ হয়েছে: {emoji} <b>{name}</b>",
        parse_mode=ParseMode.HTML
    )

async def remove_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """অ্যাডমিনের জন্য /remove কমান্ড, বাটন সিলেক্ট করে রিমুভ"""
    if update.effective_user.id != ADMIN_ID:
        return

    buttons = load_buttons()
    if not buttons:
        await update.message.reply_text("❌ রিমুভ করার মতো কোনো বাটন নাই!")
        return

    keyboard = []
    for idx, btn in enumerate(buttons):
        name = btn["name"]
        color = btn.get("color")
        emoji = get_color_emoji(color) if color else "🔹"
        text = f"{emoji} {name}"
        # callback_data: remove_<index>
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"remove_{idx}")])

    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🗑️ <b>রিমুভ করতে কোনো বাটনে ক্লিক করুন:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )

async def remove_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # লোডিং বন্ধ

    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        await query.answer("একশন অ্যালাউ নয়!", show_alert=True)
        return

    data = query.data
    if not data.startswith("remove_"):
        return

    try:
        index = int(data.split("_")[1])
    except:
        await query.answer("ভুল ইনডেক্স!", show_alert=True)
        return

    buttons = load_buttons()
    if index < 0 or index >= len(buttons):
        await query.answer("বাটন খুঁজে পাই নাই!", show_alert=True)
        return

    removed = buttons.pop(index)
    save_buttons(buttons)

    emoji = get_color_emoji(removed.get("color")) if removed.get("color") else "🔹"
    await query.answer(f"{emoji} {removed['name']} রিমুভ করা হয়েছে!", show_alert=False)

    # এখন একই মেসেজের বাটন লিস্ট আপডেট করা
    new_buttons = load_buttons()
    if new_buttons:
        keyboard = []
        for idx, btn in enumerate(new_buttons):
            emoji = get_color_emoji(btn.get("color")) if btn.get("color") else "🔹"
            text = f"{emoji} {btn['name']}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"remove_{idx}")])
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=markup)
    else:
        # সব রিমুভ হয়ে গেলে কি-বোর্ড মুছিয়ে মেসেজ আপডেট
        await query.edit_message_text("🧹 সব বাটন রিমুভ হয়ে গেছে!", reply_markup=None)

async def clear_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    save_buttons([])
    await update.message.reply_text("🧹 সব বাটন একসাথে ক্লিয়ার করা হয়েছে।")

# ---------- মেইন ----------
def main():
    app = Application.builder().token(TOKEN).build()

    # কমান্ড হ্যান্ডলার
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_button))
    app.add_handler(CommandHandler("remove", remove_buttons))
    app.add_handler(CommandHandler("clear", clear_buttons))

    # কলব্যাক হ্যান্ডলার (remove_* প্যাটার্ন)
    app.add_handler(CallbackQueryHandler(remove_button_callback, pattern=r"^remove_\d+$"))

    print("⚙️ Tool IO Box বট চলছে...")
    app.run_polling()

if __name__ == "__main__":
    main()
