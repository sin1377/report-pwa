#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
save_report.py — 把行情(market)或健康(health)数据写入 APP 的 data.js 并推送 GitHub
用法:
  python3 save_report.py market <json文件>
  python3 save_report.py health <json文件>
json 格式: {"date":"2026-09-27", "summary":"...", "detail":"...", "status":"grey|amber|red|green"}
"""
import re, json, sys, subprocess, os, time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def git(*args):
    return subprocess.run(['git']+list(args), capture_output=True, text=True)

def main():
    if len(sys.argv) < 3:
        print('usage: save_report.py market|health|intel <json>'); sys.exit(1)
    kind = sys.argv[1]
    if kind not in ('market', 'health', 'intel'):
        print('kind must be market/health/intel'); sys.exit(1)
    payload = json.load(open(sys.argv[2]))
    today = payload.get('date')
    if not today:
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')

    js = open('data.js').read()
    m = re.search(r'(var REPORTS\s*=\s*)(\[[\s\S]*?\]);', js)
    entries = json.loads(m.group(2))

    target = next((e for e in entries if e['date'] == today), None)
    if not target:
        # 自动补一条当日条目
        import datetime as dt
        weekday_names = ['周一','周二','周三','周四','周五','周六','周日']
        d = dt.datetime.strptime(today, '%Y-%m-%d')
        target = {"date": today, "label": d.strftime('%m-%d') + ' ' + weekday_names[d.weekday()],
                  "market": {"status":"grey","summary":"数据生成中","detail":""},
                  "health": {"status":"grey","summary":"数据生成中","detail":""},
                  "intel":  {"status":"grey","summary":"数据生成中","detail":""}}
        entries.insert(0, target)

    target[kind] = {
        'status': payload.get('status', 'grey'),
        'summary': payload.get('summary', ''),
        'detail': payload.get('detail', '')
    }

    new_js = js[:m.start(2)] + json.dumps(entries, ensure_ascii=False, indent=2) + js[m.end(2):]
    open('data.js', 'w').write(new_js)

    git('add', 'data.js')
    git('commit', '-m', f'{kind} update for {today}')
    r = git('push', 'origin', 'main')
    if r.returncode != 0:
        # 网络抖动重试最多3次
        for i in range(3):
            time.sleep(5)
            r = git('push', 'origin', 'main')
            if r.returncode == 0: break
        if r.returncode != 0:
            print('PUSH FAILED:', r.stderr[:300]); sys.exit(1)
    print(f'OK - {kind} saved for {today}')

if __name__ == '__main__':
    main()
