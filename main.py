import os
import time
import threading
from flask import Flask, render_template_string, request, jsonify
import telebot
from groq import Groq

app = Flask(__name__)

# --- CONFIGURATION ---
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY)

# Data storage
chat_memory = {}
bot_rules = {}
active_bots = {}

# --- CSS & HTML INTERFACE (Improved Black & Yellow Theme) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🔱 TECHY ABHI | Bot Engine</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body { 
            background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
            color: #ffcc00; 
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container { 
            background: rgba(15, 15, 15, 0.95);
            border: 2px solid #ffcc00;
            border-radius: 16px;
            width: 100%;
            max-width: 700px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(255, 204, 0, 0.15);
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }
        
        .container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #ffcc00, #ff9900, #ffcc00);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 204, 0, 0.2);
        }
        
        h1 { 
            font-size: 2.5rem; 
            color: #ffcc00; 
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(255, 204, 0, 0.3);
            letter-spacing: 1px;
        }
        
        .tagline {
            font-size: 1.1rem;
            color: #cccccc;
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 0.9rem;
            color: #888888;
            margin-bottom: 25px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #ffcc00;
            font-size: 0.95rem;
        }
        
        input, select, textarea { 
            width: 100%; 
            padding: 14px; 
            border-radius: 10px; 
            border: 1px solid rgba(255, 204, 0, 0.3); 
            background: rgba(26, 26, 26, 0.8); 
            color: #ffffff; 
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #ffcc00;
            box-shadow: 0 0 0 2px rgba(255, 204, 0, 0.1);
        }
        
        textarea { 
            height: 100px; 
            resize: vertical; 
            line-height: 1.5;
        }
        
        .btn-container {
            margin-top: 30px;
        }
        
        .btn { 
            background: linear-gradient(135deg, #ffcc00 0%, #e6b800 100%);
            color: #000000; 
            padding: 16px 30px; 
            border: none; 
            border-radius: 10px; 
            cursor: pointer; 
            font-weight: 700;
            font-size: 1.1rem;
            width: 100%;
            transition: all 0.3s ease;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 204, 0, 0.3);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .tg-btn { 
            background: transparent; 
            color: #ffcc00;
            border: 2px solid #ffcc00;
            margin-top: 15px;
            padding: 14px;
        }
        
        .tg-btn:hover {
            background: rgba(255, 204, 0, 0.1);
        }
        
        .status {
            text-align: center;
            padding: 15px;
            margin: 20px 0;
            background: rgba(255, 204, 0, 0.1);
            border-radius: 10px;
            border-left: 4px solid #ffcc00;
            display: none;
        }
        
        .status.active {
            display: block;
            animation: fadeIn 0.5s ease;
        }
        
        .footer { 
            margin-top: 30px; 
            text-align: center; 
            padding-top: 20px;
            border-top: 1px solid rgba(255, 204, 0, 0.2);
            color: #666666; 
            font-size: 0.9rem;
        }
        
        .dev { 
            color: #ffcc00; 
            font-weight: bold; 
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        .dev:hover {
            color: #ffffff;
            text-decoration: underline;
        }
        
        .credit {
            font-size: 0.8rem;
            margin-top: 10px;
            color: #555555;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
                margin: 10px;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .btn {
                padding: 14px 20px;
                font-size: 1rem;
            }
        }
        
        @media (max-width: 480px) {
            body {
                padding: 10px;
            }
            
            .container {
                padding: 15px;
            }
            
            h1 {
                font-size: 1.8rem;
            }
            
            input, select, textarea {
                padding: 12px;
            }
        }
    </style>
    <script>
        function showLoading() {
            const status = document.getElementById('status');
            const btn = document.querySelector('.btn');
            status.textContent = '🚀 Bot is being activated... Please wait!';
            status.classList.add('active');
            btn.disabled = true;
            btn.innerHTML = '⚡ ACTIVATING...';
            return true;
        }
        
        function copyToken() {
            const tokenField = document.querySelector('input[name="token"]');
            tokenField.select();
            document.execCommand('copy');
            alert('Token copied to clipboard!');
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔱 TECHY ABHI</h1>
            <div class="tagline">Advanced Multi-Bot Deployment System</div>
            <div class="subtitle">Create AI-powered Telegram bots in seconds</div>
        </div>
        
        <div id="status" class="status"></div>
        
        <form method="POST" action="/start_bot" onsubmit="return showLoading()">
            <div class="form-group">
                <label for="token">🤖 Telegram Bot Token</label>
                <input type="text" id="token" name="token" placeholder="Enter bot token from @BotFather" required>
            </div>
            
            <div class="form-group">
                <label for="admin_id">👑 Admin Telegram ID</label>
                <input type="text" id="admin_id" name="admin_id" placeholder="Your numeric Telegram ID" required>
            </div>
            
            <div class="form-group">
                <label for="bot_name">📛 Bot Display Name</label>
                <input type="text" id="bot_name" name="bot_name" placeholder="e.g., Nezuko, Chhota Bheem" required>
            </div>
            
            <div class="form-group">
                <label for="dev_name">💻 Developer Name</label>
                <input type="text" id="dev_name" name="dev_name" placeholder="Owner/Developer Name" required>
            </div>
            
            <div class="form-group">
                <label for="gender">⚤ Gender & Personality</label>
                <select id="gender" name="gender" required>
                    <option value="Male">Male Personality (Ladka Style)</option>
                    <option value="Female">Female Personality (Ladki Style)</option>
                    <option value="Friendly">Friendly & Casual</option>
                    <option value="Professional">Professional Style</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="behavior">🎭 Behavior & Style</label>
                <textarea id="behavior" name="behavior" placeholder="Describe bot's personality. Example: Friendly Indian girl who loves chatting, uses emojis 😊, speaks Hinglish, and is helpful"></textarea>
            </div>
            
            <div class="form-group">
                <label for="rules">📜 Group Rules (Optional)</label>
                <textarea id="rules" name="rules" placeholder="Rules for group members to follow. Users can see them via /rules command"></textarea>
            </div>
            
            <div class="btn-container">
                <button type="submit" class="btn">
                    <span>⚡</span> ACTIVATE GOD MODE
                </button>
            </div>
        </form>
        
        <a href="https://t.me/abhi0w0" target="_blank">
            <button class="btn tg-btn">
                <span>📢</span> JOIN TELEGRAM CHANNEL
            </button>
        </a>
        
        <div class="footer">
            <p>Developed with ❤️ by <a href="https://t.me/a6h1ii" class="dev" target="_blank">Abhi</a></p>
            <p class="credit">© 2026 🔱 TECHY ABHI Engine | All Rights Reserved</p>
            <p class="credit">Powered by Groq AI & Flask</p>
        </div>
    </div>
</body>
</html>
"""

# --- BOT ENGINE ---
def start_telegram_bot(token, admin_id, bot_name, dev_name, gender, behavior, rules_text):
    """Start Telegram bot with given configuration"""
    try:
        bot = telebot.TeleBot(token)
        bot_info = bot.get_me()
        bot_rules[token] = rules_text if rules_text else "No rules defined by admin."
        
        # Store active bot info
        active_bots[token] = {
            'name': bot_name,
            'status': 'running',
            'started_at': time.time(),
            'bot_username': bot_info.username
        }
        
        def get_ai_response(user_id, user_text):
            """Get AI response from Groq"""
            if user_id not in chat_memory:
                chat_memory[user_id] = []
            
            chat_memory[user_id].append({"role": "user", "content": user_text})
            
            # Keep only last 15 messages
            if len(chat_memory[user_id]) > 15:
                chat_memory[user_id] = chat_memory[user_id][-15:]
            
            # Enhanced system prompt
            gender_map = {
                "Male": "Ladke ki tarah baat karein. Casual and friendly.",
                "Female": "Ladki ki tarah baat karein. Sweet and caring.",
                "Friendly": "Very friendly and casual. Use lots of emojis.",
                "Professional": "Professional but friendly tone."
            }
            
            gender_desc = gender_map.get(gender, "Friendly and casual")
            
            system_prompt = f"""You are {bot_name}, created by {dev_name}.
Gender Style: {gender_desc}
Behavior: {behavior}
Language: Use Hinglish (Hindi+English mix) naturally. Use emojis appropriately.
Be human-like, friendly, and engaging. Keep responses concise (2-3 lines max)."""
            
            messages = [{"role": "system", "content": system_prompt}] + chat_memory[user_id]
            
            try:
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150
                )
                ai_msg = completion.choices[0].message.content
                chat_memory[user_id].append({"role": "assistant", "content": ai_msg})
                return ai_msg
            except Exception as e:
                print(f"AI Error: {e}")
                return "Arey yaar, thoda technical issue aa gaya! Thodi der baad try karna 😅"

        # --- COMMAND HANDLERS ---
        @bot.message_handler(commands=['start', 'help'])
        def help_cmd(m):
            help_text = f"""🤖 *{bot_name} - GOD MODE* ⚡

*Basic Commands:*
🔹 /start - Welcome message
🔹 /help - All commands list
🔹 /rules - Group rules
🔹 /me - Bot info
🔹 /clear - Clear chat memory

*Admin Commands:* (Admin Only)
🔸 /kick [reply] - Remove user
🔸 /mute [reply] - Mute user
🔸 /unmute [reply] - Unmute user
🔸 /spam [text] - Spam messages
🔸 /stop - Stop spam
🔸 /del [reply] - Delete message

*Note:* Just chat normally for AI conversation!"""
            bot.reply_to(m, help_text, parse_mode="Markdown")

        @bot.message_handler(commands=['start'])
        def welcome_cmd(m):
            welcome_msg = f"""Namaste! 🙏

I'm *{bot_name}*, your friendly AI assistant!
Created by *{dev_name}* ✨

Type /help to see all commands.
Or just start chatting with me! 😊"""
            bot.reply_to(m, welcome_msg, parse_mode="Markdown")

        @bot.message_handler(commands=['rules'])
        def show_rules(m):
            bot.reply_to(m, f"📜 *{bot_name}'s Rules*:\n\n{bot_rules[token]}", parse_mode="Markdown")

        @bot.message_handler(commands=['me'])
        def about_me(m):
            bot_info_text = f"""🤖 *Bot Information*:

*Name:* {bot_name}
*Creator:* {dev_name}
*Gender Mode:* {gender}
*Status:* 🟢 Active
*Username:* @{bot_info.username}
*Powered By:* @a6h1ii"""
            bot.reply_to(m, bot_info_text, parse_mode="Markdown")

        @bot.message_handler(commands=['kick'])
        def kick_user(m):
            if str(m.from_user.id) == admin_id:
                if m.reply_to_message:
                    try:
                        bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
                        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
                        bot.reply_to(m, "Uda diya gaya! 👋 Goodbye!")
                    except:
                        bot.reply_to(m, "Cannot kick this user.")
                else:
                    bot.reply_to(m, "Please reply to a user's message to kick.")
            else:
                bot.reply_to(m, "⚠️ Admin command only!")

        @bot.message_handler(commands=['clear'])
        def clear_memory(m):
            if m.from_user.id in chat_memory:
                chat_memory[m.from_user.id] = []
                bot.reply_to(m, "Memory cleared! 🧹 Fresh start!")
            else:
                bot.reply_to(m, "No memory to clear!")

        @bot.message_handler(func=lambda m: True)
        def ai_chat(m):
            """Handle all messages"""
            # Ignore commands
            if m.text.startswith('/'):
                return
            
            # In groups, only respond when mentioned
            if m.chat.type != "private":
                if bot_info.username and f"@{bot_info.username}" not in m.text:
                    return
            
            # Typing action
            bot.send_chat_action(m.chat.id, 'typing')
            
            # Get AI response
            response = get_ai_response(m.from_user.id, m.text)
            
            # Send response
            bot.reply_to(m, response)

        # Start bot
        print(f"🤖 Starting bot: {bot_name}")
        bot.polling(none_stop=True, timeout=60)
        
    except Exception as e:
        print(f"❌ Bot startup failed: {e}")
        if token in active_bots:
            active_bots[token]['status'] = 'failed'
            active_bots[token]['error'] = str(e)

# --- FLASK ROUTES ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start_bot', methods=['POST'])
def start_bot():
    """Start bot endpoint"""
    try:
        data = request.form
        
        # Validate inputs
        if not all([data['token'], data['admin_id'], data['bot_name'], data['dev_name']]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Start bot in separate thread
        thread = threading.Thread(
            target=start_telegram_bot,
            args=(
                data['token'].strip(),
                data['admin_id'].strip(),
                data['bot_name'].strip(),
                data['dev_name'].strip(),
                data['gender'],
                data['behavior'].strip(),
                data.get('rules', '').strip()
            ),
            daemon=True
        )
        thread.start()
        
        # Success response
        success_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bot Activated!</title>
            <style>
                body {{
                    background: #000;
                    color: #ffcc00;
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    text-align: center;
                    background: rgba(15, 15, 15, 0.95);
                    padding: 40px;
                    border-radius: 20px;
                    border: 2px solid #ffcc00;
                    max-width: 600px;
                }}
                h1 {{
                    color: #ffcc00;
                    margin-bottom: 20px;
                }}
                .success-icon {{
                    font-size: 4rem;
                    margin-bottom: 20px;
                }}
                .btn {{
                    background: #ffcc00;
                    color: #000;
                    padding: 12px 30px;
                    border: none;
                    border-radius: 10px;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 20px;
                    font-weight: bold;
                    cursor: pointer;
                }}
                .info {{
                    background: rgba(255, 204, 0, 0.1);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>🚀 Bot Activated Successfully!</h1>
                <div class="info">
                    <p><strong>🤖 Bot Name:</strong> {data['bot_name']}</p>
                    <p><strong>👑 Developer:</strong> {data['dev_name']}</p>
                    <p><strong>⚤ Personality:</strong> {data['gender']}</p>
                    <p><strong>⏱ Status:</strong> 🟢 Running</p>
                </div>
                <p>Your bot is now live on Telegram! Go to Telegram and start chatting.</p>
                <p><em>Note: It may take 10-15 seconds to fully initialize.</em></p>
                <a href="/" class="btn">← Create Another Bot</a>
            </div>
        </body>
        </html>
        """
        
        return success_html
        
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <body style="background:#000;color:#ffcc00;text-align:center;padding:100px 20px;">
            <h1>❌ Error Occurred</h1>
            <p>{str(e)}</p>
            <a href="/" style="color:#ffcc00;">← Go Back</a>
        </body>
        </html>
        """
        return error_html

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'ok',
        'service': 'Techy Abhi Bot Engine',
        'active_bots': len(active_bots)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
