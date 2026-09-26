#!/usr/bin/env python3
"""
Daily update script for the Report Archive PWA.
Pulls the latest repo state, appends new daily data to index.html,
commits and pushes to GitHub Pages.
"""
import os, sys, json, re, subprocess, datetime

REPO_DIR = '/home/sandbox/.openclaw/workspace/report-pwa'
GIT_REMOTE = 'https://ghp_Gy…X1RM@github.com/sin1377/report-pwa.git'

def run(cmd, cwd=REPO_DIR):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'ERROR [{cmd}]: {result.stderr[:200]}')
        return None
    return result.stdout.strip()

def main():
    today = datetime.date.today()
    weekday_names = ['周一','周二','周三','周四','周五','周六','周日']
    date_str = today.strftime('%Y-%m-%d')
    label = f"{today.strftime('%m-%d')} {weekday_names[today.weekday()]}"
    
    os.chdir(REPO_DIR)
    
    # Pull latest
    run('git pull origin main')
    
    # Read current index.html
    with open('index.html', 'r') as f:
        html = f.read()
    
    # Check if today's entry already exists
    if date_str in html:
        print(f'Entry for {date_str} already exists, skipping')
        return
    
    # Find the REPORTS array
    match = re.search(r'(var REPORTS\s*=\s*)(\[.*?\]);', html, re.DOTALL)
    if not match:
        print('ERROR: Could not find REPORTS array in index.html')
        return
    
    prefix = match.group(1)
    current_array = match.group(2)
    
    # Generate placeholder entry (will be replaced by actual data from the morning reports)
    new_entry = {
        "date": date_str,
        "label": label,
        "market": {
            "status": "grey",
            "summary": "数据生成中...每日8:30更新",
            "detail": "行情数据将在每日早报生成后自动更新。请稍后刷新页面。"
        },
        "health": {
            "status": "grey",
            "summary": "手表数据待同步",
            "detail": "⌚ 华为手表数据尚未同步。请确保华为健康App已绑定手表并开启数据同步。"
        },
        "intel": {
            "status": "grey",
            "summary": "情报生成中...每日凌晨更新",
            "detail": "🌍 全球市场情报与地缘政治分析将在每日凌晨自动更新。"
        }
    }
    
    # Parse existing array and prepend new entry
    try:
        entries = json.loads(current_array)
    except json.JSONDecodeError:
        print('ERROR: Could not parse REPORTS array')
        return
    
    entries.insert(0, new_entry)
    new_array = json.dumps(entries, ensure_ascii=False, indent=2)
    
    # Replace in HTML
    new_html = html[:match.start(2)] + new_array + html[match.end(2):]
    
    with open('index.html', 'w') as f:
        f.write(new_html)
    
    # Commit and push
    run('git add index.html')
    run(f'git commit -m "Update data for {date_str}"')
    run('git push origin main')
    
    print(f'Updated index.html with entry for {date_str}')

if __name__ == '__main__':
    main()
