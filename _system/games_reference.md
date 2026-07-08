# מדריך משחקים — תפזורת ותשבץ

מדריך יישום למשחקי מילים חדשים בסדרה, לצד מנוע ה-MC הגנרי (שאלות רב-ברירה)
המתועד ב-`lesson_template.html`. עקרון העל זהה: **מנוע קבוע + תוכן משתנה**.
הסוכן היוצר מספק רק את הנתונים (רשת/מילים, או רשומות תשבץ) ווו אחד לסצנה
הוויזואלית הייחודית של השיעור (`onWordFound` / `onCrosswordSolved`,
בדיוק כמו `onCorrectComp` / `onCorrectGram`) — **לא לשנות את קוד המנוע עצמו**.

## למה תשבץ (תַּשְׁבֵּץ) ולא תשחץ (תַּשְׁחֵץ)?

תשחץ (תשבץ-חצים) מציג את ההגדרות בתוך תאים עם חץ שמצביע לכיוון המילה, בלי
רשימת "מאוזן/מאונך" נפרדת. זה דורש תכנון גיאומטרי מדויק מאוד: לכל מילה
צריך תא-חץ פנוי בדיוק בכיוון הנכון, בלי התנגשות עם מילים אחרות, ובעברית
(RTL) כיוון "ימינה" ו"למטה" מתהפכים בקלות בטעות. זה סוג טעות שקשה לתפוס
אוטומטית (זה לא עניין של אות שגויה אלא פריסה גרפית שלמה), ובלי בדיקה
ויזואלית אנושית הסיכוי לחץ שמצביע למקום הלא נכון גבוה. **לכן ההחלטה: מיישמים
תשבץ רגיל** (מספור בתא + רשימת הגדרות "מאוזן"/"מאונך" בצד) — אותו אפשר
לאמת אוטומטית (ראו הבדיקות ב-`verify_lesson.py`, סעיף 10) בלי צורך בבדיקה
ויזואלית של כיוון חצים.

## עקרונות עבריים משותפים לשני המשחקים

1. **RTL בכל מקום** — עוטפים את הרשת ב-`dir="rtl"` וב-CSS `direction:rtl`
   על מיכל ה-grid, כך שהעמודה הראשונה (אינדקס 0 במערך הנתונים) מוצגת
   מימין — בדיוק כמו קריאה טבעית בעברית. **חשוב:** קואורדינטות `row`/`col`
   בנתונים (`wsGrid`, `cwEntries`) הן תמיד אינדקס מערך רגיל (0 = ראשון);
   ה-CSS `direction:rtl` הוא זה שהופך את הכיוון הוויזואלי — אין צורך
   להפוך מחרוזות או לשחק עם האינדקסים בעצמכם.
2. **בלי ניקוד ברשת/בתשובות** — האותיות בתאי הרשת (`wsGrid`) ובתשובות
   התשבץ (`cwEntries[].answer`) הן תמיד אותיות רגילות בלי סימני ניקוד.
   ניקוד שייך לרשימת אוצר המילים של השיעור (`vocab-grid`) ולהגדרות/רמזים
   (`clue`) בטקסט חופשי — לא לתאי הרשת עצמם. `verify_lesson.py` בודק את
   זה אוטומטית ומסמן שגיאה אם יש ניקוד בתוך `wsGrid`/`wsWords`/
   `cwEntries[].answer`.
3. **אותיות סופיות (ך ם ן ף ץ)** — כלל ברזל: **אות סופית מותרת רק כאות
   האחרונה של המילה**, אף פעם לא באמצע. בתשבץ זה קורה אוטומטית כי כל
   רשומה היא מילה שלמה אמיתית — האות הסופית, אם יש, נופלת ממילא בסוף
   ה-`answer`. **בתפזורת יש סיכון אמיתי**: אם ממקמים מילה בכיוון "אחורה"
   (reversed) ברשת, האות הסופית שלה תיפול פיזית באמצע השרשרת שנקראת
   בכיוון ההפוך — טעות עברית קלאסית. **הפתרון במנוע כאן: מנוע התפזורת
   לא הופך מילים — `wsLocate` מחפש את `wsWords[i]` בדיוק כפי שהיא כתובה,
   בכל אחד מ-8 הכיוונים הישרים, אבל האותיות ברשת חייבות להיות מונחות
   כך שהאות הסופית (אם יש) תיפול בקצה שבו המילה באמת נגמרת** — כלומר
   כשאתם ממלאים את `wsGrid` בעצמכם, ודאו שכתבתם את המילה ברצף הנכון
   (לא הפוך) בכיוון שבחרתם. `verify_lesson.py` בודק שאין אות סופית
   באמצע אף מילה ב-`wsWords`/`cwEntries[].answer`, ושכל מילה אכן נמצאת
   ברשת בכיוון ישר — אבל **לא** בודק שהכיוון בפועל שמרתם עליו ברשת
   "נכון" מבחינת סופית-מול-רגילה; זו אחריות הסוכן היוצר בזמן שמכינים
   את הרשת.
4. **גודל תא נוח למגע** — לפחות 32–36px בכל צד (כמו בדוגמאות למטה), כדי
   שילד יוכל ללחוץ/לגעת בנוחות גם בטלפון.

## תפזורת (Word Search)

### אינטראקציה
לחיצה/מגע על **האות הראשונה** של מילה, ואז לחיצה/מגע על **האות האחרונה**
שלה. המנוע מזהה את הקו הישר ביניהן (8 כיוונים: אופקי, אנכי, ואלכסוני,
בשני הכיוונים) ובודק אם הוא תואם אחת מהמילים המבוקשות. שיטת "שתי לחיצות"
הזו עדיפה על גרירה (drag) כי היא עובדת זהה בעכבר ובמגע, ולא דורשת טיפול
ב-`touchmove`/`mousemove`.

### חיבור למנוע הניקוד/משוב של השיעור
משתמשים מחדש במחלקות הקיימות מהתבנית: `.progress-dots`/`.dot` (נקודה
אחת לכל מילה, מסומנת `.done` כשנמצאה), `.result-banner` (מוצג כשכל
המילים נמצאו). הווה הסצנה הייחודית הוא `onWordFound(word, foundCount, total)`
— בדיוק כמו `onCorrectComp`, כאן מוסיפים את "הקסם" הספציפי לשיעור (למשל
ציור שמתמלא, פרח שפורח וכו').

### קונבנציית נתונים (פורמט קבוע — כך `verify_lesson.py` מזהה ומאמת)
```js
const wsGrid = [
  'ספרגןנב',   // כל השורות באותו אורך! בלי רווחים, בלי ניקוד
  'עטבחברת',
  'טירונקש',
  'שגמחברת',
  'ילדבתיר',
  'םכיתהשם'
];
const wsWords = ['ספר','גן','מחברת','ילד','כיתה']; // בלי ניקוד
```

### דוגמה עצמאית ומלאה (HTML + CSS + JS) — בדוקה, עוברת את verify_lesson.py

```html
<div class="game-box">
  <div class="game-title">🔍 תַּפְזֹרֶת מִלִּים</div>
  <div class="game-subtitle">לְחַצְתֶּם עַל הָאוֹת הָרִאשׁוֹנָה וְעַל הָאַחֲרוֹנָה שֶׁל הַמִּלָּה</div>
  <div class="progress-dots" id="ws-dots"></div>
  <div id="ws-grid" class="ws-grid" dir="rtl"></div>
  <div id="ws-wordlist" class="ws-wordlist"></div>
  <div class="result-banner" id="ws-result"></div>
</div>
```

```css
.ws-grid{display:grid;direction:rtl;gap:3px;justify-content:center;margin:14px auto;width:max-content}
.ws-cell{width:34px;height:34px;display:flex;align-items:center;justify-content:center;
  font-family:'Frank Ruhl Libre',serif;font-size:1.15rem;font-weight:700;color:var(--ink);
  background:#fff;border:2px solid var(--p1lt);border-radius:8px;cursor:pointer;user-select:none}
.ws-cell:hover{border-color:var(--p1)}
.ws-cell.picked{background:var(--p1lt);border-color:var(--p1)}
.ws-cell.found{background:#dcfce7;border-color:var(--ok);color:#15803d}
.ws-wordlist{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:14px}
.ws-word-chip{background:var(--p1lt);border:1.5px solid var(--p1md);border-radius:20px;padding:5px 14px;
  font-family:'Frank Ruhl Libre',serif;font-size:1rem;font-weight:700;color:var(--p1dk)}
.ws-word-chip.found{background:#dcfce7;border-color:var(--ok);color:#15803d;text-decoration:line-through}
```

```js
const wsGrid = [
  'ספרגןנב',
  'עטבחברת',
  'טירונקש',
  'שגמחברת',
  'ילדבתיר',
  'םכיתהשם'
];
const wsWords = ['ספר','גן','מחברת','ילד','כיתה'];

function onWordFound(word, foundCount, total){ /* וו לסצנה - לשנות בכל שיעור */ }

/* מנוע תפזורת גנרי — לא לשנות */
const WS_DIRS = [[0,1],[0,-1],[1,0],[-1,0],[1,1],[1,-1],[-1,1],[-1,-1]];
function wsLocate(grid, word){
  const R=grid.length, C=grid[0].length;
  for(let r=0;r<R;r++) for(let c=0;c<C;c++) for(const [dr,dc] of WS_DIRS){
    let ok=true;
    for(let k=0;k<word.length;k++){
      const rr=r+dr*k, cc=c+dc*k;
      if(rr<0||rr>=R||cc<0||cc>=C||grid[rr][cc]!==word[k]){ ok=false; break; }
    }
    if(ok) return {r,c,dr,dc,len:word.length};
  }
  return null;
}
let wsPlacements={}, wsFound=new Set(), wsPick=null;
function wsInit(){
  const gridEl=document.getElementById('ws-grid');
  gridEl.style.gridTemplateColumns='repeat('+wsGrid[0].length+',1fr)';
  gridEl.innerHTML='';
  wsGrid.forEach((row,r)=>{
    [...row].forEach((ch,c)=>{
      const cell=document.createElement('div'); cell.className='ws-cell';
      cell.textContent=ch; cell.dataset.r=r; cell.dataset.c=c;
      cell.onclick=()=>wsClick(r,c,cell);
      gridEl.appendChild(cell);
    });
  });
  wsWords.forEach(w=>{ const p=wsLocate(wsGrid,w); if(p) wsPlacements[w]=p; });
  const list=document.getElementById('ws-wordlist'); list.innerHTML='';
  wsWords.forEach(w=>{ const chip=document.createElement('span'); chip.className='ws-word-chip'; chip.id='ws-chip-'+w; chip.textContent=w; list.appendChild(chip); });
  const dots=document.getElementById('ws-dots'); dots.innerHTML='';
  wsWords.forEach((_,i)=>{ const d=document.createElement('div'); d.className='dot'; d.id='ws-dot-'+i; dots.appendChild(d); });
}
function wsClick(r,c,cell){
  if(cell.classList.contains('found')) return;
  if(!wsPick){ wsPick={r,c}; cell.classList.add('picked'); return; }
  document.querySelectorAll('.ws-cell.picked').forEach(x=>x.classList.remove('picked'));
  const start=wsPick, end={r,c}; wsPick=null;
  for(const w of wsWords){
    if(wsFound.has(w)) continue;
    const p=wsPlacements[w]; if(!p) continue;
    const er=p.r+p.dr*(p.len-1), ec=p.c+p.dc*(p.len-1);
    const matchFwd = start.r===p.r&&start.c===p.c&&end.r===er&&end.c===ec;
    const matchBack = start.r===er&&start.c===ec&&end.r===p.r&&end.c===p.c;
    if(matchFwd||matchBack){
      wsFound.add(w);
      for(let k=0;k<p.len;k++){
        const rr=p.r+p.dr*k, cc=p.c+p.dc*k;
        document.querySelector('.ws-cell[data-r="'+rr+'"][data-c="'+cc+'"]').classList.add('found');
      }
      document.getElementById('ws-chip-'+w).classList.add('found');
      document.getElementById('ws-dot-'+wsWords.indexOf(w)).classList.add('done');
      onWordFound(w, wsFound.size, wsWords.length);
      if(wsFound.size===wsWords.length){
        const res=document.getElementById('ws-result');
        res.textContent='🌟 כָּל הַכָּבוֹד! מָצָאתָ אֶת כָּל '+wsWords.length+' הַמִּלִּים!';
        res.style.display='block';
      }
      return;
    }
  }
}
wsInit();
```

`wsLocate` מחפש בעצמו את המיקום/כיוון של כל מילה ברשת שהוכנה מראש —
הסוכן היוצר לא צריך לחשב קואורדינטות ידנית, רק לוודא שהמילה באמת כתובה
ברשת (ואם לא — `verify_lesson.py` יתפוס את זה).

## תשבץ (Crossword)

### אינטראקציה
כל תא פעיל הוא `<input maxlength="1">`. לוחצים על תא ומקלידים אות אחת;
המספור בפינת התא מציין תחילת רשומה (בדיוק כמו תשבץ מודפס). כפתור "בְּדֹק"
(`.submit-btn` הקיים) משווה כל תא לתשובה הנכונה ומסמן `.correct`/`.wrong`;
כשהכול נכון מוצג `.result-banner` והווה `onCrosswordSolved()` מופעל.
(אין כאן ניווט אוטומטי בין תאים בהקלדה — בכוונה, כדי לשמור על המנוע פשוט
ואמין; זה לא פוגע בשימושיות כי הילד רואה מיד את המספור והרמזים בצד).

### חיבור למנוע הניקוד/משוב של השיעור
`.submit-btn`/`.result-banner` — אותן מחלקות בדיוק כמו במנוע ה-MC ובמנוע
התפזורת, כדי לשמור על מראה אחיד בין המשחקים. הרמזים מוצגים בשתי רשימות
("מְאֻזָּן"/"מְאֻנָּך"), ממוספרות וממוינות לפי `num`.

### קונבנציית נתונים (פורמט קבוע — סדר השדות חייב להישאר num,dir,row,col,answer,clue, עם מרכאות בודדות)
```js
const cwEntries = [
  {num:1, dir:'across', row:0, col:0, answer:'בית', clue:'גרים בו'},
  {num:2, dir:'down',  row:0, col:1, answer:'ילד', clue:'זכר צעיר, לא מבוגר'},
  {num:3, dir:'across', row:2, col:3, answer:'דג', clue:'שוחה בים ובנהר'}
];
```
- `row`/`col` — קואורדינטת התא הראשון של הרשומה (אינדקס 0).
- `dir` — `'across'` (המילה ממלאת `col, col+1, col+2...` באותה `row`) או
  `'down'` (המילה ממלאת `row, row+1, row+2...` באותה `col`).
- כשמילה "מאוזן" ומילה "מאונך" חולקות תא, **האות בשתיהן באותו תא חייבת
  להיות זהה** — `verify_lesson.py` בודק את זה אוטומטית ומדווח על התנגשות
  אם לא (ראו סעיף 10 שם).

### דוגמה עצמאית ומלאה (HTML + CSS + JS) — בדוקה, עוברת את verify_lesson.py

```html
<div class="game-box">
  <div class="game-title">🧩 תַּשְׁבֵּץ</div>
  <div class="game-subtitle">מַלְּאוּ כָּל תָּא בְּאוֹת אַחַת לְפִי הַהֶגְדָּרוֹת</div>
  <div id="cw-grid" class="cw-grid" dir="rtl"></div>
  <div class="cw-clues">
    <div><h4>מְאֻזָּן →</h4><ol id="cw-across"></ol></div>
    <div><h4>מְאֻנָּך ↓</h4><ol id="cw-down"></ol></div>
  </div>
  <button class="submit-btn" onclick="cwCheck()">בְּדֹק ✓</button>
  <div class="result-banner" id="cw-result"></div>
</div>
```

```css
.cw-grid{display:grid;direction:rtl;gap:2px;justify-content:center;margin:14px auto;width:max-content}
.cw-cell{width:34px;height:34px;position:relative;background:var(--ink);border-radius:4px}
.cw-cell.active{background:#fff;border:2px solid var(--p1md)}
.cw-cell .num{position:absolute;top:1px;right:3px;font-size:.55rem;font-weight:800;color:var(--p1dk)}
.cw-cell input{width:100%;height:100%;border:none;background:transparent;text-align:center;
  font-family:'Frank Ruhl Libre',serif;font-size:1.05rem;font-weight:700;color:var(--ink);outline:none}
.cw-cell.correct{background:#dcfce7}
.cw-cell.wrong{background:#fee2e2}
.cw-clues{display:flex;gap:24px;flex-wrap:wrap;justify-content:center;margin-top:16px;font-size:.95rem}
.cw-clues ol{padding-right:18px;line-height:1.9}
```

```js
const cwEntries = [
  {num:1, dir:'across', row:0, col:0, answer:'בית', clue:'גרים בו'},
  {num:2, dir:'down',  row:0, col:1, answer:'ילד', clue:'זכר צעיר, לא מבוגר'},
  {num:3, dir:'across', row:2, col:3, answer:'דג', clue:'שוחה בים ובנהר'}
];

function onCrosswordSolved(){ /* וו לסצנה - לשנות בכל שיעור */ }

/* מנוע תשבץ גנרי — לא לשנות */
let cwCells={};
function cwBuild(){
  let maxR=0,maxC=0;
  cwEntries.forEach(e=>{
    for(let k=0;k<e.answer.length;k++){
      const r=e.dir==='down'? e.row+k : e.row;
      const c=e.dir==='across'? e.col+k : e.col;
      maxR=Math.max(maxR,r); maxC=Math.max(maxC,c);
      const key=r+'_'+c;
      if(!cwCells[key]) cwCells[key]={r,c,letter:e.answer[k],nums:new Set()};
      if(k===0) cwCells[key].nums.add(e.num);
    }
  });
  const gridEl=document.getElementById('cw-grid');
  gridEl.style.gridTemplateColumns='repeat('+(maxC+1)+',1fr)';
  gridEl.innerHTML='';
  for(let r=0;r<=maxR;r++) for(let c=0;c<=maxC;c++){
    const key=r+'_'+c, data=cwCells[key];
    const cell=document.createElement('div'); cell.className='cw-cell'+(data?' active':'');
    if(data){
      if(data.nums.size){ const n=document.createElement('span'); n.className='num'; n.textContent=[...data.nums][0]; cell.appendChild(n); }
      const inp=document.createElement('input'); inp.maxLength=1; inp.id='cw-'+key;
      inp.oninput=()=>{ inp.value=inp.value.slice(-1); };
      cell.appendChild(inp);
    }
    gridEl.appendChild(cell);
  }
  const acrossEl=document.getElementById('cw-across'), downEl=document.getElementById('cw-down');
  acrossEl.innerHTML=''; downEl.innerHTML='';
  cwEntries.slice().sort((a,b)=>a.num-b.num).forEach(e=>{
    const li=document.createElement('li'); li.textContent=e.num+'. '+e.clue;
    (e.dir==='across'?acrossEl:downEl).appendChild(li);
  });
}
function cwCheck(){
  let allOk=true;
  Object.values(cwCells).forEach(data=>{
    const inp=document.getElementById('cw-'+data.r+'_'+data.c);
    const ok = inp.value === data.letter;
    inp.parentElement.classList.toggle('correct', ok && inp.value!=='');
    inp.parentElement.classList.toggle('wrong', !ok && inp.value!=='');
    if(!ok) allOk=false;
  });
  if(allOk){
    const res=document.getElementById('cw-result');
    res.textContent='🏆 כָּל הַכָּבוֹד! פִּתַּרְתֶּם אֶת הַתַּשְׁבֵּץ!';
    res.style.display='block';
    onCrosswordSolved();
  }
}
cwBuild();
```

### כתיבת רמזים ידידותית לילד (כיתה ה׳)
- רמז אחד ברור לכל מילה, לא ניסוח כפול-משמעות — עדיף הגדרה פשוטה על
  פני חידה.
- לשאוב את אוצר המילים של השיעור עצמו (מ-`vocab-grid`) — כך התשבץ מחזק
  את מה שנלמד, לא מוסיף מילים חדשות בלי הקשר.
- אורך מילה סביר לכיתה ה׳: 2–6 אותיות. מילים ארוכות מאוד מקשות על
  הצלבות ברשת קטנה.
- לפחות הצלבה אחת אמיתית בין "מאוזן" ל"מאונך" נותנת תחושת תשבץ אמיתי
  (לא רשימת מילים מבודדות) — אבל זה לא חובה טכנית; תשבץ עם רשומות לא
  מצטלבות עדיין תקין ועדיין עובר את הבדיקות.

## איפה ממקמים את המשחקים בשיעור

תפזורת/תשבץ יכולים להחליף את מנוע ה-MC **בדיוק באחד** משני חלקי המשחק
של השיעור (חלק ג — משחק הבנת הנקרא, או חלק ה — משחק דקדוק) — משאירים
את שאר מבנה השיעור (`section-title`, `game-box`, כותרת+תת-כותרת) כרגיל.
מומלץ שלא שני חלקי המשחק באותו שיעור יהיו תפזורת/תשבץ יחד עם MC — לגיוון,
עדיף לשלב סוג אחד מהם עם מנוע ה-MC הרגיל בחלק השני.

## רשימת בדיקה לפני commit

1. כל מילה ב-`wsWords`/כל תשובה ב-`cwEntries` — בלי ניקוד, בלי אות סופית
   באמצע.
2. שורות `wsGrid` — כולן באותו אורך.
3. גודל הרשת הגיוני ביחס למספר/אורך המילים (בערך: מספר תאים ≥ סכום
   אורכי המילים, פלוס מרחב פנוי לאותיות "רעש").
4. הרצת `python3 _system/verify_lesson.py lessonNN_*.html` — חייב ✅.
   הבדיקות הרלוונטיות (סעיף 10 שם) רצות אוטומטית ברגע שהקובץ מכריז
   `wsGrid`/`wsWords` או `cwEntries` — אין צורך בדגל נוסף.
