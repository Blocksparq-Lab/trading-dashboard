import os
import re
from datetime import datetime

def parse_briefing(briefing_text):
    """Parse the text briefing into structured data"""
    data = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M PT'),
        'equities': [],
        'crypto': [],
        'levels': [],
        'alerts': []
    }
    
    # Extract equity setups
    equity_section = re.search(r'Equity Setups:(.*?)(?=Crypto|Cryptocurrency|$)', briefing_text, re.DOTALL | re.IGNORECASE)
    if equity_section:
        # Look for ticker patterns
        tickers = re.findall(r'([A-Z]{2,5})[^\n]*?Entry[^\d]*(\d+\.?\d*)[^\n]*?Stop[^\d]*(\d+\.?\d*)[^\n]*?Target[^\d]*(\d+\.?\d*)', equity_section.group(1), re.IGNORECASE)
        for ticker, entry, stop, target in tickers:
            data['equities'].append({
                'ticker': ticker,
                'entry': f"${entry}",
                'stop': f"${stop}",
                'target': f"${target}",
                'bias': 'Bullish' if float(target) > float(entry) else 'Bearish'
            })
    
    # Extract crypto setups
    btc_match = re.search(r'BTC[^$]*\$?(\d{2,3},?\d{3})[^$]*\$?(\d{2,3},?\d{3})', briefing_text)
    if btc_match:
        data['crypto'].append({
            'name': 'BTC',
            'support': f"${btc_match.group(1)}",
            'resist': f"${btc_match.group(2)}",
            'bias': 'Bearish' if 'bearish' in briefing_text.lower() else 'Neutral'
        })
    
    eth_match = re.search(r'ETH[^$]*\$?(\d{1,2},?\d{3})[^$]*\$?(\d{1,2},?\d{3})', briefing_text)
    if eth_match:
        data['crypto'].append({
            'name': 'ETH',
            'support': f"${eth_match.group(1)}",
            'resist': f"${eth_match.group(2)}",
            'bias': 'Bearish' if 'bearish' in briefing_text.lower() else 'Neutral'
        })
    
    return data

def create_html(data, briefing_text):
    """Create mobile-optimized HTML dashboard"""
    
    # Build equity cards
    equity_html = ''
    for eq in data['equities'][:3]:  # Max 3
        bias_class = 'bias-bull' if eq['bias'] == 'Bullish' else 'bias-bear'
        equity_html += f'''
        <div class="setup">
            <div class="ticker">{eq['ticker']} <span class="{bias_class}">{eq['bias']}</span></div>
            <div class="levels">
                <div class="level"><div class="label">Entry</div><div class="price">{eq['entry']}</div></div>
                <div class="level"><div class="label">Stop</div><div class="price support">{eq['stop']}</div></div>
                <div class="level"><div class="label">Target</div><div class="price resist">{eq['target']}</div></div>
            </div>
        </div>'''
    
    if not equity_html:
        equity_html = '<div class="setup"><div class="ticker">No specific setups found</div></div>'
    
    # Build crypto cards
    crypto_html = ''
    for crypto in data['crypto']:
        bias_class = 'bias-bull' if crypto['bias'] == 'Bullish' else 'bias-bear'
        crypto_html += f'''
        <div class="setup">
            <div class="ticker">{crypto['name']} <span class="{bias_class}">{crypto['bias']}</span></div>
            <div class="levels">
                <div class="level"><div class="label">Support</div><div class="price support">{crypto['support']}</div></div>
                <div class="level"><div class="label">Resistance</div><div class="price resist">{crypto['resist']}</div></div>
            </div>
        </div>'''
    
    if not crypto_html:
        crypto_html = '<div class="setup"><div class="ticker">No crypto data</div></div>'
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Trading Briefing</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: #0d1117; 
            color: #c9d1d9; 
            line-height: 1.5;
            padding-bottom: 40px;
        }}
        .header {{ 
            background: linear-gradient(135deg, #161b22 0%, #21262d 100%); 
            padding: 24px 20px; 
            border-bottom: 1px solid #30363d;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .header h1 {{ 
            font-size: 28px; 
            font-weight: 700;
            background: linear-gradient(90deg, #58a6ff, #a371f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
        }}
        .header .time {{ 
            color: #8b949e; 
            font-size: 14px; 
            font-weight: 500;
        }}
        .container {{ padding: 16px; }}
        .card {{ 
            background: #161b22; 
            border: 1px solid #30363d;
            border-radius: 16px; 
            margin-bottom: 16px;
            overflow: hidden;
        }}
        .card-header {{ 
            background: #21262d;
            padding: 16px 20px;
            border-bottom: 1px solid #30363d;
        }}
        .card-header h2 {{ 
            font-size: 18px; 
            font-weight: 600;
            color: #f0f6fc;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .card-body {{ padding: 16px; }}
        .setup {{ 
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 12px; 
            padding: 16px;
            margin-bottom: 12px;
        }}
        .setup:last-child {{ margin-bottom: 0; }}
        .ticker {{ 
            font-size: 24px; 
            font-weight: 700;
            color: #58a6ff;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .bias-bull {{ 
            background: #238636; 
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .bias-bear {{ 
            background: #da3633; 
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .levels {{ 
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }}
        .level {{ 
            text-align: center;
            padding: 12px 8px;
            background: #21262d;
            border-radius: 8px;
        }}
        .level .label {{ 
            font-size: 11px; 
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        .level .price {{ 
            font-size: 16px; 
            font-weight: 700;
            color: #f0f6fc;
        }}
        .support {{ color: #3fb950 !important; }}
        .resist {{ color: #f85149 !important; }}
        .alert {{ 
            background: linear-gradient(135deg, #da3633 0%, #b62324 100%);
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            margin-top: 16px;
        }}
        .alert h3 {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
            opacity: 0.9;
        }}
        .raw-text {{
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 16px;
            font-size: 13px;
            line-height: 1.6;
            color: #8b949e;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }}
        .toggle-btn {{
            background: #21262d;
            border: 1px solid #30363d;
            color: #58a6ff;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            width: 100%;
            margin-top: 16px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Trading Briefing</h1>
        <div class="time">{data['date']}</div>
    </div>
    
    <div class="container">
        <div class="card">
            <div class="card-header">
                <h2>🎯 Equity Setups</h2>
            </div>
            <div class="card-body">
                {equity_html}
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>₿ Crypto Levels</h2>
            </div>
            <div class="card-body">
                {crypto_html}
            </div>
        </div>
        
        <div class="alert">
            <h3>⚠️ Risk Management</h3>
            <div>Don't trade past 9:30 AM PT. Max 3% risk per trade.</div>
        </div>
        
        <button class="toggle-btn" onclick="document.getElementById('raw').style.display='block';this.style.display='none';">
            Show Full Text Briefing
        </button>
        
        <div id="raw" style="display:none; margin-top:16px;">
            <div class="raw-text">{briefing_text.replace('<', '&lt;').replace('>', '&gt;')}</div>
        </div>
    </div>
</body>
</html>'''
    
    return html

if __name__ == '__main__':
    # Read latest briefing
    try:
        with open(os.path.expanduser('~/trading-ai/latest_briefing.txt'), 'r') as f:
            briefing = f.read()
    except:
        briefing = 'No briefing available'
    
    # Parse and generate
    data = parse_briefing(briefing)
    html = create_html(data, briefing)
    
    # Save
    path = os.path.expanduser('~/trading-ai/dashboard.html')
    with open(path, 'w') as f:
        f.write(html)
    
    print(f'✅ Dashboard created: {path}')
    print(f'📱 Open in browser: file://{path}')
