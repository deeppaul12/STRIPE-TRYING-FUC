from flask import Flask, request, jsonify
import stripe
import os

app = Flask(__name__)

# ==================== CONFIGURATION ====================
# CODE MEIN KEY NAHI DALNI HAI.
# Hum Vercel Environment Variable se read kar rahe hain.
# Name: STRIPE_SECRET_KEY
STRIPE_SK_KEY = os.environ.get("sk_live_awWzIlT3bp7cGsy4Ord9cRU0")

# Agar env var nahi mila to error denge, hardcode nahi karenge
if not STRIPE_SK_KEY:
    # Fallback for local testing only (agar local test karna ho to yahan likh sakte ho par Vercel pe mat likho)
    pass 

stripe.api_key = STRIPE_SK_KEY

# ==================== SK CHECKER LOGIC ====================
def check_with_sk(cc, mm, yy, cvv):
    if not stripe.api_key:
        return {"status": "Error", "response": "Server Key Missing"}

    try:
        # Year 4 digit fix
        if len(str(yy)) == 2:
            yy = "20" + str(yy)

        # Stripe Token Create (Direct API)
        token = stripe.Token.create(
            card={
                "number": cc,
                "exp_month": mm,
                "exp_year": yy,
                "cvc": cvv,
            },
        )

        if token and token.id:
            return {"status": "Approved", "response": "Card is Live (Token Created)"}
        else:
            return {"status": "Declined", "response": "Unknown Error"}

    except stripe.error.CardError as e:
        err_msg = e.user_message if e.user_message else str(e)
        # Live Detection
        if "insufficient funds" in err_msg.lower():
            return {"status": "Approved", "response": "Live (Insufficient Funds)"}
        elif "incorrect_cvc" in str(e).lower():
            return {"status": "Approved", "response": "Live (Incorrect CVV)"}
        else:
            return {"status": "Declined", "response": err_msg}

    except stripe.error.AuthenticationError:
        return {"status": "Error", "response": "Invalid SK Key (Check Vercel Env)"}
        
    except Exception as e:
        return {"status": "Error", "response": f"Exception: {str(e)[:40]}"}

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
    res = check_with_sk(cc, mm, yy, cvv)
    
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True)
