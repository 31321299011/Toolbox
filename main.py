import json
import os
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

# ---------- কালার ইমোজি ম্যাপিং ----------
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
    if not hex_color:
        return "🔹"
    try:
        rgb = hex_to_rgb(hex_color)
    except:
        return "🔹"
    closest = min(COLOR_MAP.values(), key=lambda x: color_distance(hex_to_rgb(x[0]), rgb))
    return closest[1]

# ---------- JSON helper ----------
def load_buttons():
    if os.path.exists(BUTTONS_FILE):
        with open(BUTTONS_FILE, "r") as f:
            return json.load(f)
    return []

def save_buttons(buttons):
    with open(BUTTONS_FILE, "w") as f:
        json.dump(buttons, f, indent=2)

# ---------- /start handler ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = load_buttons()
    keyboard = []
    for idx, btn in enumerate(buttons):
        emoji = get_color_emoji(btn.get("color"))
        text = f"{emoji} {btn['name']}"
        keyboard.append([InlineKeyboardButton(
            text=text,
            callback_data=f"open_{idx}"  # <-- মেইন ম্যাজিক
        )])
    markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    msg = (
        "⚡ <b>TOOL IO BOX</b> ⚡\n"
        "┌────────────────┐\n"
        "│ ▶️  টুল বক্সে স্বাগতম!  │\n"
        "└────────────────┘\n"
        "নিচের বাটনে ক্লিক করলেই সরাসরি লিংক ওপেন হবে 👇"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)

# ---------- Callback handler (open ও remove দুটোর জন্য) ----------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("open_"):
        # বাটন ওপেন
        await query.answer()  # লোডিং বন্ধ
        try:
            index = int(data.split("_")[1])
        except:
            await query.answer("ভুল ডাটা!", show_alert=True)
            return
        buttons = load_buttons()
        if 0 <= index < len(buttons):
            url = buttons[index]["url"]
            # সরাসরি লিংক ওপেন, কোনো কনফার্মেশন নাই
            await query.answer(url=url)
        else:
            await query.answer("বাটন খুঁজে পাইনি!", show_alert=True)

    elif data.startswith("remove_"):
        # শুধু অ্যাডমিন পারবে
        if query.from_user.id != ADMIN_ID:
            await query.answer("তুমি অ্যাডমিন না!", show_alert=True)
            return
        await query.answer()
        try:
            index = int(data.split("_")[1])
        except:
            await query.answer("ভুল!", show_alert=True)
            return
        buttons = load_buttons()
        if 0 <= index < len(buttons):
            removed = buttons.pop(index)
            save_buttons(buttons)
            emoji = get_color_emoji(removed.get("color"))
            await query.answer(f"{emoji} {removed['name']} মুছে ফেলা হয়েছে", show_alert=False)
            # ইনলাইন কি-বোর্ড আপডেট
            new_buttons = load_buttons()
            if new_buttons:
                kb = []
                for i, b in enumerate(new_buttons):
                    e = get_color_emoji(b.get("color"))
                    kb.append([InlineKeyboardButton(f"{e} {b['name']}", callback_data=f"remove_{i}")])
                await query.edit_message_reply_markup(InlineKeyboardMarkup(kb))
            else:
                await query.edit_message_text("🧹 সব বাটন মুছে ফেলা হয়েছে!", reply_markup=None)
        else:
            await query.answer("বাটন নেই!", show_alert=True)

# ---------- অ্যাডমিন কমান্ড: সেট / রিমুভ / ক্লিয়ার ----------
async def set_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ তুমি অ্যাডমিন না!")
        return

    text = update.message.text.strip()
    parts = text.split(" - ", 3)
    if len(parts) < 3:
        await update.message.reply_text(
            "❗ <b>ফরম্যাট:</b>\n<code>/set - নাম - লিংক - #কালার</code> (কালার অপশনাল)\n"
            "উদা: <code>/set - Google - https://google.com - #FF0000</code>",
            parse_mode=ParseMode.HTML
        )
        return

    name = parts[1].strip()
    url = parts[2].strip()
    color = parts[3].strip() if len(parts) == 4 else None

    if not name or not url:
        await update.message.reply_text("❌ নাম আর লিংক দিতে হবে")
        return
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ লিংক http/https দিয়ে শুরু হওয়া লাগবে")
        return
    if color and not color.startswith("#"):
        await update.message.reply_text("❌ কালার # দিয়ে শুরু হতে হবে")
        return

    buttons = load_buttons()
    buttons.append({"name": name, "url": url, "color": color})
    save_buttons(buttons)

    emoji = get_color_emoji(color) if color else "🔹"
    await update.message.reply_text(
        f"✅ বাটন যোগ হয়েছে: {emoji} <b>{name}</b>",
        parse_mode=ParseMode.HTML
    )

async def remove_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    buttons = load_buttons()
    if not buttons:
        await update.message.reply_text("রিমুভ করার কোনো বাটন নাই!")
        return
    kb = []
    for i, b in enumerate(buttons):
        e = get_color_emoji(b.get("color"))
        kb.append([InlineKeyboardButton(f"{e} {b['name']}", callback_data=f"remove_{i}")])
    await update.message.reply_text(
        "🗑️ <b>যে বাটন মুছতে চাও সেটাতে ক্লিক কর:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def clear_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    save_buttons([])
    await update.message.reply_text("🧹 সব বাটন সাফ করে দিয়েছি।")

# ---------- মেইন ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_button))
    app.add_handler(CommandHandler("remove", remove_menu))
    app.add_handler(CommandHandler("clear", clear_buttons))

    # open_ এবং remove_ দুটোর জন্য কলব্যাক হ্যান্ডলার
    app.add_handler(CallbackQueryHandler(button_callback, pattern=r"^(open_|remove_)\d+$"))

    print("✅ TOOL IO BOX বট রান করছে...")
    app.run_polling()

if __name__ == "__main__":
    main()
