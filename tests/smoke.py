#!/usr/bin/env python3
"""Rauchtest für Spotter: öffnet die App mit simulierter Supabase im iPhone-Format.
Aufruf: python3 tests/smoke.py [filter]"""
import pathlib, re, sys, shutil, subprocess, tempfile
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
TESTS = ROOT / 'tests'
SHOTS = TESTS / 'screenshots'
SHOTS.mkdir(exist_ok=True)
MOCK = (TESTS / 'mock-supabase.js').read_text(encoding='utf-8')
FAILS = []

def check(cond, msg):
    if not cond:
        FAILS.append(msg); print('  ✗', msg)
    else:
        print('  ✓', msg)

def syntax_check():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    js = re.findall(r'<script>(.*?)</script>', html, re.S)[-1]
    if not shutil.which('node'):
        # Ohne Node: Chromium kompiliert das Script, ohne es auszuführen.
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page()
            err = pg.evaluate('js => { try { new Function(js); return ""; } catch (e) { return String(e); } }', js)
            b.close()
        check(not err, 'JavaScript-Syntax' + (': ' + err[:300] if err else ''))
        return
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(js); path = f.name
    r = subprocess.run(['node', '--check', path], capture_output=True, text=True)
    check(r.returncode == 0, 'JavaScript-Syntax' + ('' if r.returncode == 0 else ': ' + r.stderr.strip()[:300]))

def route(r):
    u = r.request.url
    if 'supabase-js' in u:
        return r.fulfill(body=MOCK, content_type='application/javascript')
    if u.startswith('http://app/'):
        f = ROOT / (u[len('http://app/'):].split('?')[0] or 'index.html')
        if f.is_file():
            body = f.read_bytes()
            if f.name == 'index.html':
                body = re.sub(rb' integrity="[^"]+"', b'', body)
            if f.name == 'config.js':
                body = b'window.APP_CONFIG={SUPABASE_URL:"https://test.supabase.co",SUPABASE_ANON_KEY:"test"};'
            ct = {'.html': 'text/html', '.js': 'application/javascript', '.png': 'image/png', '.svg': 'image/svg+xml'}.get(f.suffix, 'application/json')
            return r.fulfill(body=body, content_type=ct)
        return r.fulfill(status=404, body='')
    return r.fulfill(status=200, body='', content_type='application/javascript')

def open_app(ctx, dismiss=True):
    pg = ctx.new_page()
    pg.errors = []
    pg.on('pageerror', lambda e: pg.errors.append(str(e)))
    pg.route('**/*', route)
    pg.goto('http://app/index.html'); pg.wait_for_timeout(1200)
    if dismiss and pg.query_selector("text=Los geht"):
        pg.click("text=Los geht"); pg.wait_for_timeout(300)
    return pg

def toast(pg): return pg.evaluate("document.querySelector('#toast').textContent")
def shot(pg, name, full=False): pg.screenshot(path=str(SHOTS / f'{name}.png'), full_page=full)
def close(pg): pg.evaluate('closeSheet()'); pg.wait_for_timeout(150)
def bottom_free(pg, name):
    # Ganz nach unten scrollen: Das letzte Element der Ansicht muss über der Tab-Leiste enden.
    pg.evaluate('window.scrollTo(0, 1e6)'); pg.wait_for_timeout(150)
    r = pg.evaluate("(()=>{const els=[...document.querySelector('#view').children].filter(e=>getComputedStyle(e).position!=='fixed');const v=els.at(-1).getBoundingClientRect();const t=[...document.querySelectorAll('.tabs-in,.fbar')].map(e=>e.getBoundingClientRect().top);return [v.bottom,Math.min(...t)]})()")
    check(r[0] <= r[1] + 1, f'{name}: Tab-Leiste verdeckt nichts')
    pg.evaluate('window.scrollTo(0, 0)')

# ---------- Abläufe ----------
def flow_start_changelog(ctx):
    pg = open_app(ctx, dismiss=False); shot(pg, 'start_changelog')
    check(pg.query_selector('text=Neu in Spotter') is not None, 'Changelog erscheint nach Update')
    pg.click('text=Los geht'); pg.wait_for_timeout(300)
    check(not pg.evaluate('sheetOpen()'), 'Changelog lässt sich schließen')
    return pg

def flow_heute(ctx):
    pg = open_app(ctx)
    check(pg.query_selector('#board .bnum') is not None, 'Heute zeigt Anzeigetafel')
    check(len(pg.query_selector_all('.wgrid .wcol')) == 7, 'Wochenleiste mit 7 Tagen')
    check(pg.query_selector('.wdot.pa') is not None, 'Wochenleiste zeigt Partnerreihe')
    bottom_free(pg, 'Heute')
    check('undefined' not in pg.inner_text('#dayl'), 'Datum ohne "undefined"')
    # Safari formatiert Datumsangaben ohne Kommas, Chrome mit. Safari-Verhalten nachbilden:
    pg.evaluate("(()=>{const o=Date.prototype.toLocaleDateString;Date.prototype.toLocaleDateString=function(...a){return o.apply(this,a).replace(/,/g,'')}})()")
    pg.click('#prev'); pg.wait_for_timeout(400)
    check('undefined' not in pg.inner_text('#dayl'), 'Datum "Gestern" ohne "undefined" (Safari-Format)')
    pg.evaluate("S.day=today();render()"); pg.wait_for_timeout(400)
    shot(pg, 'heute', True)
    pg.click('.wcol >> nth=0'); pg.wait_for_timeout(400)
    check(pg.evaluate('wd(S.day)') == 0, 'Tipp auf Wochentag springt dorthin')
    pg.evaluate("S.day=today();render()"); pg.wait_for_timeout(400)
    pg.click('.pline'); pg.wait_for_timeout(400); shot(pg, 'heute_partner')
    check(pg.query_selector('#sheetBody .kudos') is not None, 'Partnertag mit Kudos öffnet')
    close(pg)
    pg.click('text=Wochenrückblick'); pg.wait_for_timeout(500); shot(pg, 'heute_wochenrueckblick')
    check(pg.query_selector('text=Tage geloggt') is not None, 'Wochenrückblick zeigt Kennzahlen')
    return pg

def flow_heute_faelle(ctx):
    pg = open_app(ctx)
    pg.evaluate("S.day = addDays(today(), -20); render()"); pg.wait_for_timeout(500); shot(pg, 'heute_leer')
    check(pg.inner_text('#board .bnum').strip() == '2.100', 'Leerer Tag: ganzes Ziel übrig')
    pg.evaluate("S.day = today(); add('log', today(), {slot:'abend',name:'Pizza',kcal:1500,p:40,c:180,f:60}).then(render)"); pg.wait_for_timeout(600)
    shot(pg, 'heute_drueber')
    check('drüber' in pg.inner_text('#board .lbl >> nth=0').lower() and pg.inner_text('#board .bnum').startswith('+'), 'Überschreitung: +Wert und „kcal drüber“')
    check(pg.query_selector('#board .track.t10.over') is not None, 'Überschreitung: Balken rot')
    pg.evaluate("S.partner.data.share = {nutrition:false, training:false, weight:false, measure:false, level:false}; render()"); pg.wait_for_timeout(500)
    shot(pg, 'heute_ohne_freigaben')
    check(pg.query_selector('.wdot.pa') is None and 'privat' in pg.inner_text('.pline'), 'Ohne Freigaben: nur eigene Reihe')
    pg.evaluate("S.partner = null; render()"); pg.wait_for_timeout(500); shot(pg, 'heute_ohne_partner')
    check(pg.query_selector('.wdot.pa') is None and 'Verbinde' in pg.inner_text('.pline'), 'Ohne Partner: nur eigene Reihe')
    return pg

def flow_kalender(ctx):
    pg = open_app(ctx)
    pg.click('#dayl'); pg.wait_for_timeout(600); shot(pg, 'kalender')
    mon = pg.evaluate("MONTHS[new Date().getMonth()]")
    check(pg.inner_text('.cmonth') == mon, 'Kalender öffnet mit dem aktuellen Monat')
    check(pg.query_selector('.cday.tdy') is not None and pg.query_selector('.cday.ok, .cday.lg') is not None, 'Kalender: heute markiert, geloggte Tage')
    check(pg.query_selector('.cday.tr') is not None, 'Kalender: Trainingsstrich')
    check(pg.is_disabled('[aria-label="Nächster Monat"]'), 'Kalender: Zukunft deaktiviert')
    pg.click('[aria-label="Vorheriger Monat"]'); pg.wait_for_timeout(500)
    check(pg.inner_text('.cmonth').startswith(pg.evaluate("MONTHS[(new Date().getMonth()+11)%12]")), 'Kalender: Monatswechsel zurück')
    pg.click('[aria-label="Nächster Monat"]'); pg.wait_for_timeout(500)
    pg.click('.cday:not(.fut) >> nth=0'); pg.wait_for_timeout(400)
    check(pg.evaluate("S.day.endsWith('-01')") and not pg.evaluate('sheetOpen()'), 'Tipp auf einen Tag springt dorthin')
    pg.click('#dayl'); pg.wait_for_timeout(500); pg.click('text=Zu heute'); pg.wait_for_timeout(300)
    check(pg.evaluate('S.day === today()'), '„Zu heute“')
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))"); pg.wait_for_timeout(200)
    pg.click('#dayl'); pg.wait_for_timeout(500)
    check(pg.query_selector('.cday.ok, .cday.lg') is not None, 'Offline: aktueller Monat aus dem Cache')
    pg.click('[aria-label="Vorheriger Monat"]'); pg.wait_for_timeout(400)
    check('offline nicht verfügbar' not in pg.inner_text('#sheetBody'), 'Offline: Vormonat vorab geladen')
    pg.click('[aria-label="Vorheriger Monat"]'); pg.wait_for_timeout(400)
    check('Dieser Monat ist offline nicht verfügbar.' in pg.inner_text('#sheetBody'), 'Offline: nicht geladener Monat mit Hinweis')
    ctx.set_offline(False); close(pg)
    pg.click('#tabs >> text=Essen'); pg.wait_for_timeout(400); pg.click('#dayl'); pg.wait_for_timeout(500)
    check(pg.query_selector('.cgrid') is not None, 'Kalender auch unter Essen')
    return pg

def flow_essen_korb(ctx):
    pg = open_app(ctx)
    pg.click('#tabs >> text=Essen'); pg.wait_for_timeout(500)
    shot(pg, 'essen'); bottom_free(pg, 'Essen')
    check(pg.query_selector('.fbar .fscan') is not None, 'Suche und Scan unten')
    check(pg.query_selector('.mshare >> text=Übernehmen') is not None, 'Vorschlag sitzt in der Mahlzeit')
    check('0 kcal' != pg.inner_text('.sec .list .row .k >> nth=0').strip(), 'Vorlage zeigt Kalorien')
    pg.click('.mplus >> nth=0'); pg.wait_for_timeout(600)
    pg.click('.qplus >> nth=0'); pg.click('.qplus >> nth=1'); pg.wait_for_timeout(200)
    check(pg.query_selector('.bbar') is not None, 'Korbleiste erscheint')
    pg.click('.bbar .binfo'); pg.wait_for_timeout(300); shot(pg, 'essen_korb')
    pg.click('text=Alle speichern'); pg.wait_for_timeout(500)
    check('gespeichert' in toast(pg), 'Korb wird gespeichert')
    pg.click('text=Essen von anderem Tag'); pg.wait_for_timeout(600)
    pg.select_option('.slotsel >> nth=0', 'abend'); pg.wait_for_timeout(150); shot(pg, 'essen_kopieren')
    pg.click('text=Auf heute kopieren'); pg.wait_for_timeout(500)
    check('kopiert' in toast(pg), 'Kopieren mit Ziel-Mahlzeit')
    check(pg.query_selector('.meal.open') is not None, 'Bearbeitete Mahlzeit ist aufgeklappt')
    pg.click('.mexp .row.tap >> nth=0'); pg.wait_for_timeout(300); shot(pg, 'essen_eintrag')
    check(pg.query_selector('text=Kopieren oder verschieben') is not None, 'Eintrag-Aktionen öffnen')
    close(pg); return pg

def flow_suche(ctx):
    pg = open_app(ctx)
    pg.click('#tabs >> text=Essen'); pg.wait_for_timeout(500)
    check(pg.evaluate("document.querySelector('.fsearch').tagName") == 'BUTTON', 'Suchleiste in Essen ist ein Button')
    pg.click('.fsearch'); pg.wait_for_timeout(50)
    check(pg.evaluate("document.activeElement && document.activeElement.id") == 'pq', 'Suchfeld sofort fokussiert (iOS-Tastatur)')
    pg.evaluate("document.querySelector('.sheet-card').scrollTop = 1e6"); pg.wait_for_timeout(100)
    r = pg.evaluate("(()=>{const a=document.querySelector('#pq').getBoundingClientRect(),c=document.querySelector('.sheet-card').getBoundingClientRect();return a.top>=c.top-1&&a.bottom<=c.bottom})()")
    check(r, 'Suchfeld bleibt beim Scrollen oben sichtbar')
    pg.evaluate("document.body.classList.add('kbopen')"); check(pg.evaluate("!document.querySelector('.bbar') || getComputedStyle(document.querySelector('.bbar')).display==='none'"), 'Korbleiste bei Tastatur aus')
    pg.evaluate("document.body.classList.remove('kbopen')"); close(pg)
    pg.click('.mplus >> nth=0'); pg.wait_for_timeout(700); shot(pg, 'suche')
    check(pg.inner_text('#pres .lbl >> nth=0') .lower() == 'oft in frühstück' and pg.inner_text('.fname .t >> nth=0') == 'Skyr', 'Suche: Oft in dieser Mahlzeit zuerst')
    check('300 g' in pg.inner_text('.fname .s >> nth=0'), 'Suche: zuletzt verwendete Menge')
    pg.click('.qplus >> nth=0'); pg.wait_for_timeout(200)
    check(pg.query_selector('.qplus.in') is not None and pg.inner_text('.bcount') == '1', 'Schnell-Plus legt in den Korb')
    pg.click('.fname >> nth=1'); pg.wait_for_timeout(300); shot(pg, 'menge_korb')
    check(pg.inner_text('#npgo') == 'In den Korb', 'Mengen-Sheet bei vollem Korb: „In den Korb“')
    [pg.click(f'#numpad >> text="{d}"') for d in '150']; pg.click('#npgo'); pg.wait_for_timeout(300)
    check(pg.inner_text('.bcount') == '2', 'Mengenauswahl legt in den Korb'); shot(pg, 'suche_korb')
    pg.click('.bbar >> text=Eintragen'); pg.wait_for_timeout(500)
    check('gespeichert' in toast(pg), 'Eintragen speichert den Korb')
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))"); pg.wait_for_timeout(200)
    pg.evaluate("openPicker({mode:'log',slot:'mittag',title:'Mittagessen'})"); pg.wait_for_timeout(700); shot(pg, 'suche_offline')
    check(pg.inner_text('.fname .t >> nth=0') == 'Hähnchen Reis', 'Offline: Sortierung aus dem Cache')
    pg.fill('#pq', 'sky'); pg.dispatch_event('#pq', 'input'); pg.wait_for_timeout(200)
    check(pg.inner_text('.fname .t >> nth=0') == 'Skyr', 'Offline: Suche in eigenen und zuletzt verwendeten')
    ctx.set_offline(False); return pg

def flow_menge(ctx):
    pg = open_app(ctx)
    pg.click('#tabs >> text=Essen'); pg.wait_for_timeout(500)
    pg.click('.mplus >> nth=3'); pg.wait_for_timeout(600)
    pg.click('.fname >> nth=0'); pg.wait_for_timeout(300); shot(pg, 'menge')
    check(pg.inner_text('#npgo') == 'Eintragen' and pg.query_selector('.slotchips button.on') is not None, 'Mengen-Sheet bei leerem Korb: „Eintragen“, Mahlzeit vorausgewählt')
    check(pg.inner_text('.slotchips button.on') == 'Snacks', 'Mahlzeit aus der man kam')
    pg.click('[aria-label="10 mehr"]'); pg.wait_for_timeout(100)
    kcal = pg.inner_text('#aprev .num >> nth=0')
    pg.click('#npgo'); pg.wait_for_timeout(600)
    check('eingetragen' in toast(pg), 'Eintragen speichert sofort'); close(pg); pg.wait_for_timeout(400)
    check(pg.query_selector('.meal.open') is not None and 'Snacks' in pg.inner_text('.meal.open .mname'), 'Eintrag landet in der gewählten Mahlzeit')
    pg.click('.mexp .row.tap >> nth=0'); pg.wait_for_timeout(300)
    pg.click('#eng'); [pg.click(f'#numpad >> text="{d}"') for d in '200']
    check(pg.inner_text('#npgo') == 'Speichern', 'Eintrag bearbeiten: „Speichern“')
    pg.click('#npgo'); pg.wait_for_timeout(500)
    check('geändert' in toast(pg), 'Eintrag bearbeiten ändert direkt')
    return pg

def flow_rueckgaengig(ctx):
    pg = open_app(ctx)
    dialogs = []; pg.on('dialog', lambda d: (dialogs.append(d.message), d.dismiss()))
    pg.click('#tabs >> text=Essen'); pg.wait_for_timeout(500)
    pg.click('.mhead >> nth=0'); pg.wait_for_timeout(300)
    left0 = pg.inner_text('.eboard .num')
    pg.click('.mexp [aria-label="Eintrag löschen"] >> nth=0'); pg.wait_for_timeout(400); shot(pg, 'rueckgaengig')
    check('Skyr gelöscht' in pg.inner_text('#undo') and pg.inner_text('.eboard .num') != left0, 'Löschen ohne Dialog, sofort ausgeblendet, Leiste „Skyr gelöscht“')
    r = pg.evaluate("(()=>{const u=document.querySelector('#undo').getBoundingClientRect(),f=document.querySelector('.fbar').getBoundingClientRect();return u.bottom<=f.top})()")
    check(r, 'Rückgängig-Leiste über der unteren Leiste')
    pg.click('#undo >> text=Rückgängig'); pg.wait_for_timeout(400)
    check(pg.inner_text('.eboard .num') == left0, 'Rückgängig stellt den Eintrag wieder her')
    pg.evaluate("S.openSlot='fruehstueck'; render()"); pg.wait_for_timeout(300)
    pg.click('.mexp [aria-label="Eintrag löschen"] >> nth=0'); pg.wait_for_timeout(5600)
    pg.evaluate("render()"); pg.wait_for_timeout(500)
    check(pg.inner_text('.eboard .num') != left0 and not pg.inner_text('#undo'), 'Nach 5 s endgültig gelöscht')
    # offline: Rückgängig sendet nichts, Verlassen der Ansicht führt das Löschen aus (Warteschlange)
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))"); pg.wait_for_timeout(200)
    pg.evaluate("S.openSlot='mittag'; render()"); pg.wait_for_timeout(300)
    pg.click('.mexp [aria-label="Eintrag löschen"] >> nth=0'); pg.wait_for_timeout(300)
    pg.click('#undo >> text=Rückgängig'); pg.wait_for_timeout(300)
    check(pg.evaluate('QUEUE.length') == 0, 'Offline: Rückgängig sendet nichts')
    pg.evaluate("S.openSlot='mittag'; render()"); pg.wait_for_timeout(300)
    pg.click('.mexp [aria-label="Eintrag löschen"] >> nth=0'); pg.wait_for_timeout(300)
    pg.click('#tabs >> text=Heute'); pg.wait_for_timeout(500)
    check(pg.evaluate("QUEUE.filter(o=>o.op==='delete').length") == 1, 'Offline: Verlassen der Ansicht führt das Löschen aus')
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(1200)
    # Einheit, Satz, Übung, Gewicht
    pg.evaluate("startWorkout('r1')"); pg.wait_for_timeout(600)
    pg.click('.ex >> nth=0 >> [aria-label="Weitere Aktionen"]'); pg.click('text=Letzten Satz entfernen'); pg.wait_for_timeout(200)
    check(pg.evaluate('W.exercises[0].sets.length') == 3 and 'Satz gelöscht' in pg.inner_text('#undo'), 'Satz löschen mit Rückgängig')
    r = pg.evaluate("(()=>{const u=document.querySelector('#undo').getBoundingClientRect(),w=document.querySelector('.wbar').getBoundingClientRect();return u.bottom<=w.top})()")
    check(r, 'Im Training sitzt die Leiste über der Pausenleiste')
    pg.click('#undo >> text=Rückgängig'); check(pg.evaluate('W.exercises[0].sets.length') == 4, 'Satz wiederhergestellt')
    pg.click('.ex >> nth=1 >> [aria-label="Weitere Aktionen"]'); pg.click('text=Übung entfernen'); pg.wait_for_timeout(200)
    pg.click('#undo >> text=Rückgängig'); check(pg.evaluate('W.exercises.length') == 2, 'Übung wiederhergestellt')
    pg.evaluate("clearDraft(); closeSheet()")
    pg.click('#tabs >> text=Training'); pg.wait_for_timeout(500)
    n = len(pg.query_selector_all('.trow2'))
    pg.click('.trow2 >> nth=0'); pg.click('#sheetBody >> text=Bearbeiten'); pg.wait_for_timeout(500)
    pg.click('text=Einheit löschen'); pg.wait_for_timeout(400)
    check(len(pg.query_selector_all('.trow2')) == n - 1, 'Einheit gelöscht ohne Dialog')
    pg.click('#undo >> text=Rückgängig'); pg.wait_for_timeout(400)
    check(len(pg.query_selector_all('.trow2')) == n, 'Einheit wiederhergestellt')
    pg.click('#tabs >> text=Körper'); pg.wait_for_timeout(500)
    pg.click('text=Gewicht eintragen'); pg.wait_for_timeout(400); pg.click('#numpad [aria-label="Zahlenfeld schließen"]')
    pg.click('text=Eintrag löschen'); pg.wait_for_timeout(400)
    check('Gewicht gelöscht' in pg.inner_text('#undo') and 'heute' not in pg.inner_text('.board .bhead'), 'Gewicht löschen mit Rückgängig')
    pg.click('#undo >> text=Rückgängig'); pg.wait_for_timeout(400)
    check('heute' in pg.inner_text('.board .bhead'), 'Gewicht wiederhergestellt')
    check(not dialogs, 'Keine Nachfrage-Dialoge beim Löschen')
    return pg

def flow_essen_teilen(ctx):
    pg = open_app(ctx)
    check(pg.query_selector('.sharein') is not None, 'Geschickte Mahlzeit erscheint')
    pg.click('.sharein >> text=Übernehmen'); pg.wait_for_timeout(400); pg.click('text=×0,75'); shot(pg, 'essen_teilen')
    pg.click('text=In mein Tagebuch übernehmen'); pg.wait_for_timeout(500)
    check('übernommen' in toast(pg), 'Mahlzeit übernommen')
    check(pg.query_selector('.sharein') is None, 'Vorschlag verschwindet danach')
    pg.click('#tabs >> text=Essen'); pg.wait_for_timeout(500)
    if not pg.query_selector('.sendbtn'): pg.click('.mhead >> nth=0'); pg.wait_for_timeout(300)
    pg.click('.sendbtn >> nth=0'); pg.wait_for_timeout(400)
    check('geschickt' in toast(pg), 'Mahlzeit an Partner schicken')
    return pg

def flow_training(ctx):
    pg = open_app(ctx)
    pg.click('#tabs >> text=Training'); pg.wait_for_timeout(500); shot(pg, 'training', True)
    check(pg.inner_text('.board .lbl') .lower() == 'als nächstes', 'Training: Tafel „Als Nächstes“')
    bottom_free(pg, 'Training')
    pg.click('.board >> text=Starten'); pg.wait_for_timeout(500)
    check(pg.inner_text('.ex >> nth=1 >> .setrow >> nth=0 >> .nf >> nth=0') == '55' and pg.inner_text('.ex >> nth=1 >> .setrow >> nth=0 >> .nf >> nth=1') == '10', 'Sätze mit Werten vom letzten Mal vorausgefüllt')
    check(pg.query_selector('.setrow.cur .chk.cur') is not None, 'Aktueller Satz hervorgehoben')
    pg.click('.chk >> nth=0'); pg.wait_for_timeout(400)
    check(pg.query_selector('.chk.on') is not None, 'Satz abgehakt')
    check(pg.evaluate('TM.end > 0'), 'Auto-Timer startet nach Abhaken')
    pg.click('.restbar >> text=+30 s'); check(pg.evaluate('TM.dur') == 120, 'Pause +30 s')
    pg.click('.rtime'); pg.click('.restbar >> text=−15'); check(pg.evaluate('TM.dur') == 105, 'Tipp auf Restzeit: −15 s')
    shot(pg, 'training_einheit')
    check(pg.query_selector('#wseg i') is not None and 'von' in pg.inner_text('#wmeta'), 'Einheit: Fortschritt im Kopf')
    save = pg.query_selector('.wsave')
    pg.evaluate("document.querySelector('.sheet-card').scrollTop = 1e6"); pg.wait_for_timeout(200)
    shot(pg, 'training_einheit_ende')
    box = save.bounding_box(); bar = pg.query_selector('#restbar').bounding_box()
    overlap = box and bar and not (box['y'] + box['height'] <= bar['y'] or bar['y'] + bar['height'] <= box['y']
                                   or box['x'] + box['width'] <= bar['x'] or bar['x'] + bar['width'] <= box['x'])
    check(box and box['x'] + box['width'] <= 390, 'Speichern-Knopf vollständig sichtbar')
    check(not overlap, 'Speichern-Knopf nicht vom Timer verdeckt')
    pg.click('.sheet-bg', position={'x': 10, 'y': 10}); pg.wait_for_timeout(300)
    pg.click('#tabs >> text=Körper'); pg.click('#tabs >> text=Training'); pg.wait_for_timeout(500)
    check(pg.query_selector('text=Nicht gespeicherte Einheit') is not None, 'Entwurf wird angeboten')
    pg.click('text=Fortsetzen'); pg.wait_for_timeout(500)
    pg.click('.autot'); pg.wait_for_timeout(200)
    pg.evaluate('stopRest()')
    pg.click('.chk >> nth=1'); pg.wait_for_timeout(300)
    check(not pg.evaluate('TM.end > 0'), 'Auto-Timer abschaltbar')
    pg.click('.chk >> nth=1'); pg.wait_for_timeout(200)
    check(not pg.evaluate('W.exercises[0].sets[1].done'), 'Erneutes Tippen setzt Satz zurück')
    pg.click('.chk >> nth=1'); pg.click('.chk >> nth=2'); pg.click('.chk >> nth=3'); pg.wait_for_timeout(300)
    check(pg.query_selector('.exdone') is not None and '4 Sätze' in pg.inner_text('.exdone'), 'Erledigte Übung klappt zusammen')
    check(pg.query_selector('#wseg i.done') is not None and pg.query_selector('#wseg i.cur') is not None, 'Segmente: erledigt und aktuell')
    shot(pg, 'training_abgehakt')
    pg.click('.wsave'); pg.wait_for_timeout(500)
    check('gespeichert' in toast(pg), 'Einheit speichern')
    check('ohne Haken nicht gespeichert' in pg.inner_text('#undo'), 'Hinweis: Sätze ohne Haken nicht gespeichert')
    n = pg.evaluate("Object.values(S.wos).at(-1).data.exercises.length")
    pg.click('#undo >> text=Rückgängig'); pg.wait_for_timeout(600)
    check(pg.evaluate("Object.values(S.wos).at(-1).data.exercises.length") > n, 'Rückgängig nimmt Sätze ohne Haken mit auf')
    pg.click('.lhead >> text=Fortschritt'); pg.wait_for_timeout(500); pg.click('#sheetBody .row.tap >> nth=0'); pg.wait_for_timeout(300)
    shot(pg, 'training_fortschritt'); close(pg)
    pg.click('.trow2 >> nth=0'); pg.wait_for_timeout(300)
    check(pg.query_selector('#sheetBody >> text=Bearbeiten') is not None, 'Einheit öffnet Details'); close(pg)
    pg.click('[aria-label="Neuer Trainingstag"]'); pg.wait_for_timeout(300); pg.click('text=+ Übung hinzufügen'); pg.wait_for_timeout(300)
    pg.click('#liblist .plus >> nth=0'); pg.wait_for_timeout(200); shot(pg, 'training_bibliothek')
    check(pg.query_selector('.presets') is not None, 'Übungsbibliothek mit Vorgaben')
    close(pg); return pg

def flow_start_von_heute(ctx):
    pg = open_app(ctx)
    pg.evaluate("S.day = addDays(today(), -3); render()"); pg.wait_for_timeout(500)
    pg.click('.tile >> text=Starten'); pg.wait_for_timeout(600)
    check(len(pg.query_selector_all('.ex')) == 2, 'Start von Heute: Übungen des Trainingstags geladen')
    pg.evaluate("clearDraft(); closeSheet()"); return pg

def flow_aufwaermen(ctx):
    pg = open_app(ctx)
    pg.evaluate("startWorkout('r1')"); pg.wait_for_timeout(600)
    pg.click('.exbtns >> text=Aufwärmsatz >> nth=0'); pg.wait_for_timeout(300)
    check(pg.query_selector('.warmlbl') is not None and pg.inner_text('.setrow.warm .n') == 'W', 'Aufwärmen: eigener Bereich mit „W“')
    pg.click('.setrow.warm .nf >> nth=0'); [pg.click(f'#numpad >> text="{d}"') for d in '200']; pg.click('#npgo')
    [pg.click(f'#numpad >> text="{d}"') for d in '10']; pg.click('#npgo'); pg.wait_for_timeout(200); shot(pg, 'training_aufwaermen')
    check(pg.evaluate("getComputedStyle(document.querySelector('.setrow.warm .chk.on')).backgroundColor") != 'rgb(255, 184, 28)', 'Aufwärmen: Haken nicht gelb')
    for k in range(4): pg.click(f'.setrow:not(.warm) .chk >> nth={k}')
    pg.wait_for_timeout(300)
    check(pg.inner_text('#wmeta').endswith('2.076 kg'), 'Aufwärmen nicht im Volumen der Einheit')
    pg.evaluate("stopRest()"); pg.click('.wsave'); pg.wait_for_timeout(600)
    w = pg.evaluate("(()=>{const w=Object.values(S.wos||{}).at(-1)||null;return w})()")
    pg.click('#tabs >> text=Training'); pg.wait_for_timeout(600)
    r = pg.evaluate("""(()=>{const all=Object.values(S.wos).sort((a,b)=>a.day<b.day?-1:1);const w=all.at(-1);
      const g=computeGame(S.me,[],all,[],[]), g2=computeGame(S.me,[],all.map(x=>({...x,data:{...x.data,exercises:x.data.exercises.map(e=>({...e,sets:e.sets.filter(s=>!s.warm)}))}})),[],[]);
      return {warm:w.data.exercises[0].sets.filter(s=>s.warm).length, vol:woVolume(w), pr:prCounts(all)[w.id], xp:g.xp===g2.xp&&g.prs===g2.prs}})()""")
    check(r['warm'] == 1, 'Aufwärmsatz gespeichert als warm: true')
    check(r['vol'] == 2076, 'Aufwärmen nicht im Volumen')  # 4 × 86,5 kg × 6
    check(r['pr'] == 0, 'Aufwärmen kein Bestwert')
    check(r['xp'], 'Aufwärmen ändert XP nicht')
    pg.click('.lhead >> text=Fortschritt'); pg.wait_for_timeout(600)
    check('200' not in pg.inner_text('#sheetBody'), 'Aufwärmen nicht im Übungsfortschritt')
    close(pg); return pg

def flow_steigerung(ctx):
    pg = open_app(ctx)
    pg.evaluate("startWorkout('r1')"); pg.wait_for_timeout(600); shot(pg, 'training_steigerung')
    # Bankdrücken 6–8, zuletzt 84 kg × 8 (oberes Ziel) -> 86,5 kg × 6; Rudern 10–12, zuletzt 55 × 10 -> keine Steigerung
    check('Heute 86,5 kg.' in pg.inner_text('.ex >> nth=0') and 'Letztes Mal 8 Wdh. mit 84 kg' in pg.inner_text('.ex >> nth=0'), 'Steigerung: Hinweis mit +2,5 kg')
    check(pg.inner_text('.ex >> nth=0 >> .setrow >> nth=0 >> .nf >> nth=0') == '86,5' and pg.inner_text('.ex >> nth=0 >> .setrow >> nth=3 >> .nf >> nth=1') == '6', 'Steigerung: alle Arbeitssätze +2,5 kg, Wdh. aufs untere Ziel')
    check(pg.query_selector('.ex >> nth=1 >> .prog') is None and pg.inner_text('.ex >> nth=1 >> .setrow >> nth=0 >> .nf >> nth=0') == '55', 'Ohne erreichtes Ziel: letzte Werte, kein Hinweis')
    pg.evaluate("clearDraft(); closeSheet(); S.rt['r1'].data.exercises[0].reps=''"); pg.evaluate("startWorkout('r1')"); pg.wait_for_timeout(600)
    check(pg.query_selector('.prog') is None and pg.inner_text('.setrow >> nth=0 >> .nf >> nth=0') == '84', 'Ohne Wiederholungsziel keine Steigerung')
    pg.evaluate("clearDraft(); closeSheet()"); return pg

def flow_als_naechstes(ctx):
    pg = open_app(ctx)
    pg.evaluate("startWorkout('r1')"); pg.wait_for_timeout(600)
    check(pg.inner_text('#wnext b') == 'Bankdrücken · Satz 1 · 86,5 kg × 6', 'Als Nächstes: erster Satz mit Übungsname')
    pg.click('.chk >> nth=0'); pg.wait_for_timeout(200)
    check(pg.inner_text('#wnext b') == 'Satz 2 · 86,5 kg × 6', 'Als Nächstes: nächster Satz')
    for k in range(3): pg.click('.setrow:not(.done) .chk >> nth=0')
    pg.wait_for_timeout(300)
    check(pg.inner_text('#wnext b') == 'Rudern am Kabel · Satz 1 · 55 kg × 10', 'Als Nächstes: nach letzter Übung die nächste mit Namen')
    shot(pg, 'training_als_naechstes')
    pg.evaluate("stopRest(); clearDraft(); closeSheet()"); return pg

def flow_zahlenfeld(ctx):
    pg = open_app(ctx)
    pg.evaluate("startWorkout('r1')"); pg.wait_for_timeout(600)
    check(pg.query_selector('.setrow input') is None, 'Keine System-Tastatur-Felder in der Einheit')
    pg.click('.setrow.cur .nf >> nth=0'); pg.wait_for_timeout(200); shot(pg, 'zahlenfeld')
    check(pg.is_visible('#numpad') and pg.inner_text('#numpad .nphead .lbl').upper() == 'GEWICHT · SATZ 1', 'Zahlenfeld: Kopf „Gewicht · Satz 1“')
    check('Vorher 84 × 8' in pg.inner_text('#numpad .nphead'), 'Zahlenfeld: Vorher-Wert')
    check(pg.query_selector('.nf.npact') is not None and not pg.is_visible('.wbar'), 'Aktives Feld markiert, untere Leiste ersetzt')
    pg.click('#numpad >> text="9"'); pg.click('#numpad >> text="0"')
    check(pg.inner_text('.nf.npact') == '90', 'Erster Tipp ersetzt den Wert')
    pg.click('[aria-label="2,5 mehr"]'); check(pg.inner_text('.nf.npact') == '92,5', '± ändert den Wert (2,5 kg)')
    pg.click('#npgo'); pg.wait_for_timeout(100)
    check(pg.inner_text('#npgo') == 'Abhaken' and pg.inner_text('#numpad .nphead .lbl').upper().startswith('WIEDERHOLUNGEN'), 'Weiter springt zu Wdh., Button heißt „Abhaken“')
    pg.click('[aria-label="1 mehr"]'); check(pg.inner_text('.nf.npact') == '7', 'Wdh. ± 1')
    pg.click('#npgo'); pg.wait_for_timeout(300)
    check(pg.evaluate('W.exercises[0].sets[0].done') and pg.evaluate('TM.end > 0') and not pg.is_visible('#numpad'), 'Abhaken hakt ab, startet Timer, schließt Zahlenfeld')
    check(pg.evaluate('W.exercises[0].sets[0].kg') == '92,5' and pg.evaluate('num(W.exercises[0].sets[0].kg)') == 92.5, 'Wert mit Komma gespeichert')
    pg.evaluate("stopRest(); clearDraft(); closeSheet()"); return pg

def flow_ziel(ctx):
    pg = open_app(ctx)
    pg.click('#tabs >> text=Training'); pg.wait_for_timeout(500)
    pg.evaluate("openRoutine('r1')"); pg.wait_for_timeout(300)
    check(pg.input_value('[aria-label="Wiederholungen von"] >> nth=0') == '6' and pg.input_value('[aria-label="Wiederholungen bis"] >> nth=0') == '8', 'Editor: Wiederholungsbereich 6–8')
    pg.fill('[aria-label="Wiederholungen von"] >> nth=1', ''); pg.fill('[aria-label="Wiederholungen bis"] >> nth=1', '')
    pg.click('text=Trainingstag speichern'); pg.wait_for_timeout(500)
    check(pg.evaluate("S.rt['r1'].data.exercises[1].reps") == '', 'Editor: ohne Ziel speicherbar')
    pg.evaluate("startWorkout('r1')"); pg.wait_for_timeout(500)
    check('Ziel 4 × 6–8' in pg.inner_text('.exsub >> nth=0') and 'Ziel' not in pg.inner_text('.exsub >> nth=1'), 'Einheit: „Ziel 4 × 6–8“, ohne Ziel keine Angabe')
    pg.evaluate("clearDraft(); closeSheet()")
    return pg

def flow_dran(ctx):
    pg = open_app(ctx)
    # Zwei Trainingstage: B wurde nie trainiert, also ist B dran; nach B ist A wieder dran (am längsten her)
    pg.evaluate("add('routine', null, {name:'Unterkörper B', exercises:[{name:'Kniebeuge',sets:3,reps:'6-8'}]})"); pg.wait_for_timeout(300)
    pg.click('#tabs >> text=Training'); pg.wait_for_timeout(500)
    check(pg.inner_text('.board .tbig') == 'Unterkörper B', 'Dran: nie trainierter Tag zuerst')
    pg.evaluate("add('workout', today(), {name:'Unterkörper B', exercises:[{name:'Kniebeuge',sets:[{kg:80,reps:8}]}]}).then(render)"); pg.wait_for_timeout(600)
    check(pg.inner_text('.board .tbig') == 'Oberkörper A', 'Dran: danach der am längsten nicht trainierte')
    pg.click('#tabs >> text=Heute'); pg.wait_for_timeout(500)
    check('Unterkörper B' in pg.inner_text('.tile.done'), 'Heute: erledigtes Training mit Volumen')
    return pg

def flow_partneransicht(ctx):
    pg = open_app(ctx)
    for tab in ['Essen', 'Training', 'Körper']:
        pg.click(f'#tabs >> text={tab}'); pg.wait_for_timeout(300)
        pg.click('.who button >> nth=1'); pg.wait_for_timeout(500)
        shot(pg, f'partner_{tab.lower()}', True)
        check(pg.query_selector('.err') is None, f'Partneransicht {tab} ohne Fehler')
        pg.click('.who button >> nth=0'); pg.wait_for_timeout(200)
    return pg

def flow_offline_sync(ctx):
    pg = open_app(ctx)
    pg.click('#tabs >> text=Körper'); pg.wait_for_timeout(400)
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))"); pg.wait_for_timeout(200)
    pg.click('text=Gewicht eintragen'); pg.wait_for_timeout(400)
    [pg.click(f'#numpad >> text="{d}"') for d in '84,9']; pg.click('#npgo'); pg.wait_for_timeout(500)
    check(pg.evaluate('QUEUE.length') == 1, 'Offline: Eintrag landet in Warteschlange')
    shot(pg, 'offline')
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(1200)
    check(pg.evaluate('QUEUE.length') == 0, 'Online: Warteschlange wird hochgeladen')
    return pg

def flow_koerper(ctx):
    pg = open_app(ctx)
    pg.click('#tabs >> text=Körper'); pg.wait_for_timeout(500); shot(pg, 'koerper', True)
    check(pg.query_selector('.board .bchart') is not None, 'Körper: Trendtafel mit Diagramm')
    check('pro Woche' in pg.inner_text('.board'), 'Körper: Tempo pro Woche')
    pg.click('.bseg >> text=3 M'); pg.wait_for_timeout(400)
    check(pg.query_selector('.bseg button.on').inner_text() == '3 M', 'Körper: Zeitraum wechseln')
    pg.click('text=Gewicht eintragen'); pg.wait_for_timeout(400)
    check(pg.inner_text('#wkg .num') == '86' and pg.inner_text('#npgo') == 'Eintragen', 'Gewicht: letzter Wert vorausgefüllt, „Eintragen“')
    pg.click('[aria-label="0,1 weniger"]'); check(pg.inner_text('#wkg .num') == '85,9', 'Gewicht: ±0,1')
    pg.click('#npgo'); pg.wait_for_timeout(500); check('gespeichert' in toast(pg), 'Gewicht eintragen')
    pg.click('[aria-label="Maße eintragen"]'); pg.wait_for_timeout(400); shot(pg, 'masse')
    pg.click('#mm_taille'); [pg.click(f'#numpad >> text="{d}"') for d in '84']
    check(pg.inner_text('#npgo') == 'Weiter', 'Maße: Weiter zum nächsten Maß')
    pg.click('#npgo'); check(pg.query_selector('#mm_huefte.npact') is not None, 'Maße: Weiter springt zum nächsten Maß')
    pg.click('[aria-label="0,5 mehr"]')
    for k in range(3): pg.click('#npgo')
    check(pg.inner_text('#npgo') == 'Eintragen', 'Maße: auf dem letzten „Eintragen“')
    pg.click('#npgo'); pg.wait_for_timeout(500)
    check(pg.query_selector('.mrow2') is not None, 'Körper: Maße als Liste')
    bottom_free(pg, 'Körper')
    return pg

def flow_profil(ctx):
    pg = open_app(ctx)
    pg.click('#tabs >> text=Profil'); pg.wait_for_timeout(600); shot(pg, 'profil', True)
    check(pg.query_selector('.board .plvl') is not None, 'Profil: Tafel mit Level')
    pg.click('text=Bedarf neu berechnen'); pg.wait_for_timeout(500); shot(pg, 'profil_rechner')
    check(pg.query_selector('#calcres .tgt') is not None, 'Kalorienrechner berechnet Ziele')
    pg.click('#sheetBody >> text=Ziele speichern'); pg.wait_for_timeout(400)
    check('gespeichert' in toast(pg), 'Ziele speichern')
    for row, probe in [('Kalorien & Makros', '#adapt'), ('Freigaben', '#sheetBody .switch'), ('Verbindung', 'text=Verbindung lösen'), ('Pausentimer', '#sheetBody select'),
                       ('Darstellung', '#sheetBody .seg'), ('Daten & Export', 'text=Meine Daten exportieren'), ('Sicherheit', 'text=Auf allen Geräten abmelden')]:
        pg.click(f'#view >> text={row}'); pg.wait_for_timeout(300)
        check(pg.query_selector(probe) is not None, f'Profil: {row} erreichbar')
        close(pg)
    check(len(pg.query_selector_all('.prow2')) == 8, 'Profil: alle Einstellungen gruppiert')
    pg.click('.plvl'); pg.wait_for_timeout(500)
    check(pg.query_selector('#sheetBody .badges') is not None, 'Profil: Level-Zeile öffnet Abzeichen')
    close(pg); bottom_free(pg, 'Profil')
    return pg

def flow_bewegung(ctx):
    pg = open_app(ctx)
    anim = lambda: pg.evaluate("getComputedStyle(document.querySelector('#board .track>i')).animationName")
    check(anim() == 'fill', 'Bewegung: Balken füllen beim Öffnen')
    pg.evaluate("render()"); pg.wait_for_timeout(500)
    check(anim() == 'none', 'Bewegung: keine erneute Animation nach Aktion')
    pg.emulate_media(reduced_motion='reduce'); pg.click('#tabs >> text=Essen'); pg.click('#tabs >> text=Heute'); pg.wait_for_timeout(500)
    check(anim() == 'none', 'Bewegung: aus bei „Bewegung reduzieren“')
    return pg

# Findet Wörter, die über mehrere Zeilen getrennt sind, und Text, der sichtbar über den Bildschirmrand ragt.
# Bindestriche dürfen trennen, abgeschnittener Text mit Ellipse zählt nicht als Überlauf.
WRAP_JS = r'''(() => { const bad = new Set(), W = innerWidth;
  const clipRight = el => { let r = W; for (let a = el; a && a !== document.body; a = a.parentElement){ const s = getComputedStyle(a); if (s.overflowX !== 'visible') r = Math.min(r, a.getBoundingClientRect().right); } return r; };
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
  while ((n = tw.nextNode())){ const el = n.parentElement; if (!el || !el.getClientRects().length) continue;
    const cr = clipRight(el), re = /[^\s\-–·\/]+/g; let m;
    while ((m = re.exec(n.data))){ const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length);
      const rs = [...r.getClientRects()].filter(x => x.width > 0); if (!rs.length) continue;
      if (new Set(rs.map(x => Math.round(x.top))).size > 1) bad.add('Wort getrennt: „' + m[0] + '“');
      if (rs.some(x => Math.min(x.right, cr) > W + 1)) bad.add('Über den Rand: „' + m[0] + '“');
      const box = el.closest('.board,.card,.list,.tile,.note,.hintbar,.ex,.fbar,.wbar,.bbar,.seg,.btn');
      if (box && rs.some(x => Math.min(x.right, cr) > box.getBoundingClientRect().right + 1)) bad.add('Über den Kartenrand: „' + m[0] + '“'); } }
  return [...bad]; })()'''

def flow_umbruch(ctx):
    pg = open_app(ctx)
    # Lange Namen wie im Auftrag
    pg.evaluate("""(async () => {
      await upd('r1', {name:'Ganzkörper A', exercises:[{name:'Rumänisches Kreuzheben',sets:3,reps:'8-10'},{name:'Bankdrücken',sets:4,reps:'6-8'}]});
      await add('log', today(), {slot:'mittag', name:'Hähnchen-Reis-Bowl mit Gemüse', grams:450, per:{kcal:140,p:10,c:15,f:4}, kcal:630, p:45, c:68, f:18});
      await add('workout', addDays(today(), -1), {name:'Rumänisches Kreuzheben', exercises:[{name:'Rumänisches Kreuzheben', sets:[{kg:90,reps:8}]}]});
      await add('weight', today(), {kg: 85.4});
    })()"""); pg.wait_for_timeout(500)
    screens = [
      ('heute', "S.tab='heute';S.day=today();render()"), ('heute_ohne_training', "S.tab='heute';S.day=addDays(today(),-3);render()"), ('heute_partner', "S.tab='heute';render().then(()=>openPartnerDay())"), ('heute_plan', "openPlan()"),
      ('woche', "S.day=today();openWeek()"), ('essen', "S.tab='essen';S.openSlot='mittag';render()"), ('suche', "openPicker({mode:'log',slot:'mittag',title:'Mittagessen'})"),
      ('koerper', "S.tab='koerper';render()"), ('training', "S.tab='training';render()"), ('anderes', "S.tab='training';render().then(()=>openOther())"),
      ('einheit', "startWorkout('r1')"), ('einheit_detail', "S.tab='training';render().then(()=>openWo(Object.keys(S.wos).at(-1)))"),
      ('editor', "openRoutine('r1')"), ('profil', "S.tab='profil';render()"), ('level', "openGame()"), ('rechner', "openCalc()")]
    pg.evaluate("S.day=addDays(today(),-3);S.tab='heute';render()"); pg.wait_for_timeout(500)
    check('Ganzkörper A' in pg.inner_text('.tile .tname'), 'Kachel zeigt langen Trainingsnamen')
    for w, h in [(390, 844), (375, 667)]:
        pg.set_viewport_size({'width': w, 'height': h})
        for scheme in ['light', 'dark']:
            pg.emulate_media(color_scheme=scheme)
            for name, js in screens:
                pg.evaluate('closeSheet(); stopRest(); clearDraft()'); pg.evaluate(js); pg.wait_for_timeout(450)
                for sc in [0, 1e6]:
                    pg.evaluate(f"window.scrollTo(0,{sc}); const c=document.querySelector('.sheet-card'); if(c) c.scrollTop={sc}"); pg.wait_for_timeout(80)
                    bad = pg.evaluate(WRAP_JS)
                    check(not bad, f'Umbruch {name} {w}×{h} {scheme}' + ('' if not bad else ': ' + '; '.join(bad[:4])))
                    if scheme == 'light' and sc == 0: shot(pg, f'umbruch_{name}_{w}')
                    if bad: break
    pg.evaluate('closeSheet(); stopRest(); clearDraft()')
    return pg

def flow_hell_dunkel(ctx):
    pg = open_app(ctx)
    for t in ['light', 'dark']:
        pg.evaluate(f"applyTheme('{t}')"); pg.click('#tabs >> text=Heute'); pg.wait_for_timeout(400)
        shot(pg, f'theme_{t}')
    return pg

FLOWS = [flow_start_changelog, flow_heute, flow_heute_faelle, flow_kalender, flow_essen_korb, flow_suche, flow_menge, flow_rueckgaengig, flow_essen_teilen, flow_training, flow_start_von_heute, flow_aufwaermen, flow_steigerung, flow_als_naechstes, flow_zahlenfeld, flow_ziel, flow_dran,
         flow_partneransicht, flow_offline_sync, flow_koerper, flow_profil, flow_bewegung, flow_umbruch, flow_hell_dunkel]

def main():
    filt = sys.argv[1] if len(sys.argv) > 1 else ''
    syntax_check()
    with sync_playwright() as p:
        b = p.chromium.launch()
        for fl in FLOWS:
            if filt and filt not in fl.__name__: continue
            print(fl.__name__)
            ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
            try:
                pg = fl(ctx)
                for e in getattr(pg, 'errors', []): check(False, 'Seitenfehler: ' + e)
            except Exception as e:
                check(False, f'{fl.__name__} abgebrochen: {str(e).splitlines()[0]}')
            ctx.close()
        b.close()
    print('\nALLE TESTS OK' if not FAILS else f'\n{len(FAILS)} FEHLER:\n- ' + '\n- '.join(FAILS))
    sys.exit(1 if FAILS else 0)

if __name__ == '__main__':
    main()
