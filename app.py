import os
import requests
from flask import Flask, request

app = Flask(__name__)

# নতুন আপডেট করা ফেসবুক পেজ টোকেন ও অ্যাডমিন আইডি
PAGE_ACCESS_TOKEN = os.getenv(
    "PAGE_ACCESS_TOKEN", 
    "EAAO6zUBiVl8BSl4ogMx1dhZCzbZA4kI2eSpndJDw7gDabclQE9bb82RiHy6YedctrhbMROsZCteYlT9qzujpeLwVxwxhZCzpHVewXuZBUVjziPXttUljWs3IFPi4Pj3j7yRErgOjmVSgZAXwJgho5h7XQLZBxrXLkCNa4SOwIWfUW5nYkdsFCGXXMTKTAZBURJ9fETeKX6jMmI8kYIrfZB8qXfs0YfYk1oG9H"
)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_secure_verify_token")

# ফায়ারবেস রিয়েলটাইম ডাটাবেজ URL
FIREBASE_URL = "https://shopbotdb-default-rtdb.firebaseio.com/"

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
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print("Facebook Send Response:", response.json())
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

# --- Flask Webhook Endpoint ---
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
        try:
            data = request.json
            print("Received webhook data:", data)
            
            if data and data.get("object") == "page":
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
        except Exception as e:
            print(f"Webhook POST Error: {e}")
            
        return "OK", 200

def handle_incoming_message(sender_id, text):
    if not sender_id:
        return
    get_user(sender_id)
    text_lower = text.lower() if text else ""
    
    if text_lower in ["/start", "start", "hi", "hello", "🏠 main menu", "buy_product", "main_menu", "get started"]:
        send_facebook_message(
            sender_id, 
            "🌸 Welcome to our Shop! Select from the menu below:", 
            quick_replies=get_main_menu_buttons()
        )
    elif text in ["🛍️ Buy Product", "BUY_PRODUCT"]:
        proxy_categories = [
            {"content_type": "text", "title": "🌐 ISP Proxy", "payload": "ISP_PROXY"},
            {"content_type": "text", "title": "📱 Mobile Proxy", "payload": "MOBILE_PROXY"},
            {"content_type": "text", "title": "🏠 Residential", "payload": "RESIDENTIAL"}
        ]
        send_facebook_message(
            sender_id, 
            "🌐 আমাদের কাছে বিভিন্ন ধরনের প্রিমিয়াম প্রক্সি ও ভিপিএন উপলব্ধ রয়েছে। নিচে থেকে আপনার পছন্দের ক্যাটাগরি সিলেক্ট করুন:", 
            quick_replies=proxy_categories
        )
    elif text in ["👤 Profile", "PROFILE"]:
        bal, total_buy = get_user(sender_id)
        profile_text = f"👤 Your Profile Information:\n\n🆔 User ID: {sender_id}\n💰 Balance: {bal:.2f} BDT\n🛍️ Total Purchases: {total_buy}"
        send_facebook_message(sender_id, profile_text, quick_replies=get_main_menu_buttons())
    elif text in ["💵 Dollar Buy/Sell", "DOLLAR_MENU"]:
        send_facebook_message(sender_id, "💸 Welcome to the Dollar Buy/Sell Zone!\n1. Want to Buy Dollar (Rate: 130 Tk)\n2. Want to Sell Dollar (Rate: 120 Tk)", quick_replies=get_main_menu_buttons())
    elif text in ["💰 Deposit", "DEPOSIT"]:
        send_facebook_message(sender_id, "💎 bKash/Nagad/Rocket Personal:\n01935164417\n\nSend Money করে ট্রানজেকশন আইডি (TrxID) বা স্ক্রিনশট দিন।", quick_replies=get_main_menu_buttons())
    elif text in ["📦 My Orders", "MY_ORDERS"]:
        send_facebook_message(sender_id, "🛒 আপনার অর্ডার এবং রিচার্জ হিস্ট্রি দেখতে এখানে ক্লিক করুন।", quick_replies=get_main_menu_buttons())
    elif text in ["☎️ Support", "SUPPORT"]:
        send_facebook_message(sender_id, "☎️ কাস্টমার সাপোর্ট:\n💬 Admin Support: m.me/proxyvpnservice17\n⏰ সার্ভিস টাইম: ২৪/৭ ঘন্টা", quick_replies=get_main_menu_buttons())
    else:
        send_facebook_message(sender_id, "দয়া করে নিচের মেনু থেকে অপশন সিলেক্ট করুন:", quick_replies=get_main_menu_buttons())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Flask Server on port {port}...")
    app.run(host="0.0.0.0", port=port)
