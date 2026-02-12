import os
import sys
import subprocess
import json
import re
from datetime import datetime
from openai import OpenAI

def get_latest_video(channel_url):
    try:
        result = subprocess.run([
            'yt-dlp', '--flat-playlist', '--dump-json',
            '--playlist-end', '1', channel_url
        ], capture_output=True, text=True, timeout=60)
        
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    return {
                        'title': data.get('title', ''),
                        'url': f"https://www.youtube.com/watch?v={data['id']}",
                        'upload_date': data.get('upload_date', ''),
                        'duration': data.get('duration', 0)
                    }
                except:
                    continue
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_transcript(video_url):
    for f in ['/tmp/mitch.en.vtt', '/tmp/mitch.vtt']:
        if os.path.exists(f):
            os.remove(f)
    
    print("Downloading transcript...")
    subprocess.run([
        'yt-dlp', '--skip-download', '--write-auto-subs',
        '--sub-langs', 'en', '--sub-format', 'vtt',
        '--output', '/tmp/mitch', video_url
    ], capture_output=True, timeout=180)
    
    vtt_file = '/tmp/mitch.en.vtt' if os.path.exists('/tmp/mitch.en.vtt') else '/tmp/mitch.vtt'
    
    if not os.path.exists(vtt_file):
        return None
    
    with open(vtt_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
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
    
    return ' '.join(unique_lines)

def normalize_prices_in_transcript(transcript):
    def expand_k(match):
        number = match.group(1)
        if '.' in number:
            return str(int(float(number) * 1000))
        else:
            return str(int(number) * 1000)
    
    transcript = re.sub(r'(\d+\.?\d*)\s*[Kk]\b', expand_k, transcript)
    return transcript

def analyze_transcript(title, transcript, duration_minutes):
    api_key = open(os.path.expanduser('~/.config/trading-ai/.env')).read().split('=')[1].strip()
    client = OpenAI(api_key=api_key)
    
    print("Normalizing price abbreviations...")
    normalized_transcript = normalize_prices_in_transcript(transcript)
    
    if "93000" in normalized_transcript or "102600" in normalized_transcript:
        print("  ✓ Expanded K abbreviations")
    
    total_chars = len(normalized_transcript)
    
    if total_chars > 30000:
        print(f"Long video ({duration_minutes} min). Sampling segments...")
        segment_size = total_chars // 5
        chunks = [
            normalized_transcript[0:8000],
            normalized_transcript[segment_size:segment_size+8000],
            normalized_transcript[segment_size*2:segment_size*2+8000],
            normalized_transcript[segment_size*3:segment_size*3+8000],
            normalized_transcript[-8000:]
        ]
    else:
        chunk_size = 8000
        chunks = [normalized_transcript[i:i+chunk_size] for i in range(0, len(normalized_transcript), chunk_size)][:4]
    
    print(f"Processing {len(chunks)} segments...")
    
    all_analysis = []
    
    for i, chunk in enumerate(chunks):
        print(f"  Segment {i+1}/{len(chunks)}...")
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': f'''Analyze this crypto video transcript segment. Extract:

CHART PATTERNS (Classic Technical Analysis):
- Cup & Handle, Head & Shoulders, Double Top/Bottom, Triangle (Ascending/Descending/Symmetrical), Wedge, Flag, Pennant, Channel, Range/Balance

CANDLESTICK PATTERNS:
- Doji, Hammer, Shooting Star/Topping Tail, Engulfing (Bullish/Bearish), Morning/Evening Star, Spinning Top, Marubozu, Gap up/down

INDICATORS MENTIONED:
- RSI, MACD, Moving Averages (EMA/SMA), Volume, VWAP, Bollinger Bands, Stochastic

For each asset (BTC, ETH, altcoins), note:
- Pattern name
- Timeframe (daily, 4H, 1H)
- Bias (bullish/bearish/neutral)

Segment {i+1}:
{chunk}'''}],
            max_tokens=1200
        )
        all_analysis.append(response.choices[0].message.content)
    
    print("Creating final technical analysis...")
    
    final = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': f'''Create comprehensive crypto trading plan with technical analysis.

Segments analyzed:
{chr(10).join(all_analysis)}

PRICE CONTEXT:
- Bitcoin: $90,000-$110,000 range
- Ethereum: $2,000-$3,000 range
- Fix any prices like $1,026 → $102,600

Format:

🎯 BTC SETUP
Price: $XXX,XXX
Pattern: [Cup & Handle, H&S, etc.]
Candlestick: [Doji, Topping Tail, etc.]
Indicators: [RSI, MACD, etc.]
Bias: [Bullish/Bearish]
Levels: Support $XXX / Resistance $XXX

🎯 ETH SETUP
[Same format]

📊 ALTCOIN TECHNICALS
- XRP: [pattern, candlestick, levels]
- SOL: [pattern, candlestick, levels]
- Others: [brief notes]

📈 CHART PATTERNS SUMMARY
[List all classic patterns found across assets]

🕯️ CANDLESTICK ALERTS
[List significant candlestick signals]

⚠️ KEY LEVELS & INDICATORS
Critical prices and indicator readings

⏰ TIMEFRAME
💡 KEY TAKEAWAY'''}],
        max_tokens=1500
    )
    
    return final.choices[0].message.content

if __name__ == '__main__':
    print("="*60)
    print("MITCH RAY CRYPTO BRIEFING")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M PT')}")
    print("="*60)
    
    video = get_latest_video("https://www.youtube.com/@MitchRayTA/videos")
    
    if not video:
        print("ERROR: Could not fetch video")
        sys.exit(1)
    
    duration_min = video.get('duration', 0) // 60
    print(f"\nVideo: {video['title']}")
    print(f"Duration: ~{duration_min} minutes")
    print(f"URL: {video['url']}")
    
    transcript = get_transcript(video['url'])
    
    if not transcript:
        print("ERROR: No transcript available")
        sys.exit(1)
    
    print(f"Transcript: {len(transcript):,} characters")
    
    analysis = analyze_transcript(video['title'], transcript, duration_min)
    
    print("\n" + "="*60)
    print("CRYPTO TRADING PLAN")
    print("="*60)
    print(analysis)
    print("="*60)
