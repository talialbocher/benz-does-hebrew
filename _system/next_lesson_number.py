# -*- coding: utf-8 -*-
"""
מדפיס את מספר השיעור הבא — הגבוה ביותר מבין כל הענפים (master, ענפי claude/* וכו'), ועוד 1.
כך שני שיעורים לא יקבלו אותו מספר גם אם שיעור קודם נשמר בטעות רק בענף צדדי.
מזהיר על שיעורים שקיימים רק בענף צדדי (לא ב-master) — אותם צריך למזג ל-master.

שימוש (משורש הריפו):  python3 _system/next_lesson_number.py
"""
import re, subprocess, sys

def git(*args):
    r = subprocess.run(['git'] + list(args), capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ''

def lesson_files(ref):
    names = git('ls-tree', '--name-only', ref + ':5thGrade').split()
    out = {}
    for n in names:
        m = re.match(r'lesson(\d+)_.*\.html$', n)
        if m:
            out[int(m.group(1))] = n
    return out

def main():
    subprocess.run(['git', 'fetch', '--all', '--prune', '-q'], capture_output=True)
    refs = [r for r in git('for-each-ref', '--format=%(refname:short)', 'refs/remotes', 'refs/heads').split() if not r.endswith('/HEAD')]
    master = 'origin/master' if 'origin/master' in refs else 'master'
    on_master = lesson_files(master)
    highest = max(on_master) if on_master else 0
    stranded = []
    for ref in refs:
        if ref == master:
            continue
        # הענפים הישנים (ללא בסיס משותף) לא רלוונטיים — מסתכלים רק על ענפים שמקורם ב-master הנוכחי
        if not git('merge-base', master, ref).strip():
            continue
        # ענף שכבר מוזג ל-master — אין בו שיעורים "תקועים"
        if subprocess.run(['git', 'merge-base', '--is-ancestor', ref, master], capture_output=True).returncode == 0:
            continue
        for n, f in lesson_files(ref).items():
            if f not in on_master.values() and n >= highest - 5:
                stranded.append((n, f, ref))
                highest = max(highest, n)
    own = lesson_files('HEAD')
    highest = max([highest] + list(own))
    for n, f, ref in sorted(stranded):
        print('אזהרה: שיעור %d (%s) קיים רק בענף %s ולא ב-%s — צריך למזג אותו.' % (n, f, ref, master), file=sys.stderr)
    print(highest + 1)

if __name__ == '__main__':
    main()
