import os
import time
import threading
from flask import Flask, render_template_string, request
import telebot
from groq import Groq

app = Flask(__name__)

# --- CONFIGURATION ---
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY)

# Data storage (Restart hone par wipe ho jayega, Render limit)
chat_memory = {}
bot_rules = {} 

# --- CSS & HTML INTERFACE (Black & Yellow Theme) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🔱 TECHY ABHI | Bot Engine</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            background-color: #000000; 
            color: #ffcc00; 
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; padding: 0;
            display: flex; justify-content: center; align-items: center; min-height: 100vh;
        }
        .container { 
            background: #0f0f0f;
            border: 3px solid #ffcc00; 
            border-radius: 20px; 
            width: 90%; max-width: 800px; 
            padding: 40px; 
            box-shadow: 0 0 30px rgba(255, 204, 0, 0.2);
            margin: 20px;
        }
        h1 { font-size: 3rem; color: #ffcc00; text-shadow: 2px 2px 10px rgba(255, 204, 0, 0.5); margin-bottom: 5px; }
        p { font-size: 1.2rem; color: #ffffff; margin-bottom: 30px; }
        
        input, select, textarea { 
            width: 100%; padding: 15px; margin: 15px 0; 
            border-radius: 10px; border: 1px solid #ffcc00; 
            background: #1a1a1a; color: #fff; font-size: 1.1rem;
            box-sizing: border-box;
        }
        textarea { height: 120px; resize: vertical; }
        
        .btn { 
            background: #ffcc00; color: #000; 
            padding: 18px 30px; border: none; border-radius: 12px; 
            cursor: pointer; font-weight: bold; font-size: 1.3rem;
            width: 100%; transition: 0.3s; margin-top: 10px;
        }
        .btn:hover { background: #e6b800; transform: scale(1.02); }
        
        .tg-btn { 
            background: transparent; color: #ffcc00; 
            border: 2px solid #ffcc00; margin-top: 20px; 
        }

        .footer { margin-top: 30px; font-size: 1rem; color: #666; }
        .dev { color: #ffcc00; font-weight: bold; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔱 TECHY ABHI</h1>
        <p>Advance Multi-Bot Deployment System</p>
        
        <form method="POST" action="/start_bot">
            <input type="text" name="token" placeholder="Enter Telegram Bot Token" required>
            <input type="text" name="admin_id" placeholder="Your Admin Telegram ID (Numeric)" required>
            <input type="text" name="bot_name" placeholder="Bot Display Name (e.g. Nezuko)" required>
            <input type="text" name="dev_name" placeholder="Developer Name (Owner Name)" required>
            
            <select name="gender">
                <option value="Male">Male (Larka Personality)</option>
                <option value="Female">Female (Larki Personality)</option>
            </select>
            
            <textarea name="behavior" placeholder="Behavior: (e.g. Talk like a friendly Indian girl, use emojis, be a bit funny)"></textarea>
            <textarea name="rules" placeholder="Group Rules: (Write rules here, users can see them via /rules command)"></textarea>
            
            <button type="submit" class="btn">⚡ ACTIVATE GOD MODE</button>
        </form>

        <a href="https://t.me/abhi0w0" target="_blank">
            <button class="btn tg-btn">JOIN TELEGRAM: @abhi0w0</button>
        </a>

        <div class="footer">
            Developed by <a href="https://t.me/a6h1ii" class="dev">Abhi</a> | 2026 🔱 TECHY ABHI Engine
        </div>
    </div>
</body>
</html>
"""

# --- BOT ENGINE ---
def start_telegram_bot(token, admin_id, bot_name, dev_name, gender, behavior, rules_text):
    bot = telebot.TeleBot(token)
    spam_status = {}
    bot_rules[token] = rules_text if rules_text else "No rules defined by admin."

    def get_ai_response(user_id, user_text):
        if user_id not in chat_memory: chat_memory[user_id] = []
        chat_memory[user_id].append({"role": "user", "content": user_text})
        if len(chat_memory[user_id]) > 20: chat_memory[user_id].pop(0)

        system_prompt = f"Name: {bot_name}. Dev: {dev_name}. Gender: {gender}. Character: {behavior}. " \
                        f"Strictly talk in Hinglish. Behave like a human, use casual language and emojis."
        
        messages = [{"role": "system", "content": system_prompt}] + chat_memory[user_id]
        
        try:
            completion = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
            ai_msg = completion.choices[0].message.content
            chat_memory[user_id].append({"role": "assistant", "content": ai_msg})
            return ai_msg
        except: return "Arey yaar, dimag thak gaya mera. Thodi der baad baat karte hain!"

    # --- COMMAND HANDLERS ---
    @bot.message_handler(commands=['help'])
    def help_cmd(m):
        bot.reply_to(m, "🔱 *GOD MODE COMMANDS* ⚡\n\n"
                        "🔹 /help - List all commands\n"
                        "🔹 /rules - Show group rules\n"
                        "🔹 /kick - Kick a member (Admin)\n"
                        "🔹 /mute - Mute a member (Admin)\n"
                        "🔹 /unmute - Unmute (Admin)\n"
                        "🔹 /spam [text] - High speed spam (Admin)\n"
                        "🔹 /stop - Stop any active spam\n"
                        "🔹 /clear - Reset bot memory\n"
                        "🔹 /me - Dev & Bot Info\n"
                        "🔹 /del - Delete replied message", parse_mode="Markdown")

    @bot.message_handler(commands=['rules'])
    def show_rules(m):
        bot.reply_to(m, f"📋 *GROUP RULES*:\n\n{bot_rules[token]}", parse_mode="Markdown")

    @bot.message_handler(commands=['kick'])
    def kick_user(m):
        if str(m.from_user.id) == admin_id:
            if m.reply_to_message:
                bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
                bot.reply_to(m, "Uda diya! 🚀 Ta-ta Bye-bye!")
        else: bot.reply_to(m, "Aap admin nahi ho, aukat mein rahein! 🤫")

    @bot.message_handler(commands=['spam'])
    def start_spam(m):
        if str(m.from_user.id) == admin_id:
            text = m.text.replace("/spam", "").strip()
            if not text: return bot.reply_to(m, "Spam ke liye kuch text to do!")
            spam_status[m.chat.id] = True
            bot.send_message(m.chat.id, "Spamming Started... 😈")
            while spam_status.get(m.chat.id):
                bot.send_message(m.chat.id, text)
                time.sleep(0.5)
        else: bot.reply_to(m, "Nahi beta, spam sirf Admin karega.")

    @bot.message_handler(commands=['stop'])
    def stop_all(m):
        spam_status[m.chat.id] = False
        bot.reply_to(m, "Sab rok diya gaya hai. ✅")

    @bot.message_handler(commands=['me'])
    def about_me(m):
        bot.reply_to(m, f"🤖 *Bot Name*: {bot_name}\n👑 *Creator*: {dev_name}\n⚡ *Powered By*: @a6h1ii", parse_mode="Markdown")

    @bot.message_handler(commands=['del'])
    def delete_msg(m):
        if str(m.from_user.id) == admin_id and m.reply_to_message:
            bot.delete_message(m.chat.id, m.reply_to_message.message_id)

    @bot.message_handler(func=lambda m: True)
    def ai_chat(m):
        if m.chat.type != "private" and f"@{bot.get_me().username}" not in m.text: return
        response = get_ai_response(m.from_user.id, m.text)
        bot.reply_to(m, response)

    bot.polling(none_stop=True)

# --- FLASK ROUTES ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start_bot', methods=['POST'])
def start_bot():
    data = request.form
    threading.Thread(target=start_telegram_bot, args=(
        data['token'], data['admin_id'], data['bot_name'], 
        data['dev_name'], data['gender'], data['behavior'], data['rules']
    )).start()
    return f"<body style='background:#000;color:#ffcc00;text-align:center;padding-top:100px;'><h1>🚀 Bot '{data['bot_name']}' is now Live!</h1><p>Check Telegram.</p><a href='/' style='color:#fff;'>Back to Home</a></body>"


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))
    # '0.0.0.0' 
    app.run(host='0.0.0.0', port=port)
    
    
                     
