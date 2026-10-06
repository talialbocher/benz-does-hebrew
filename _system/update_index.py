# -*- coding: utf-8 -*-
"""
מוסיף ל-index.html כותרת עברית לכל שיעור שחסר ב-titleMap.
הכותרת נלקחת מתגית <title> של קובץ השיעור עצמו (בלי הקידומת "שִׁיעוּר N — ").
לא נוגע בכותרות שכבר קיימות.

שימוש (משורש הריפו):  python3 _system/update_index.py
"""
import re, os, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'index.html')
PREFIX = re.compile(r'^\s*[^\d]{0,14}\d+\s*[—–-]\s*')

def lesson_num(name):
    return int(re.match(r'lesson(\d+)_', name).group(1))

def js_quote(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"

def title_of(path):
    html = open(path, encoding='utf-8').read()
    m = re.search(r'<title>(.*?)</title>', html, re.S)
    if not m:
        return None
    t = PREFIX.sub('', m.group(1).strip()).strip()
    return t if re.search(r'[א-ת]', t) else None

def main():
    src = open(INDEX, encoding='utf-8').read()
    m = re.search(r'(const titleMap = \{\n)(.*?)(\n\};)', src, re.S)
    if not m:
        sys.exit('לא נמצא titleMap ב-index.html')
    body = m.group(2)
    existing = set(re.findall(r"'(lesson\d+_[^']+\.html)'\s*:", body))
    files = sorted((os.path.basename(f) for f in glob.glob(os.path.join(ROOT, '5thGrade', 'lesson*.html'))),
                   key=lesson_num)
    new_lines = []
    for f in files:
        if f in existing:
            continue
        t = title_of(os.path.join(ROOT, '5thGrade', f))
        if not t:
            print('!! אין כותרת עברית ב-<title> של', f)
            continue
        new_lines.append("  %s: %s" % (js_quote(f), js_quote(t)))
        print('נוסף:', f, '->', t)
    if not new_lines:
        print('index.html כבר מעודכן — אין שיעורים חדשים.')
        return
    body = body.rstrip().rstrip(',') + ',\n' + ',\n'.join(new_lines)
    open(INDEX, 'w', encoding='utf-8').write(src[:m.start(2)] + body + src[m.end(2):])
    print('עודכנו %d כותרות ב-index.html' % len(new_lines))

if __name__ == '__main__':
    main()
