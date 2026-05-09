import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

# ----- কনফিগ -----
TOKEN = "8787041046:AAF8g2MD6fB-hhQ16oAdXl9XN5FQ7u4C0j8"
ADMIN_ID = 8194390770
BUTTONS_FILE = "buttons.json"

# ----- কালার কোড থেকে স্কোয়ার ইমোজি -----
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
    "pink": ("#FFC0CB", "🩷"),  # হালকা গোলাপি হার্ট, আগেরটা কাজ না করলে 💗
}

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2))

def get_color_emoji(hex_color):
    """নিকটতম রঙের স্কোয়ার ইমোজি রিটার্ন করবে"""
    try:
        rgb = hex_to_rgb(hex_color)
    except:
        return None
    closest = min(COLOR_MAP.values(), key=lambda x: color_distance(hex_to_rgb(x[0]), rgb))
    return closest[1]

# ----- JSON হেল্পার -----
def load_buttons():
    if os.path.exists(BUTTONS_FILE):
        with open(BUTTONS_FILE, "r") as f:
            return json.load(f)
    return []

def save_buttons(buttons):
    with open(BUTTONS_FILE, "w") as f:
        json.dump(buttons, f, indent=2)

# ----- কমান্ড হ্যান্ডলার -----
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

    text = update.message.text.strip()
    # ফরম্যাট: /set - নাম - লিংক - কালার(optional)
    parts = text.split(" - ", 3)  # সর্বোচ্চ ৪ ভাগ
    if len(parts) < 3:
        await update.message.reply_text(
            "❗ ফরম্যাট: <code>/set - নাম - লিংক - #কালার(optional)</code>\n"
            "উদাহরণ: <code>/set - Google - https://google.com - #FF0000</code>",
            parse_mode=ParseMode.HTML
        )
        return

    name = parts[1].strip()
    url = parts[2].strip()
    color = parts[3].strip() if len(parts) == 4 else None

    if not name or not url:
        await update.message.reply_text("নাম এবং লিংক দিতেই হবে!")
        return
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("লিংক http:// বা https:// দিয়ে শুরু হতে হবে!")
        return
    if color and not color.startswith("#"):
        await update.message.reply_text("কালার কোড # দিয়ে শুরু হওয়া লাগবে (যেমন #FF00FF)")
        return

    buttons = load_buttons()
    buttons.append({"name": name, "url": url, "color": color})
    save_buttons(buttons)

    emoji = get_color_emoji(color) if color else "🔹"
    await update.message.reply_text(
        f"✅ বাটন যোগ হয়েছে: {emoji} <b>{name}</b> → {url}",
        parse_mode=ParseMode.HTML
    )

async def clear_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    save_buttons([])
    await update.message.reply_text("🧹 সব বাটন ক্লিয়ার করে দিয়েছি।")

# ----- মেইন -----
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_button))
    app.add_handler(CommandHandler("clear", clear_buttons))
    print("⚙️ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
