import os
import requests
from flask import Flask, request

app = Flask(__name__)

# আপনার পেজ অ্যাক্সেস টোকেন এবং ভেরিফাই টোকেন
PAGE_ACCESS_TOKEN = "EAAO6zUBiVl8BSoFqFruzMM5zj0eZBMbuEIZAQ9r0s5qY8BorPA5p64KREMyG3LbFOMI9pN9RrU4NizbZCGZAPJ1ZAJZBZAYfG6f7QlUtmLVqxrZBAfZAWktiuRsuCiywZBfgbvJtO9jn2qnBp4kw4rX38b0ZCFAzFJ6WWRJAFIJuDtdD8FeB2Q4HIxhukFywWZBJgvfGwzj0gTQTdpTrhJJwiwyNE3DlvpYz3umZC"
VERIFY_TOKEN = "my_secure_verify_token"  # মেটা ডেভেলপার কনসোলে যে ভেরিফাই টোকেন দিয়েছেন সেটাই এখানে থাকবে


@app.route("/", methods=["GET"])
def home():
  return "Flask Server is Live & Running!"


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
  # ১. ফেসবুক ওয়েবহুক ভেরিফিকেশন (GET রিকোয়েস্ট)
  if request.method == "GET":
    token_sent = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token_sent == VERIFY_TOKEN:
      return challenge, 200
    return "Verification token mismatch", 403

  # ২. পেজে মেসেজ আসার পর হ্যান্ডেল করা (POST রিকোয়েস্ট)
  elif request.method == "POST":
    data = request.get_json()

    if data.get("object") == "page":
      for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
          sender_id = messaging_event["sender"]["id"]

          # টেক্সট মেসেজ আসলে
          if "message" in messaging_event and "text" in messaging_event["message"]:
            message_text = messaging_event["message"]["text"]
            send_message(
                sender_id,
                f"আপনার মেসেজটি পেয়েছি: '{message_text}'. আমাদের সেবা নিতে চাইলে নিচের অপশনগুলো দেখুন।",
            )

          # গেট স্টার্টেড বাটন বা পোস্টব্যাক ক্লিক করলে
          elif "postback" in messaging_event:
            payload = messaging_event["postback"].get("payload")
            send_message(
                sender_id, "স্বাগতম! আমাদের প্রক্সি ভিপিএন সার্ভিসে আপনাকে."
            )

      return "EVENT_RECEIVED", 200
    return "Not Found", 404


def send_message(recipient_id, message_text):
  """ফেসবুক পেজ থেকে ইউজারের ইনবক্সে মেসেজ পাঠানোর ফাংশন"""
  url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
  headers = {"Content-Type": "application/json"}
  payload = {
      "recipient": {"id": recipient_id},
      "message": {"text": message_text},
  }
  response = requests.post(url, json=payload, headers=headers)
  return response.json()


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
