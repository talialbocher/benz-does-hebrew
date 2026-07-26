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

# ── תפזורת/תשבץ: בדיקות אופציונליות (ראו _system/games_reference.md) ──
# רצות רק אם השיעור מכריז על wsGrid/wsWords או cwEntries בפורמט המתועד;
# שיעורים שלא משתמשים במשחקים האלה לא מושפעים כלל.
NIKUD_RE = re.compile(r'[֑-ׇ]')
HEB_FINALS = set('םןךףץ')

def _mid_word_final_letters(word):
    return [ch for ch in word[:-1] if ch in HEB_FINALS]

def check_word_search(body):
    issues = []
    m_grid = re.search(r'const\s+wsGrid\s*=\s*\[(.*?)\]\s*;', body, re.S)
    m_words = re.search(r'const\s+wsWords\s*=\s*\[(.*?)\]\s*;', body, re.S)
    if not m_grid and not m_words:
        return issues
    if not (m_grid and m_words):
        issues.append('תפזורת: נמצא wsGrid בלי wsWords (או להפך) — צריך את שניהם')
        return issues
    grid = re.findall(r'''['"]([^'"]*)['"]''', m_grid.group(1))
    words = re.findall(r'''['"]([^'"]*)['"]''', m_words.group(1))
    if not grid or not words:
        issues.append('תפזורת: wsGrid או wsWords ריקים')
        return issues
    rowlen = len(grid[0])
    if any(len(r) != rowlen for r in grid):
        issues.append('תפזורת: שורות הרשת (wsGrid) לא באותו אורך')
    if NIKUD_RE.search(''.join(grid)):
        issues.append('תפזורת: הרשת (wsGrid) מכילה ניקוד — האותיות ברשת צריכות להיות בלי ניקוד')
    for w in words:
        if NIKUD_RE.search(w):
            issues.append('תפזורת: המילה "%s" ב-wsWords מכילה ניקוד' % w)
        bad = _mid_word_final_letters(w)
        if bad:
            issues.append('תפזורת: המילה "%s" — אות סופית (%s) לא בסוף המילה' % (w, ','.join(bad)))
    R, C = len(grid), rowlen
    dirs = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
    for w in words:
        found = False
        for r in range(R):
            for c in range(C):
                for dr, dc in dirs:
                    ok = True
                    for k, ch in enumerate(w):
                        rr, cc = r + dr*k, c + dc*k
                        if not (0 <= rr < R and 0 <= cc < C) or grid[rr][cc] != ch:
                            ok = False; break
                    if ok:
                        found = True; break
                if found: break
            if found: break
        if not found:
            issues.append('תפזורת: המילה "%s" לא נמצאת ברשת (wsGrid) באף כיוון ישר' % w)
    return issues

def check_crossword(body):
    issues = []
    m = re.search(r'const\s+cwEntries\s*=\s*\[(.*?)\]\s*;', body, re.S)
    if not m:
        return issues
    entry_re = re.compile(
        r"\{\s*num\s*:\s*(\d+)\s*,\s*dir\s*:\s*'(across|down)'\s*,\s*row\s*:\s*(\d+)\s*,\s*col\s*:\s*(\d+)\s*,"
        r"\s*answer\s*:\s*'([^']*)'\s*,\s*clue\s*:\s*'([^']*)'\s*\}"
    )
    entries = entry_re.findall(m.group(1))
    if not entries:
        issues.append('תשבץ: נמצא cwEntries אבל לא הצלחתי לפרסר אף רשומה — ודאו פורמט '
                       '{num:N, dir:\'across\'|\'down\', row:R, col:C, answer:\'...\', clue:\'...\'} '
                       'בדיוק בסדר הזה, עם מרכאות בודדות')
        return issues
    cells = {}
    for num, dir_, row, col, answer, clue in entries:
        row, col = int(row), int(col)
        if NIKUD_RE.search(answer):
            issues.append('תשבץ: התשובה "%s" (מספר %s) מכילה ניקוד' % (answer, num))
        bad = _mid_word_final_letters(answer)
        if bad:
            issues.append('תשבץ: התשובה "%s" (מספר %s) — אות סופית (%s) לא בסוף המילה' % (answer, num, ','.join(bad)))
        for k, ch in enumerate(answer):
            r = row + k if dir_ == 'down' else row
            c = col + k if dir_ == 'across' else col
            key = (r, c)
            if key in cells and cells[key] != ch:
                issues.append('תשבץ: התנגשות בתא (%d,%d) בין מילים שונות — "%s" מול "%s"' % (r, c, cells[key], ch))
            cells[key] = ch
    return issues

# ── שאלות רב-ברירה: התשובה הנכונה לא צריכה "לבלוט" ──
# הבעיה הנפוצה: בהבנת הנקרא התשובה הנכונה היא המפורטת והארוכה ביותר,
# ולכן אפשר לזהות אותה בלי לקרוא את הסיפור.
LEN_RATIO = 1.4   # התשובה הנכונה ארוכה פי-כמה מהמסיח הארוך ביותר
LEN_GAP   = 8     # ובנוסף — הפרש מוחלט בתווים (בלי ניקוד)
LONGEST_SHARE = 0.6  # שיעור השאלות שבהן הנכונה היא הארוכה ביותר

def _js_strings(s):
    """מפרק גוף של מערך JS למחרוזות — תומך ב-' וב-" ובתווי בריחה."""
    out, i, n = [], 0, len(s)
    while i < n:
        if s[i] in '"\'':
            q, i, buf = s[i], i + 1, []
            while i < n:
                if s[i] == '\\' and i + 1 < n:
                    buf.append(s[i+1]); i += 2; continue
                if s[i] == q: break
                buf.append(s[i]); i += 1
            out.append(''.join(buf))
        i += 1
    return out

def _scan_to_close(s, i, open_ch='[', close_ch=']'):
    """מחזיר את המיקום שאחרי הסוגר הסוגר, בהתעלם מסוגריים בתוך מחרוזות."""
    depth = 1
    while i < len(s) and depth:
        c = s[i]
        if c in '"\'':
            q = c; i += 1
            while i < len(s):
                if s[i] == '\\': i += 2; continue
                if s[i] == q: break
                i += 1
        elif c == open_ch: depth += 1
        elif c == close_ch: depth -= 1
        i += 1
    return i

def _js_array(body, varname):
    m = re.search(r'\b(?:const|let|var)\s+%s\s*=\s*\[' % re.escape(varname), body)
    if not m: return None
    end = _scan_to_close(body, m.end())
    return body[m.end():end-1]

def _mc_questions(block):
    """מחזיר רשימת (opts, ans) לכל שאלה בבלוק."""
    qs = []
    for m in re.finditer(r'opts\s*:\s*\[', block):
        end = _scan_to_close(block, m.end())
        opts = _js_strings(block[m.end():end-1])
        ma = re.search(r'ans\s*:\s*(\d+)', block[end:end+150])
        if opts and ma:
            a = int(ma.group(1))
            if 0 <= a < len(opts):
                qs.append((opts, a))
    return qs

def check_mc_options(body, html):
    issues = []
    shuffles = 'shuffleOptions' in html
    for varname, label in (('compQuestions', 'הבנת הנקרא'), ('gramQuestions', 'דקדוק')):
        block = _js_array(body, varname)
        if block is None: continue
        qs = _mc_questions(block)
        if not qs: continue

        longest = 0
        for n, (opts, a) in enumerate(qs, 1):
            plain = [NIKUD_RE.sub('', o) for o in opts]
            if len(plain) < 2: continue
            c = len(plain[a])
            other = max(len(o) for i, o in enumerate(plain) if i != a)
            if not other: continue
            if c > other: longest += 1
            if c >= LEN_RATIO * other and c - other >= LEN_GAP:
                issues.append(
                    '%s, שאלה %d: התשובה הנכונה ארוכה בהרבה מכל המסיחים '
                    '(%d תווים מול %d) — אפשר לזהות אותה בלי לקרוא. '
                    'קצרו אותה או הרחיבו את המסיחים לאותו אורך.' % (label, n, c, other))

        if len(qs) >= 4 and longest / len(qs) >= LONGEST_SHARE:
            issues.append(
                '%s: ב-%d מתוך %d שאלות התשובה הנכונה היא האפשרות הארוכה ביותר — '
                'דפוס שמאפשר לנחש לפי אורך. אזנו את אורכי האפשרויות.'
                % (label, longest, len(qs)))

        if not shuffles and len(qs) >= 4 and len(set(a for _, a in qs)) == 1:
            issues.append(
                '%s: התשובה הנכונה נמצאת באותו מיקום (ans:%d) בכל %d השאלות. '
                'פזרו את המיקומים, או השתמשו במנוע מהתבנית שמערבב את האפשרויות '
                '(shuffleOptions ב-_system/lesson_template.html).'
                % (label, qs[0][1], len(qs)))
    return issues

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

    # 10. תפזורת/תשבץ (אופציונלי — רק אם השיעור מכריז wsGrid/wsWords או cwEntries)
    issues += check_word_search(body)
    issues += check_crossword(body)

    # 11. שאלות רב-ברירה: התשובה הנכונה לא בולטת באורך או במיקום
    issues += check_mc_options(body, html)

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
