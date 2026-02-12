import os
import sys
from openai import OpenAI
import subprocess

def get_transcript(video_url):
    """Download YouTube transcript using yt-dlp"""
    try:
        result = subprocess.run([
            'yt-dlp', '--skip-download', '--write-subs', 
            '--write-auto-subs', '--sub-langs', 'en',
            '--sub-format', 'txt', '--output', '/tmp/transcript',
            video_url
        ], capture_output=True, text=True, timeout=60)
        
        # Read the transcript file
        if os.path.exists('/tmp/transcript.en.txt'):
            with open('/tmp/transcript.en.txt', 'r') as f:
                return f.read()
        else:
            return "Transcript not available for this video."
    except Exception as e:
        return f"Error getting transcript: {str(e)}"

def analyze_with_openai(transcript):
    """Send transcript to OpenAI for trading analysis"""
    api_key = open(os.path.expanduser('~/.config/trading-ai/.env')).read().split('=')[1].strip()
    client = OpenAI(api_key=api_key)
    
    prompt = f"""You are a trading assistant for a West Coast day trader. 
Analyze this video transcript and extract:
1. Ticker symbols mentioned with directional bias (bullish/bearish)
2. Key price levels (support/resistance targets)
3. Timeframe or catalyst
4. Confidence level (High/Medium/Low)

Format as a concise trading plan. If multiple stocks, list separately.

Transcript:
{transcript[:4000]}  # Limit to first 4000 chars
"""
    
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=500
    )
    
    return response.choices[0].message.content

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_youtube.py <youtube_url>")
        sys.exit(1)
    
    video_url = sys.argv[1]
    print("Downloading transcript...")
    transcript = get_transcript(video_url)
    
    print("Analyzing with AI...")
    analysis = analyze_with_openai(transcript)
    
    print("\n" + "="*50)
    print("TRADING ANALYSIS")
    print("="*50)
    print(analysis)
