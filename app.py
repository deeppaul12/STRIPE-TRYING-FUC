from flask import Flask, request, jsonify
import stripe

app = Flask(__name__)

# ==================== CONFIGURATION ====================
# DIRECT KEY INJECTION (Easy Method)
# Maine yahan apni key daal di hai
stripe.api_key = "sk_live_awWzIlT3bp7cGsy4Ord9cRU0"

# ==================== SK CHECKER LOGIC ====================
def check_with_sk(cc, mm, yy, cvv):
    # Agar key nahi mili to error
    if not stripe.api_key:
        return {"status": "Error", "response": "Key Not Found in Code"}

    try:
        # Year 4 digit fix
        if len(str(yy)) == 2:
            yy = "20" + str(yy)

        # Stripe Token Create (Direct)
        token = stripe.Token.create(
            card={
                "number": cc,
                "exp_month": mm,
                "exp_year": yy,
                "cvc": cvv,
            },
        )

        # Success
        if token and token.id:
            return {"status": "Approved", "response": "Card is Live (Token Created)"}
        else:
            return {"status": "Declined", "response": "Unknown Error"}

    except stripe.error.CardError as e:
        # Card Decline Scenarios
        err_msg = e.user_message if e.user_message else str(e)
        
        # Specific Checks for Live Cards
        if "insufficient funds" in err_msg.lower():
            return {"status": "Approved", "response": "Live (Insufficient Funds)"}
        elif "incorrect_cvc" in err_msg.lower():
             return {"status": "Approved", "response": "Live (Incorrect CVV)"}
        elif "security code" in err_msg.lower():
             return {"status": "Approved", "response": "Live (Security Code Check)"}
        else:
            return {"status": "Declined", "response": err_msg}

    except stripe.error.AuthenticationError:
        return {"status": "Error", "response": "Invalid SK Key (Check Code)"}
        
    except Exception as e:
        return {"status": "Error", "response": f"Exception: {str(e)[:50]}"}

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
