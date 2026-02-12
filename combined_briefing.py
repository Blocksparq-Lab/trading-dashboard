#!/usr/bin/env python3
import os, subprocess, json, re, base64, requests
from datetime import datetime
from pathlib import Path
from openai import OpenAI

GITHUB_REPO = "Blocksparq-Lab/trading-dashboard"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".config" / "trading-ai"
DASHBOARD_PATH = HOME_DIR / "trading-ai" / "dashboard.html"

VERIFIED_INVESTING_URLS = [
    "https://www.youtube.com/watch?v=0lmmV9Weyms",
    "https://www.youtube.com/watch?v=QAs8cVeqdNs",
]
MITCH_RAY_URLS = ["https://www.youtube.com/watch?v=H3rtdD8lgN4"]

class GitHubPublisher:
    def __init__(self, repo, token):
        self.repo = repo
        self.token = token
        self.headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    def publish(self, html, text):
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        date = datetime.now().strftime("%Y-%m-%d")
        self._upload("index.html", html, f"Update {ts}")
        self._upload(f"archive/{date}/briefing_{ts}.html", html, f"Archive {ts}")
        return f"https://{self.repo.split('/')[0]}.github.io/{self.repo.split('/')[1]}/"
    
    def _upload(self, path, content, msg):
        url = f"https://api.github.com/repos/{self.repo}/contents/{path}"
        r = requests.get(url, headers=self.headers)
        data = {"message": msg, "content": base64.b64encode(content.encode()).decode()}
        if r.status_code == 200:
            data["sha"] = r.json()["sha"]
        requests.put(url, headers=self.headers, json=data)

def create_dashboard(data, briefing_text):
    equities = data.get('equities', [])
    crypto = data.get('crypto', [])
    
    eq_html = ""
    for eq in equities[:5]:
        bias = "bull" if eq.get('bias') == 'Bullish' else "bear"
        eq_html += f'<div class="card"><div class="ticker-row"><span class="ticker">{eq.get("ticker")}</span><span class="badge {bias}">{eq.get("bias")}</span></div><div class="grid"><div class="box"><div class="label">Entry</div><div class="price">{eq.get("entry")}</div></div><div class="box support"><div class="label">Stop</div><div class="price">{eq.get("stop")}</div></div><div class="box resist"><div class="label">Target</div><div class="price">{eq.get("target")}</div></div></div></div>'
    
    crypto_html = ""
    for c in crypto[:3]:
        bias = "bull" if c.get('bias') == 'Bullish' else "bear"
        crypto_html += f'<div class="card"><div class="ticker-row"><span class="ticker">{c.get("name")}</span><span class="badge {bias}">{c.get("bias")}</span></div><div class="grid two"><div class="box support"><div class="label">Support</div><div class="price">{c.get("support")}</div></div><div class="box resist"><div class="label">Resistance</div><div class="price">{c.get("resist")}</div></div></div></div>'
    
    css = """:root{--bg:#0d1117;--bg2:#161b22;--bg3:#21262d;--border:#30363d;--text:#f0f6fc;--text2:#8b949e;--blue:#58a6ff;--green:#238636;--red:#da3633}*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;padding-bottom:40px}.header{background:linear-gradient(135deg,var(--bg2) 0%,var(--bg3) 100%);padding:30px 20px;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100}.header h1{font-size:28px;font-weight:700;background:linear-gradient(90deg,var(--blue),#a371f7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.meta{color:var(--text2);font-size:14px}.container{padding:20px;max-width:600px;margin:0 auto}.section{margin-bottom:24px}.section-title{font-size:18px;font-weight:600;margin-bottom:16px;display:flex;align-items:center;gap:8px}.section-title::before{content:'';width:4px;height:20px;background:var(--blue);border-radius:2px}.card{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:12px}.ticker-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}.ticker{font-size:24px;font-weight:700;color:var(--blue)}.badge{padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600}.bull{background:rgba(35,134,54,.2);color:#3fb950}.bear{background:rgba(218,54,51,.2);color:#f85149}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.two{grid-template-columns:repeat(2,1fr)}.box{background:var(--bg3);padding:12px;border-radius:8px;text-align:center}.support{border:1px solid rgba(63,185,80,.3)}.resist{border:1px solid rgba(248,81,73,.3)}.label{font-size:11px;color:var(--text2);text-transform:uppercase;margin-bottom:4px}.price{font-size:16px;font-weight:700}.alert{background:linear-gradient(135deg,rgba(218,54,51,.2) 0%,rgba(182,35,36,.2) 100%);border:1px solid var(--red);border-radius:12px;padding:16px;margin-top:20px}.alert h3{color:#f85149;font-size:14px;margin-bottom:8px}"""
    
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Trading Briefing</title><style>{css}</style></head><body><div class="header"><h1>Trading Briefing</h1><div class="meta">{datetime.now().strftime('%Y-%m-%d %H:%M PT')}</div></div><div class="container"><div class="section"><div class="section-title">Equity Setups</div>{eq_html or '<div style="text-align:center;padding:40px;color:var(--text2)">No setups</div>'}</div><div class="section"><div class="section-title">Crypto Levels</div>{crypto_html or '<div style="text-align:center;padding:40px;color:var(--text2)">No crypto data</div>'}</div><div class="alert"><h3>⚠️ Risk Management</h3><ul style="list-style:none;font-size:14px;color:var(--text2)"><li style="margin-bottom:4px">• Don't trade past 9:30 AM PT</li><li style="margin-bottom:4px">• Max 3% risk per trade</li><li>• Set stops immediately</li></ul></div></div></body></html>"""

def send_telegram(token, chat, data, url):
    msg = f"📊 <b>Trading Briefing</b>\n<code>{datetime.now().strftime('%Y-%m-%d %H:%M PT')}</code>\n\n"
    for eq in data.get('equities', [])[:3]:
        emoji = "🟢" if eq.get('bias') == 'Bullish' else "🔴"
        msg += f"{emoji} <b>{eq.get('ticker')}</b> | E:{eq.get('entry')} S:{eq.get('stop')} T:{eq.get('target')}\n"
    msg += f"\n🔗 <a href='{url}'>View Dashboard</a>"
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={'chat_id':chat,'text':msg,'parse_mode':'HTML','reply_markup':json.dumps({'inline_keyboard':[[{'text':'📱 Open Dashboard','url':url}]]})})

def get_transcript(url):
    for f in ['/tmp/vid.en.vtt','/tmp/vid.vtt']: 
        if os.path.exists(f): os.remove(f)
    subprocess.run(['yt-dlp','--skip-download','--write-auto-subs','--sub-langs','en','--sub-format','vtt','--output','/tmp/vid',url], capture_output=True, timeout=120)
    vtt = '/tmp/vid.en.vtt' if os.path.exists('/tmp/vid.en.vtt') else '/tmp/vid.vtt'
    if not os.path.exists(vtt): return None
    with open(vtt,'r',encoding='utf-8',errors='ignore') as f: content=f.read()
    lines=[re.sub(r'<[^>]+>','',line.strip()) for line in content.split('\n') if line.strip() and '-->' not in line and not line.startswith('WEBVTT')]
    return ' '.join(dict.fromkeys(lines))

def analyze(transcript, api_key, type='trading'):
    client = OpenAI(api_key=api_key)
    prompt = "Extract trading setups. Tickers, entry, stop, target, patterns, confidence. Transcript: " if type=='trading' else "Extract crypto setups. BTC/ETH/altcoins, levels, patterns. Transcript: "
    return client.chat.completions.create(model='gpt-4o-mini',messages=[{'role':'user','content':prompt+transcript[:6000]}],max_tokens=800).choices[0].message.content

def parse_analysis(text):
    data={'equities':[],'crypto':[],'market_context':text[:500]}
    for line in text.split('\n'):
        if re.match(r'^[A-Z]{2,5}\s*[-:]', line):
            nums=re.findall(r'\0([\d,.]+)',line)
            if len(nums)>=3:
                data['equities'].append({'ticker':re.match(r'^([A-Z]{2,5})',line).group(1),'entry':f"",'stop':f"",'target':f"",'bias':'Bullish' if float(nums[2].replace(',',''))>float(nums[0].replace(',','')) else 'Bearish'})
        if 'BTC' in line:
            nums=re.findall(r'\0([\d,]+)',line)
            if len(nums)>=2: data['crypto'].append({'name':'BTC','support':f"",'resist':f"",'bias':'Neutral'})
    return data

def main():
    print("="*60)
    print("TRADING BRIEFING - Phase 1")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M PT')}")
    print("="*60)
    
    # Load config
    env_path = CONFIG_DIR / ".env"
    config = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k,v=line.strip().split('=',1)
                    config[k]=v
    
    api_key = config.get('OPENAI_API_KEY')
    bot_token = config.get('TELEGRAM_BOT_TOKEN')
    chat_id = config.get('TELEGRAM_CHAT_ID')
    
    analyses = []
    
    # Process VI
    print("\n📺 Processing Verified Investing...")
    for url in VERIFIED_INVESTING_URLS:
        print(f"  {url}")
        transcript = get_transcript(url)
        if transcript:
            print(f"  Transcript: {len(transcript):,} chars")
            analysis = analyze(transcript, api_key, 'trading')
            if analysis:
                analyses.append(f"VI: {analysis}")
                print("  ✓ Analyzed")
    
    # Process Mitch Ray
    print("\n📺 Processing Mitch Ray...")
    for url in MITCH_RAY_URLS:
        print(f"  {url}")
        transcript = get_transcript(url)
        if transcript:
            analysis = analyze(transcript, api_key, 'crypto')
            if analysis:
                analyses.append(f"MR: {analysis}")
                print("  ✓ Analyzed")
    
    if not analyses:
        print("❌ No analyses generated")
        return
    
    combined = "\n\n".join(analyses)
    structured = parse_analysis(combined)
    
    # Generate dashboard
    print("\n📊 Generating dashboard...")
    html = create_dashboard(structured, combined)
    DASHBOARD_PATH.write_text(html)
    print(f"  Saved: {DASHBOARD_PATH}")
    
    # Publish to GitHub
    dashboard_url = f"file://{DASHBOARD_PATH}"
    if GITHUB_TOKEN and GITHUB_REPO:
        print("\n🚀 Publishing to GitHub Pages...")
        try:
            publisher = GitHubPublisher(GITHUB_REPO, GITHUB_TOKEN)
            dashboard_url = publisher.publish(html, combined)
            print(f"  URL: {dashboard_url}")
        except Exception as e:
            print(f"  ⚠️ Publish failed: {e}")
    
    # Send Telegram
    if bot_token and chat_id:
        print("\n📱 Sending to Telegram...")
        try:
            send_telegram(bot_token, chat_id, structured, dashboard_url)
            print("  ✓ Sent")
        except Exception as e:
            print(f"  ⚠️ Telegram failed: {e}")
    
    # Open locally
    print("\n🌐 Opening dashboard...")
    os.system(f"open {DASHBOARD_PATH}")
    print(f"\n✅ Done! Dashboard: {dashboard_url}")

if __name__ == '__main__':
    main()
