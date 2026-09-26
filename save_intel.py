#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
save_intel.py — 把市场情报（全球新闻+地缘政治独立分析）写入 APP 数据
用法: python3 save_intel.py <json文件>
json 格式: {"summary": "...", "detail": "...", "status": "amber|red|green|grey"}
"""
import re, json, sys, subprocess, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def git(*args):
    return subprocess.run(['git']+list(args), capture_output=True, text=True)

def main():
    if len(sys.argv) < 2:
        print('usage: save_intel.py <json>'); sys.exit(1)
    intel = json.load(open(sys.argv[1]))
    today = intel.get('date')
    if not today:
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')

    html = open('index.html').read()
    m = re.search(r'(var REPORTS\s*=\s*)(\[[\s\S]*?\]);', html)
    entries = json.loads(m.group(2))

    target = next((e for e in entries if e['date'] == today), None)
    if not target:
        print(f'ERROR: no entry for {today}'); sys.exit(1)

    target['intel'] = {
        'status': intel.get('status', 'amber'),
        'summary': intel['summary'],
        'detail': intel['detail']
    }
    # 去掉旧占位
    if 'intel_placeholder' in target:
        del target['intel_placeholder']

    new_html = html[:m.start(2)] + json.dumps(entries, ensure_ascii=False, indent=2) + html[m.end(2):]
    open('index.html', 'w').write(new_html)

    git('add', 'index.html')
    git('commit', '-m', f'Intel update for {today}')
    r = git('push', 'origin', 'main')
    if r.returncode != 0:
        print('PUSH FAILED:', r.stderr[:300]); sys.exit(1)
    print(f'OK - intel saved for {today}')

if __name__ == '__main__':
    main()
