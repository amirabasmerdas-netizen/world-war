from flask import Flask, request
from child_bot import ChildBot
from database import DatabaseManager
import threading
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ذخیره instance ربات‌های فعال
active_bots = {}

def run_child_bot(bot_token, bot_id):
    """اجرای ربات فرزند در thread جداگانه"""
    bot = ChildBot(bot_token, bot_id)
    active_bots[bot_id] = bot
    bot.run()

@app.route('/webhook/<bot_token>', methods=['POST'])
def webhook(bot_token):
    """دریافت وب‌هوک از تلگرام"""
    try:
        update = request.get_json()
        # اینجا باید منطق پردازش update اضافه شود
        # برای سادگی، فقط log می‌کنیم
        logging.info(f"Received update for bot with token: {bot_token[:10]}...")
        return 'OK'
    except Exception as e:
        logging.error(f"Error processing webhook: {e}")
        return 'ERROR', 500

@app.route('/health')
def health_check():
    """بررسی سلامت سرور"""
    return {'status': 'healthy', 'active_bots': len(active_bots)}

@app.route('/start_bot/<int:bot_id>')
def start_bot(bot_id):
    """شروع ربات فرزند"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        from models import ChildBot
        bot = session.query(ChildBot).filter(ChildBot.id == bot_id).first()
        
        if not bot:
            return {'error': 'Bot not found'}, 404
        
        # بررسی اینکه ربات قبلاً اجرا نشده باشد
        if bot_id not in active_bots:
            # اجرای ربات در thread جدید
            thread = threading.Thread(
                target=run_child_bot,
                args=(bot.bot_token, bot_id),
                daemon=True
            )
            thread.start()
            
            return {
                'success': True,
                'message': f'Bot {bot_id} started',
                'owner_id': bot.owner_id
            }
        else:
            return {
                'success': True,
                'message': f'Bot {bot_id} is already running'
            }
            
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        session.close()

if __name__ == '__main__':
    # شروع سرور Flask
    app.run(host='0.0.0.0', port=8443)
