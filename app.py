import os
import requests
from flask import Flask, request

# ⚠️ ফেসবুক পেজ টোকেন ও অ্যাডমিন আইডি
PAGE_ACCESS_TOKEN = os.getenv(
    "PAGE_ACCESS_TOKEN", 
    "EAAO6zUBiVl8BSQCawL5gLoZBZA2dHSq4Hh4kpAVh443iCz1JvuFlBhcKxKZBsjdY0CD7Sr3fQY3RkSZAPgQNJ3FVdBOGxTpbxiw8WIf64vKWmrOnkXqaZAKpTgLYH4UGSRb0cB7KgALPy7f6Vp7w1NdavuQYBA2SAPZAU7WGZAtWUBQHLFOK9QAsuDhcqixugQy2ZCC539xMYCkzFeBrd1RmA62ZBnBpsNajn"
)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_secure_verify_token")
ADMIN_ID = "8138758919"  # অ্যাডমিন আইডি

# ফায়ারবেস রিয়েলটাইম ডাটাবেজ URL
FIREBASE_URL = "https://shopbotdb-default-rtdb.firebaseio.com/"

# ডলার কেনা-বেচার রেট ও ওয়ালেট
DOLLAR_CONFIG = {
    'buy_rate': 130,          
    'sell_rate': 120,         
    'bkash': '01935164417',
    'nagad': '01935164417',
    'rocket': '01935164417',
    'binance_id': '751363394',
    'ltc_address': 'Lh2JLpZrtSKyt6rLXrmoMCQ81A18wkYs5e'
}

app = Flask(__name__)
user_states = {}
trade_data = {}


# --- Facebook Send API Helper ---
def send_facebook_message(recipient_id, text, quick_replies=None):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    if quick_replies:
        payload["message"]["quick_replies"] = quick_replies
        
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"Facebook Send Error: {e}")


def get_main_menu_buttons():
    return [
        {"content_type": "text", "title": "🛍️ Buy Product", "payload": "BUY_PRODUCT"},
        {"content_type": "text", "title": "💵 Dollar Buy/Sell", "payload": "DOLLAR_MENU"},
        {"content_type": "text", "title": "👤 Profile", "payload": "PROFILE"},
        {"content_type": "text", "title": "💰 Deposit", "payload": "DEPOSIT"},
        {"content_type": "text", "title": "📦 My Orders", "payload": "MY_ORDERS"},
        {"content_type": "text", "title": "☎️ Support", "payload": "SUPPORT"}
    ]


# --- Firebase Helper Functions ---
def get_user(user_id, first_name="Unknown"):
    try:
        url = f"{FIREBASE_URL}users/{user_id}.json"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        if not data:
            new_user = {
                "user_id": user_id, 
                "first_name": first_name,
                "balance": 0.0, 
                "total_buy": 0
            }
            requests.put(url, json=new_user, timeout=10)
            return 0.0, 0
            
        return float(data.get("balance", 0.0)), int(data.get("total_buy", 0))
    except Exception as e:
        print(f"Firebase Error: {e}")
        return 0.0, 0


def update_balance(user_id, amount):
    try:
        url = f"{FIREBASE_URL}users/{user_id}.json"
        res = requests.get(url, timeout=10)
        data = res.json()
        current_bal = float(data.get("balance", 0.0)) if data else 0.0
        new_bal = current_bal + amount
        
        requests.put(f"{FIREBASE_URL}users/{user_id}/balance.json", json=new_bal, timeout=10)
        return new_bal
    except Exception as e:
        print(f"Update balance error: {e}")
        return 0.0


# --- Flask Webhook Endpoint for Facebook ---
@app.route("/", methods=["GET", "POST"])
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode and token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                return challenge, 200
            else:
                return "Verification failed", 403
        return "Facebook Bot is alive and running smoothly!", 200

    elif request.method == "POST":
        data = request.json
        if data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event.get("sender", {}).get("id")
                    
                    # Handle Text Messages & Quick Replies
                    if messaging_event.get("message"):
                        msg_text = messaging_event["message"].get("text", "")
                        handle_incoming_message(sender_id, msg_text)
                        
                    # Handle Postbacks / Button clicks
                    elif messaging_event.get("postback"):
                        payload = messaging_event["postback"].get("payload")
                        handle_incoming_message(sender_id, payload)
                        
        return "EVENT_RECEIVED", 200


def handle_incoming_message(sender_id, text):
    get_user(sender_id)
    
    if text in ["/start", "🏠 Main Menu", "BUY_PRODUCT"]:
        send_facebook_message(
            sender_id, 
            "🌸 Welcome to our Shop! Select from the menu below:", 
            quick_replies=get_main_menu_buttons()
        )
    elif text == "🛍️ Buy Product":
        send_facebook_message(
            sender_id, 
            "🌐 Proxy / VPN / Premium Apps / AI Tools / Gift Card কিনতে আমাদের মেনু ব্যবহার করুন।"
        )
    elif text == "👤 Profile":
        bal, total_buy = get_user(sender_id)
        profile_text = f"👤 Your Profile Information:\n\n🆔 User ID: {sender_id}\n💰 Balance: {bal:.2f} BDT\n🛍️ Total Purchases: {total_buy}"
        send_facebook_message(sender_id, profile_text, quick_replies=get_main_menu_buttons())
    elif text == "💵 Dollar Buy/Sell":
        send_facebook_message(sender_id, "💸 Welcome to the Dollar Buy/Sell Zone!\n1. Want to Buy Dollar (Rate: 130 Tk)\n2. Want to Sell Dollar (Rate: 120 Tk)")
    elif text == "💰 Deposit":
        send_facebook_message(sender_id, "💎 bKash/Nagad/Rocket Personal:\n01935164417\n\nSend Money করে ট্রানজেকশন আইডি (TrxID) বা স্ক্রিনশট দিন।")
    elif text == "📦 My Orders":
        send_facebook_message(sender_id, "🛒 আপনার অর্ডার এবং রিচার্জ হিস্ট্রি দেখতে এখানে ক্লিক করুন।")
    elif text == "☎️ Support":
        send_facebook_message(sender_id, "☎️ কাস্টমার সাপোর্ট:\n💬 Admin Support: m.me/proxyvpnservice17\n⏰ সার্ভিস টাইম: ২৪/৭ ঘন্টা")
    else:
        send_facebook_message(sender_id, "দয়া করে নিচের মেনু থেকে অপশন সিলেক্ট করুন:", quick_replies=get_main_menu_buttons())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Flask Server on port {port}...")
    app.run(host="0.0.0.0", port=port)
