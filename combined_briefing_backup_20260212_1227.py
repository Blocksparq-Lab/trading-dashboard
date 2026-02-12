import os
import requests
import sys
import subprocess
import json
import re
from datetime import datetime
from openai import OpenAI

# SPECIFIC VIDEO URLs TO PROCESS
VERIFIED_INVESTING_VIDEOS = [
    'https://www.youtube.com/watch?v=0lmmV9Weyms',  # Today's Best Trade Setups
    'https://www.youtube.com/watch?v=QAs8cVeqdNs',  # My Trading Game Plan
]

MITCH_RAY_VIDEOS = [
    'https://www.youtube.com/watch?v=H3rtdD8lgN4',  # Latest live stream
]

def get_video_info(video_url):
    """Get video metadata and check if accessible"""
    try:
        result = subprocess.run([
            'yt-dlp', '--dump-json', '--skip-download',
            video_url
        ], capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            print(f'   Error: {result.stderr[:100]}')
            return None

        if not result.stdout:
            return None

        data = json.loads(result.stdout.strip().split('\n')[0])
        return {
            'title': data.get('title', 'Unknown'),
            'upload_date': data.get('upload_date', 'Unknown'),
            'duration': data.get('duration', 0),
            'uploader': data.get('uploader', 'Unknown'),
            'url': video_url
        }
    except Exception as e:
        print(f'   Error fetching info: {e}')
        return None

def get_transcript(video_url):
    """Get transcript for video"""
    for f in ['/tmp/vid.en.vtt', '/tmp/vid.vtt', '/tmp/vid.en.txt']:
        if os.path.exists(f):
            os.remove(f)

    try:
        result = subprocess.run([
            'yt-dlp', '--skip-download', '--write-auto-subs',
            '--sub-langs', 'en', '--sub-format', 'vtt',
            '--output', '/tmp/vid', video_url
        ], capture_output=True, timeout=120)

        vtt_file = '/tmp/vid.en.vtt' if os.path.exists('/tmp/vid.en.vtt') else '/tmp/vid.vtt'

        if os.path.exists(vtt_file):
            with open(vtt_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        elif os.path.exists('/tmp/vid.en.txt'):
            with open('/tmp/vid.en.txt', 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        else:
            print('   No transcript file found')
            return None

        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if not line or '-->' in line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
                continue
            line = re.sub(r'<[^>]+>', '', line)
            if line:
                lines.append(line)

        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)

        transcript = ' '.join(unique_lines)
        return transcript if transcript else None

    except Exception as e:
        print(f'   Error getting transcript: {e}')
        return None

def normalize_prices(transcript):
    def expand_k(match):
        number = match.group(1)
        if '.' in number:
            return str(int(float(number) * 1000))
        else:
            return str(int(number) * 1000)
    return re.sub(r'(\d+\.?\d*)\s*[Kk]\b', expand_k, transcript)

def analyze_video(video_info, transcript, source_name):
    api_key = None
    with open(os.path.expanduser('~/.config/trading-ai/.env'), 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break

    if not api_key:
        return None, 'No API key'

    client = OpenAI(api_key=api_key)

    if source_name == 'Verified Investing':
        prompt = 'Extract key trading setups. List: Tickers, entry levels, stops, targets, patterns, confidence. Transcript: '
    else:
        prompt = 'Extract crypto setups. List: BTC/ETH/altcoins, levels, patterns, candlesticks, indicators, bias. Transcript: '

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt + transcript[:6000]}],
        max_tokens=800
    )

    return response.choices[0].message.content, None

def process_verified_investing():
    print('Processing Verified Investing videos...')

    analyses = []

    for i, url in enumerate(VERIFIED_INVESTING_VIDEOS, 1):
        print(f'\nVideo {i}/{len(VERIFIED_INVESTING_VIDEOS)}:')
        print(f'URL: {url}')

        info = get_video_info(url)
        if not info:
            print('   ✗ Could not access video (may be private or not ready)')
            continue

        print(f'   Title: {info["title"]}')
        print(f'   Date: {info["upload_date"]}')

        transcript = get_transcript(url)
        if not transcript:
            print('   ✗ No transcript available')
            continue

        print(f'   Transcript: {len(transcript):,} characters')

        analysis, error = analyze_video(info, transcript, 'Verified Investing')
        if error:
            print(f'   ✗ Analysis failed: {error}')
            continue

        print('   ✓ Analysis complete')
        analyses.append({
            'title': info['title'],
            'analysis': analysis
        })

    if not analyses:
        return None, 'No videos could be processed'

    combined = '\n\n'.join([f"VIDEO: {a['title']}\n{a['analysis']}" for a in analyses])

    return {
        'title': 'Verified Investing Combined',
        'analysis': combined
    }, None

def process_mitch_ray():
    print('\nProcessing Mitch Ray video...')

    if not MITCH_RAY_VIDEOS:
        return None, 'No Mitch Ray URLs configured'

    url = MITCH_RAY_VIDEOS[0]
    print(f'URL: {url}')

    info = get_video_info(url)
    if not info:
        return None, 'Could not access video'

    print(f'Title: {info["title"]}')
    print(f'Date: {info["upload_date"]}')

    transcript = get_transcript(url)
    if not transcript:
        return None, 'No transcript available'

    print(f'Transcript: {len(transcript):,} characters')

    normalized = normalize_prices(transcript)

    analysis, error = analyze_video(info, normalized, 'Mitch Ray')
    if error:
        return None, error

    print('✓ Analysis complete')

    return {
        'title': info['title'],
        'analysis': analysis
    }, None

def synthesize(vi_data, mr_data):
    api_key = None
    with open(os.path.expanduser('~/.config/trading-ai/.env'), 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break

    client = OpenAI(api_key=api_key)

    print('\nSynthesizing final briefing...')

    vi_section = vi_data['analysis'] if vi_data else 'No Verified Investing data available'
    mr_section = mr_data['analysis'] if mr_data else 'No Mitch Ray data available'

    warnings = []
    if not vi_data:
        warnings.append('WARNING: No Verified Investing videos processed.')
    if not mr_data:
        warnings.append('NOTE: No Mitch Ray video processed.')

    prompt = """Create ONE integrated trading plan for a West Coast trader (6:30-9:30 AM PT).

VERIFIED INVESTING:
""" + vi_section + """

MITCH RAY:
""" + mr_section + """

""" + "\n".join(warnings) + """

SYNTHESIZE:

CRITICAL PRICE RULES:
- BTC trades around $90,000-$110,000 (six figures, never $1,000)
- ETH trades around $2,000-$3,000
- If you see BTC at $1,026 or $1,105, these are WRONG — correct to $102,600 and $110,500
- Always use full dollar amounts (e.g., $102,600 never $1,026)
- Use CURRENT market prices from the transcripts, not old levels

PRE-MARKET BRIEFING (""" + datetime.now().strftime('%Y-%m-%d %H:%M') + """ PT)

MARKET CONTEXT
EQUITY SETUPS
CRYPTO SETUPS
RISK MANAGEMENT
EXECUTION CHECKLIST
KEY LEVELS"""

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=1500
    )

    return response.choices[0].message.content

def send_telegram(message):
    try:
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
            print('Telegram credentials not found')
            return False

        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        max_length = 4000
        parts = [message[i:i+max_length] for i in range(0, len(message), max_length)]

        for part in parts:
            payload = {
                'chat_id': chat_id,
                'text': part,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            requests.post(url, json=payload, timeout=30)

        print('Sent to Telegram successfully')
        return True

    except Exception as e:
        print(f'Telegram error: {e}')
        return False

if __name__ == '__main__':
    print('='*60)
    print('COMBINED TRADING BRIEFING')
    print('Generated: ' + datetime.now().strftime('%Y-%m-%d %H:%M PT'))
    print('='*60)

    vi_data, vi_error = process_verified_investing()
    if vi_error:
        print(f'\nVerified Investing Error: {vi_error}')

    mr_data, mr_error = process_mitch_ray()
    if mr_error:
        print(f'\nMitch Ray Error: {mr_error}')

    if not vi_data and not mr_data:
        print('\nERROR: No data from any source')
        sys.exit(1)

    final = synthesize(vi_data, mr_data)

    print()
    print('='*60)
    print('FINAL TRADING PLAN')
    print('='*60)
    print(final)
    print('='*60)

    with open(os.path.expanduser('~/trading-ai/latest_briefing.txt'), 'w') as f:
        f.write(final)
    print('\nSaved to ~/trading-ai/latest_briefing.txt')

    print('\nSending to Telegram...')
    send_telegram(final)
