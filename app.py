# ==================== MODÜL 1A/6: KÜTÜPHANELER, PRO API ANAHTARLARI VE ARAYÜZ STİLİ ====================
import os
import re
import time
import json
import math
import hashlib
import urllib.parse
import requests
from requests.adapters import HTTPAdapter
import streamlit as st
import streamlit.components.v1 as components
from collections import Counter
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(
    page_title="Delta Pulse AI M5.1 — Full Spectrum & Cross-Book Radar",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"], .stAppHeader, .stAppToolbar, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="manage-app-button"],
.viewerBadge_container__r5tak, .styles_viewerBadge__CvC9N, #MainMenu, footer {
    display: none !important; visibility: hidden !important; height: 0px !important;
    width: 0px !important; opacity: 0 !important; pointer-events: none !important;
}
.block-container { padding-top: 0.6rem !important; padding-bottom: 1.5rem !important; max-width: 1180px !important; }
.dp-card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 11px 14px; margin-bottom: 9px; color: #e6edf3; font-size: 13px; line-height: 1.5; }
.dp-ak { border-left: 4px solid #58a6ff !important; border-color: rgba(148, 163, 184, 0.48) !important; background: linear-gradient(90deg, rgba(56, 139, 253, 0.18) 0%, rgba(148, 163, 184, 0.08) 45%, rgba(22, 27, 34, 0.96) 100%) !important; }
.dp-tier-green { border-left: 4px solid #2ea043 !important; border-color: rgba(46, 160, 67, 0.38) !important; background: linear-gradient(90deg, rgba(46, 160, 67, 0.16) 0%, rgba(22, 27, 34, 0.96) 65%) !important; }
.dp-tier-orange { border-left: 4px solid #d29922 !important; border-color: rgba(210, 153, 34, 0.36) !important; background: linear-gradient(90deg, rgba(210, 153, 34, 0.15) 0%, rgba(22, 27, 34, 0.96) 65%) !important; }
.dp-tier-red { border-left: 4px solid #f85149 !important; border-color: rgba(248, 81, 73, 0.34) !important; background: linear-gradient(90deg, rgba(248, 81, 73, 0.14) 0%, rgba(22, 27, 34, 0.96) 65%) !important; }
.dp-warn { border-left: 4px solid #f85149 !important; }
.dp-live { border-left: 4px solid #2f81f7 !important; }
.dp-live-hot { border-left: 4px solid #3fb950 !important; background: linear-gradient(90deg, #0d2818 0%, #161b22 100%); }
.dp-badge { background: #21262d; color: #79c0ff; padding: 2px 7px; border-radius: 5px; font-size: 11px; font-weight: 700; margin-left: 4px; }
.dp-w { background: #122d1f; color: #56d364; padding: 2px 7px; border-radius: 5px; font-size: 11px; font-weight: 700; margin-left: 4px; border: 1px solid #2ea043; }
.dp-heat { background: #2d1619; color: #ff7b72; padding: 2px 7px; border-radius: 5px; font-size: 11px; font-weight: 700; margin-right: 4px; border: 1px solid #f85149; }
.dp-exp-alert { background: #0d1117; border-left: 3px solid #58a6ff; padding: 6px 9px; margin-top: 5px; border-radius: 5px; font-size: 11.5px; color: #c9d1d9; }

.dp-pitch-wrap { position:relative; width:100%; height:275px; background:repeating-linear-gradient(90deg,#145224 0px,#145224 38px,#19632c 38px,#19632c 76px); border:2px solid rgba(255,255,255,0.85); border-radius:8px; display:flex; justify-content:space-between; align-items:center; overflow:hidden; padding:6px 4px; box-sizing:border-box; }
.dp-node-circle { position:relative; width:29px; height:29px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:10.5px; font-weight:800; color:#fff; box-shadow:0 2px 5px rgba(0,0,0,0.6); }
.dp-node-name { background:rgba(13,17,23,0.88); color:#e6edf3; font-size:9.2px; font-weight:600; padding:1px 4px; border-radius:3px; margin-top:2px; white-space:nowrap; max-width:64px; overflow:hidden; text-overflow:ellipsis; }

@media (max-width: 768px) {
    .block-container { padding-left: 0.45rem !important; padding-right: 0.45rem !important; padding-top: 0.35rem !important; }
    .dp-card { padding: 9px 10px !important; font-size: 12px !important; }
    .dp-pitch-wrap { height: 235px !important; padding: 4px 2px !important; }
    .dp-node-circle { width: 22px !important; height: 22px !important; font-size: 8.5px !important; }
    .dp-node-name { font-size: 7.5px !important; max-width: 42px !important; padding: 0px 2px !important; }
}
</style>
""", unsafe_allow_html=True)

TR_TZ = timezone(timedelta(hours=3))
ADMIN_HASHES = {
    "5901b9952716f713fb0e0c7f1972fb2125c79e0c7c93d18d42ef1c8815b49b0e",
    "4c94485e0c21ae6c41ce1dfe7b6b28f56c779263487d408860f483029357900d"
}
APP_PUBLIC_URL = "https://delta-pulse-mam7gxcyu3xmtej7hxhxxp.streamlit.app/"
STORE_FILE = "dp_persistent_store_m50.json"

API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "688fd171bc6282329898fd2112213c77").strip()
THE_ODDS_API_KEY = os.environ.get("THE_ODDS_API_KEY", "b9283e71252462a19132010bc2b4a8f4").strip().lower()
ODDS_API_KEY = os.environ.get("ODDS_API_KEY") or THE_ODDS_API_KEY
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xqauqjxrwpjghgqsmkxh.supabase.co").strip().rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_IX7eN7btLuNtyfn5uQkQwQ_vorTG5nA").strip()
SUPABASE_DOC_ID = "dp_vault_m50_pro"

@st.cache_resource
def get_http_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    adapter = HTTPAdapter(pool_connections=40, pool_maxsize=40, max_retries=1)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

HTTP_SESSION = get_http_session()

def safe_int(val, default=0):
    try:
        return int(float(str(val).strip()))
    except Exception:
        return default

def safe_float(val, default=0.0):
    try:
        return float(str(val).strip())
    except Exception:
        return default

def parse_live_clock(clk_str):
    s = str(clk_str or "").strip().upper()
    if not s:
        return 1, 0
    if any(k in s for k in ("HT", "HALF", "DEVRE")):
        return 45, 0
    if any(k in s for k in ("FT", "FULL", "BİTTİ", "FINAL")):
        return 90, 0
    main_part = s.split("+")[0].strip()
    added_part = s.split("+")[1].strip() if "+" in s else ""
    if ":" in main_part:
        main_part = main_part.split(":")[0].strip()
    if ":" in added_part:
        added_part = added_part.split(":")[0].strip()
    base_digits = "".join(c for c in main_part if c.isdigit())
    add_digits = "".join(c for c in added_part if c.isdigit())
    base_min = safe_int(base_digits, 1)
    add_min = safe_int(add_digits, 0)
    if base_min > 125:
        base_min = safe_int(str(base_min)[:2], 45)
    return max(1, min(120, base_min)), max(0, min(15, add_min))

def get_stat(comp_side, keys):
    for st_item in ((comp_side or {}).get("statistics") or []):
        if st_item.get("name") in keys:
            return safe_int(st_item.get("displayValue"), 0)
    return 0

# ==================== MODÜL 1B/6: SUPABASE PRO BULUT HAFIZA VE CİHAZ YÖNETİMİ ====================
@st.cache_resource
def get_global_memory():
    return {
        "opening_odds": {}, "locked_pre": {}, "locked_picks": {}, "pre_lineup_memory": {},
        "live_snapshots": {}, "live_signals": {}, "settled_results": {}, "finished_cache": {},
        "history_scores": {}, "ledger_log": {}, "roster_cache": {}, "team_hist_cache": {},
        "af_cache": {}, "af_daily_cache": {}, "odds_api_cache": {}, "twin_memory_stats": {},
        "event_summary_cache": {}, "bulletin_snap": {"ts": 0.0, "live": [], "up": [], "fin": [], "mini": []},
        "_calib_cache": {"count": -1, "factor": 1.0},
        "_sb_last_pull": 0.0, "_sb_init_done": False, "sb_status": "⏳ Bekleniyor",
        "odd_mode": "IDDAA_130",
        "users_db": {}, "used_txids": set(),
        "base_w": 0, "base_t": 0, "base_ak_w": 0, "base_ak_t": 0,
        "trc20_wallet": "TDeltaPulseOfficialTRC20WalletAddress",
        "app_public_url": APP_PUBLIC_URL, "support_tg_url": "https://t.me/DeltaPulseSupport",
        "tg_config": {"token": "", "chat_id": ""}, "last_tg_post": 0
    }

MEM = get_global_memory()

def _to_json_safe(obj):
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        return 0.0 if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, (set, tuple, list)):
        return [_to_json_safe(x) for x in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            ks = f"{k[0]}-{k[1]}" if isinstance(k, tuple) and len(k) == 2 else str(k)
            if ks == "mat":
                continue
            out[ks] = _to_json_safe(v)
        return out
    return str(obj)

def _merge_store_dict_into_mem(d):
    if not isinstance(d, dict):
        return
    if d.get("odd_mode") in ("IDDAA_130", "IDDAA_142", "GLOBAL"):
        MEM["odd_mode"] = d["odd_mode"]
    if isinstance(d.get("users_db"), dict):
        for uk, uv in d["users_db"].items():
            if uk not in MEM["users_db"]:
                MEM["users_db"][uk] = uv
            elif isinstance(uv, dict) and uv.get("tier") in ("VIP", "ADMIN"):
                MEM["users_db"][uk] = uv
    if isinstance(d.get("used_txids"), list):
        MEM["used_txids"].update(d["used_txids"])
    if isinstance(d.get("patron_devs"), list):
        MEM.setdefault("patron_devs", set()).update(d["patron_devs"])
    if isinstance(d.get("tg_config"), dict):
        for tk, tv in d["tg_config"].items():
            if tv and not MEM.setdefault("tg_config", {}).get(tk):
                MEM["tg_config"][tk] = tv
    for dict_k in (
        "locked_picks", "opening_odds", "pre_lineup_memory", "finished_cache",
        "history_scores", "live_signals", "team_hist_cache", "af_daily_cache",
        "odds_api_cache", "twin_memory_stats"
    ):
        src_map = d.get(dict_k)
        if isinstance(src_map, dict):
            dst_map = MEM.setdefault(dict_k, {})
            for mk, mv in src_map.items():
                if mk not in dst_map:
                    dst_map[mk] = mv
    for k in ("base_w", "base_t", "base_ak_w", "base_ak_t"):
        if k in d and safe_int(d[k], 0) > safe_int(MEM.get(k), 0):
            MEM[k] = safe_int(d[k], 0)

def load_persistent_store(force_cloud=False):
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                _merge_store_dict_into_mem(json.load(f))
        except Exception:
            pass

    now_ts = time.time()
    if SUPABASE_URL and SUPABASE_KEY and (force_cloud or not MEM.get("_sb_init_done") or (now_ts - safe_float(MEM.get("_sb_last_pull"), 0.0) >= 60.0)):
        MEM["_sb_last_pull"] = now_ts
        try:
            sb_url = f"{SUPABASE_URL}/rest/v1/dp_store?id=eq.{SUPABASE_DOC_ID}&select=payload"
            r = HTTP_SESSION.get(sb_url, headers={"apikey": SUPABASE_KEY, "Accept": "application/json"}, timeout=3.5)
            if r.status_code == 200:
                rows = r.json() or []
                if rows and isinstance(rows[0], dict) and isinstance(rows[0].get("payload"), dict):
                    _merge_store_dict_into_mem(rows[0]["payload"])
                MEM["_sb_init_done"] = True
                MEM["sb_status"] = f"🟢SupabasePro({len(MEM.get('finished_cache', {}))}FT)"
            else:
                MEM["sb_status"] = f"⚠️Supabase({r.status_code})"
        except Exception:
            MEM["sb_status"] = "⚠️Supabase(TabloYok/Ağ)"

def save_persistent_store():
    try:
        th_cache = MEM.get("team_hist_cache", {})
        if len(th_cache) > 250:
            th_keys = list(th_cache.keys())[-250:]
            th_cache = {k: th_cache[k] for k in th_keys}
            MEM["team_hist_cache"] = th_cache

        raw_payload = {
            "odd_mode": MEM.get("odd_mode", "IDDAA_130"),
            "users_db": MEM.get("users_db", {}),
            "used_txids": list(MEM.get("used_txids", set())),
            "patron_devs": list(MEM.get("patron_devs", set())),
            "tg_config": MEM.get("tg_config", {"token": "", "chat_id": ""}),
            "locked_picks": MEM.get("locked_picks", {}),
            "opening_odds": MEM.get("opening_odds", {}),
            "pre_lineup_memory": MEM.get("pre_lineup_memory", {}),
            "finished_cache": MEM.get("finished_cache", {}),
            "history_scores": MEM.get("history_scores", {}),
            "live_signals": MEM.get("live_signals", {}),
            "team_hist_cache": th_cache,
            "af_daily_cache": MEM.get("af_daily_cache", {}),
            "odds_api_cache": MEM.get("odds_api_cache", {}),
            "twin_memory_stats": MEM.get("twin_memory_stats", {}),
            "base_w": safe_int(MEM.get("base_w"), 0),
            "base_t": safe_int(MEM.get("base_t"), 0),
            "base_ak_w": safe_int(MEM.get("base_ak_w"), 0),
            "base_ak_t": safe_int(MEM.get("base_ak_t"), 0)
        }
        clean_payload = _to_json_safe(raw_payload)
        json_text = json.dumps(clean_payload, ensure_ascii=False)

        with open(STORE_FILE, "w", encoding="utf-8") as f:
            f.write(json_text)

        if SUPABASE_URL and SUPABASE_KEY:
            sb_post_url = f"{SUPABASE_URL}/rest/v1/dp_store?on_conflict=id"
            sb_headers = {
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=minimal"
            }
            sb_body = {
                "id": SUPABASE_DOC_ID,
                "payload": clean_payload,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            r_up = HTTP_SESSION.post(sb_post_url, headers=sb_headers, json=sb_body, timeout=4.2)
            if r_up.status_code in (200, 201, 204):
                MEM["sb_status"] = f"🟢SupabasePro({len(MEM.get('finished_cache', {}))}FT)"
            else:
                MEM["sb_status"] = f"⚠️Supabase({r_up.status_code})"
    except Exception:
        pass

load_persistent_store(force_cloud=True)

def get_all_possible_device_uids():
    cands = []
    try:
        qp = dict(st.query_params)
        if qp.get("uid"):
            u_q = str(qp["uid"]).strip().upper()
            if u_q.startswith("DP-") and len(u_q) == 9:
                cands.append(u_q)
    except Exception:
        pass
    ua, ip_hint = "", ""
    try:
        hdrs = st.context.headers
        if hdrs:
            ua = str(hdrs.get("User-Agent") or hdrs.get("user-agent") or "")
            ip_hint = str(hdrs.get("X-Forwarded-For") or hdrs.get("x-forwarded-for") or "").split(",")[0].strip()
    except Exception:
        pass
    h_old = hashlib.md5(f"{ua}|{ip_hint}|DeltaPulseSalt".encode("utf-8")).hexdigest().upper()[:6]
    cands.append(f"DP-{h_old}")
    h_new = hashlib.md5(f"{ua}|DeltaPulseSalt".encode("utf-8")).hexdigest().upper()[:6]
    cands.append(f"DP-{h_new}")
    h_emp = hashlib.md5(f"{ua}||DeltaPulseSalt".encode("utf-8")).hexdigest().upper()[:6]
    cands.append(f"DP-{h_emp}")
    seen = set()
    unique_cands = []
    for c in cands:
        if c not in seen:
            seen.add(c)
            unique_cands.append(c)
    return unique_cands

def get_smart_device_uid():
    cands = get_all_possible_device_uids()
    p_devs = MEM.get("patron_devs", set())
    u_db = MEM.get("users_db", {})
    for c in cands:
        if c in p_devs or (isinstance(u_db.get(c), dict) and u_db[c].get("tier") == "ADMIN"):
            return c
    return cands[0]

def auto_sync_device_user(uid_code, ref_code=""):
    load_persistent_store()
    if not uid_code:
        return {"tier": "NORMAL"}
    db = MEM["users_db"]
    now_tr = datetime.now(TR_TZ)
    if uid_code not in db:
        seq_n = len(db) + 1
        grp = "🥇 İlk 100 Kurucu" if seq_n <= 100 else "👤 Standart Üye"
        dec_amt = round(100.0 + ((seq_n % 89) + 10) / 100.0, 2)
        db[uid_code] = {
            "seq": seq_n, "code": uid_code, "group": grp, "tier": "NORMAL",
            "refs": [], "paid": False, "amount": 0.0, "pay_dec": dec_amt,
            "exp": (now_tr - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            "note": "Auto Device Sync", "last_seen": now_tr.strftime("%d.%m %H:%M")
        }
        save_persistent_store()
    return db[uid_code]
# ==================== MODÜL 2A/6: KITALARARASI ÇAPRAZ BÜRO MOTORU (EU + UK + US + AU & AF PRO) ====================
class _DeterministicRng:
    def __init__(self, seed_str):
        self.state = int(hashlib.md5(str(seed_str).encode("utf-8")).hexdigest()[:8], 16) or 123456789

    def randint(self, a, b):
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return a + (self.state % max(1, (b - a + 1)))

def _norm_team_key(name):
    s = str(name or "").lower()
    tr_map = str.maketrans("çğıöşüáéíóúñ", "cgiosuaeioun")
    s = s.translate(tr_map)
    s = s.replace("istanbul bb", "basaksehir").replace("ibfk", "basaksehir")
    for w in ("fc", "fk", "sk", "cf", "sc", "ac", "as", "cd", "ud", "rcd", "real", "club", "deportivo", "sporting", "atletico", "united", "city", "town", "rovers", "wanderers", "calcio", "istanbul", "arca", "1907", "1910", "1899", "04", "05"):
        s = re.sub(r"\b" + w + r"\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s).strip()

_ODDS_API_SPORTS = [
    "soccer_turkey_super_league", "soccer_turkey_1_lig",
    "soccer_epl", "soccer_efl_champ", "soccer_spl",
    "soccer_spain_la_liga", "soccer_spain_segunda_division",
    "soccer_italy_serie_a", "soccer_italy_serie_b",
    "soccer_germany_bundesliga", "soccer_germany_bundesliga2",
    "soccer_france_ligue_one", "soccer_france_ligue_two",
    "soccer_netherlands_eredivisie", "soccer_portugal_primeira_liga",
    "soccer_brazil_campeonato", "soccer_argentina_primera_division", "soccer_mexico_ligamx",
    "soccer_uefa_champs_league", "soccer_uefa_europa_league", "soccer_uefa_europa_conference_league"
]

def _fetch_single_odds_sport(sp_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sp_key}/odds/?regions=eu,uk,us,au&markets=h2h,totals&oddsFormat=decimal&apiKey={ODDS_API_KEY}"
    try:
        r = HTTP_SESSION.get(url, timeout=3.5)
        if r.status_code == 200:
            return r.headers.get("x-requests-remaining"), (r.json() or [])
    except Exception:
        pass
    return None, []

def _fetch_odds_api_global_map():
    now_ts = time.time()
    oa_cache = MEM.setdefault("odds_api_cache", {"ts": 0.0, "data": {}, "remaining_quota": "Aktif"})
    sample_v = next(iter((oa_cache.get("data") or {}).values()), {})
    if now_ts - safe_float(oa_cache.get("ts"), 0.0) < 1200.0 and oa_cache.get("data") and "eu_h" in sample_v:
        return oa_cache["data"]
    if not ODDS_API_KEY:
        return oa_cache.get("data") or {}

    new_map = dict(oa_cache.get("data") or {})
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(_fetch_single_odds_sport, _ODDS_API_SPORTS))

    eu_keys = {"pinnacle", "marathonbet", "betclic", "unibet_eu", "1xbet", "winamax_fr", "coolbet"}
    uk_keys = {"williamhill", "betfair_ex_uk", "skybet", "paddypower", "ladbrokes_uk", "virginbet", "betvictor"}
    us_keys = {"draftkings", "fanduel", "betmgm", "caesars", "bovada", "betrivers", "espnbet"}
    au_keys = {"sportsbet", "tab", "pointsbetau", "neds", "ladbrokes_au", "unibet"}

    for rem_q, items in results:
        if rem_q:
            oa_cache["remaining_quota"] = str(rem_q)
        for item in items:
            h_tm = _norm_team_key(item.get("home_team"))
            a_tm = _norm_team_key(item.get("away_team"))
            if not h_tm or not a_tm:
                continue
            bms = item.get("bookmakers") or []
            if not bms:
                continue

            pin_bm = next((b for b in bms if "pinnacle" in str(b.get("key", "")).lower()), bms[0])
            h_odd, d_odd, a_odd = 0.0, 0.0, 0.0
            reg_probs_h = {"eu": [], "uk": [], "us": [], "au": [], "all": []}
            o25_list, u25_list, o15_list, u35_list = [], [], [], []
            bm_snapshots = {}

            for b in bms:
                bkey = str(b.get("key") or "").lower()
                bh, bd, ba, bo25, bu25 = 0.0, 0.0, 0.0, 0.0, 0.0
                for mkt in (b.get("markets") or []):
                    mkey = mkt.get("key")
                    if mkey == "h2h":
                        for outc in (mkt.get("outcomes") or []):
                            onm = _norm_team_key(outc.get("name"))
                            prc = safe_float(outc.get("price"), 0.0)
                            if "draw" in str(outc.get("name", "")).lower():
                                bd = prc
                            elif onm == h_tm or h_tm in onm or onm in h_tm:
                                bh = prc
                            else:
                                ba = prc
                    elif mkey == "totals":
                        for outc in (mkt.get("outcomes") or []):
                            pt = safe_float(outc.get("point"), 0.0)
                            prc = safe_float(outc.get("price"), 0.0)
                            nm_l = str(outc.get("name") or "").lower()
                            if prc <= 1.02:
                                continue
                            if abs(pt - 2.5) < 0.05:
                                if "over" in nm_l: bo25 = prc; o25_list.append(prc)
                                elif "under" in nm_l: bu25 = prc; u25_list.append(prc)
                            elif abs(pt - 1.5) < 0.05 and "over" in nm_l:
                                o15_list.append(prc)
                            elif abs(pt - 3.5) < 0.05 and "under" in nm_l:
                                u35_list.append(prc)

                if bh > 1.01 and bd > 1.01 and ba > 1.01:
                    inv_b = (1.0 / bh) + (1.0 / bd) + (1.0 / ba)
                    ph_b = round(((1.0 / bh) / inv_b) * 100.0, 1)
                    reg_probs_h["all"].append(ph_b)
                    if bkey in eu_keys: reg_probs_h["eu"].append(ph_b)
                    elif bkey in uk_keys: reg_probs_h["uk"].append(ph_b)
                    elif bkey in us_keys: reg_probs_h["us"].append(ph_b)
                    elif bkey in au_keys: reg_probs_h["au"].append(ph_b)
                    if len(bm_snapshots) < 10:
                        bm_snapshots[bkey] = {"h": bh, "d": bd, "a": ba, "o25": bo25, "u25": bu25}
                    if b == pin_bm:
                        h_odd, d_odd, a_odd = bh, bd, ba

            if h_odd > 1.01 and d_odd > 1.01 and a_odd > 1.01:
                inv_s = (1.0 / h_odd) + (1.0 / d_odd) + (1.0 / a_odd)
                nv_h = round(((1.0 / h_odd) / inv_s) * 100.0, 1)
                nv_d = round(((1.0 / d_odd) / inv_s) * 100.0, 1)
                nv_a = round(((1.0 / a_odd) / inv_s) * 100.0, 1)
                avg_ph = sum(reg_probs_h["all"]) / max(1, len(reg_probs_h["all"]))
                pin_sharp_h = round(nv_h - avg_ph, 1)
                eu_m = round(sum(reg_probs_h["eu"]) / len(reg_probs_h["eu"]), 1) if reg_probs_h["eu"] else nv_h
                uk_m = round(sum(reg_probs_h["uk"]) / len(reg_probs_h["uk"]), 1) if reg_probs_h["uk"] else round(avg_ph, 1)
                us_m = round(sum(reg_probs_h["us"]) / len(reg_probs_h["us"]), 1) if reg_probs_h["us"] else round(avg_ph, 1)
                au_m = round(sum(reg_probs_h["au"]) / len(reg_probs_h["au"]), 1) if reg_probs_h["au"] else round(avg_ph, 1)
                reg_vals = [eu_m, uk_m, us_m, au_m]
                reg_spread = round(max(reg_vals) - min(reg_vals), 1)
                o25_avg = round(sum(o25_list) / len(o25_list), 2) if o25_list else 0.0
                u25_avg = round(sum(u25_list) / len(u25_list), 2) if u25_list else 0.0
                nv_o25 = round(((1.0 / o25_avg) / ((1.0 / o25_avg) + (1.0 / u25_avg))) * 100.0, 1) if (o25_avg > 1.02 and u25_avg > 1.02) else 0.0

                new_map[f"{h_tm}_{a_tm}"] = {
                    "dec_h": h_odd, "dec_d": d_odd, "dec_a": a_odd,
                    "nv_h": nv_h, "nv_d": nv_d, "nv_a": nv_a,
                    "pin_sharp_h": pin_sharp_h, "pin_sharp_a": -pin_sharp_h,
                    "eu_h": eu_m, "uk_h": uk_m, "us_h": us_m, "au_h": au_m,
                    "reg_spread": reg_spread, "bm_count": len(reg_probs_h["all"]),
                    "o25_dec": o25_avg, "u25_dec": u25_avg, "nv_o25": nv_o25,
                    "o15_dec": round(sum(o15_list) / len(o15_list), 2) if o15_list else 0.0,
                    "u35_dec": round(sum(u35_list) / len(u35_list), 2) if u35_list else 0.0,
                    "books": bm_snapshots, "bm_title": str(pin_bm.get("title") or "Pinnacle/Global")
                }
    oa_cache["ts"] = now_ts
    oa_cache["data"] = new_map
    return new_map
def _match_in_odds_api(h_name, a_name, oa_map):
    if not oa_map:
        return {}
    hk, ak = _norm_team_key(h_name), _norm_team_key(a_name)
    if f"{hk}_{ak}" in oa_map:
        return oa_map[f"{hk}_{ak}"]
    for k, v in oa_map.items():
        pts = k.split("_")
        if len(pts) == 2 and len(hk) >= 3 and len(ak) >= 3:
            if (hk in pts[0] or pts[0] in hk) and (ak in pts[1] or pts[1] in ak):
                return v
    return {}

def _fetch_af_daily_fixtures_map():
    now_ts = time.time()
    af_cache = MEM.setdefault("af_daily_cache", {"ts": 0.0, "fixtures": {}, "odds": {}})
    if now_ts - safe_float(af_cache.get("ts"), 0.0) < 1800.0 and af_cache.get("fixtures"):
        return af_cache["fixtures"]
    if not API_FOOTBALL_KEY:
        return af_cache.get("fixtures") or {}

    now_tr_dt = datetime.now(TR_TZ)
    dates_to_pull = [now_tr_dt.strftime("%Y-%m-%d"), (now_tr_dt + timedelta(days=1)).strftime("%Y-%m-%d")]
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    fx_map = dict(af_cache.get("fixtures") or {})
    for d_iso in dates_to_pull:
        try:
            r = HTTP_SESSION.get(f"https://v3.football.api-sports.io/fixtures?date={d_iso}&timezone=Europe/Istanbul", headers=headers, timeout=3.8)
            if r.status_code == 200:
                for item in (r.json().get("response") or []):
                    fx = item.get("fixture") or {}
                    tms = item.get("teams") or {}
                    sc = item.get("score") or {}
                    fid = fx.get("id")
                    hk = _norm_team_key((tms.get("home") or {}).get("name"))
                    ak = _norm_team_key((tms.get("away") or {}).get("name"))
                    if fid and hk and ak:
                        fx_map[f"{hk}_{ak}"] = {
                            "fid": fid,
                            "referee": str(fx.get("referee") or "").split(",")[0].strip(),
                            "ht_home": safe_int((sc.get("halftime") or {}).get("home"), 0),
                            "ht_away": safe_int((sc.get("halftime") or {}).get("away"), 0)
                        }
        except Exception:
            pass
    af_cache["ts"] = now_ts
    af_cache["fixtures"] = fx_map
    return fx_map

def _fetch_af_real_odds(fid):
    if not fid or not API_FOOTBALL_KEY:
        return {}
    af_cache = MEM.setdefault("af_daily_cache", {"ts": 0.0, "fixtures": {}, "odds": {}})
    odds_map = af_cache.setdefault("odds", {})
    if fid in odds_map and isinstance(odds_map[fid], dict) and odds_map[fid].get("_v") == 3:
        return odds_map[fid]
    if len(odds_map) >= 300:
        return odds_map.get(fid, {})

    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    parsed, multi_bms, agg_lists = {}, {}, {}

    def _add_agg(k, val):
        if 1.12 <= val <= 3.60:
            agg_lists.setdefault(k, []).append(val)

    try:
        r = HTTP_SESSION.get(f"https://v3.football.api-sports.io/odds?fixture={fid}", headers=headers, timeout=3.0)
        if r.status_code == 200:
            resp = r.json().get("response") or []
            if resp:
                for bm in (resp[0].get("bookmakers") or [])[:8]:
                    bm_nm = str(bm.get("name") or "Book").strip()
                    bm_rec = {}
                    for bet in (bm.get("bets") or []):
                        bname = str(bet.get("name") or "").lower()
                        vals = bet.get("values") or []
                        if "goals over/under" in bname and "first half" not in bname and "second half" not in bname:
                            for v in vals:
                                vs, ov = str(v.get("value") or ""), safe_float(v.get("odd"), 0.0)
                                if vs == "Over 1.5": _add_agg("o15_odd", ov); bm_rec["o15"] = ov
                                elif vs == "Under 1.5": _add_agg("u15_odd", ov)
                                elif vs == "Over 2.5": _add_agg("o25_odd", ov); bm_rec["o25"] = ov
                                elif vs == "Under 2.5": _add_agg("u25_odd", ov); bm_rec["u25"] = ov
                                elif vs == "Over 3.5": _add_agg("o35_odd", ov)
                                elif vs == "Under 3.5": _add_agg("u35_odd", ov); bm_rec["u35"] = ov
                        elif "first half" in bname and "over/under" in bname:
                            for v in vals:
                                vs, ov = str(v.get("value") or ""), safe_float(v.get("odd"), 0.0)
                                if vs == "Over 0.5": _add_agg("ht_o05_odd", ov)
                                elif vs == "Under 0.5": _add_agg("ht_u05_odd", ov)
                                elif vs == "Over 1.5": _add_agg("ht_o15_odd", ov)
                                elif vs == "Under 1.5": _add_agg("ht_u15_odd", ov)
                        elif "both teams score" in bname and "half" not in bname:
                            for v in vals:
                                vl, ov = str(v.get("value") or "").lower(), safe_float(v.get("odd"), 0.0)
                                if vl == "yes": _add_agg("btts_odd", ov); bm_rec["btts_y"] = ov
                                elif vl == "no": _add_agg("btts_no_odd", ov); bm_rec["btts_n"] = ov
                        elif "total - home" in bname:
                            for v in vals:
                                if str(v.get("value") or "") == "Over 1.5": _add_agg("h_o15_odd", safe_float(v.get("odd"), 0.0))
                        elif "total - away" in bname:
                            for v in vals:
                                if str(v.get("value") or "") == "Over 1.5": _add_agg("a_o15_odd", safe_float(v.get("odd"), 0.0))
                        elif bname in ("corners over/under", "total corners"):
                            for v in vals:
                                vs, ov = str(v.get("value") or ""), safe_float(v.get("odd"), 0.0)
                                if "Over 7.5" in vs: _add_agg("cor75_odd", ov)
                                elif "Under 7.5" in vs: _add_agg("cor_u75_odd", ov)
                                elif "Over 8.5" in vs: _add_agg("cor85_odd", ov)
                                elif "Under 8.5" in vs: _add_agg("cor_u85_odd", ov)
                                elif "Over 9.5" in vs: _add_agg("cor95_odd", ov)
                                elif "Under 9.5" in vs: _add_agg("cor_u95_odd", ov)
                        elif "cards over/under" in bname or "yellow cards" in bname:
                            for v in vals:
                                vs, ov = str(v.get("value") or ""), safe_float(v.get("odd"), 0.0)
                                if "Over 3.5" in vs: _add_agg("card35_odd", ov)
                                elif "Under 3.5" in vs: _add_agg("card_u35_odd", ov)
                                elif "Over 4.5" in vs: _add_agg("card45_odd", ov)
                                elif "Under 4.5" in vs: _add_agg("card_u45_odd", ov)
                    if bm_rec:
                        multi_bms[bm_nm] = bm_rec

        for ak_k, av_list in agg_lists.items():
            parsed[ak_k] = round(sum(av_list) / len(av_list), 2)
        if multi_bms:
            parsed["multi_books"] = multi_bms
            parsed["af_bm_cnt"] = len(multi_bms)
    except Exception:
        pass
    parsed["_v"] = 3
    odds_map[fid] = parsed
    return parsed
# ==================== MODÜL 2B/6: EWMA-5 GEÇMİŞ MAÇ İSTATİSTİK MOTORU ====================
def _calc_ewma(vals, default_val):
    if not vals:
        return default_val
    weights = [1.80, 1.45, 1.15, 0.90, 0.70][:len(vals)]
    return sum(v * w for v, w in zip(vals, weights)) / sum(weights)

def fetch_last_match_twin(slug, team_id, current_ev_id, curr_starters, curr_tac, team_name=""):
    twin_cache = MEM.setdefault("twin_cache", {})
    cache_key = f"{slug}_{team_id}_{current_ev_id}_v50"
    if cache_key in twin_cache:
        cached_res = twin_cache[cache_key]
        if isinstance(cached_res, dict) and "cor_avg" in cached_res and "sh_avg" in cached_res:
            return cached_res

    rng = _DeterministicRng(f"twin_{team_name}_{team_id}")
    res = {
        "rot_cnt": 0, "def_shift": False, "wing_drop": False, "hungry_sub": False, "sub_rat": 72,
        "xg_avg": round(1.18 + rng.randint(0, 40) * 0.01, 2),
        "sot_avg": round(3.6 + rng.randint(0, 22) * 0.1, 1),
        "sh_avg": round(10.5 + rng.randint(0, 45) * 0.1, 1),
        "cor_avg": round(4.4 + rng.randint(0, 24) * 0.1, 1),
        "foul_avg": round(10.8 + rng.randint(0, 30) * 0.1, 1),
        "card_avg": round(1.8 + rng.randint(0, 14) * 0.1, 1),
        "rest_days": 6, "wing_impact": 0, "emp_n": 0
    }
    if not team_id:
        return res
    try:
        r = HTTP_SESSION.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/teams/{team_id}/schedule", timeout=2.6)
        if r.status_code == 200:
            evs = [
                e for e in (r.json().get("events") or [])
                if str(e.get("id")) != str(current_ev_id)
                and (((e.get("competitions") or [{}])[0].get("status") or {}).get("type") or {}).get("state") == "post"
            ]
            if evs:
                last_5 = evs[-5:][::-1]
                sot_list, sh_list, cor_list, foul_list, card_list, xg_list = [], [], [], [], [], []
                missing_stat_ev_ids = set()
                try:
                    last_dt_str = str(last_5[0].get("date") or "").replace("Z", "+00:00")
                    last_dt = datetime.fromisoformat(last_dt_str)
                    res["rest_days"] = int(max(2, min(14, (datetime.now(timezone.utc) - last_dt).days)))
                except Exception:
                    pass

                for ev_item in last_5:
                    ev_item_id = str(ev_item.get("id") or "")
                    comp_i = (ev_item.get("competitions") or [{}])[0]
                    found_stat = False
                    for c_tm in (comp_i.get("competitors") or []):
                        if str((c_tm.get("team") or {}).get("id")) == str(team_id):
                            sot_v = get_stat(c_tm, ["shotsOnTarget", "onGoal"])
                            sh_v = get_stat(c_tm, ["totalShots", "shotsSummary"])
                            cor_v = get_stat(c_tm, ["wonCorners", "corners"])
                            fl_v = get_stat(c_tm, ["foulsCommitted", "fouls"])
                            yc_v = get_stat(c_tm, ["yellowCards", "yellowCard"])
                            rc_v = get_stat(c_tm, ["redCards", "redCard"])
                            if sh_v > 0 or sot_v > 0 or cor_v > 0:
                                found_stat = True
                                sot_list.append(float(sot_v))
                                sh_list.append(float(max(sh_v, sot_v)))
                                cor_list.append(float(cor_v))
                                if fl_v > 0: foul_list.append(float(fl_v))
                                card_list.append(float(yc_v + rc_v))
                                xg_list.append(max(0.45, min(3.10, round(sot_v * 0.30 + max(0, sh_v - sot_v) * 0.05 + cor_v * 0.035, 2))))
                    if not found_stat and ev_item_id:
                        missing_stat_ev_ids.add(ev_item_id)

                core_counts = {}
                ev_sum_cache = MEM.setdefault("event_summary_cache", {})
                for p_ev in last_5:
                    p_id = str(p_ev.get("id") or "")
                    if not p_id:
                        continue
                    try:
                        s_json = ev_sum_cache.get(p_id)
                        if not isinstance(s_json, dict):
                            r_s = HTTP_SESSION.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={p_id}", timeout=1.9)
                            if r_s.status_code == 200:
                                s_json = r_s.json()
                                if len(ev_sum_cache) > 350: ev_sum_cache.clear()
                                ev_sum_cache[p_id] = s_json
                        if isinstance(s_json, dict):
                            for r_t in (s_json.get("rosters") or []):
                                if str((r_t.get("team") or {}).get("id")) == str(team_id):
                                    for a in (r_t.get("roster") or []):
                                        if a.get("starter"):
                                            nm = str((a.get("athlete") or {}).get("displayName") or "").strip()
                                            if nm: core_counts[nm] = core_counts.get(nm, 0) + 1
                            if p_id in missing_stat_ev_ids:
                                for bs_t in ((s_json.get("boxscore") or {}).get("teams") or []):
                                    if str((bs_t.get("team") or {}).get("id")) == str(team_id):
                                        sot_b = get_stat(bs_t, ["shotsOnTarget", "onGoal"])
                                        sh_b = get_stat(bs_t, ["totalShots", "shotsSummary"])
                                        cor_b = get_stat(bs_t, ["wonCorners", "corners"])
                                        fl_b = get_stat(bs_t, ["foulsCommitted", "fouls"])
                                        yc_b = get_stat(bs_t, ["yellowCards", "yellowCard"])
                                        rc_b = get_stat(bs_t, ["redCards", "redCard"])
                                        if sh_b > 0 or sot_b > 0 or cor_b > 0:
                                            sot_list.append(float(sot_b)); sh_list.append(float(max(sh_b, sot_b))); cor_list.append(float(cor_b))
                                            if fl_b > 0: foul_list.append(float(fl_b))
                                            card_list.append(float(yc_b + rc_b))
                                            xg_list.append(max(0.45, min(3.10, round(sot_b * 0.30 + max(0, sh_b - sot_b) * 0.05 + cor_b * 0.035, 2))))
                    except Exception:
                        pass

                res["emp_n"] = len(sh_list)
                if sot_list: res["sot_avg"] = round(_calc_ewma(sot_list, res["sot_avg"]), 2)
                if sh_list: res["sh_avg"] = round(_calc_ewma(sh_list, res["sh_avg"]), 2)
                if cor_list: res["cor_avg"] = round(_calc_ewma(cor_list, res["cor_avg"]), 2)
                if foul_list: res["foul_avg"] = round(_calc_ewma(foul_list, res["foul_avg"]), 1)
                if card_list: res["card_avg"] = round(_calc_ewma(card_list, res["card_avg"]), 2)
                if xg_list: res["xg_avg"] = round(_calc_ewma(xg_list, res["xg_avg"]), 2)

                if core_counts and curr_starters:
                    core_xi = {k for k, v in sorted(core_counts.items(), key=lambda item: item[1], reverse=True)[:11]}
                    rot = len(set(curr_starters) - core_xi)
                    res["rot_cnt"] = rot
                    res["def_shift"] = (rot >= 4)
                    res["wing_drop"] = (rot >= 3)
                    res["hungry_sub"] = (1 <= rot <= 3)
                    res["sub_rat"] = min(88, 73 + rot * 4)
                    res["wing_impact"] = -min(10, rot * 2) if rot >= 3 else 0
            twin_cache[cache_key] = res
    except Exception:
        pass
    return res
# ==================== MODÜL 2C/6: KADRO DOĞRULAMA, 5D REYTİNG, HAKEM VE HAVA FİZİĞİ ====================
def analyze_lineup(roster_obj, team_name, mom, is_fav, slug, current_ev_id, fallback_team_id=""):
    rng = _DeterministicRng(f"lineup_{team_name}_{slug}")
    base = max(60, min(88, int(68 + (mom - 50) * 0.22 + (4 if is_fav else 0))))
    def_r = max(55, min(91, base + rng.randint(-3, 3)))
    pas_r = max(55, min(92, base + rng.randint(-2, 4)))
    dri_r = max(55, min(92, base + rng.randint(-2, 5)))
    sho_r = max(55, min(93, base + rng.randint(-2, 5)))
    raw_tac = str((roster_obj or {}).get("formation") or "").strip()
    tac_verified = bool(raw_tac and raw_tac != "None")
    tac = raw_tac if tac_verified else ["4-2-3-1", "4-3-3", "4-4-2", "3-5-2", "3-4-2-1", "5-3-2"][rng.randint(0, 5)]

    starters, bench, starter_names, gk_starter = [], [], [], True
    pos_sho, pos_pas, pos_dri, pos_def = [], [], [], []
    for idx, p in enumerate((roster_obj or {}).get("roster") or []):
        ath = p.get("athlete") or {}
        p_name = str(ath.get("displayName") or ath.get("shortName") or f"Oyuncu {idx+1}")
        p_short = str(ath.get("shortName") or p_name).split()[-1][:10]
        p_num = str(p.get("jersey") or ath.get("jersey") or (idx + 1))
        pos_abbr = str(((p.get("position") or ath.get("position")) or {}).get("abbreviation") or "M").upper()
        p_rat = max(62, min(91, base + _DeterministicRng(f"plr_{team_name}_{p_name}").randint(-3, 6)))
        p_dict = {
            "num": p_num, "name": p_short, "full_name": p_name, "rat": p_rat, "pos": pos_abbr,
            "subbed": bool(p.get("subbedOut") or p.get("subbedIn")),
            "yellow": bool(p.get("yellowCard")), "red": bool(p.get("redCard"))
        }
        if p.get("starter") or (not starters and idx < 11):
            starters.append(p_dict); starter_names.append(p_name)
            if pos_abbr in ("G", "GK") and p_rat < 66: gk_starter = False
            if pos_abbr in ("F", "FW", "ST", "CF", "LW", "RW"):
                pos_sho.append(min(94, p_rat + 3)); pos_dri.append(min(93, p_rat + 2))
            elif pos_abbr in ("M", "MF", "CM", "AM", "CAM", "CDM", "LM", "RM"):
                pos_pas.append(min(93, p_rat + 2)); pos_dri.append(min(92, p_rat + 1))
            elif pos_abbr in ("D", "DF", "CB", "LB", "RB", "WB", "G", "GK"):
                pos_def.append(min(92, p_rat + 2))
        else:
            bench.append(p_dict)

    if not starters:
        for i in range(11):
            starters.append({
                "num": str(i + 1), "name": f"XI-{i+1}", "full_name": f"Oyuncu {i+1}", "rat": base,
                "pos": "GK" if i == 0 else ("DF" if i <= 4 else ("MF" if i <= 8 else "FW")),
                "subbed": False, "yellow": False, "red": False
            })

    if pos_sho: sho_r = int(round(sum(pos_sho) / len(pos_sho)))
    if pos_pas: pas_r = int(round(sum(pos_pas) / len(pos_pas)))
    if pos_dri: dri_r = int(round(sum(pos_dri) / len(pos_dri)))
    if pos_def: def_r = int(round(sum(pos_def) / len(pos_def)))

    ovr_r = int(round((def_r + pas_r + dri_r + sho_r) / 4.0))
    team_id = str(((roster_obj or {}).get("team") or {}).get("id") or fallback_team_id or "")
    hist = fetch_last_match_twin(slug, team_id, current_ev_id, starter_names, tac, team_name)
    return {
        "ovr": ovr_r, "def": def_r, "pas": pas_r, "dri": dri_r, "sho": sho_r,
        "tac": tac, "tac_verified": tac_verified,
        "rot_gk": (not gk_starter) or (hist.get("rot_cnt", 0) >= 5),
        "rot_cnt": hist.get("rot_cnt", 0), "cor_avg": round(safe_float(hist.get("cor_avg"), 4.6), 1), "hist": hist,
        "starters": starters[:11], "bench": bench[:7], "has_real_xi": len(starter_names) >= 7
    }

def fetch_and_analyze_roster(args):
    if len(args) >= 16:
        slug, ev_id, match_title, h_name, a_name, h_mom, a_mom, odd_str, state, kademe, fav_abbr, fav_val, a_abbr, mins_to_ko, h_tid, a_tid = args[:16]
    else:
        slug, ev_id, match_title, h_name, a_name, h_mom, a_mom, odd_str, state, kademe, fav_abbr, fav_val, a_abbr, mins_to_ko = args[:14]
        h_tid, a_tid = "", ""

    oa_match = _match_in_odds_api(h_name, a_name, _fetch_odds_api_global_map())
    af_fx_map = _fetch_af_daily_fixtures_map()
    roster_cache = MEM.setdefault("roster_cache", {})
    hk, ak = _norm_team_key(h_name), _norm_team_key(a_name)
    af_fx = af_fx_map.get(f"{hk}_{ak}") or {}
    if not af_fx:
        for fk, fv in af_fx_map.items():
            pts = fk.split("_")
            if len(pts) == 2 and len(hk) >= 3 and len(ak) >= 3 and (hk in pts[0] or pts[0] in hk) and (ak in pts[1] or pts[1] in ak):
                af_fx = fv; break

    af_odds = _fetch_af_real_odds(af_fx["fid"]) if (af_fx.get("fid") and state == "pre" and -15 <= mins_to_ko <= 1440) else {}
    if ev_id in roster_cache:
        cached = roster_cache[ev_id]
        st_check = ((cached.get("h") or {}).get("starters") or [None])[0]
        emp_cached = min(safe_int((((cached.get("h") or {}).get("hist") or {}).get("emp_n")), 0), safe_int((((cached.get("a") or {}).get("hist") or {}).get("emp_n")), 0))
        if isinstance(cached, dict) and isinstance(st_check, dict) and "ovr" in (cached.get("h") or {}) and (emp_cached > 0 or not (h_tid and a_tid)):
            cached["odds_api"] = oa_match
            if af_odds: cached["af_odds"] = af_odds
            if not ((state in ("in", "post") or mins_to_ko <= 65) and not cached.get("official")):
                return match_title, cached

    r_h, r_a, is_off, live_cards_cnt = {}, {}, False, 0
    ref_name = str(af_fx.get("referee") or "Atanmadı")
    weather_str, venue_str = "Parçalı Bulutlu 16°C", f"{h_name} Stadium"
    box_stats = {"h_sh": 0, "a_sh": 0, "h_sot": 0, "a_sot": 0, "h_cor": 0, "a_cor": 0, "cards": 0}
    if ev_id and ((state in ("in", "post")) or (mins_to_ko <= 480) or (kademe == 1 and mins_to_ko <= 960)):
        try:
            r = HTTP_SESSION.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={ev_id}", timeout=2.6)
            if r.status_code == 200:
                data = r.json()
                rosters = data.get("rosters") or []
                if len(rosters) >= 2:
                    r_h = next((x for x in rosters if x.get("homeAway") == "home"), rosters[0])
                    r_a = next((x for x in rosters if x.get("homeAway") == "away"), rosters[1])
                    is_off = (len(r_h.get("roster") or []) >= 7 and len(r_a.get("roster") or []) >= 7)
                bs_teams = (data.get("boxscore") or {}).get("teams") or []
                if len(bs_teams) >= 2:
                    bs_h = next((x for x in bs_teams if x.get("homeAway") == "home"), bs_teams[0])
                    bs_a = next((x for x in bs_teams if x.get("homeAway") == "away"), bs_teams[1])
                    box_stats["h_sh"], box_stats["a_sh"] = get_stat(bs_h, ["totalShots", "shotsSummary"]), get_stat(bs_a, ["totalShots", "shotsSummary"])
                    box_stats["h_sot"], box_stats["a_sot"] = get_stat(bs_h, ["shotsOnTarget", "onGoal"]), get_stat(bs_a, ["shotsOnTarget", "onGoal"])
                    box_stats["h_cor"], box_stats["a_cor"] = get_stat(bs_h, ["wonCorners", "corners"]), get_stat(bs_a, ["wonCorners", "corners"])
                    box_stats["cards"] = get_stat(bs_h, ["yellowCards", "yellowCard"]) + get_stat(bs_a, ["yellowCards", "yellowCard"]) + get_stat(bs_h, ["redCards", "redCard"]) + get_stat(bs_a, ["redCards", "redCard"])
                for ev_k in ((data.get("keyEvents") or []) + (data.get("commentary") or [])):
                    if isinstance(ev_k, dict) and any(k in str((ev_k.get("type") or {}).get("text") or "").lower() for k in ("yellow card", "red card", "second yellow")):
                        live_cards_cnt += 1
                live_cards_cnt = max(live_cards_cnt, box_stats["cards"])
                g_info = data.get("gameInfo") or {}
                if (g_info.get("venue") or {}).get("fullName"): venue_str = str(g_info["venue"]["fullName"])
                officials = g_info.get("officials") or []
                if officials and isinstance(officials[0], dict): ref_name = str(officials[0].get("displayName") or officials[0].get("fullName") or ref_name)
                wx = g_info.get("weather") or {}
                if wx:
                    tf = safe_float(wx.get("temperature"), 62.0)
                    tc = int(round((tf - 32.0) * 5.0 / 9.0)) if tf > 42 else int(tf)
                    cond = str(wx.get("displayValue") or wx.get("conditionId") or "Açık")
                    weather_str = f"🌧️ Yağışlı ({cond}) {tc}°C" if any(w in cond.lower() for w in ("rain", "shower", "storm", "snow", "yağmur", "yağış")) else f"☀️ {cond} {tc}°C"
        except Exception:
            pass

    ref_avg = round(3.4 + _DeterministicRng(f"ref_{ref_name}_{match_title}").randint(0, 22) * 0.1, 1)
    ref_style = "🔥 Çok Sert (Kart Sever)" if ref_avg >= 4.7 else ("⚖️ Dengeli / Otori" if ref_avg >= 3.9 else "🟢 Akıcı / Kart Cimrisi")
    h_is_fav = (fav_abbr != a_abbr)
    h_info = analyze_lineup(r_h, h_name, h_mom, h_is_fav, slug, ev_id, fallback_team_id=h_tid)
    a_info = analyze_lineup(r_a, a_name, a_mom, not h_is_fav, slug, ev_id, fallback_team_id=a_tid)
    res = {
        "official": is_off or (h_info["has_real_xi"] and a_info["has_real_xi"]),
        "h": h_info, "a": a_info, "weather": weather_str, "venue": venue_str,
        "live_cards": live_cards_cnt, "box_stats": box_stats, "af_fx": af_fx,
        "ref": {"name": ref_name, "avg": ref_avg, "style": ref_style, "pen": round(0.18 + (ref_avg - 3.4) * 0.12, 2)},
        "odds_api": oa_match, "af_odds": af_odds
    }
    if ev_id and state == "pre": roster_cache[ev_id] = res
    return match_title, res
# ==================== MODÜL 3A/6: LİG DNA, İDDAA KALKANI VE DIXON-COLES MOTORU ====================
MODEL_VERSION = "M5.1.9_CORNER_REALITY"

DEFAULT_LIG_DNA = {"goal_mult": 1.00, "cor_mult": 1.00, "card_mult": 1.00, "disp_r": 10.5, "rho": -0.09}
LEAGUE_DNA_PROFILES = {
    "tur.1": {"goal_mult": 1.02, "cor_mult": 0.99, "card_mult": 1.12, "disp_r": 9.8, "rho": -0.08},
    "tur.2": {"goal_mult": 0.97, "cor_mult": 0.96, "card_mult": 1.14, "disp_r": 10.0, "rho": -0.10},
    "eng.1": {"goal_mult": 1.06, "cor_mult": 1.05, "card_mult": 0.95, "disp_r": 9.5, "rho": -0.06},
    "eng.2": {"goal_mult": 0.98, "cor_mult": 1.04, "card_mult": 1.02, "disp_r": 9.8, "rho": -0.10},
    "sco.1": {"goal_mult": 1.03, "cor_mult": 1.06, "card_mult": 1.02, "disp_r": 9.5, "rho": -0.08},
    "esp.1": {"goal_mult": 0.98, "cor_mult": 0.98, "card_mult": 1.08, "disp_r": 10.2, "rho": -0.10},
    "esp.2": {"goal_mult": 0.89, "cor_mult": 0.95, "card_mult": 1.12, "disp_r": 10.8, "rho": -0.13},
    "ita.1": {"goal_mult": 0.99, "cor_mult": 0.99, "card_mult": 1.04, "disp_r": 10.2, "rho": -0.10},
    "ita.2": {"goal_mult": 0.95, "cor_mult": 0.97, "card_mult": 1.12, "disp_r": 10.4, "rho": -0.11},
    "ger.1": {"goal_mult": 1.09, "cor_mult": 1.02, "card_mult": 0.96, "disp_r": 9.8, "rho": -0.06},
    "ger.2": {"goal_mult": 1.07, "cor_mult": 1.02, "card_mult": 1.01, "disp_r": 9.8, "rho": -0.07},
    "fra.1": {"goal_mult": 1.01, "cor_mult": 0.98, "card_mult": 1.01, "disp_r": 10.2, "rho": -0.09},
    "fra.2": {"goal_mult": 0.93, "cor_mult": 0.95, "card_mult": 1.03, "disp_r": 10.6, "rho": -0.11},
    "ned.1": {"goal_mult": 1.10, "cor_mult": 1.03, "card_mult": 0.90, "disp_r": 9.6, "rho": -0.05},
    "ned.2": {"goal_mult": 1.12, "cor_mult": 1.03, "card_mult": 0.88, "disp_r": 9.6, "rho": -0.05},
    "por.1": {"goal_mult": 0.98, "cor_mult": 1.01, "card_mult": 1.10, "disp_r": 10.2, "rho": -0.10},
    "bra.1": {"goal_mult": 0.95, "cor_mult": 1.03, "card_mult": 1.14, "disp_r": 9.8, "rho": -0.11},
    "arg.1": {"goal_mult": 0.90, "cor_mult": 0.98, "card_mult": 1.16, "disp_r": 10.4, "rho": -0.13},
    "mex.1": {"goal_mult": 1.03, "cor_mult": 1.02, "card_mult": 1.08, "disp_r": 9.8, "rho": -0.08},
    "uefa.champions": {"goal_mult": 1.05, "cor_mult": 1.01, "card_mult": 0.97, "disp_r": 9.8, "rho": -0.07},
    "uefa.europa": {"goal_mult": 1.03, "cor_mult": 0.98, "card_mult": 1.02, "disp_r": 10.2, "rho": -0.08},
    "uefa.europa.conf": {"goal_mult": 1.02, "cor_mult": 0.96, "card_mult": 1.03, "disp_r": 10.5, "rho": -0.08}
}

def is_iddaa_prop_league_open(slug, lig_adi=""):
    s = str(slug or "").lower()
    if s in ("bra.1", "arg.1", "mex.1", "ned.2", "fra.2", "tur.2", "esp.2", "ita.2", "eng.2", "ger.2"):
        return False
    return s in (
        "tur.1", "eng.1", "esp.1", "ita.1", "ger.1", "fra.1",
        "ned.1", "por.1", "sco.1", "uefa.champions", "uefa.europa", "uefa.europa.conf"
    )

def neg_binom_prob_over(line_val, mu, disp_r=10.0):
    k_max = int(math.floor(float(line_val)))
    mu = max(0.3, float(mu))
    r = max(1.5, float(disp_r))
    p = r / (r + mu)
    cdf = 0.0
    for k in range(0, k_max + 1):
        log_p = math.lgamma(k + r) - math.lgamma(k + 1) - math.lgamma(r) + r * math.log(p) + k * math.log(max(1e-9, 1.0 - p))
        cdf += math.exp(log_p)
    return max(0.02, min(0.97, 1.0 - cdf))

def _compute_empirical_shot_pressure_delta(h_hist, a_hist, h_mom, a_mom):
    h_sh = safe_float((h_hist or {}).get("sh_avg"), 11.0)
    a_sh = safe_float((a_hist or {}).get("sh_avg"), 10.5)
    h_sot = safe_float((h_hist or {}).get("sot_avg"), 3.6)
    a_sot = safe_float((a_hist or {}).get("sot_avg"), 3.6)
    d_h = round((h_sh - 11.0) * 0.8 + (h_sot - 3.6) * 1.4 + (safe_int(h_mom, 50) - 50) * 0.08, 1)
    d_a = round((a_sh - 10.5) * 0.8 + (a_sot - 3.6) * 1.4 + (safe_int(a_mom, 50) - 50) * 0.08, 1)
    return d_h, d_a, round(d_h - d_a, 1), "ΔÜ"

def _poisson_pmf(k, lam):
    lam = max(0.05, float(lam))
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1))

def compute_dixon_coles_matrix(h_name, a_name, h_mom, a_mom, fav_val, ou_val, is_home_fav, r_data):
    r_d = r_data or {}
    slug = str(r_d.get("slug") or "eng.1")
    dna = LEAGUE_DNA_PROFILES.get(slug, DEFAULT_LIG_DNA)
    h_d, a_d = r_d.get("h") or {}, r_d.get("a") or {}
    h_hist, a_hist = h_d.get("hist") or {}, a_d.get("hist") or {}
    oa = r_d.get("odds_api") or {}

    base_tot = max(2.15, min(3.65, (safe_float(ou_val, 2.5) * 0.62 + (safe_float(h_hist.get("xg_avg"), 1.3) + safe_float(a_hist.get("xg_avg"), 1.2)) * 0.42) * dna["goal_mult"]))
    if oa.get("nv_h") and oa.get("nv_a"):
        share_h = max(0.22, min(0.78, (oa["nv_h"] + oa.get("nv_d", 26.0) * 0.5) / 100.0))
    else:
        abs_f = abs(safe_int(fav_val, -125))
        fav_sh = min(0.76, 0.52 + max(0, abs_f - 110) * 0.00055 + abs(h_mom - a_mom) * 0.0018)
        share_h = fav_sh if is_home_fav else (1.0 - fav_sh)

    inj_def_boost = 1.06 if (h_hist.get("def_shift") or a_hist.get("def_shift") or h_d.get("rot_gk") or a_d.get("rot_gk")) else 1.0
    lam_h = round(max(0.45, min(2.85, base_tot * share_h * inj_def_boost)), 2)
    lam_a = round(max(0.42, min(2.65, base_tot * (1.0 - share_h) * inj_def_boost)), 2)
    rho = safe_float(dna.get("rho"), -0.09)

    mat = {}
    tot_p = 0.0
    for i in range(7):
        for j in range(7):
            p = _poisson_pmf(i, lam_h) * _poisson_pmf(j, lam_a)
            if i == 0 and j == 0: p *= max(0.2, 1.0 - lam_h * lam_a * rho)
            elif i == 0 and j == 1: p *= max(0.2, 1.0 + lam_h * rho)
            elif i == 1 and j == 0: p *= max(0.2, 1.0 + lam_a * rho)
            elif i == 1 and j == 1: p *= max(0.2, 1.0 - rho)
            mat[(i, j)] = p
            tot_p += p
    for k in mat:
        mat[k] /= max(1e-9, tot_p)

    top_sc, top_pr = max(mat.items(), key=lambda x: x[1])
    d_weak = max(4, min(68, int(round((100 - (safe_int(h_d.get("def"), 72) + safe_int(a_d.get("def"), 72)) * 0.5) * 0.9 + (16 if inj_def_boost > 1.0 else 0) - (6 if r_d.get("official") else 0)))))
    return {
        "lam_h": lam_h, "lam_a": lam_a, "mat": mat,
        "top_score": f"{top_sc[0]}-{top_sc[1]}", "top_prob": int(round(top_pr * 100)),
        "p11": int(round(mat.get((1, 1), 0.11) * 100)), "d_weak": d_weak
    }
# ==================== MODÜL 3B/6: SÜRTÜNME FİZİĞİ (KORNER TAVANLI) & 28 PAZAR SPEKTRUMU ====================
def compute_friction_physics(h_name, a_name, h_tac, a_tac, h_mom, a_mom, fav_val, ou_val, kademe, r_data, lig_adi="", is_home_fav=True):
    r_d = r_data or {}
    slug = str(r_d.get("slug") or "eng.1")
    lig_dna = LEAGUE_DNA_PROFILES.get(slug, DEFAULT_LIG_DNA)
    h_d, a_d = r_d.get("h") or {}, r_d.get("a") or {}
    h_hist, a_hist = h_d.get("hist") or {}, a_d.get("hist") or {}
    ref_d = r_d.get("ref") or {}
    wx_str = str(r_d.get("weather") or "")

    h_cor_avg = safe_float(h_hist.get("cor_avg") or h_d.get("cor_avg"), 5.0)
    a_cor_avg = safe_float(a_hist.get("cor_avg") or a_d.get("cor_avg"), 4.5)
    min_side_cor = round(min(h_cor_avg, a_cor_avg), 1)
    real_cor_sum = round(h_cor_avg + a_cor_avg, 1)
    sh_sum = safe_float(h_hist.get("sh_avg"), 11.0) + safe_float(a_hist.get("sh_avg"), 10.5)
    sot_sum = safe_float(h_hist.get("sot_avg"), 3.6) + safe_float(a_hist.get("sot_avg"), 3.6)

    delta_h, delta_a, _, delta_lbl = _compute_empirical_shot_pressure_delta(h_hist, a_hist, h_mom, a_mom)
    fav_delta = delta_h if is_home_fav else delta_a

    h_dri, a_dri = safe_int(h_d.get("dri"), 70), safe_int(a_d.get("dri"), 70)
    wing_asym = bool((max(h_dri, a_dri) >= 75 and real_cor_sum >= 10.0) or (("3-4-" in str(h_tac) or "3-5-" in str(h_tac) or "3-4-" in str(a_tac) or "3-5-" in str(a_tac)) and real_cor_sum >= 9.6))

    hungry_pts = max(safe_int(h_hist.get("sub_rat"), 0) if h_hist.get("hungry_sub") else 0, safe_int(a_hist.get("sub_rat"), 0) if a_hist.get("hungry_sub") else 0)
    rot_pen = safe_int(h_hist.get("wing_impact"), 0) + safe_int(a_hist.get("wing_impact"), 0)
    inj_wing = bool(h_hist.get("wing_drop") or a_hist.get("wing_drop"))
    inj_def = bool(h_hist.get("def_shift") or a_hist.get("def_shift") or h_d.get("rot_gk") or a_d.get("rot_gk"))

    mom_gap = abs(safe_int(h_mom, 50) - safe_int(a_mom, 50))
    abs_fav = abs(safe_int(fav_val, -130)) if fav_val < 0 else 100
    blowout_prob = min(88, 52 + int(mom_gap * 0.6) + int(max(0, abs_fav - 150) * 0.12)) if ((fav_val <= -200) or (mom_gap >= 24 and fav_val <= -145) or (ou_val >= 3.5 and fav_val <= -170)) else 20
    is_blowout = (blowout_prob >= 58)

    is_karavana = (sh_sum >= 21.0 and (sot_sum / max(1.0, sh_sum)) < 0.32)
    is_goal_cannibal = (sh_sum >= 22.0 and (sot_sum / max(1.0, sh_sum)) >= 0.35) or (ou_val >= 3.5 and min_side_cor < 4.7)
    min_emp_cor = min(safe_int(h_hist.get("emp_n"), 0), safe_int(a_hist.get("emp_n"), 0))
    is_uefa_sec_cup = slug in ("uefa.europa.conf", "uefa.europa")

    eff_cor_sum = (real_cor_sum * 0.72 + 9.5 * 0.28) if is_uefa_sec_cup else ((real_cor_sum * 0.78 + 9.5 * 0.22) if min_emp_cor < 4 else real_cor_sum)
    blocked_shot_cor_boost = 1.07 if ((sh_sum >= 22.0 and abs(fav_delta) < 4.0 and eff_cor_sum >= 9.6 and not is_goal_cannibal) or (is_karavana and eff_cor_sum >= 9.5)) else 1.0
    cannibal_pen = 0.90 if is_goal_cannibal else 1.0
    wx_mult = 1.04 if "Yağışlı" in wx_str else 1.0
    wing_mult = 1.05 if (wing_asym and not inj_wing) else (0.90 if inj_wing else 1.0)
    cor_mu = max(5.2, min(12.1, eff_cor_sum * 0.95 * wing_mult * wx_mult * blocked_shot_cor_boost * cannibal_pen * safe_float(lig_dna.get("cor_mult"), 1.0)))

    is_high_cor_lig = any(k in str(lig_adi).upper() for k in ("PREMIER", "İSKOÇYA", "EFL"))
    cor_line_num = 9.5 if is_high_cor_lig else 8.5
    disp_r_use = 8.0 if blocked_shot_cor_boost > 1.0 else min(9.5, safe_float(lig_dna.get("disp_r"), 10.5))
    cor_prob_pct = int(round(neg_binom_prob_over(cor_line_num, cor_mu, disp_r=disp_r_use) * 100.0))

    ref_avg = safe_float(ref_d.get("avg"), 4.0)
    hist_cards = safe_float(h_hist.get("card_avg"), 1.8) + safe_float(a_hist.get("card_avg"), 1.8)
    hist_fouls = safe_float(h_hist.get("foul_avg"), 11.0) + safe_float(a_hist.get("foul_avg"), 11.0)
    is_hot_lig = any(k in str(lig_adi).upper() for k in ("SERIE B", "LA LIGA 2", "BREZİLYA", "ARJANTİN", "SÜPER LİG"))
    card_line_num = 4.5 if is_hot_lig else 3.5

    foul_adj = max(-0.4, min(0.6, (hist_fouls - 22.0) * 0.05))
    raw_card_mu = ((ref_avg * 0.50) + (hist_cards * 0.50)) * safe_float(lig_dna.get("card_mult"), 1.0) + foul_adj + (0.45 if is_hot_lig else 0.0) + (0.25 if mom_gap <= 14 else 0.0) - (0.55 if is_blowout else 0.0)
    card_mu = max(1.8, min(8.2, raw_card_mu))
    card_prob_pct = int(round(neg_binom_prob_over(card_line_num, card_mu, disp_r=10.0) * 100.0))

    tags = [f"📊Son5Kor(EWMA):{real_cor_sum}", f"{delta_lbl}:{fav_delta:+.1f}"]
    if blocked_shot_cor_boost > 1.0: tags.append("🧱BlokŞut->Korner")
    if is_goal_cannibal: tags.append("⚠️GolKanibal")
    if hungry_pts >= 75: tags.append(f"🔥AçYedek({hungry_pts}p)")
    if is_blowout: tags.append(f"💥ErkenKopar(%{blowout_prob})")
    if wing_asym and not inj_wing: tags.append("📐KanatKorner")
    if inj_wing: tags.append("🏥KanatKaybı")
    if inj_def: tags.append("🛡️SakatKapanma")
    if rot_pen < 0: tags.append(f"🧬RotasyonUyum({rot_pen}p)")

    return {
        "cor_score": cor_prob_pct, "card_score": card_prob_pct, "cor_p": cor_prob_pct, "card_p": card_prob_pct,
        "real_cor_sum": real_cor_sum, "min_side_cor": min_side_cor, "sh_sum": round(sh_sum, 1), "is_karavana": is_karavana,
        "cor_lambda": round(cor_mu, 2), "card_lambda": round(card_mu, 2), "disp_r_use": disp_r_use,
        "est_cor_cnt": max(5, min(16, int(round(cor_mu)))), "est_card_cnt": max(2, min(8, int(round(card_mu)))),
        "wing_asym": wing_asym, "is_blowout": is_blowout, "blowout_prob": blowout_prob,
        "hungry_pts": hungry_pts, "rot_pen": rot_pen, "inj_wing": inj_wing, "inj_def": inj_def, "tags_str": " ".join(tags)
    }

def compute_full_spectrum_28_markets(m4, fr):
    mat = (m4 or {}).get("mat") or {}
    lh, la = safe_float((m4 or {}).get("lam_h"), 1.35), safe_float((m4 or {}).get("lam_a"), 1.15)
    cor_mu = safe_float((fr or {}).get("cor_lambda"), 9.5)
    card_mu = safe_float((fr or {}).get("card_lambda"), 4.0)
    dr = safe_float((fr or {}).get("disp_r_use"), 9.8)

    p_1 = sum(v for (i, j), v in mat.items() if i > j)
    p_x = sum(v for (i, j), v in mat.items() if i == j)
    p_2 = sum(v for (i, j), v in mat.items() if i < j)
    p_o15 = sum(v for (i, j), v in mat.items() if (i + j) >= 2)
    p_o25 = sum(v for (i, j), v in mat.items() if (i + j) >= 3)
    p_o35 = sum(v for (i, j), v in mat.items() if (i + j) >= 4)
    p_btts = sum(v for (i, j), v in mat.items() if i >= 1 and j >= 1)
    p_h_o15 = sum(v for (i, j), v in mat.items() if i >= 2)
    p_a_o15 = sum(v for (i, j), v in mat.items() if j >= 2)
    p_1_o15 = sum(v for (i, j), v in mat.items() if i > j and (i + j) >= 2)
    p_2_o15 = sum(v for (i, j), v in mat.items() if j > i and (i + j) >= 2)

    lam_ht = max(0.35, (lh + la) * 0.44)
    ht_0 = math.exp(-lam_ht)
    ht_1 = lam_ht * ht_0
    p_ht_o05 = 1.0 - ht_0
    p_ht_u15 = min(0.92, ht_0 + ht_1)

    c_o85 = neg_binom_prob_over(8.5, cor_mu, dr)
    c_o95 = neg_binom_prob_over(9.5, cor_mu, dr)
    k_o35 = neg_binom_prob_over(3.5, card_mu, 10.0)
    k_o45 = neg_binom_prob_over(4.5, card_mu, 10.0)

    pct = lambda x: max(4, min(95, int(round(float(x) * 100.0))))
    return {
        "MS_1": pct(p_1), "MS_X": pct(p_x), "MS_2": pct(p_2),
        "DC_1X": pct(p_1 + p_x), "DC_X2": pct(p_2 + p_x), "DC_12": pct(p_1 + p_2),
        "MS_O15": pct(p_o15), "MS_U15": pct(1.0 - p_o15),
        "MS_O25": pct(p_o25), "MS_U25": pct(1.0 - p_o25),
        "MS_O35": pct(p_o35), "MS_U35": pct(1.0 - p_o35),
        "BTTS_YES": pct(p_btts), "BTTS_NO": pct(1.0 - p_btts),
        "HT_O05": pct(p_ht_o05), "HT_U05": pct(1.0 - p_ht_o05),
        "HT_O15": pct(1.0 - p_ht_u15), "HT_U15": pct(p_ht_u15),
        "H_O15": pct(p_h_o15), "A_O15": pct(p_a_o15),
        "WIN1_O15": pct(p_1_o15), "WIN2_O15": pct(p_2_o15),
        "COR_O85": pct(c_o85), "COR_U85": pct(1.0 - c_o85),
        "COR_O95": pct(c_o95), "COR_U95": pct(1.0 - c_o95),
        "CARD_O35": pct(k_o35), "CARD_U35": pct(1.0 - k_o35),
        "CARD_O45": pct(k_o45), "CARD_U45": pct(1.0 - k_o45)
    }
# ==================== MODÜL 3C/6: KALİBRASYON TAVANI, İKİZ HAFIZA VE SAF İDDAA KARAR MOTORU ====================
def _classify_pick_market_type(pick_str):
    s = str(pick_str or "").upper()
    if "KORNER ALT" in s or "KORA" in s: return "COR_U"
    if "KORNER ÜST" in s or "KORÜ" in s or "KORNER" in s: return "COR_O"
    if "KART ALT" in s or "KARTA" in s: return "CARD_U"
    if "KART ÜST" in s or "KARTÜ" in s or "KART" in s: return "CARD_O"
    if "İLK YARI" in s and "ALT" in s: return "HT_U"
    if "İY 1.5A" in s or "İY 0.5A" in s: return "HT_U"
    if ("İLK YARI" in s or "İY ") and "ÜST" in s: return "HT_O05"
    if "KARŞILIKLI GOL VAR" in s or "KG VAR" in s: return "BTTS_YES"
    if "KARŞILIKLI GOL YOK" in s or "KG YOK" in s: return "BTTS_NO"
    if "TAKIM GOLÜ" in s or "TG 1.5" in s: return "TEAM_O15"
    if "KAZANIR" in s: return "WIN"
    if "3.5" in s and "ALT" in s: return "U35"
    if "2.5" in s and "ALT" in s: return "U25"
    if "1.5" in s and "ÜST" in s: return "O15"
    if ("2.5" in s or "3.5" in s) and "ÜST" in s: return "O25"
    return "WIN"

def _calibrate_decision_score_by_market_and_band(raw_prob_pct, mkt_type="WIN", max_allowed_conf=90):
    if mkt_type in ("COR_U", "CARD_O", "CARD_U"):
        max_allowed_conf = min(max_allowed_conf, 75)
    elif mkt_type in ("BTTS_YES", "O25", "U25", "TEAM_O15"):
        max_allowed_conf = min(max_allowed_conf, 76)
    elif mkt_type == "COR_O":
        max_allowed_conf = min(max_allowed_conf, 78)

    p = min(92.0, max(5.0, float(raw_prob_pct))) / 100.0
    fin_map = MEM.get("finished_cache", {})
    same_mkt = [
        m for m in fin_map.values()
        if isinstance(m, dict) and "pick" in m and "won" in m and _classify_pick_market_type(m.get("pick")) == mkt_type
    ]
    if len(same_mkt) < 10:
        calib_p = 0.50 + (p - 0.50) * 0.92
        return int(round(min(float(max_allowed_conf), max(45.0, calib_p * 100.0))))

    band_low, band_high = max(0.40, p - 0.10), min(0.98, p + 0.10)
    in_band = [x for x in same_mkt if band_low <= (safe_float(x.get("conf"), 70.0) / 100.0) <= band_high]
    pool = in_band if len(in_band) >= 5 else same_mkt[-25:]
    emp_hit = sum(1.0 for x in pool if x.get("won")) / len(pool)
    avg_pred = sum(safe_float(x.get("conf"), 70.0) / 100.0 for x in pool) / len(pool)
    adj_p = p + max(-0.06, min(0.03, (emp_hit - avg_pred) * 0.28))
    return int(round(min(float(max_allowed_conf), max(45.0, adj_p * 100.0))))

def compute_conditional_twin_memory_bonus(mkt_type, curr_ctx=None, lig_adi=""):
    fin_map = MEM.get("finished_cache", {})
    matches = [
        m for m in fin_map.values()
        if isinstance(m, dict) and "won" in m and _classify_pick_market_type(m.get("pick")) == mkt_type
    ]
    if len(matches) < 5:
        return 0
    same_lig = [m for m in matches if str(m.get("lig") or "") == str(lig_adi)]
    sample = same_lig if len(same_lig) >= 4 else matches[-20:]
    hit_rate = sum(1.0 for m in sample if m.get("won")) / len(sample)
    if hit_rate >= 0.78: return 6
    if hit_rate >= 0.70: return 3
    if hit_rate <= 0.48: return -5
    return 0

def _estimate_iddaa_and_eu_odd(pick_lbl, prob_pct, r_data, is_home_pick=True):
    r_d = r_data or {}
    oa = r_d.get("odds_api") or {}
    af = r_d.get("af_odds") or {}
    s = str(pick_lbl or "")
    eu_odd = 0.0

    if "2.5 Gol Üst" in s and "Kazanır" not in s:
        eu_odd = safe_float(af.get("o25_odd") or oa.get("o25_dec"), 0.0)
    elif "2.5 Gol Alt" in s:
        eu_odd = safe_float(af.get("u25_odd") or oa.get("u25_dec"), 0.0)
    elif "3.5 Gol Alt" in s:
        eu_odd = safe_float(af.get("u35_odd") or oa.get("u35_dec"), 0.0)
    elif "3.5 Gol Üst" in s:
        eu_odd = safe_float(af.get("o35_odd"), 0.0)
    elif "1.5 Gol Üst" in s and "Kazanır" not in s and "İlk Yarı" not in s:
        eu_odd = safe_float(af.get("o15_odd") or oa.get("o15_dec"), 0.0)
    elif "Karşılıklı Gol Var" in s:
        eu_odd = safe_float(af.get("btts_odd"), 0.0)
    elif "Karşılıklı Gol Yok" in s:
        eu_odd = safe_float(af.get("btts_no_odd"), 0.0)
    elif "İlk Yarı 1.5 Gol Alt" in s:
        eu_odd = safe_float(af.get("ht_u15_odd"), 0.0)
    elif "İlk Yarı 0.5 Gol Üst" in s:
        eu_odd = safe_float(af.get("ht_o05_odd"), 0.0)
    elif "8.5 Korner Üst" in s:
        eu_odd = safe_float(af.get("cor85_odd"), 0.0)
    elif "9.5 Korner Üst" in s:
        eu_odd = safe_float(af.get("cor95_odd"), 0.0)
    elif "9.5 Korner Alt" in s:
        eu_odd = safe_float(af.get("cor_u95_odd"), 0.0)
    elif "8.5 Korner Alt" in s:
        eu_odd = safe_float(af.get("cor_u85_odd"), 0.0)
    elif "3.5 Kart Üst" in s:
        eu_odd = safe_float(af.get("card35_odd"), 0.0)
    elif "4.5 Kart Üst" in s:
        eu_odd = safe_float(af.get("card45_odd"), 0.0)
    elif "4.5 Kart Alt" in s:
        eu_odd = safe_float(af.get("card_u45_odd"), 0.0)
    elif "Kazanır & 1.5 Gol Üst" in s:
        base_w = safe_float(oa.get("dec_h") if is_home_pick else oa.get("dec_a"), 0.0)
        if base_w > 1.05:
            eu_odd = round(base_w * 1.22, 2)

    has_real_eu = (eu_odd >= 1.08)
    if not has_real_eu:
        p_clamped = max(0.28, min(0.84, float(prob_pct) / 100.0))
        eu_odd = round(0.94 / p_clamped, 2)

    tr_odd = round(max(1.08, eu_odd * 0.915), 2)
    return tr_odd, round(eu_odd, 2), has_real_eu
def _select_best_autonomous_market(h_name, a_name, fav_team, is_home_fav, fav_val, ou_val, spec, m4, fr, r_data, lig_adi=""):
    r_d = r_data or {}
    slug = str(r_d.get("slug") or "eng.1")
    oa = r_d.get("odds_api") or {}
    af = r_d.get("af_odds") or {}
    odd_mode = MEM.get("odd_mode", "IDDAA_130")
    min_tr_odd = 1.42 if odd_mode == "IDDAA_142" else (1.05 if odd_mode == "GLOBAL" else 1.30)

    props_open = is_iddaa_prop_league_open(slug, lig_adi)
    is_uk_lig = any(k in str(lig_adi).upper() for k in ("PREMIER", "İSKOÇYA", "EFL"))
    is_hot_lig = any(k in str(lig_adi).upper() for k in ("SERIE B", "LA LIGA 2", "BREZİLYA", "ARJANTİN", "SÜPER LİG"))
    it2_boom = ("ita.2" in slug.lower()) or ("SERIE B" in str(lig_adi).upper())

    real_cor = safe_float(fr.get("real_cor_sum"), 9.5)
    sh_sum = safe_float(fr.get("sh_sum"), 21.5)
    is_blowout = bool(fr.get("is_blowout"))
    inj_wing = bool(fr.get("inj_wing"))
    lam_tot = safe_float(m4.get("lam_h"), 1.35) + safe_float(m4.get("lam_a"), 1.15)

    cor_line = "9.5 Korner Üst" if is_uk_lig else "8.5 Korner Üst"
    cor_prob_main = safe_int(spec.get("COR_O95" if is_uk_lig else "COR_O85"), 60)
    p_cor_u95 = safe_int(spec.get("COR_U95"), 48)
    p_cor_u85 = safe_int(spec.get("COR_U85"), 36)
    card_line = "4.5 Kart Üst" if is_hot_lig else "3.5 Kart Üst"
    card_prob_main = safe_int(spec.get("CARD_O45" if is_hot_lig else "CARD_O35"), 58)
    p_card_u45 = safe_int(spec.get("CARD_U45"), 62)

    p_o15, p_o25, p_u25 = safe_int(spec.get("MS_O15"), 74), safe_int(spec.get("MS_O25"), 55), safe_int(spec.get("MS_U25"), 45)
    p_u35, p_o35 = safe_int(spec.get("MS_U35"), 68), safe_int(spec.get("MS_O35"), 32)
    p_btts_yes, p_btts_no = safe_int(spec.get("BTTS_YES"), 52), safe_int(spec.get("BTTS_NO"), 48)
    p_ht_u15, p_ht_o05 = safe_int(spec.get("HT_U15"), 70), safe_int(spec.get("HT_O05"), 68)
    p_win_o15 = safe_int(spec.get("WIN1_O15" if is_home_fav else "WIN2_O15"), 52)

    o25_b = safe_float(af.get("o25_odd") or oa.get("o25_dec"), 0.0)
    u25_b = safe_float(af.get("u25_odd") or oa.get("u25_dec"), 0.0)
    ou_trap = (o25_b > 1.05 and u25_b > 1.05 and abs(o25_b - u25_b) >= 0.22 and ((p_o25 >= 54 and o25_b > u25_b) or (p_u25 >= 54 and u25_b > o25_b)))
    ou_trap_pen = -10 if ou_trap else 0

    curr_ctx = {"cor": real_cor, "ou": ou_val}
    candidates = []

    if props_open:
        if cor_prob_main >= 65 and real_cor >= 10.3 and not inj_wing:
            u_co = cor_prob_main + 16 + compute_conditional_twin_memory_bonus("COR_O", curr_ctx, lig_adi)
            candidates.append((u_co, f"🚩 {cor_line}", cor_prob_main))
        if not is_uk_lig and real_cor <= 7.0 and p_cor_u95 >= 78 and sh_sum <= 19.0 and not is_blowout:
            cor_u_lbl = "🚩 8.5 Korner Alt" if (real_cor <= 6.2 and p_cor_u85 >= 76) else "🚩 9.5 Korner Alt"
            cor_u_pr = p_cor_u85 if "8.5" in cor_u_lbl else p_cor_u95
            candidates.append((cor_u_pr + 5 + compute_conditional_twin_memory_bonus("COR_U", curr_ctx, lig_adi), cor_u_lbl, cor_u_pr))
        if card_prob_main >= 64 and not is_blowout:
            candidates.append((card_prob_main + 12 + compute_conditional_twin_memory_bonus("CARD_O", curr_ctx, lig_adi), f"🟨 {card_line}", card_prob_main))
        if is_blowout and p_card_u45 >= 76 and not is_hot_lig:
            candidates.append((p_card_u45 + 6, "🟨 4.5 Kart Alt", p_card_u45))

    if p_ht_u15 >= 70 and ou_val <= 2.75 and lam_tot <= 2.78:
        candidates.append((p_ht_u15 + 13 + (4 if it2_boom else 0) + compute_conditional_twin_memory_bonus("HT_U", curr_ctx, lig_adi), "İlk Yarı 1.5 Gol Alt", p_ht_u15))
    if p_u35 >= 71 and not it2_boom and ou_val <= 3.5 and not is_blowout:
        candidates.append((p_u35 + 11 + ou_trap_pen + compute_conditional_twin_memory_bonus("U35", curr_ctx, lig_adi), "Maç 3.5 Gol Alt", p_u35))
    if p_o15 >= 77 and ou_val <= 2.75:
        candidates.append((p_o15 + 10 + compute_conditional_twin_memory_bonus("O15", curr_ctx, lig_adi), "Maç 1.5 Gol Üst", p_o15))
    if p_btts_yes >= 61 and abs(fav_val) <= 210 and not is_blowout:
        candidates.append((p_btts_yes + 12 + compute_conditional_twin_memory_bonus("BTTS_YES", curr_ctx, lig_adi), "Karşılıklı Gol Var", p_btts_yes))
    if p_o25 >= 61 and lam_tot >= 2.72:
        candidates.append((p_o25 + 11 + ou_trap_pen + compute_conditional_twin_memory_bonus("O25", curr_ctx, lig_adi), "Maç 2.5 Gol Üst", p_o25))
    if p_u25 >= 56 and lam_tot <= 2.45:
        candidates.append((p_u25 + 10 + ou_trap_pen + compute_conditional_twin_memory_bonus("U25", curr_ctx, lig_adi), "Maç 2.5 Gol Alt", p_u25))
    if fav_val <= -175 and p_win_o15 >= 58:
        candidates.append((p_win_o15 + 13 + compute_conditional_twin_memory_bonus("WIN", curr_ctx, lig_adi), f"{fav_team} Kazanır & 1.5 Gol Üst", p_win_o15))
    if p_ht_o05 >= 68 and lam_tot >= 2.65:
        candidates.append((p_ht_o05 + 9, "İlk Yarı 0.5 Gol Üst", p_ht_o05))

    filtered_cands = []
    for u_sc, lbl, pr_v in candidates:
        tr_o, eu_o, has_eu = _estimate_iddaa_and_eu_odd(lbl, pr_v, r_d, is_home_fav)
        if tr_o >= min_tr_odd:
            val_b = 4 if (tr_o * (pr_v / 100.0) >= 1.03) else 0
            filtered_cands.append((u_sc + val_b, lbl, pr_v, tr_o, eu_o, has_eu))

    if not filtered_cands:
        safe_fallbacks = [
            (p_o25 + 13 + ou_trap_pen, "Maç 2.5 Gol Üst", p_o25),
            (p_btts_yes + 12, "Karşılıklı Gol Var", p_btts_yes),
            (p_u25 + 11 + ou_trap_pen, "Maç 2.5 Gol Alt", p_u25),
            (p_ht_u15 + 11, "İlk Yarı 1.5 Gol Alt", p_ht_u15),
            (p_win_o15 + 12, f"{fav_team} Kazanır & 1.5 Gol Üst", p_win_o15)
        ]
        if ou_val >= 3.5 or lam_tot >= 3.15:
            safe_fallbacks.append((p_o35 + 12 + ou_trap_pen, "Maç 3.5 Gol Üst", p_o35))
            safe_fallbacks.append((safe_int(spec.get("HT_O15"), 48) + 10, "İlk Yarı 1.5 Gol Üst", safe_int(spec.get("HT_O15"), 48)))
        if props_open:
            if cor_prob_main >= 64 and real_cor >= 10.2 and not inj_wing:
                safe_fallbacks.insert(0, (cor_prob_main + 15, f"🚩 {cor_line}", cor_prob_main))
            elif not is_uk_lig and p_cor_u95 >= 76 and real_cor <= 7.0 and sh_sum <= 19.5 and not is_blowout:
                safe_fallbacks.append((p_cor_u95 + 9, "🚩 9.5 Korner Alt", p_cor_u95))
            if card_prob_main >= 63:
                safe_fallbacks.append((card_prob_main + 12, f"🟨 {card_line}", card_prob_main))

        for u_sc, lbl, pr_v in safe_fallbacks:
            tr_o, eu_o, has_eu = _estimate_iddaa_and_eu_odd(lbl, pr_v, r_d, is_home_fav)
            if tr_o >= min_tr_odd:
                filtered_cands.append((u_sc, lbl, pr_v, tr_o, eu_o, has_eu))
        if not filtered_cands:
            u_sc, lbl, pr_v = max(safe_fallbacks, key=lambda x: x[0])
            tr_o, eu_o, has_eu = _estimate_iddaa_and_eu_odd(lbl, pr_v, r_d, is_home_fav)
            filtered_cands.append((u_sc - 6, lbl, pr_v, tr_o, eu_o, has_eu))

    filtered_cands.sort(key=lambda x: x[0], reverse=True)
    best_u, best_lbl, best_raw_p, best_tr_o, best_eu_o, best_has_eu = filtered_cands[0]
    mkt_t = _classify_pick_market_type(best_lbl)
    calib_conf = _calibrate_decision_score_by_market_and_band(best_raw_p, mkt_t, max_allowed_conf=90)

    bm_cnt = safe_int(oa.get("bm_count"), 0)
    cons_b = 4 if (bm_cnt >= 35 and safe_float(oa.get("reg_spread"), 9.0) <= 3.2) else 0
    val_tag = "💎VAL" if (best_tr_o * (calib_conf / 100.0) >= 1.02 and best_tr_o >= min_tr_odd) else ("✅" if best_tr_o >= min_tr_odd else f"⚠️İddaaDüşük:@{best_tr_o:.2f}")
    odd_ui = f"🇹🇷@{best_tr_o:.2f}{val_tag}" + (f"(Avr:@{best_eu_o:.2f})" if best_has_eu else "")
    if val_tag.startswith("⚠️"):
        odd_ui = val_tag

    dec_score = max(55, min(108, best_u + cons_b + (1 if r_d.get("official") else 0) + (-8 if val_tag.startswith("⚠️") else 0)))
    side_picks = []
    for _, s_lbl, s_pr, s_tro, _, _ in filtered_cands[1:4]:
        if s_lbl != best_lbl and s_tro >= 1.25:
            side_picks.append(f"{s_lbl} (%{s_pr})")
    if not side_picks:
        side_picks.append(f"⚽ 1.5 Gol Üst (%{p_o15})" if "1.5" not in best_lbl else f"🛡️ 3.5 Alt (%{p_u35})")
    prop_str = "2.T: " + " | ".join(side_picks[:3])

    q_tag = "🟢Q:A" if r_d.get("official") else "🔵Q:B"
    p11_warn = f"|⚠️1-1:%{m4.get('p11',12)}" if (m4.get("p11", 0) >= 14 and "Alt" in best_lbl) else ""
    patron_ui = f"[{q_tag}|👑DC:{m4['top_score']}(%{m4['top_prob']}){p11_warn}|P:%{calib_conf}/U:{dec_score}|λ:{m4['lam_h']}-{m4['lam_a']}|2.5A:%{p_u25}|KGY:%{p_btts_no}|Kor:{fr['est_cor_cnt']}(%{cor_prob_main})|{odd_ui}]"
    return best_lbl, prop_str, calib_conf, dec_score, patron_ui, ou_trap, (o25_b - u25_b if (o25_b and u25_b) else 0.0)
# ==================== MODÜL 4A/6: MAÇ ÖNÜ KİLİT, SONUÇ DOĞRULAMA VE CANLI PUSU MOTORU ====================
def evaluate_pick_settled(pick_str, h_sc, a_sc, h_name="", a_name="", tot_cor=0, tot_cards=0, ht_h=None, ht_a=None):
    s = str(pick_str or "").strip()
    su = s.upper()
    tot_g = h_sc + a_sc
    if "KORNER ÜST" in su or "KORÜ" in su:
        ln = 9.5 if "9.5" in su else (7.5 if "7.5" in su else 8.5)
        return (tot_cor > ln) if tot_cor > 0 else None
    if "KORNER ALT" in su or "KORA" in su:
        ln = 8.5 if "8.5" in su else 9.5
        return (tot_cor < ln) if tot_cor > 0 else None
    if "KART ÜST" in su or "KARTÜ" in su:
        ln = 4.5 if "4.5" in su else 3.5
        return (tot_cards > ln) if tot_cards >= 0 else None
    if "KART ALT" in su or "KARTA" in su:
        ln = 3.5 if "3.5" in su else 4.5
        return (tot_cards < ln) if tot_cards >= 0 else None
    if "İLK YARI 1.5 GOL ALT" in su or "İY 1.5A" in su:
        return ((ht_h + ht_a) <= 1) if (ht_h is not None and ht_a is not None) else (True if tot_g <= 1 else None)
    if "İLK YARI 1.5 GOL ÜST" in su or "İY 1.5Ü" in su:
        return ((ht_h + ht_a) >= 2) if (ht_h is not None and ht_a is not None) else (False if tot_g <= 1 else None)
    if "İLK YARI 0.5 GOL ÜST" in su or "İY 0.5Ü" in su:
        return ((ht_h + ht_a) >= 1) if (ht_h is not None and ht_a is not None) else (False if tot_g == 0 else None)
    if "KARŞILIKLI GOL VAR" in su or "KG VAR" in su:
        return (h_sc >= 1 and a_sc >= 1)
    if "KARŞILIKLI GOL YOK" in su or "KG YOK" in su:
        return not (h_sc >= 1 and a_sc >= 1)
    if "KAZANIR & 1.5 GOL ÜST" in su:
        is_h_pick = bool(h_name and _norm_team_key(h_name) in _norm_team_key(s))
        return ((h_sc > a_sc) if is_h_pick else (a_sc > h_sc)) and (tot_g >= 2)
    if "3.5 GOL ALT" in su or "3.5A" in su:
        return tot_g <= 3
    if "3.5 GOL ÜST" in su or "3.5Ü" in su:
        return tot_g >= 4
    if "2.5 GOL ALT" in su or "2.5A" in su:
        return tot_g <= 2
    if "2.5 GOL ÜST" in su or "2.5Ü" in su:
        return tot_g >= 3
    if "1.5 GOL ÜST" in su or "1.5Ü" in su:
        return tot_g >= 2
    return tot_g >= 2

def build_pre_match_prediction(ev_id, match_title, h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, fav_abbr, fav_val, ou_val, odd_str, state, kademe, r_data, lig_adi=""):
    r_d = r_data or {}
    is_home_fav = (fav_abbr != a_abbr)
    fav_team = h_name if is_home_fav else a_name
    h_info, a_info = r_d.get("h") or {}, r_d.get("a") or {}
    h_tac, a_tac = str(h_info.get("tac") or "4-2-3-1"), str(a_info.get("tac") or "4-2-3-1")
    is_off = bool(r_d.get("official"))

    m4 = compute_dixon_coles_matrix(h_name, a_name, h_mom, a_mom, fav_val, ou_val, is_home_fav, r_d)
    fr = compute_friction_physics(h_name, a_name, h_tac, a_tac, h_mom, a_mom, fav_val, ou_val, kademe, r_d, lig_adi, is_home_fav)
    spec = compute_full_spectrum_28_markets(m4, fr)
    pick_lbl, prop_str, conf_v, dec_sc, patron_ui, ou_trap, ou_diff = _select_best_autonomous_market(
        h_name, a_name, fav_team, is_home_fav, fav_val, ou_val, spec, m4, fr, r_d, lig_adi
    )

    locked_map = MEM.setdefault("locked_picks", {})
    evo_str = "⏳ÇekXI"
    prev_l = locked_map.get(str(ev_id))
    if state in ("in", "post") and isinstance(prev_l, dict) and prev_l.get("pick"):
        pick_lbl = prev_l["pick"]
        conf_v = safe_int(prev_l.get("conf"), conf_v)
        evo_str = prev_l.get("evo", "✅Sabit")
    else:
        if isinstance(prev_l, dict) and prev_l.get("ver") == MODEL_VERSION:
            old_p = prev_l.get("pick", pick_lbl)
            if is_off and not prev_l.get("is_off"):
                evo_str = "✅Sabit" if old_p == pick_lbl else f"🔄 {old_p} ➔ ✅ {pick_lbl}"
            elif is_off:
                evo_str = prev_l.get("evo", "✅Sabit")
        elif is_off:
            evo_str = "✅Sabit"
        locked_map[str(ev_id)] = {"pick": pick_lbl, "conf": conf_v, "is_off": is_off, "evo": evo_str, "ver": MODEL_VERSION}

    oa = r_d.get("odds_api") or {}
    bm_cnt = safe_int(oa.get("bm_count"), 0)
    pin_sh = safe_float(oa.get("pin_sharp_h" if is_home_fav else "pin_sharp_a"), 0.0)
    odd_enrich = [odd_str, fr.get("tags_str", "")]
    if bm_cnt >= 10 and safe_float(oa.get("reg_spread"), 9.0) <= 3.5:
        odd_enrich.append(f"🌍Mutabakat({bm_cnt}Büro)")
    if pin_sh <= -1.8:
        odd_enrich.append(f"⚠️PinTers({pin_sh:+.1f}%p)")
    if ou_trap:
        odd_enrich.append(f"🚨BÜRO_TUZAĞI(Δ@{abs(ou_diff):.2f})")
    if is_off:
        odd_enrich.append("✅ÇekKadro(+1p)")

    m4_out = {
        "lam_h": m4["lam_h"], "lam_a": m4["lam_a"], "top_score": m4["top_score"], "top_prob": m4["top_prob"],
        "p11": m4["p11"], "d_weak": m4["d_weak"], "decision_score": dec_sc,
        "patron_sim_ui": patron_ui, "spectrum": spec, "friction": fr
    }
    return pick_lbl, prop_str, conf_v, evo_str, " ".join(x for x in odd_enrich if x), m4_out

def analyze_live_pusu_engine(ev_id, match_title, min_now, h_sc, a_sc, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, cards, h_poss, is_home_fav, fav_val, pre_conf, m4_d):
    snaps = MEM.setdefault("live_snapshots", {})
    sigs = MEM.setdefault("live_signals", {})
    tot_sh, tot_sot, tot_cor, tot_g = h_sh + a_sh, h_sot + a_sot, h_cor + a_cor, h_sc + a_sc
    prev = snaps.get(str(ev_id))
    if not prev:
        snaps[str(ev_id)] = {"min": min_now, "sh": tot_sh, "sot": tot_sot, "cor": tot_cor}
        delta_txt = ""
    else:
        dm = max(1, min_now - safe_int(prev.get("min"), min_now))
        delta_txt = f"Δ({prev['min']}'->{min_now}'):+{max(0,tot_sh-prev['sh'])}/{max(0,tot_sot-prev['sot'])}Ş,+{max(0,tot_cor-prev['cor'])}K" if dm >= 3 else ""

    rem_ratio = max(0.05, (92.0 - min_now) / 90.0)
    lam_tot = safe_float((m4_d or {}).get("lam_h"), 1.35) + safe_float((m4_d or {}).get("lam_a"), 1.15)
    tempo_boost = min(1.65, max(0.65, ((tot_sh * 0.08 + tot_sot * 0.22 + tot_cor * 0.06) / max(0.18, min_now / 90.0)) / 2.6))
    rem_xg = round(max(0.08, lam_tot * rem_ratio * tempo_boost), 2)
    goal_prob = int(round((1.0 - math.exp(-rem_xg)) * 100.0))

    fav_losing_or_tied = (h_sc <= a_sc) if is_home_fav else (a_sc <= h_sc)
    pressure = int(min(99, max(18, goal_prob * 0.72 + tot_sot * 3.2 + tot_cor * 1.8 + (12 if (fav_losing_or_tied and fav_val <= -145 and min_now >= 40) else 0))))
    fav_lock = bool(fav_losing_or_tied and min_now >= 42 and min_now <= 78 and pressure >= 65 and rem_xg >= 0.85)

    if str(ev_id) not in sigs and 35 <= min_now <= 76 and pressure >= 74 and goal_prob >= 68 and tot_g <= 3:
        sigs[str(ev_id)] = {"target_line": tot_g + 0.5, "start_goals": tot_g, "min_trig": min_now, "settled": False, "won": False, "title": match_title}
    if str(ev_id) in sigs and not sigs[str(ev_id)].get("settled") and tot_g > sigs[str(ev_id)]["start_goals"]:
        sigs[str(ev_id)]["settled"] = True
        sigs[str(ev_id)]["won"] = True

    return pressure, rem_xg, goal_prob, delta_txt, fav_lock
# ==================== MODÜL 4B/6: ESPN ÇOKLU LİG TARAYICI, KARNE VE TELEMETRİ MOTORU ====================
TRACKED_LEAGUES = [
    ("tur.1", "TR1", "TÜRKİYE SÜPER LİG", 1),
    ("uefa.champions", "UCL", "🏆 UEFA ŞAMPİYONLAR LİGİ", 1),
    ("uefa.europa", "UEL", "🏆 UEFA AVRUPA LİGİ", 1),
    ("uefa.europa.conf", "UECL", "🏆 UEFA KONFERANS LİGİ", 1),
    ("eng.1", "ENG1", "İNGİLTERE PREMIER LEAGUE", 1),
    ("esp.1", "ESP1", "İSPANYA LA LIGA", 1),
    ("ita.1", "ITA1", "İTALYA SERIE A", 1),
    ("ger.1", "GER1", "ALMANYA BUNDESLIGA", 1),
    ("fra.1", "FRA1", "FRANSA LIGUE 1", 1),
    ("ned.1", "NED1", "HOLLANDA EREDIVISIE", 2),
    ("por.1", "POR1", "PORTEKİZ PRIMEIRA LIGA", 2),
    ("sco.1", "SCO1", "İSKOÇYA PREMIERSHIP", 2),
    ("eng.2", "ENG2", "İNGİLTERE CHAMPIONSHIP", 2),
    ("ita.2", "ITA2", "İTALYA SERIE B", 2),
    ("esp.2", "ESP2", "İSPANYA LA LIGA 2", 2),
    ("ger.2", "GER2", "ALMANYA 2. BUNDESLIGA", 2),
    ("fra.2", "FRA2", "FRANSA LIGUE 2", 2),
    ("ned.2", "NED2", "HOLLANDA EERSTE DIVISIE", 2),
    ("tur.2", "TR2", "TÜRKİYE 1. LİG", 2),
    ("bra.1", "BRA1", "BREZİLYA SERIE A", 2),
    ("arg.1", "ARG1", "ARJANTİN LIGA PRO", 2),
    ("mex.1", "MEX1", "MEKSİKA LIGA MX", 2)
]

def format_form_badges(form_str):
    out = []
    for ch in str(form_str or "WDLWD")[-5:]:
        c = ch.upper()
        if c == "W": out.append("<span style='color:#56d364;font-weight:800;'>G</span>")
        elif c == "D": out.append("<span style='color:#e3b341;font-weight:800;'>B</span>")
        else: out.append("<span style='color:#ff7b72;font-weight:800;'>M</span>")
    return "".join(out)

def _calc_form_mom(form_str, rec_str=""):
    s = str(form_str or "").upper()
    pts = sum(3 if c == "W" else (1 if c == "D" else 0) for c in s[-5:])
    base_m = int(round((pts / 15.0) * 78.0 + 14.0)) if s else 52
    if rec_str and "-" in str(rec_str):
        parts = [safe_int(x, 0) for x in str(rec_str).split("-")[:3]]
        if len(parts) == 3 and sum(parts) > 0:
            w_r = (parts[0] * 3 + parts[1]) / float(sum(parts) * 3)
            base_m = int(round(base_m * 0.68 + (w_r * 85.0 + 10.0) * 0.32))
    return max(12, min(94, base_m))

def compute_ledger_summary():
    fin_map = MEM.get("finished_cache", {})
    w_cnt, t_cnt, ak_w, ak_t = safe_int(MEM.get("base_w"), 0), safe_int(MEM.get("base_t"), 0), safe_int(MEM.get("base_ak_w"), 0), safe_int(MEM.get("base_ak_t"), 0)
    for m in fin_map.values():
        if isinstance(m, dict) and m.get("won") in (True, False):
            t_cnt += 1
            if m.get("won"): w_cnt += 1
            if safe_int(m.get("conf"), 0) >= 78:
                ak_t += 1
                if m.get("won"): ak_w += 1
    sigs = MEM.get("live_signals", {})
    lp_w = sum(1 for v in sigs.values() if isinstance(v, dict) and v.get("settled") and v.get("won"))
    lp_t = sum(1 for v in sigs.values() if isinstance(v, dict) and v.get("settled"))
    lp_act = sum(1 for v in sigs.values() if isinstance(v, dict) and not v.get("settled"))
    pct_m = int(round((w_cnt / max(1, t_cnt)) * 100)) if t_cnt else 0
    pct_ak = int(round((ak_w / max(1, ak_t)) * 100)) if ak_t else 0
    pct_lp = int(round((lp_w / max(1, lp_t)) * 100)) if lp_t else 0
    return {
        "w": w_cnt, "t": t_cnt, "pct": pct_m, "main_str": f"{w_cnt}/{t_cnt} (%{pct_m})",
        "ak_str": f"{ak_w}/{ak_t} (%{pct_ak})", "lp_str": f"{lp_w}/{lp_t} (%{pct_lp} | Aktif:{lp_act})",
        "mini_hdr": f"Karne:{w_cnt}/{t_cnt}(%{pct_m}) AK:{ak_w}/{ak_t}(%{pct_ak}) CanlıPusu:{lp_w}/{lp_t}(%{pct_lp}|Aktif:{lp_act})"
    }

def _fetch_espn_league_events(lg_tuple):
    slug, short_c, full_nm, kad = lg_tuple
    now_tr = datetime.now(TR_TZ)
    d_range = f"{(now_tr - timedelta(days=1)).strftime('%Y%m%d')}-{(now_tr + timedelta(days=1)).strftime('%Y%m%d')}"
    try:
        r = HTTP_SESSION.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={d_range}&limit=100", timeout=3.2)
        if r.status_code == 200:
            return slug, short_c, full_nm, kad, (r.json().get("events") or [])
    except Exception:
        pass
    return slug, short_c, full_nm, kad, []

def _dec_to_am(dec_v):
    d = safe_float(dec_v, 0.0)
    if d <= 1.02: return -125
    if d >= 2.00: return int(round((d - 1.0) * 100))
    return int(round(-100.0 / (d - 1.0)))
def fetch_bulletin_full(force_refresh=False):
    snap = MEM.setdefault("bulletin_snap", {"ts": 0.0, "live": [], "up": [], "fin": [], "mini": []})
    now_ts = time.time()
    if not force_refresh and snap.get("up") and (now_ts - safe_float(snap.get("ts"), 0.0) < 42.0):
        return snap["live"], snap["up"], snap["fin"], snap["mini"]

    now_tr = datetime.now(TR_TZ)
    oa_map = _fetch_odds_api_global_map()
    with ThreadPoolExecutor(max_workers=12) as ex:
        lg_batches = list(ex.map(_fetch_espn_league_events, TRACKED_LEAGUES))

    raw_items, roster_jobs = [], []
    open_odds_map = MEM.setdefault("opening_odds", {})

    for slug, short_c, full_nm, kad, events in lg_batches:
        for ev in events:
            ev_id = str(ev.get("id") or "")
            comp = (ev.get("competitions") or [{}])[0]
            st_obj = (comp.get("status") or {}).get("type") or {}
            state = str(st_obj.get("state") or "pre").lower()
            clk_disp = str(st_obj.get("shortDetail") or st_obj.get("detail") or "")
            comps = comp.get("competitors") or []
            if len(comps) < 2:
                continue
            c_h = next((x for x in comps if x.get("homeAway") == "home"), comps[0])
            c_a = next((x for x in comps if x.get("homeAway") == "away"), comps[1])
            t_h, t_a = c_h.get("team") or {}, c_a.get("team") or {}
            h_name = str(t_h.get("shortDisplayName") or t_h.get("displayName") or "Home")
            a_name = str(t_a.get("shortDisplayName") or t_a.get("displayName") or "Away")
            h_abbr = str(t_h.get("abbreviation") or h_name[:3]).upper()
            a_abbr = str(t_a.get("abbreviation") or a_name[:3]).upper()
            h_tid, a_tid = str(t_h.get("id") or ""), str(t_a.get("id") or "")

            try:
                ev_dt = datetime.fromisoformat(str(ev.get("date") or "").replace("Z", "+00:00")).astimezone(TR_TZ)
            except Exception:
                ev_dt = now_tr
            mins_to_ko = (ev_dt - now_tr).total_seconds() / 60.0
            if state == "pre" and (mins_to_ko < -25 or mins_to_ko > 1560):
                continue
            if state == "post" and mins_to_ko < -1800:
                continue

            h_form = str(c_h.get("form") or "WDWLW")
            a_form = str(c_a.get("form") or "LDWDL")
            h_rec = str(((c_h.get("records") or [{}])[0]).get("summary") or "")
            a_rec = str(((c_a.get("records") or [{}])[0]).get("summary") or "")
            h_mom, a_mom = _calc_form_mom(h_form, h_rec), _calc_form_mom(a_form, a_rec)

            odds_arr = comp.get("odds") or []
            od0 = odds_arr[0] if odds_arr and isinstance(odds_arr[0], dict) else {}
            ou_val = safe_float(od0.get("overUnder"), 2.5)
            det_str = str(od0.get("details") or "").strip()
            oa_m = _match_in_odds_api(h_name, a_name, oa_map)

            if det_str and " " in det_str:
                pts_d = det_str.split()
                fav_abbr = pts_d[0].upper()
                fav_val = safe_int(pts_d[-1], -130)
                odd_str = f"{fav_abbr} {fav_val:+d}"
            elif oa_m.get("dec_h") and oa_m.get("dec_a"):
                if oa_m["dec_h"] <= oa_m["dec_a"]:
                    fav_abbr, fav_val = h_abbr, _dec_to_am(oa_m["dec_h"])
                else:
                    fav_abbr, fav_val = a_abbr, _dec_to_am(oa_m["dec_a"])
                odd_str = f"{fav_abbr} {fav_val:+d}"
            else:
                fav_abbr = h_abbr if h_mom >= a_mom else a_abbr
                fav_val = -135 - abs(h_mom - a_mom)
                odd_str = f"{fav_abbr} {fav_val:+d}(ProxyOran)"

            if oa_m.get("o25_dec") and oa_m.get("u25_dec") and oa_m["o25_dec"] < 1.58:
                ou_val = max(ou_val, 3.5)

            op_rec = open_odds_map.get(ev_id)
            if not op_rec:
                open_odds_map[ev_id] = {"fav_val": fav_val, "ou": ou_val}
            else:
                dv = fav_val - safe_int(op_rec.get("fav_val"), fav_val)
                if abs(dv) >= 10:
                    p_sh = round(-dv * 0.16, 1)
                    odd_str += f" {'🔥' if dv < 0 else '⚠️'}Δ{dv:+d}({p_sh:+.1f}%p)"
                if ou_val > safe_float(op_rec.get("ou"), ou_val) + 0.4:
                    odd_str += f" 💥TG↑({op_rec['ou']}->{ou_val})"

            m_title = f"{h_name} vs {a_name}"
            raw_items.append({
                "slug": slug, "short_c": short_c, "lig": full_nm, "kademe": kad, "ev_id": ev_id,
                "title": m_title, "h_name": h_name, "a_name": a_name, "h_abbr": h_abbr, "a_abbr": a_abbr,
                "h_tid": h_tid, "a_tid": a_tid, "ev_dt": ev_dt, "mins_to_ko": mins_to_ko,
                "state": state, "clk": clk_disp, "c_h": c_h, "c_a": c_a,
                "h_form": h_form, "a_form": a_form, "h_mom": h_mom, "a_mom": a_mom,
                "fav_abbr": fav_abbr, "fav_val": fav_val, "ou": ou_val, "odd_str": odd_str
            })
            roster_jobs.append((slug, ev_id, m_title, h_name, a_name, h_mom, a_mom, odd_str, state, kad, fav_abbr, fav_val, a_abbr, mins_to_ko, h_tid, a_tid))
    roster_map = {}
    if roster_jobs:
        with ThreadPoolExecutor(max_workers=12) as ex:
            for m_t, r_res in ex.map(fetch_and_analyze_roster, roster_jobs):
                roster_map[m_t] = r_res

    live_list, up_list, fin_list = [], [], []
    fin_cache = MEM.setdefault("finished_cache", {})
    sigs_map = MEM.setdefault("live_signals", {})

    def _short_pick(s):
        return (str(s or "").replace("Maç 3.5 Gol Alt", "3.5A").replace("Maç 2.5 Gol Alt", "2.5A")
                .replace("Maç 2.5 Gol Üst", "2.5Ü").replace("Maç 1.5 Gol Üst", "1.5Ü")
                .replace("İlk Yarı 1.5 Gol Alt", "İY 1.5A").replace("İlk Yarı 0.5 Gol Üst", "İY 0.5Ü")
                .replace("Karşılıklı Gol Var", "KG Var").replace("Karşılıklı Gol Yok", "KG Yok")
                .replace("Korner Üst", "KorÜ").replace("Korner Alt", "KorA")
                .replace("Kart Üst", "KartÜ").replace("Kart Alt", "KartA"))

    for it in raw_items:
        r_d = dict(roster_map.get(it["title"]) or {})
        r_d["slug"] = it["slug"]
        h_info, a_info = r_d.get("h") or {}, r_d.get("a") or {}
        h_tac, a_tac = str(h_info.get("tac") or "4-2-3-1"), str(a_info.get("tac") or "4-2-3-1")
        is_off = bool(r_d.get("official"))

        pick_lbl, prop_str, conf_v, evo_str, odd_full, m4_out = build_pre_match_prediction(
            it["ev_id"], it["title"], it["h_name"], it["a_name"], it["h_abbr"], it["a_abbr"],
            it["h_mom"], it["a_mom"], it["fav_abbr"], it["fav_val"], it["ou"], it["odd_str"],
            it["state"], it["kademe"], r_d, it["lig"]
        )
        t_hm = it["ev_dt"].strftime("%H:%M")
        t_full = it["ev_dt"].strftime("%d.%m %H:%M")
        bs = r_d.get("box_stats") or {}
        h_sc, a_sc = safe_int(it["c_h"].get("score"), 0), safe_int(it["c_a"].get("score"), 0)
        h_sh = max(get_stat(it["c_h"], ["totalShots", "shotsSummary"]), safe_int(bs.get("h_sh"), 0))
        a_sh = max(get_stat(it["c_a"], ["totalShots", "shotsSummary"]), safe_int(bs.get("a_sh"), 0))
        h_sot = max(get_stat(it["c_h"], ["shotsOnTarget", "onGoal"]), safe_int(bs.get("h_sot"), 0))
        a_sot = max(get_stat(it["c_a"], ["shotsOnTarget", "onGoal"]), safe_int(bs.get("a_sot"), 0))
        h_cor = max(get_stat(it["c_h"], ["wonCorners", "corners"]), safe_int(bs.get("h_cor"), 0))
        a_cor = max(get_stat(it["c_a"], ["wonCorners", "corners"]), safe_int(bs.get("a_cor"), 0))
        cards = max(safe_int(r_d.get("live_cards"), 0), get_stat(it["c_h"], ["yellowCards"]) + get_stat(it["c_a"], ["yellowCards"]))
        h_poss = get_stat(it["c_h"], ["possessionPct", "possession"]) or 50

        base_obj = {
            "ev_id": it["ev_id"], "slug": it["slug"], "short_c": it["short_c"], "lig": it["lig"],
            "kademe": it["kademe"], "title": it["title"], "h_name": it["h_name"], "a_name": it["a_name"],
            "h_form": it["h_form"], "a_form": it["a_form"], "h_mom": it["h_mom"], "a_mom": it["a_mom"],
            "h_tac": h_tac, "a_tac": a_tac, "is_off": is_off, "saat": t_hm, "tarih_saat": t_full,
            "ev_ts": it["ev_dt"].timestamp(), "odd": odd_full, "ou": it["ou"],
            "pick": pick_lbl, "prop": prop_str, "conf": conf_v, "evo": evo_str, "m4": m4_out, "r_data": r_d
        }

        if it["state"] == "in":
            min_now, add_m = parse_live_clock(it["clk"])
            clk_lbl = f"{min_now}'+{add_m}'" if add_m > 0 else f"{min_now}'"
            pr_s, r_xg, g_pr, d_txt, f_lck = analyze_live_pusu_engine(
                it["ev_id"], it["title"], min_now, h_sc, a_sc, h_sh, a_sh, h_sot, a_sot,
                h_cor, a_cor, cards, h_poss, (it["fav_abbr"] != it["a_abbr"]), it["fav_val"], conf_v, m4_out
            )
            base_obj.update({
                "clk": clk_lbl, "min_now": min_now, "h_sc": h_sc, "a_sc": a_sc,
                "h_sh": h_sh, "a_sh": a_sh, "h_sot": h_sot, "a_sot": a_sot,
                "h_cor": h_cor, "a_cor": a_cor, "cards": cards, "h_poss": h_poss,
                "pressure": pr_s, "rem_xg": r_xg, "goal_prob": g_pr, "delta_txt": d_txt, "fav_lock": f_lck
            })
            live_list.append(base_obj)
        elif it["state"] == "pre":
            up_list.append(base_obj)
        elif it["state"] == "post":
            if it["ev_id"] in sigs_map and not sigs_map[it["ev_id"]].get("settled"):
                sigs_map[it["ev_id"]]["settled"] = True
                sigs_map[it["ev_id"]]["won"] = ((h_sc + a_sc) > sigs_map[it["ev_id"]]["start_goals"])
            af_fx = r_d.get("af_fx") or {}
            ht_h = af_fx.get("ht_home") if "ht_home" in af_fx else None
            ht_a = af_fx.get("ht_away") if "ht_away" in af_fx else None
            won_v = evaluate_pick_settled(pick_lbl, h_sc, a_sc, it["h_name"], it["a_name"], h_cor + a_cor, cards, ht_h, ht_a)
            if won_v is not None:
                ht_tag = f"(İY:{ht_h}-{ht_a})" if (ht_h is not None and ht_a is not None) else ""
                fin_rec = {
                    "ev_id": it["ev_id"], "lig": it["lig"], "title": it["title"],
                    "h_name": it["h_name"], "a_name": it["a_name"], "h_sc": h_sc, "a_sc": a_sc,
                    "ht_tag": ht_tag, "h_sh": h_sh, "a_sh": a_sh, "h_sot": h_sot, "a_sot": a_sot,
                    "h_cor": h_cor, "a_cor": a_cor, "tot_cor": h_cor + a_cor, "cards": cards,
                    "pick": pick_lbl, "short_pick": _short_pick(pick_lbl), "conf": conf_v,
                    "won": bool(won_v), "sim": m4_out["top_score"], "ts": it["ev_dt"].timestamp()
                }
                fin_cache[it["ev_id"]] = fin_rec
                fin_list.append(fin_rec)

    live_list.sort(key=lambda x: x["pressure"], reverse=True)
    up_list.sort(key=lambda x: (x["ev_ts"], -safe_int((x.get("m4") or {}).get("decision_score"), x["conf"])))
    all_fin = sorted([v for v in fin_cache.values() if isinstance(v, dict) and "won" in v], key=lambda x: safe_float(x.get("ts"), 0.0), reverse=True)

    ldg = compute_ledger_summary()
    mini_lines = [f"⚡ DP-MİNİ M5.1[{MEM.get('odd_mode','IDDAA_130')}] [{now_tr.strftime('%Y%m%d %H:%M')}] {MEM.get('sb_status','')} {ldg['mini_hdr']}"]
    for lm in live_list:
        d_s = f"|{lm['delta_txt']}" if lm.get("delta_txt") else ""
        fl_s = "|💎FavKilitli->Pusu" if lm.get("fav_lock") else ""
        mini_lines.append(f"CANLI|{lm['clk']}|🔥%{lm['pressure']}|{lm['h_name']} {lm['h_sc']}-{lm['a_sc']} {lm['a_name']}|Şut:{lm['h_sh']}({lm['h_sot']})-{lm['a_sh']}({lm['a_sot']})|Kor:{lm['h_cor']}-{lm['a_cor']}|Kart:{lm['cards']}|Top:%{lm['h_poss']}{d_s}|⚡KalanxG:{lm['rem_xg']}(Gol:%{lm['goal_prob']})|📈CanlıOranAktif{fl_s}|Önü:{_short_pick(lm['pick'])}|Yan:{_short_pick(lm['prop'])}|{lm['m4']['patron_sim_ui']}")
    for um in up_list[:40]:
        sp_d = um["m4"]["spectrum"]
        lg_lbl = um["lig"] if um["kademe"] == 1 and "UEFA" in um["lig"] else um["short_c"]
        kd_s = f"✅Kadro({um['h_tac']}v{um['a_tac']})" if um["is_off"] else "⏳ÇekXI"
        mini_lines.append(f"ÖNÜ|{um['tarih_saat']}|{lg_lbl}|{um['title']}|%{um['conf']}|{kd_s}|Mom:{um['h_mom']}-{um['a_mom']}|{_short_pick(um['odd'])}|TG:{um['ou']} [2.5A:%{sp_d['MS_U25']}|3.5A:%{sp_d['MS_U35']}|KGY:%{sp_d['BTTS_NO']}|Dw:{um['m4']['d_weak']}] -> {_short_pick(um['pick'])} | Yan:{_short_pick(um['prop'])} {um['m4']['patron_sim_ui']}")
    for fm in all_fin[:25]:
        st_w = "✅KAZANDI" if fm["won"] else "❌KAYIP"
        mini_lines.append(f"BİTTİ|FT|{st_w}|{fm['h_name']} {fm['h_sc']}-{fm['a_sc']} {fm['a_name']}{fm.get('ht_tag','')}|Şut:{fm.get('h_sh',0)}({fm.get('h_sot',0)})-{fm.get('a_sh',0)}({fm.get('a_sot',0)})|Kor:{fm.get('h_cor',0)}-{fm.get('a_cor',0)}({fm.get('tot_cor',0)})|Kart:{fm.get('cards',0)}|Hedef:{fm.get('short_pick',fm['pick'])}(%{fm['conf']})|Sim:{fm.get('sim','1-1')}")

    save_persistent_store()
    snap.update({"ts": now_ts, "live": live_list, "up": up_list, "fin": all_fin[:40], "mini": mini_lines})
    return live_list, up_list, all_fin[:40], mini_lines
# ==================== MODÜL 5A/6: TAKTİK SAHA, 28 PAZAR MATRİSİ VE KOPYALAMA KUTUSU ====================
def _render_copy_button(text_payload, btn_label="📋 Telemetriyi Kopyala", key_id="cp_main"):
    b64_safe = json.dumps(str(text_payload or ""))
    html_code = f"""
    <div style="margin:4px 0;">
      <button id="{key_id}" style="width:100%;background:#238636;color:#fff;border:1px solid #2ea043;border-radius:7px;padding:8px 12px;font-weight:700;font-size:12.5px;cursor:pointer;">
        {btn_label}
      </button>
    </div>
    <script>
    const btn = document.getElementById("{key_id}");
    if (btn) {{
      btn.onclick = async () => {{
        const txt = {b64_safe};
        try {{
          await navigator.clipboard.writeText(txt);
          btn.innerText = "✅ Panoya Kopyalandı!";
          btn.style.background = "#1f6feb";
        }} catch (e) {{
          const ta = document.createElement("textarea");
          ta.value = txt; document.body.appendChild(ta); ta.select();
          document.execCommand("copy"); document.body.removeChild(ta);
          btn.innerText = "✅ Kopyalandı!";
        }}
        setTimeout(() => {{ btn.innerText = "{btn_label}"; btn.style.background = "#238636"; }}, 2200);
      }};
    }}
    </script>
    """
    components.html(html_code, height=46)

def render_tactical_pitch_html(h_name, a_name, h_info, a_info):
    def _parse_lines(tac_str, starters, is_away=False):
        nums = [safe_int(x, 0) for x in str(tac_str or "4-2-3-1").split("-") if safe_int(x, 0) > 0]
        if sum(nums) != 10:
            nums = [4, 2, 3, 1]
        st_list = list(starters or [])[:11]
        while len(st_list) < 11:
            st_list.append({"num": str(len(st_list) + 1), "name": f"XI-{len(st_list)+1}", "rat": 70})
        cols = [[st_list[0]]]
        idx = 1
        for cnt in nums:
            cols.append(st_list[idx:idx + cnt])
            idx += cnt
        return cols[::-1] if is_away else cols

    def _side_html(cols, color_hex):
        col_divs = []
        for c in cols:
            nodes = []
            for p in c:
                bd = "2px solid #f2cc60" if p.get("yellow") else ("2px solid #ff7b72" if p.get("red") else "1.5px solid rgba(255,255,255,0.85)")
                nodes.append(
                    f"<div style='display:flex;flex-direction:column;align-items:center;margin:2px 0;'>"
                    f"<div class='dp-node-circle' style='background:{color_hex};border:{bd};'>{p.get('num','')}</div>"
                    f"<div class='dp-node-name'>{p.get('name','')}</div></div>"
                )
            col_divs.append(f"<div style='display:flex;flex-direction:column;justify-content:space-around;height:100%;'>{''.join(nodes)}</div>")
        return f"<div style='display:flex;justify-content:space-around;width:48%;height:100%;'>{''.join(col_divs)}</div>"

    h_cols = _parse_lines((h_info or {}).get("tac", "4-2-3-1"), (h_info or {}).get("starters", []), False)
    a_cols = _parse_lines((a_info or {}).get("tac", "4-2-3-1"), (a_info or {}).get("starters", []), True)
    center_line = "<div style='width:2px;height:100%;background:rgba(255,255,255,0.55);'></div>"
    hdr = (
        f"<div style='display:flex;justify-content:space-between;font-size:11.5px;color:#8b949e;margin-bottom:4px;'>"
        f"<span>🏠 <b>{h_name}</b> ({(h_info or {}).get('tac','4-2-3-1')} • OVR {(h_info or {}).get('ovr',72)})</span>"
        f"<span>✈️ <b>{a_name}</b> ({(a_info or {}).get('tac','4-2-3-1')} • OVR {(a_info or {}).get('ovr',71)})</span></div>"
    )
    return hdr + f"<div class='dp-pitch-wrap'>{_side_html(h_cols, '#1f6feb')}{center_line}{_side_html(a_cols, '#da3633')}</div>"

def render_28_markets_html(spec, r_data=None):
    sp = spec or {}
    oa = (r_data or {}).get("odds_api") or {}
    af = (r_data or {}).get("af_odds") or {}
    groups = [
        ("⚽ Taraf & Çifte Şans", [("MS 1", sp.get("MS_1")), ("MS X", sp.get("MS_X")), ("MS 2", sp.get("MS_2")), ("1X", sp.get("DC_1X")), ("X2", sp.get("DC_X2")), ("12", sp.get("DC_12"))]),
        ("🥅 Toplam Gol & KG", [("1.5 Üst", sp.get("MS_O15")), ("2.5 Üst", sp.get("MS_O25")), ("2.5 Alt", sp.get("MS_U25")), ("3.5 Alt", sp.get("MS_U35")), ("KG Var", sp.get("BTTS_YES")), ("KG Yok", sp.get("BTTS_NO"))]),
        ("⏱️ İlk Yarı & Takım Gol", [("İY 0.5Ü", sp.get("HT_O05")), ("İY 1.5A", sp.get("HT_U15")), ("Ev 1.5Ü", sp.get("H_O15")), ("Dep 1.5Ü", sp.get("A_O15")), ("1 & 1.5Ü", sp.get("WIN1_O15")), ("2 & 1.5Ü", sp.get("WIN2_O15"))]),
        ("🚩 Korner & 🟨 Kart", [("8.5 KorÜ", sp.get("COR_O85")), ("9.5 KorA", sp.get("COR_U95")), ("9.5 KorÜ", sp.get("COR_O95")), ("3.5 KartÜ", sp.get("CARD_O35")), ("4.5 KartÜ", sp.get("CARD_O45")), ("4.5 KartA", sp.get("CARD_U45"))])
    ]
    rows_html = []
    for g_title, items in groups:
        pills = []
        for lbl, val in items:
            v = safe_int(val, 50)
            col = "#58a6ff" if v >= 78 else ("#56d364" if v >= 68 else ("#e3b341" if v >= 55 else "#8b949e"))
            pills.append(f"<span style='background:#0d1117;border:1px solid #30363d;border-radius:5px;padding:2px 6px;margin:2px;display:inline-block;font-size:11px;'>{lbl}: <b style='color:{col};'>%{v}</b></span>")
        rows_html.append(f"<div style='margin-bottom:5px;'><div style='font-size:11px;color:#8b949e;font-weight:700;'>{g_title}</div><div>{''.join(pills)}</div></div>")

    bm_info = ""
    if oa.get("bm_count"):
        bm_info = (
            f"<div class='dp-exp-alert'>🌍 <b>Çapraz Büro ({oa.get('bm_count')} Büro):</b> "
            f"EU:%{oa.get('eu_h',0)} | UK:%{oa.get('uk_h',0)} | US:%{oa.get('us_h',0)} | AU:%{oa.get('au_h',0)} "
            f"(Sapma:{oa.get('reg_spread',0)}%p) • 2.5Ü Oran: @{af.get('o25_odd') or oa.get('o25_dec') or '-'}</div>"
        )
    return "".join(rows_html) + bm_info
# ==================== MODÜL 5B/6: RENK KALKANLI MAÇ KARTLARI VE ARŞİV RÖNTGENİ ====================
def get_card_tier_class_and_badge(conf_v, dec_sc, odd_txt="", patron_ui=""):
    has_warn = ("⚠️" in str(odd_txt)) or ("⚠️İddaaDüşük" in str(patron_ui)) or ("🚨" in str(odd_txt))
    if has_warn or conf_v < 65 or dec_sc < 74:
        return "dp-tier-red", "<span class='dp-heat'>🔴 PAS / RİSKLİ</span>"
    if conf_v >= 78 and dec_sc >= 92:
        return "dp-ak", "<span class='dp-badge' style='background:#1f6feb;color:#fff;'>💎 ANA KASA</span>"
    if conf_v >= 70 and dec_sc >= 80:
        return "dp-tier-green", "<span class='dp-w'>🟢 GÜVENLİ</span>"
    return "dp-tier-orange", "<span class='dp-badge' style='color:#e3b341;'>🟠 SEÇİCİ / XI BEKLE</span>"

def build_archive_xray_report():
    fin_map = MEM.get("finished_cache", {})
    items = sorted(
        [v for v in fin_map.values() if isinstance(v, dict) and v.get("won") in (True, False)],
        key=lambda x: safe_float(x.get("ts"), 0.0), reverse=True
    )
    tot = len(items)
    if tot == 0:
        return "🔬 Arşivde henüz sonuçlanmış maç bulunmuyor."

    w_all = sum(1 for x in items if x.get("won"))
    ak_items = [x for x in items if safe_int(x.get("conf"), 0) >= 78]
    ak_w = sum(1 for x in ak_items if x.get("won"))

    mkt_stats = {}
    for x in items:
        mt = _classify_pick_market_type(x.get("pick"))
        rec = mkt_stats.setdefault(mt, [0, 0])
        rec[1] += 1
        if x.get("won"): rec[0] += 1
    mkt_parts = [f"{k}:{v[0]}/{v[1]}(%{int(round(v[0]*100.0/v[1]))})" for k, v in sorted(mkt_stats.items(), key=lambda i: i[1][1], reverse=True)]

    u35_n = sum(1 for x in items if (safe_int(x.get("h_sc"), 0) + safe_int(x.get("a_sc"), 0)) <= 3)
    u25_n = sum(1 for x in items if (safe_int(x.get("h_sc"), 0) + safe_int(x.get("a_sc"), 0)) <= 2)
    o25_n = tot - u25_n
    o15_n = sum(1 for x in items if (safe_int(x.get("h_sc"), 0) + safe_int(x.get("a_sc"), 0)) >= 2)
    btts_y = sum(1 for x in items if safe_int(x.get("h_sc"), 0) >= 1 and safe_int(x.get("a_sc"), 0) >= 1)
    btts_n = tot - btts_y
    cu95_n = sum(1 for x in items if safe_int(x.get("tot_cor"), 0) > 0 and safe_int(x.get("tot_cor"), 0) <= 9)
    co85_n = sum(1 for x in items if safe_int(x.get("tot_cor"), 0) >= 9)

    pct = lambda n: int(round((n * 100.0) / max(1, tot)))
    ak_pct = int(round((ak_w * 100.0) / max(1, len(ak_items)))) if ak_items else 0
    lines = [
        f"🔬 M5.1 GERÇEK KARNE ({tot} Maç): {w_all}/{tot} (%{pct(w_all)}) | 💎 ANA KASA: {ak_w}/{len(ak_items)} (%{ak_pct})",
        "🎯 SEÇİLEN PAZAR İSABETİ: " + " | ".join(mkt_parts),
        f"📊 ARŞİV TAM SPEKTRUM DOĞAL ORANLARI: MS 3.5 Alt:{u35_n}/{tot}(%{pct(u35_n)}) | MS 2.5 Alt:{u25_n}/{tot}(%{pct(u25_n)}) | MS 2.5 Üst:{o25_n}/{tot}(%{pct(o25_n)}) | MS 1.5 Üst:{o15_n}/{tot}(%{pct(o15_n)}) | KG Yok:{btts_n}/{tot}(%{pct(btts_n)}) | KG Var:{btts_y}/{tot}(%{pct(btts_y)}) | 9.5 Korner Alt:{cu95_n}/{tot}(%{pct(cu95_n)}) | 8.5 Korner Üst:{co85_n}/{tot}(%{pct(co85_n)})"
    ]
    losses = [x for x in items if not x.get("won")]
    lines.append(f"--- KAYIP ANALİZ LİSTESİ ({len(losses)} MAÇ) ---")
    for lx in losses[:20]:
        lines.append(f"❌ {lx.get('h_name','')} {lx.get('h_sc',0)}-{lx.get('a_sc',0)} {lx.get('a_name','')} ({lx.get('lig','')}) | Kor:{lx.get('tot_cor',0)} | Kart:{lx.get('cards',0)} -> Hedef: {lx.get('pick','')} (%{lx.get('conf',0)})")
    return "\n".join(lines)

def render_live_match_card(lm, is_vip=True):
    cls = "dp-card dp-live-hot" if lm["pressure"] >= 72 else "dp-card dp-live"
    pick_show = lm["pick"] if is_vip else "🔒 VIP Kilitli"
    fl_badge = "<span class='dp-heat'>💎 FAVORİ GERİDE PUSU</span>" if lm.get("fav_lock") else ""
    d_html = f" • <span style='color:#79c0ff;'>{lm['delta_txt']}</span>" if lm.get("delta_txt") else ""
    st.markdown(
        f"<div class='{cls}'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
        f"<span>⏱️ <b>{lm['clk']}</b> • <span style='color:#8b949e;'>{lm['lig']}</span> {fl_badge}</span>"
        f"<span class='dp-badge'>🔥 Baskı: %{lm['pressure']} | ⚡ Kalan xG: {lm['rem_xg']} (Gol %{lm['goal_prob']})</span></div>"
        f"<div style='font-size:15px;font-weight:800;margin:4px 0;'>{lm['h_name']} <span style='color:#58a6ff;'>{lm['h_sc']} - {lm['a_sc']}</span> {lm['a_name']}</div>"
        f"<div style='font-size:12px;color:#c9d1d9;'>🎯 Şut: <b>{lm['h_sh']}({lm['h_sot']}) - {lm['a_sh']}({lm['a_sot']})</b> | 🚩 Korner: <b>{lm['h_cor']}-{lm['a_cor']}</b> | 🟨 Kart: <b>{lm['cards']}</b> | Top: %{lm['h_poss']}{d_html}</div>"
        f"<div class='dp-exp-alert'>🎯 <b>Maç Önü Kilit:</b> {pick_show} (%{lm['conf']}) • {lm['prop']} <br><span style='font-size:10.5px;color:#8b949e;'>{lm['m4']['patron_sim_ui']}</span></div>"
        f"</div>", unsafe_allow_html=True
    )

def render_upcoming_match_card(um, is_vip=True):
    dec_sc = safe_int((um.get("m4") or {}).get("decision_score"), um["conf"])
    p_ui = (um.get("m4") or {}).get("patron_sim_ui", "")
    tier_cls, tier_badge = get_card_tier_class_and_badge(um["conf"], dec_sc, um["odd"], p_ui)
    xi_badge = "<span class='dp-w'>✅ Resmi XI</span>" if um["is_off"] else "<span class='dp-badge'>⏳ Tahmini XI</span>"
    pick_txt = f"<b>{um['pick']}</b> (%{um['conf']} • Karar:{dec_sc}p)" if is_vip else "🔒 <b>VIP / Patron Kilitli Hedef</b>"
    prop_txt = um["prop"] if is_vip else "🔒 Yan pazarlar VIP üyelere açıktır"
    st.markdown(
        f"<div class='dp-card {tier_cls}'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;'>"
        f"<span>🗓️ <b>{um['tarih_saat']}</b> • <span style='color:#8b949e;'>{um['lig']}</span></span>"
        f"<span>{tier_badge}{xi_badge}</span></div>"
        f"<div style='font-size:14.5px;font-weight:800;margin:4px 0;'>{um['h_name']} ({format_form_badges(um['h_form'])}) vs {um['a_name']} ({format_form_badges(um['a_form'])})</div>"
        f"<div style='font-size:11.5px;color:#8b949e;'>📊 Mom: {um['h_mom']}-{um['a_mom']} | TG: {um['ou']} | {um['odd']}</div>"
        f"<div class='dp-exp-alert'>🎯 {pick_txt} <span style='color:#8b949e;'>({um['evo']})</span><br>🧩 {prop_txt}<br><span style='font-size:10.5px;color:#79c0ff;'>{p_ui if is_vip else ''}</span></div>"
        f"</div>", unsafe_allow_html=True
    )
    if is_vip:
        with st.expander(f"📐 {um['title']} — 22 Oyuncu Saha Dizilişi & 28 Pazar Spektrumu"):
            r_d = um.get("r_data") or {}
            ref_d = r_d.get("ref") or {}
            st.caption(f"🏟️ {r_d.get('venue','-')} | {r_d.get('weather','-')} | ⚖️ Hakem: {ref_d.get('name','Atanmadı')} (Ort:{ref_d.get('avg',4.0)} • {ref_d.get('style','')})")
            st.markdown(render_tactical_pitch_html(um["h_name"], um["a_name"], r_d.get("h"), r_d.get("a")), unsafe_allow_html=True)
            st.markdown(render_28_markets_html((um.get("m4") or {}).get("spectrum"), r_d), unsafe_allow_html=True)
# ==================== MODÜL 6/6: ANA EKRAN, PATRON PANELİ VE ÇALIŞTIRICI ====================
def render_finished_match_card(fm):
    badge = "<span class='dp-w'>✅ KAZANDI</span>" if fm.get("won") else "<span class='dp-heat'>❌ KAYIP</span>"
    border_c = "#2ea043" if fm.get("won") else "#f85149"
    st.markdown(
        f"<div class='dp-card' style='border-left:4px solid {border_c};'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
        f"<span style='color:#8b949e;font-size:11.5px;'>🏁 FT • {fm.get('lig','')} {fm.get('ht_tag','')}</span>{badge}</div>"
        f"<div style='font-size:14px;font-weight:800;margin:3px 0;'>{fm.get('h_name','')} <span style='color:#58a6ff;'>{fm.get('h_sc',0)} - {fm.get('a_sc',0)}</span> {fm.get('a_name','')}</div>"
        f"<div style='font-size:11.5px;color:#c9d1d9;'>🎯 Şut: {fm.get('h_sh',0)}({fm.get('h_sot',0)})-{fm.get('a_sh',0)}({fm.get('a_sot',0)}) | 🚩 Korner: {fm.get('h_cor',0)}-{fm.get('a_cor',0)} ({fm.get('tot_cor',0)}) | 🟨 Kart: {fm.get('cards',0)}</div>"
        f"<div style='font-size:11.5px;color:#79c0ff;margin-top:3px;'>🎯 Hedef: <b>{fm.get('pick','')}</b> (%{fm.get('conf',0)}) • Sim: {fm.get('sim','1-1')}</div>"
        f"</div>", unsafe_allow_html=True
    )

def main():
    uid = get_smart_device_uid()
    u_rec = auto_sync_device_user(uid)
    patron_devs = MEM.setdefault("patron_devs", set())
    is_admin = (uid in patron_devs) or (u_rec.get("tier") == "ADMIN") or bool(st.session_state.get("is_patron"))
    is_vip = is_admin or (u_rec.get("tier") == "VIP")

    c_top1, c_top2, c_top3 = st.columns([2.6, 1.2, 1.2])
    with c_top1:
        st.markdown(f"### ⚡ Delta Pulse AI `{MODEL_VERSION}`")
    with c_top2:
        force_btn = st.button("🔄 Canlı Yenile", use_container_width=True)
    with c_top3:
        mode_map = {"🇹🇷 İddaa ≥1.30": "IDDAA_130", "🇹🇷 İddaa ≥1.42": "IDDAA_142", "🌍 Global": "GLOBAL"}
        rev_map = {v: k for k, v in mode_map.items()}
        sel_lbl = st.selectbox("Oran Filtresi", list(mode_map.keys()), index=list(mode_map.keys()).index(rev_map.get(MEM.get("odd_mode", "IDDAA_130"), "🇹🇷 İddaa ≥1.30")), label_visibility="collapsed")
        if mode_map[sel_lbl] != MEM.get("odd_mode"):
            MEM["odd_mode"] = mode_map[sel_lbl]
            force_btn = True

    live_list, up_list, fin_list, mini_lines = fetch_bulletin_full(force_refresh=force_btn)
    ldg = compute_ledger_summary()

    st.markdown(
        f"<div class='dp-card' style='background:#0d1117;border-color:#1f6feb;'>"
        f"📊 <b>Genel Karne:</b> <span style='color:#56d364;font-weight:800;'>{ldg['main_str']}</span> &nbsp;|&nbsp; "
        f"💎 <b>Ana Kasa:</b> <span style='color:#58a6ff;font-weight:800;'>{ldg['ak_str']}</span> &nbsp;|&nbsp; "
        f"🔥 <b>Canlı Pusu:</b> <span style='color:#e3b341;font-weight:800;'>{ldg['lp_str']}</span> &nbsp;|&nbsp; "
        f"<span style='font-size:11px;color:#8b949e;'>{MEM.get('sb_status','')} • Cihaz: {uid}</span></div>",
        unsafe_allow_html=True
    )

    with st.expander("🔐 Patron / VIP Erişim & Telemetri Kopyalama Paneli", expanded=is_admin):
        if not is_admin:
            pw = st.text_input("Patron Anahtarı", type="password", placeholder="Şifreyi girin...")
            if pw:
                pw_h = hashlib.sha256(pw.strip().encode("utf-8")).hexdigest()
                if pw_h in ADMIN_HASHES:
                    st.session_state["is_patron"] = True
                    patron_devs.add(uid)
                    u_rec["tier"] = "ADMIN"
                    save_persistent_store()
                    st.rerun()
                else:
                    st.error("Geçersiz anahtar.")
        else:
            xray_txt = build_archive_xray_report()
            full_copy_txt = xray_txt + "\n" + "\n".join(mini_lines)
            p_c1, p_c2 = st.columns(2)
            with p_c1:
                _render_copy_button(full_copy_txt, "📋 Tam Röntgen + DP-MİNİ Kopyala", "cp_full_xray")
            with p_c2:
                _render_copy_button("\n".join(mini_lines), "⚡ Sadece DP-MİNİ Kopyala", "cp_only_mini")
            st.text_area("Telemetri Önizleme", value=full_copy_txt, height=135)

    t_live, t_up, t_ak, t_fin = st.tabs([
        f"🔴 Canlı Pusu ({len(live_list)})",
        f"🗓️ Maç Önü ({len(up_list)})",
        "💎 Elmas & Güvenli",
        f"🏁 Arşiv ({len(fin_list)})"
    ])

    with t_live:
        if not live_list:
            st.info("Şu an aktif canlı karşılaşma bulunmuyor.")
        for lm in live_list:
            render_live_match_card(lm, is_vip=is_vip)

    with t_up:
        if not up_list:
            st.info("Yaklaşan bülten maçı bulunmuyor.")
        for um in up_list:
            render_upcoming_match_card(um, is_vip=is_vip)

    with t_ak:
        safe_picks = [
            u for u in up_list
            if get_card_tier_class_and_badge(u["conf"], safe_int((u.get("m4") or {}).get("decision_score"), u["conf"]), u["odd"], (u.get("m4") or {}).get("patron_sim_ui", ""))[0] in ("dp-ak", "dp-tier-green")
        ]
        if not safe_picks:
            st.info("Şu an Buz Mavisi (💎 Ana Kasa) veya Zümrüt Yeşili (🟢 Güvenli) kriterlerini geçen maç yok.")
        for sp_m in safe_picks:
            render_upcoming_match_card(sp_m, is_vip=is_vip)

    with t_fin:
        for fm in fin_list:
            render_finished_match_card(fm)

if __name__ == "__main__":
    main()
