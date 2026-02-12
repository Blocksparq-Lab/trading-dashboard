import os
import sys
import subprocess
import json
from datetime import datetime
from openai import OpenAI

def get_latest_videos(channel_url, max_results=5):
    """Get latest video URLs and titles from channel"""
    try:
        result = subprocess.run([
            'yt-dlp', '--flat-playlist', '--dump-json',
            '--playlist-end', str(max_results),
            channel_url
        ], capture_output=True, text=True, timeout=60)
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    videos.append({
                        'title': data.get('title', ''),
                        'url': f"https://www.youtube.com/watch?v={data['id']}",
                        'upload_date': data.get('upload_date', '')
                    })
                except:
                    continue
        return videos
    except Exception as e:
        print(f"Error fetching videos: {e}")
        return []

def find_target_video(videos):
    """Find video matching target titles from today"""
    target_patterns = [
        "Today's Best Trade Setups",
        "My Trading Game Plan",
        "Best Trade Setups"
    ]
    
    today = datetime.now().strftime('%Y%m%d')
    
    for video in videos:
        # Check if uploaded today and matches pattern
        if any(pattern.lower() in video['title'].lower() for pattern in target_patterns):
            return video
    
    # If no today match, return most recent
    return videos[0] if videos else None

def get_transcript(video_url):
    """Download YouTube transcript"""
    try:
        # Clean up old files
        for f in ['/tmp/transcript.en.txt', '/tmp/transcript.en.vtt']:
            if os.path.exists(f):
                os.remove(f)
        
        result = subprocess.run([
            'yt-dlp', '--skip-download', '--write-auto-subs',
            '--sub-langs', 'en', '--convert-subs', 'txt',
            '--output', '/tmp/transcript', video_url
        ], capture_output=True, text=True, timeout=120)
        
        # Try different transcript file names
        possible_files = [
            '/tmp/transcript.en.txt',
            '/tmp/transcript.en.vtt',
            '/tmp/transcript.txt'
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Clean up VTT formatting if needed
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    return ' '.join(lines[:500])  # First 500 lines
        
        return "No transcript available for this video."
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_transcript(title, transcript):
    """Analyze with OpenAI"""
    api_key = open(os.path.expanduser('~/.config/trading-ai/.env')).read().split('=')[1].strip()
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Analyze this trading video for a West Coast day trader.

Video Title: {title}

Transcript:
{transcript[:3000]}

Extract and format as TRADING PLAN:
1. TICKERS: List each stock/crypto mentioned with directional bias (Bullish/Bearish/Neutral)
2. LEVELS: Key price levels (support/resistance/entry/targets)
3. SETUP: What pattern or catalyst is mentioned
4. TIMEFRAME: Day trade or swing trade
5. RISK: Any risk management mentioned
6. CONFIDENCE: Rate High/Medium/Low based on conviction in video

If multiple setups, list separately. Be concise and actionable."""

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=800,
        temperature=0.3
    )
    
    return response.choices[0].message.content

if __name__ == '__main__':
    print("="*60)
    print("DAILY TRADING BRIEFING - Verified Investing")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)
    
    # Get latest videos
    print("\nFetching latest videos...")
    videos = get_latest_videos("https://www.youtube.com/@verifiedinvesting/videos")
    
    if not videos:
        print("ERROR: Could not fetch videos")
        sys.exit(1)
    
    # Find target video
    target = find_target_video(videos)
    if not target:
        print("ERROR: No suitable video found")
        sys.exit(1)
    
    print(f"\nSelected: {target['title']}")
    print(f"URL: {target['url']}")
    
    # Get transcript
    print("\nDownloading transcript...")
    transcript = get_transcript(target['url'])
    
    if transcript.startswith("Error") or transcript.startswith("No transcript"):
        print(f"WARNING: {transcript}")
        print("Attempting analysis from title only...")
        transcript = f"Video title: {target['title']}. No transcript available."
    
    # Analyze
    print("Analyzing with AI...")
    analysis = analyze_transcript(target['title'], transcript)
    
    print("\n" + "="*60)
    print("TRADING PLAN")
    print("="*60)
    print(analysis)
    print("="*60)
