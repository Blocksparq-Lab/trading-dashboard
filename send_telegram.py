import os
import sys
import requests

def send_message(message):
    with open(os.path.expanduser('~/.config/trading-ai/.env'), 'r') as f:
        lines = f.readlines()
    
    bot_token = None
    chat_id = None
    
    for line in lines:
        if line.startswith('TELEGRAM_BOT_TOKEN='):
            bot_token = line.split('=', 1)[1].strip()
        elif line.startswith('TELEGRAM_CHAT_ID='):
            chat_id = line.split('=', 1)[1].strip()
    
    if not bot_token or not chat_id:
        print('ERROR: Credentials not found')
        return False
    
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    
    max_length = 4000
    parts = [message[i:i+max_length] for i in range(0, len(message), max_length)]
    
    for i, part in enumerate(parts):
        payload = {
            'chat_id': chat_id,
            'text': part,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code != 200:
                print(f'Error: {response.text}')
                return False
        except Exception as e:
            print(f'Error: {e}')
            return False
    
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        try:
            with open(os.path.expanduser('~/trading-ai/latest_briefing.txt'), 'r') as f:
                message = f.read()
        except:
            print('ERROR: No briefing file')
            sys.exit(1)
    else:
        message = sys.argv[1]
    
    if send_message(message):
        print('Message sent to Telegram')
    else:
        print('Failed to send')
