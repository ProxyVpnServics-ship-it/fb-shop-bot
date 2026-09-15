import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Render এনভায়রনমেন্ট বা ডিফল্ট টোকেন
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_secure_verify_token")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

@app.route("/", methods=["GET"])
def home():
    return "FB Shop Bot is Running!", 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # ফেসবুক ওয়েবহুক ভেরিফিকেশন (GET রিকোয়েস্ট)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                print("WEBHOOK_VERIFIED")
                return challenge, 200
            else:
                return "Verification failed", 403
        return "Invalid verification request", 400

    # ফেসবুক থেকে মেসেজ আসা (POST রিকোয়েস্ট)
    elif request.method == "POST":
        data = request.json
        print("Received webhook data:", data)

        try:
            if data.get("object") == "page":
                for entry in data.get("entry", []):
                    for messaging_event in entry.get("messaging", []):
                        sender_id = messaging_event.get("sender", {}).get("id")
                        
                        # যদি ইউজার টেক্সট বা পোস্টব্যাক পাঠায়
                        if sender_id and (messaging_event.get("message") or messaging_event.get("postback")):
                            send_welcome_message(sender_id)
        except Exception as e:
            print(f"Error handling webhook: {e}")

        # ফ্ল্যাস্ক সার্ভার যেন অবশ্যই একটি ভ্যালিড রেসপন্স রিটার্ন করে
        return "EVENT_RECEIVED", 200


def send_welcome_message(recipient_id):
    if not PAGE_ACCESS_TOKEN:
        print("Error: PAGE_ACCESS_TOKEN is missing!")
        return

    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    # ওয়েলকাম মেসেজ এবং শপের অপশন বাটন
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": "স্বাগতম! Proxy Vpn Services Shop-এ আপনাকে স্বাগতম। নিচে থেকে আপনার পছন্দের সেবাটি বেছে নিন:",
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": "🛡️ Proxy Services",
                    "payload": "PROXY_SERVICES"
                },
                {
                    "content_type": "text",
                    "title": "🔒 VPN Services",
                    "payload": "VPN_SERVICES"
                },
                {
                    "content_type": "text",
                    "title": "📞 Support",
                    "payload": "SUPPORT"
                }
            ]
        }
    }
    
    response = requests.post(url, json=payload)
    print("Message send response:", response.json())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
