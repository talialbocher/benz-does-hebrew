# -*- coding: utf-8 -*-
"""
בדיקה טכנית אוטומטית לשיעור עברית (שלב 4 בתהליך).
שימוש:  python3 verify_lesson.py <lesson_file.html> [...]
מחזיר קוד יציאה 0 אם הכל תקין, 1 אם נמצאו בעיות.
"""
import re, sys, os, glob, colorsys, subprocess, tempfile
from html.parser import HTMLParser

KNOWN_BAD = [
    'שִׁעוּר', 'שִּׁעוּר',            # איות הסדרה: שִׁיעוּר
    'בְּזְמַן', 'בְּנְקֻדָּה', 'בְּפְּסִיק',  # בכ"ל לפני שווא
    'מִתוֹךְ',                        # חסר דגש
    'כַּדּוּרְרֶגֶל',                  # רי"ש כפולה
    'מִמְתָּק', 'יִנְפֹּל', 'שֶׁלְחָן', 'סִיֹּמֶת', 'מַדּוּבָּר',
    'אֵיזֶה צוּרָה', 'מַשְׁמָעוּיּוֹת', 'מְוּכָּרוֹת',
    'אֲנִי גָּרִים', 'הַעֲגוֹרָן', 'עֲגוֹרַן',
]

class TagChecker(HTMLParser):
    VOID = {'meta','link','br','img','input','hr','circle','rect','path',
            'ellipse','polygon','line','polyline','use','stop'}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errs = [], []
    def handle_starttag(self, t, a):
        if t not in self.VOID: self.stack.append(t)
    def handle_endtag(self, t):
        if t in self.VOID: return
        if self.stack and self.stack[-1] == t: self.stack.pop()
        elif t in self.stack:
            while self.stack and self.stack[-1] != t:
                self.errs.append('unclosed <%s>' % self.stack.pop())
            self.stack.pop()
        else:
            self.errs.append('stray </%s>' % t)

def lum(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(c*2 for c in h)
    r, g, b = (int(h[i:i+2], 16)/255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)[1]

def check(path):
    issues = []
    folder = os.path.dirname(os.path.abspath(path)) or '.'
    html = open(path, encoding='utf-8').read()
    body = re.sub(r'<style>.*?</style>', '', html, flags=re.S)

    # 1. מבנה HTML
    p = TagChecker(); p.feed(html)
    issues += ['HTML: ' + e for e in p.errs[:5]]
    if p.stack: issues.append('HTML: תגיות לא סגורות: ' + ','.join(p.stack[:5]))

    # 2. JavaScript תקין (דורש node)
    for i, m in enumerate(re.finditer(r'<script>(.*?)</script>', html, flags=re.S)):
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as t:
            t.write(m.group(1)); tmp = t.name
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            issues.append('JS בלוק %d: %s' % (i, r.stderr.strip().splitlines()[0]))

    # 3. קטע כתיבה אחד בלבד (לפי כותרות, לא לפי אימוג׳י)
    n = len(re.findall(r'מַטְלַת כְּתִיבָה|כְּתִיבָה יְצִירָתִית', body))
    if n != 1: issues.append('קטעי כתיבה: %d (צריך בדיוק 1)' % n)

    # 4. עיצוב אחיד
    if 'fonts.googleapis' not in html: issues.append('חסר קישור לפונטים')
    if 'header35' not in html: issues.append('חסרה כותרת בסגנון הסדרה (header35)')
    if not re.search(r'--p1:', html): issues.append('חסרות הגדרות צבע (:root --p1)')
    if re.search(r': (hover|disabled|active|focus)', html):
        issues.append('CSS: רווח אחרי נקודתיים ב-pseudo-class')

    # 5. ניגודיות: רקע וטקסט קרובים מדי באותו כלל CSS
    css = ' '.join(re.findall(r'<style>(.*?)</style>', html, re.S))
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        sel, decl = m.group(1).strip()[-40:], m.group(2)
        bg = re.search(r'background[a-z-]*\s*:\s*([^;]+)', decl)
        col = re.search(r'(?<![a-z-])color\s*:\s*(#[0-9a-fA-F]{3,6})', decl)
        if bg and col:
            bgh = re.findall(r'#[0-9a-fA-F]{3,6}\b', bg.group(1))
            if bgh and abs(lum(bgh[0]) - lum(col.group(1))) < 0.25:
                issues.append('ניגודיות חלשה: %s (רקע %s, טקסט %s)' % (sel, bgh[0], col.group(1)))

    # 6. שגיאות עברית מוכרות
    for bad in KNOWN_BAD:
        if bad in body:
            issues.append('שגיאה מוכרת בטקסט: "%s"' % bad)

    # 7. מספר השיעור אחיד בין שם הקובץ, הכותרת והניווט
    mnum = re.search(r'lesson(\d+)', os.path.basename(path))
    if mnum:
        num = int(mnum.group(1))
        if ('שִׁיעוּר %d' % num) not in body:
            issues.append('מספר השיעור %d לא מופיע בגוף הדף' % num)

    # 8. קישורי ניווט מצביעים לקבצים קיימים
    for href in re.findall(r'class="nav-btn" href="([^"]+)"', html):
        if not os.path.exists(os.path.join(folder, href)):
            issues.append('קישור ניווט שבור: %s' % href)

    # 9. אין placeholders של התבנית
    if '{{' in html: issues.append('נשארו placeholders של התבנית ({{...}})')

    return issues

if __name__ == '__main__':
    files = sys.argv[1:] or sorted(glob.glob('lesson*.html'))
    bad = 0
    for f in files:
        issues = check(f)
        if issues:
            bad += 1
            print('❌ %s' % f)
            for i in issues: print('   - %s' % i)
        else:
            print('✅ %s' % f)
    sys.exit(1 if bad else 0)
