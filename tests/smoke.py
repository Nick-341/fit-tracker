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
    pg.click('#dayl'); pg.wait_for_timeout(400)
    shot(pg, 'heute', True)
    pg.click('.wcol >> nth=0'); pg.wait_for_timeout(400)
    check(pg.evaluate('wd(S.day)') == 0, 'Tipp auf Wochentag springt dorthin')
    pg.click('#dayl'); pg.wait_for_timeout(400)
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
    pg.click('.mplus >> nth=0'); pg.wait_for_timeout(700); shot(pg, 'suche')
    check(pg.inner_text('#pres .lbl >> nth=0') .lower() == 'oft in frühstück' and pg.inner_text('.fname .t >> nth=0') == 'Skyr', 'Suche: Oft in dieser Mahlzeit zuerst')
    check('300 g' in pg.inner_text('.fname .s >> nth=0'), 'Suche: zuletzt verwendete Menge')
    pg.click('.qplus >> nth=0'); pg.wait_for_timeout(200)
    check(pg.query_selector('.qplus.in') is not None and pg.inner_text('.bcount') == '1', 'Schnell-Plus legt in den Korb')
    pg.click('.fname >> nth=1'); pg.wait_for_timeout(300); pg.fill('#ag', '150'); pg.dispatch_event('#ag', 'input'); pg.click('text=In den Korb'); pg.wait_for_timeout(300)
    check(pg.inner_text('.bcount') == '2', 'Mengenauswahl legt in den Korb'); shot(pg, 'suche_korb')
    pg.click('.bbar >> text=Eintragen'); pg.wait_for_timeout(500)
    check('gespeichert' in toast(pg), 'Eintragen speichert den Korb')
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))"); pg.wait_for_timeout(200)
    pg.evaluate("openPicker({mode:'log',slot:'mittag',title:'Mittagessen'})"); pg.wait_for_timeout(700); shot(pg, 'suche_offline')
    check(pg.inner_text('.fname .t >> nth=0') == 'Hähnchen Reis', 'Offline: Sortierung aus dem Cache')
    pg.fill('#pq', 'sky'); pg.dispatch_event('#pq', 'input'); pg.wait_for_timeout(200)
    check(pg.inner_text('.fname .t >> nth=0') == 'Skyr', 'Offline: Suche in eigenen und zuletzt verwendeten')
    ctx.set_offline(False); return pg

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
    pg.click('#tabs >> text=Training'); pg.wait_for_timeout(500)
    pg.click('text=Starten'); pg.wait_for_timeout(500)
    pg.fill('.setrow >> nth=0 >> input >> nth=1', '8'); pg.dispatch_event('.setrow >> nth=0 >> input >> nth=1', 'change'); pg.wait_for_timeout(600)
    check(pg.evaluate('TM.end > 0'), 'Auto-Timer startet nach Satz')
    shot(pg, 'training_einheit')
    save = pg.query_selector('text=Einheit speichern')
    pg.evaluate("document.querySelector('.sheet-card').scrollTop = 1e6"); pg.wait_for_timeout(200)
    shot(pg, 'training_einheit_ende')
    box = save.bounding_box(); bar = pg.query_selector('#restbar').bounding_box()
    overlap = box and bar and not (box['y'] + box['height'] <= bar['y'] or bar['y'] + bar['height'] <= box['y'])
    check(not overlap, 'Speichern-Knopf nicht vom Timer verdeckt')
    pg.click('.sheet-bg', position={'x': 10, 'y': 10}); pg.wait_for_timeout(300)
    pg.click('#tabs >> text=Körper'); pg.click('#tabs >> text=Training'); pg.wait_for_timeout(500)
    check(pg.query_selector('text=Nicht gespeicherte Einheit') is not None, 'Entwurf wird angeboten')
    pg.click('text=Fortsetzen'); pg.wait_for_timeout(500)
    pg.click('.autot'); pg.wait_for_timeout(200)
    pg.evaluate('stopRest()')
    pg.fill('.setrow >> nth=1 >> input >> nth=1', '7'); pg.dispatch_event('.setrow >> nth=1 >> input >> nth=1', 'change'); pg.wait_for_timeout(300)
    check(not pg.evaluate('TM.end > 0'), 'Auto-Timer abschaltbar')
    pg.click('text=Einheit speichern'); pg.wait_for_timeout(500)
    check('gespeichert' in toast(pg), 'Einheit speichern')
    pg.click('text=Übungsfortschritt'); pg.wait_for_timeout(500); pg.click('#sheetBody .row.tap >> nth=0'); pg.wait_for_timeout(300)
    shot(pg, 'training_fortschritt'); close(pg)
    pg.click('text=Neuer Trainingstag'); pg.wait_for_timeout(300); pg.click('text=+ Übung hinzufügen'); pg.wait_for_timeout(300)
    pg.click('#liblist .plus >> nth=0'); pg.wait_for_timeout(200); shot(pg, 'training_bibliothek')
    check(pg.query_selector('.presets') is not None, 'Übungsbibliothek mit Vorgaben')
    close(pg); return pg

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
    pg.fill('#wkg', '84,9'); pg.click('#view >> text=Speichern >> nth=0'); pg.wait_for_timeout(500)
    check(pg.evaluate('QUEUE.length') == 1, 'Offline: Eintrag landet in Warteschlange')
    shot(pg, 'offline')
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(1200)
    check(pg.evaluate('QUEUE.length') == 0, 'Online: Warteschlange wird hochgeladen')
    return pg

def flow_profil(ctx):
    pg = open_app(ctx)
    pg.click('#tabs >> text=Profil'); pg.wait_for_timeout(600); shot(pg, 'profil', True)
    check(pg.query_selector('#calcres .tgt') is not None, 'Kalorienrechner berechnet Ziele')
    check(pg.query_selector('text=Freigaben') is not None, 'Freigaben vorhanden')
    return pg

def flow_hell_dunkel(ctx):
    pg = open_app(ctx)
    for t in ['light', 'dark']:
        pg.evaluate(f"applyTheme('{t}')"); pg.click('#tabs >> text=Heute'); pg.wait_for_timeout(400)
        shot(pg, f'theme_{t}')
    return pg

FLOWS = [flow_start_changelog, flow_heute, flow_heute_faelle, flow_essen_korb, flow_suche, flow_essen_teilen, flow_training,
         flow_partneransicht, flow_offline_sync, flow_profil, flow_hell_dunkel]

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
