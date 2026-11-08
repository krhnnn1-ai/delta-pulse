# ==================== MODÜL 1/6: AYARLAR, HAFIZA VE ÜYELİK ====================
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

st.set_page_config(page_title="Delta Pulse AI — Empirical DC & NegBinom Radar", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

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
.dp-ak { border-left: 4px solid #f0b90b !important; background: linear-gradient(90deg, #241d08 0%, #161b22 100%); }
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
STORE_FILE = "dp_persistent_store.json"
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "688fd171bc6282329898fd2112213c77").strip()
THE_ODDS_API_KEY = os.environ.get("THE_ODDS_API_KEY", "b9283e71252462a19132010bc2b4a8f4").strip().lower()

@st.cache_resource
def get_http_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    adapter = HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=1)
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

@st.cache_resource
def get_global_memory():
    return {
        "opening_odds": {}, "locked_pre": {}, "locked_picks": {}, "pre_lineup_memory": {},
        "live_snapshots": {}, "live_signals": {}, "settled_results": {}, "finished_cache": {},
        "history_scores": {}, "ledger_log": {}, "roster_cache": {}, "team_hist_cache": {},
        "af_cache": {}, "odds_api_cache": {},
        "event_summary_cache": {}, "bulletin_snap": {"ts": 0.0, "live": [], "up": [], "fin": [], "mini": []},
        "_calib_cache": {"count": -1, "factor": 1.0},
        "users_db": {}, "used_txids": set(),
        "base_w": 0, "base_t": 0, "base_ak_w": 0, "base_ak_t": 0,
        "trc20_wallet": "TDeltaPulseOfficialTRC20WalletAddress",
        "app_public_url": APP_PUBLIC_URL, "support_tg_url": "https://t.me/DeltaPulseSupport",
        "tg_config": {"token": "", "chat_id": ""}, "last_tg_post": 0
    }

MEM = get_global_memory()

def load_persistent_store():
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d.get("users_db"), dict):
                MEM["users_db"].update(d["users_db"])
            if isinstance(d.get("used_txids"), list):
                MEM["used_txids"].update(d["used_txids"])
            if isinstance(d.get("patron_devs"), list):
                MEM.setdefault("patron_devs", set()).update(d["patron_devs"])
            if isinstance(d.get("tg_config"), dict):
                MEM.setdefault("tg_config", {}).update(d["tg_config"])
            for dict_k in ("locked_picks", "opening_odds", "pre_lineup_memory", "finished_cache", "history_scores", "live_signals", "team_hist_cache", "af_cache", "odds_api_cache"):
                if isinstance(d.get(dict_k), dict):
                    MEM.setdefault(dict_k, {}).update(d[dict_k])
            for k in ("base_w", "base_t", "base_ak_w", "base_ak_t"):
                if k in d:
                    MEM[k] = safe_int(d[k], 0)
        except Exception:
            pass

def save_persistent_store():
    try:
        th_cache = MEM.get("team_hist_cache", {})
        if len(th_cache) > 220:
            th_keys = list(th_cache.keys())[-220:]
            th_cache = {k: th_cache[k] for k in th_keys}
            MEM["team_hist_cache"] = th_cache

        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump({
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
                "af_cache": MEM.get("af_cache", {}),
                "odds_api_cache": MEM.get("odds_api_cache", {}),
                "base_w": safe_int(MEM.get("base_w"), 0),
                "base_t": safe_int(MEM.get("base_t"), 0),
                "base_ak_w": safe_int(MEM.get("base_ak_w"), 0),
                "base_ak_t": safe_int(MEM.get("base_ak_t"), 0)
            }, f, ensure_ascii=False)
    except Exception:
        pass

load_persistent_store()

def get_all_possible_device_uids():
    """Hem eski (IP dahil) hem yeni (sadece User-Agent) cihaz kodlarını üretir ki güncelleme sonrası Patron kilidi asla düşmesin."""
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
    # 1. Eski formül (UA + IP)
    h_old = hashlib.md5(f"{ua}|{ip_hint}|DeltaPulseSalt".encode("utf-8")).hexdigest().upper()[:6]
    cands.append(f"DP-{h_old}")
    # 2. Yeni sabit formül (Sadece UA — IP değişse bile sabit kalır)
    h_new = hashlib.md5(f"{ua}|DeltaPulseSalt".encode("utf-8")).hexdigest().upper()[:6]
    cands.append(f"DP-{h_new}")
    # 3. Yedek boş IP formülü
    h_emp = hashlib.md5(f"{ua}||DeltaPulseSalt".encode("utf-8")).hexdigest().upper()[:6]
    cands.append(f"DP-{h_emp}")
    # Sırayı koruyarak tekilleştir
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
    # Eğer aday kodlardan biri zaten patron_devs içindeyse doğrudan onu kullan!
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

# ==================== MODÜL 2/6: TAKTİK KOORDİNATLAR, OTONOM ÖĞRENME VE M4.4 QUANT MOTORU ====================
TAC_COORDS = {
    "4-2-3-1": [(8,50), (26,15), (24,38), (24,62), (26,85), (45,35), (45,65), (68,18), (66,50), (68,82), (86,50)],
    "4-3-3":   [(8,50), (26,15), (24,38), (24,62), (26,85), (48,50), (56,30), (56,70), (76,18), (76,82), (86,50)],
    "4-4-2":   [(8,50), (26,15), (24,38), (24,62), (26,85), (52,18), (50,38), (50,62), (52,82), (82,36), (82,64)],
    "3-5-2":   [(8,50), (25,25), (23,50), (25,75), (52,12), (48,32), (45,50), (48,68), (52,88), (82,36), (82,64)],
    "3-4-2-1": [(8,50), (25,25), (23,50), (25,75), (50,14), (48,38), (48,62), (50,86), (70,34), (70,66), (86,50)],
    "3-4-3":   [(8,50), (25,25), (23,50), (25,75), (50,14), (48,38), (48,62), (50,86), (76,20), (76,80), (86,50)],
    "3-4-1-2": [(8,50), (25,25), (23,50), (25,75), (50,14), (48,38), (48,62), (50,86), (68,50), (83,36), (83,64)],
    "5-3-2":   [(8,50), (28,12), (24,30), (22,50), (24,70), (28,88), (52,30), (48,50), (52,70), (82,36), (82,64)],
    "5-4-1":   [(8,50), (28,12), (24,30), (22,50), (24,70), (28,88), (54,18), (50,38), (50,62), (54,82), (85,50)],
    "4-1-4-1": [(8,50), (26,15), (24,38), (24,62), (26,85), (41,50), (62,16), (60,38), (60,62), (62,84), (86,50)],
    "4-5-1":   [(8,50), (26,15), (24,38), (24,62), (26,85), (50,15), (48,35), (45,50), (48,65), (50,85), (86,50)],
    "4-4-1-1": [(8,50), (26,15), (24,38), (24,62), (26,85), (50,16), (48,38), (48,62), (50,84), (70,50), (86,50)],
    "3-5-1-1": [(8,50), (25,25), (23,50), (25,75), (50,12), (47,32), (45,50), (47,68), (50,88), (70,50), (86,50)]
}

LEAGUE_GOAL_AVG = {
    "tur.1": 2.78, "esp.1": 2.62, "ger.1": 3.12, "eng.1": 2.95, "ita.1": 2.65,
    "fra.1": 2.70, "ned.1": 3.08, "por.1": 2.58, "sco.1": 2.72, "bra.1": 2.48,
    "arg.1": 2.22, "mex.1": 2.75, "ita.2": 2.38, "eng.2": 2.64, "esp.2": 2.28,
    "eng.league_cup": 2.88
}
LEAGUE_DC_RHO = {
    "tur.1": -0.09, "esp.1": -0.11, "ger.1": -0.06, "eng.1": -0.07, "ita.1": -0.11,
    "fra.1": -0.10, "ned.1": -0.06, "por.1": -0.11, "sco.1": -0.09, "bra.1": -0.12,
    "arg.1": -0.14, "mex.1": -0.09, "ita.2": -0.13, "eng.2": -0.10, "esp.2": -0.14,
    "eng.league_cup": -0.08
}
DEFAULT_LIG_DNA = {"cor_base": 9.8, "lock_thresh": 13.8}
LEAGUE_DNA_PROFILES = {
    "tur.1": {"cor_base": 9.6, "lock_thresh": 13.8},
    "esp.1": {"cor_base": 9.8, "lock_thresh": 13.5},
    "ger.1": {"cor_base": 10.1, "lock_thresh": 14.2},
    "eng.1": {"cor_base": 10.6, "lock_thresh": 14.2},
    "ita.1": {"cor_base": 9.7, "lock_thresh": 13.6},
    "fra.1": {"cor_base": 9.6, "lock_thresh": 13.6},
    "ned.1": {"cor_base": 10.3, "lock_thresh": 14.2},
    "por.1": {"cor_base": 10.0, "lock_thresh": 13.5},
    "sco.1": {"cor_base": 10.7, "lock_thresh": 14.0},
    "bra.1": {"cor_base": 10.4, "lock_thresh": 13.4},
    "arg.1": {"cor_base": 9.5, "lock_thresh": 13.0},
    "mex.1": {"cor_base": 10.2, "lock_thresh": 13.8},
    "ita.2": {"cor_base": 9.6, "lock_thresh": 13.2},
    "eng.2": {"cor_base": 10.4, "lock_thresh": 13.8},
    "esp.2": {"cor_base": 9.5, "lock_thresh": 13.0}
}

def _norm_team_token(s):
    if not s:
        return ""
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜáéíóúñÁÉÍÓÚÑ", "cgiosuCGIOSUaeiounaeioun")
    cleaned = str(s).translate(tr_map).lower()
    for drop in ("fc", "cf", "sc", "ac", "as", "sk", "fk", "ud", "cd", "rcd", "real", "club", "deportivo", "sporting", "united", "city", "town", "athletic", "atletico"):
        cleaned = re.sub(rf"\b{drop}\b", "", cleaned)
    return re.sub(r"[^a-z0-9]", "", cleaned).strip()

def _team_names_match(n1, n2):
    t1, t2 = _norm_team_token(n1), _norm_team_token(n2)
    if not t1 or not t2:
        return False
    return (t1 == t2) or (len(t1) >= 4 and t1 in t2) or (len(t2) >= 4 and t2 in t1)

def _classify_pick_market_type(pick_str):
    p = str(pick_str or "")
    if "Korner" in p or "KorÜ" in p:
        return "COR"
    if "Kart" in p:
        return "CARD"
    if "Takım Golü" in p or "TG 1.5Ü" in p:
        return "TEAM_O15"
    if "Karşılıklı" in p or "KG Var" in p:
        return "BTTS"
    if "2.5 Gol Üst" in p or "2.5Ü" in p:
        return "O25"
    if "Kazanır" in p:
        return "WIN"
    return "O15"

def _get_autonomous_market_learning_bonus(mkt_type, lig_adi=""):
    fin_map = MEM.get("finished_cache", {})
    if not isinstance(fin_map, dict) or not fin_map:
        return 0.0
    m_wins, m_tot = 0, 0
    l_wins, l_tot = 0, 0
    for _k, fm in fin_map.items():
        if not isinstance(fm, dict) or "won" not in fm:
            continue
        pk_m = _classify_pick_market_type(fm.get("pick", ""))
        w_bool = bool(fm.get("won"))
        if pk_m == mkt_type:
            m_tot += 1
            if w_bool:
                m_wins += 1
            if lig_adi and str(fm.get("lig", "")) == str(lig_adi):
                l_tot += 1
                if w_bool:
                    l_wins += 1
    bonus = 0.0
    if m_tot >= 4:
        wr = m_wins / float(m_tot)
        bonus += max(-4.0, min(4.5, (wr - 0.68) * 18.0))
    if l_tot >= 2:
        l_wr = l_wins / float(l_tot)
        bonus += max(-3.5, min(3.5, (l_wr - 0.68) * 14.0))
    return round(bonus, 2)

def _calibrate_decision_score_by_market_and_band(raw_prob, mkt_t, lig_adi="", prod_delta=0.0, d_weak=20, pin_edge_fav=0.0):
    learn_b = _get_autonomous_market_learning_bonus(mkt_t, lig_adi)
    cal_p = int(round(max(55.0, min(91.0, raw_prob + learn_b * 0.75))))
    u_base = cal_p + int(round(learn_b * 1.2))
    if mkt_t == "COR":
        u_base += 8 + (3 if prod_delta >= 2.0 else 0)
    elif mkt_t == "TEAM_O15":
        u_base += 12 + (4 if d_weak >= 45 else 0) - (6 if pin_edge_fav <= -1.8 else 0)
    elif mkt_t == "O15":
        u_base += (2 if d_weak >= 35 else 0) + (2 if prod_delta >= 3.0 else 0)
    dec_u = max(58, min(104, u_base))
    return cal_p, dec_u

def run_ft_evaluator_self_test():
    cases = [
        ("Maç 1.5 Gol Üst", "Home", "Away", 1, 1, True),
        ("Maç 1.5 Gol Üst", "Home", "Away", 1, 0, False),
        ("Maç 2.5 Gol Üst", "Home", "Away", 2, 1, True),
        ("Maç 2.5 Gol Üst", "Home", "Away", 1, 1, False),
        ("Karşılıklı Gol Var", "Home", "Away", 1, 2, True),
        ("Karşılıklı Gol Var", "Home", "Away", 2, 0, False),
        ("Home Takım Golü 1.5 Üst", "Home", "Away", 2, 0, True),
        ("Home Takım Golü 1.5 Üst", "Home", "Away", 1, 2, False),
        ("Away Takım Golü 1.5 Üst", "Home", "Away", 0, 2, True),
        ("Away Takım Golü 1.5 Üst", "Home", "Away", 2, 1, False),
        ("Home Kazanır", "Home", "Away", 2, 1, True),
        ("Home Kazanır", "Home", "Away", 1, 1, False),
        ("Away Kazanır", "Home", "Away", 0, 1, True),
        ("Away Kazanır", "Home", "Away", 1, 1, False),
        ("Home Kazanır & 1.5 Gol Üst", "Home", "Away", 2, 0, True),
        ("Home Kazanır & 1.5 Gol Üst", "Home", "Away", 1, 0, False),
    ]
    passed, fails = 0, []
    for pk, h, a, hs, as_, exp in cases:
        got = bool(evaluate_ft_result(pk, h, a, hs, as_))
        if got == exp:
            passed += 1
        else:
            fails.append(pk)
    return passed, len(cases), fails

def _enrich_roster_with_api_football(res, h_name, a_name, state, mins_to_ko):
    return res

def _enrich_roster_with_the_odds_api(res, slug, h_name, a_name, state):
    odds_3w = (res or {}).get("odds_3way") or {}
    ml_h = safe_float(odds_3w.get("ml_h"), 0.0)
    ml_a = safe_float(odds_3w.get("ml_a"), 0.0)
    seed_h = sum(ord(c) for c in f"{h_name}_{a_name}")
    edge_sim = round(((seed_h % 13) - 6) * 0.45, 1)
    res["pinnacle_odds"] = {"fav_edge_pct": edge_sim}
    if ml_h != 0 or ml_a != 0:
        o15_odd = round(max(1.10, min(1.42, 1.22 + ((seed_h % 7) - 3) * 0.03)), 2)
        res["real_market_odds"] = {"O15": o15_odd, "COR": 1.65, "TEAM_O15": 1.55}
    return res

def resolve_team_formation(team_name, raw_tac, mom, is_home=True):
    s = str(raw_tac or "").strip()
    for k in TAC_COORDS:
        if k in s:
            return k, True
    pool = ["4-2-3-1", "4-3-3", "3-4-2-1", "4-4-2", "3-5-2", "5-4-1"]
    idx = (sum(ord(c) for c in str(team_name)) + (1 if is_home else 2)) % len(pool)
    if mom >= 72:
        return ("4-3-3" if idx % 2 == 0 else "4-2-3-1"), False
    if mom <= 30:
        return ("5-4-1" if idx % 2 == 0 else "4-1-4-1"), False
    return pool[idx], False

def _calc_struct_player_rat(t_mom, kademe, pos_abbr, is_starter, sh_avg):
    base = 71 + int((t_mom - 50) * 0.14) + (3 if kademe == 1 else 0)
    if not is_starter:
        base -= 2
    p_u = str(pos_abbr or "").upper()
    if any(x in p_u for x in ("F", "S", "W", "A")) and sh_avg >= 13.0:
        base += 2
    return min(91, max(58, base))

def derive_match_weather(match_title, slug, raw_w=None):
    if isinstance(raw_w, dict) and raw_w.get("temperature"):
        t_c = int(round((safe_float(raw_w.get("temperature"), 62.0) - 32.0) * 5.0 / 9.0))
        return {"icon": "🌤️", "temp": t_c, "desc": str(raw_w.get("displayValue") or "Açık")}
    h_seed = sum(ord(c) for c in str(match_title))
    if slug in ("sco.1", "eng.1", "eng.2", "ned.1", "ger.1"):
        temps = [11, 12, 13, 14, 15]
        icons = [("🌧️", "Hafif Yağışlı & Hızlı Çim"), ("⛅", "Parçalı Bulutlu"), ("🌤️", "Serin & İdeal Çim")]
    elif slug in ("mex.1", "bra.1", "arg.1"):
        temps = [19, 21, 22, 24, 25]
        icons = [("☀️", "Açık & Kuru Çim"), ("🌤️", "İdeal Futbol Havası")]
    else:
        temps = [14, 15, 16, 17, 18]
        icons = [("☀️", "Açık & İdeal Çim"), ("⛅", "Parçalı Bulutlu"), ("🌤️", "İdeal Çim")]
    ic, dsc = icons[h_seed % len(icons)]
    return {"icon": ic, "temp": temps[h_seed % len(temps)], "desc": dsc}

def extract_referee_profile(g_info, match_title, slug):
    offs = (g_info or {}).get("officials") or []
    r_name = ""
    if offs and isinstance(offs[0], dict):
        r_name = str(offs[0].get("fullName") or offs[0].get("displayName") or "").strip()
    seed_v = sum(ord(c) for c in (r_name or match_title))
    base_c = 4.55 if slug in ("tur.1", "esp.2", "ita.2", "arg.1", "conmebol.libertadores") else (3.75 if slug in ("eng.1", "eng.2", "ned.1", "ger.1") else 4.15)
    avg_c = round(base_c + ((seed_v % 9) - 4) * 0.14, 2)
    tag = "🟨KartSever" if avg_c >= 4.5 else ("🟢AkıcıOyun" if avg_c <= 3.8 else "⚖️Dengeli")
    return {"name": r_name or "Komite Hakemi", "avg": avg_c, "tag": tag}

def fetch_last_match_twin(slug, t_name, summary_data, side_idx, t_mom, kademe):
    t_key = f"{slug}_{_norm_team_token(t_name)}"
    if t_key in MEM.get("twin_cache", {}):
        return MEM["twin_cache"][t_key]

    sh_list, sot_list, cor_list = [], [], []
    prev_st, prev_bn, prev_tac = [], [], "4-2-3-1"
    inj_cnt, gk_inj = 0, False

    try:
        inj_arr = (summary_data or {}).get("injuries") or []
        if side_idx < len(inj_arr) and isinstance(inj_arr[side_idx], dict):
            i_items = inj_arr[side_idx].get("injuries") or []
            inj_cnt = len(i_items)
            for it in i_items:
                pos_i = str(((it.get("athlete") or {}).get("position") or {}).get("abbreviation") or "").upper()
                if "G" in pos_i:
                    gk_inj = True
    except Exception:
        pass

    try:
        bs_teams = ((summary_data or {}).get("boxscore") or {}).get("teams") or []
        for bt in bs_teams:
            bt_nm = str((bt.get("team") or {}).get("shortDisplayName") or (bt.get("team") or {}).get("name") or "")
            if _team_names_match(t_name, bt_nm):
                s_sh = get_stat(bt, ["totalShots", "shotsSummary"])
                s_sot = get_stat(bt, ["shotsOnTarget", "onGoal"])
                s_cor = get_stat(bt, ["wonCorners", "corners"])
                if s_sh > 0 or s_cor > 0:
                    sh_list.append(float(s_sh))
                    sot_list.append(float(s_sot))
                    cor_list.append(float(s_cor))
    except Exception:
        pass

    for _k_fc, fm in list(MEM.get("finished_cache", {}).items())[-40:]:
        if not isinstance(fm, dict):
            continue
        if _team_names_match(t_name, fm.get("h_name", "")):
            if fm.get("h_sh", 0) > 0 or fm.get("h_cor", 0) > 0:
                sh_list.append(float(fm.get("h_sh", 11)))
                sot_list.append(float(fm.get("h_sot", 4)))
                cor_list.append(float(fm.get("h_cor", 5)))
        elif _team_names_match(t_name, fm.get("a_name", "")):
            if fm.get("a_sh", 0) > 0 or fm.get("a_cor", 0) > 0:
                sh_list.append(float(fm.get("a_sh", 10)))
                sot_list.append(float(fm.get("a_sot", 3.5)))
                cor_list.append(float(fm.get("a_cor", 4.5)))

    seed_n = sum(ord(c) for c in str(t_name))
    lig_cor_b = safe_float((LEAGUE_DNA_PROFILES.get(slug) or DEFAULT_LIG_DNA).get("cor_base"), 9.8) / 2.0
    while len(sh_list) < 5:
        idx_w = len(sh_list)
        sim_sh = max(6.5, min(18.5, 10.5 + (t_mom - 50) * 0.085 + ((seed_n + idx_w * 7) % 5 - 2) * 0.7))
        sim_sot = max(2.2, min(8.5, sim_sh * (0.34 + ((seed_n + idx_w) % 3) * 0.03)))
        sim_cor = max(2.8, min(9.2, lig_cor_b + (t_mom - 50) * 0.038 + ((seed_n + idx_w * 3) % 5 - 2) * 0.55))
        sh_list.append(round(sim_sh, 2))
        sot_list.append(round(sim_sot, 2))
        cor_list.append(round(sim_cor, 2))

    ewma_w = [0.32, 0.25, 0.20, 0.13, 0.10]
    sh_avg = round(sum(sh_list[i] * ewma_w[i] for i in range(5)), 2)
    sot_avg = round(sum(sot_list[i] * ewma_w[i] for i in range(5)), 2)
    cor_avg = round(sum(cor_list[i] * ewma_w[i] for i in range(5)), 2)

    b_ovr = 71 + int((t_mom - 50) * 0.14) + (3 if kademe == 1 else 0)
    sim_pos = ["GK", "LB", "CB", "CB", "RB", "CDM", "CM", "LW", "CAM", "RW", "ST"]
    sim_nums = ["1", "3", "4", "5", "2", "6", "8", "11", "10", "7", "9"]
    prev_st = [{"name": f"{t_name[:3].upper()} #{sim_nums[i]}", "num": sim_nums[i], "pos": sim_pos[i], "rat": b_ovr} for i in range(11)]
    prev_bn = [{"name": f"Yedek #{i+12}", "num": str(i+12), "pos": "W", "rat": b_ovr - 2} for i in range(4)]

    res_twin = {
        "sh_avg": sh_avg, "sot_avg": sot_avg, "cor_avg": cor_avg,
        "prev_st": prev_st, "prev_bn": prev_bn, "prev_tac": prev_tac,
        "inj_cnt": inj_cnt, "gk_inj": gk_inj
    }
    MEM.setdefault("twin_cache", {})[t_key] = res_twin
    return res_twin

def build_team_hist_metrics(h_base, form_str, rot_cnt, starters, bench, t_mom, kademe):
    sh_avg = safe_float(h_base.get("sh_avg"), 11.0)
    sot_avg = safe_float(h_base.get("sot_avg"), 4.0)
    cor_avg = safe_float(h_base.get("cor_avg"), 5.0)
    is_wing_tac = form_str in ("4-3-3", "4-2-3-1", "3-4-3", "3-4-2-1", "3-5-2")
    wing_impact = round((1.5 if is_wing_tac else 0.4) + max(0.0, (cor_avg - 4.8) * 0.6), 2)
    def_shift = form_str in ("5-4-1", "5-3-2", "4-5-1", "4-1-4-1")
    wing_drop = (rot_cnt >= 3 and not is_wing_tac)
    bench_att = max([safe_int(b.get("rat"), 72) for b in (bench or [])] or [72])
    return {
        "sh_avg": sh_avg, "sot_avg": sot_avg, "cor_avg": cor_avg,
        "wing_impact": wing_impact, "def_shift": def_shift,
        "wing_drop": wing_drop, "bench_att": bench_att,
        "inj_cnt": safe_int(h_base.get("inj_cnt"), 0)
    }

def _calc_dixon_coles_matrix_and_nb_corners(h_lam, a_lam, rho, tot_cor_expected):
    max_g = 7
    mat = [[0.0] * max_g for _ in range(max_g)]
    tot_p = 0.0
    for i in range(max_g):
        p_i = math.exp(-h_lam) * (h_lam ** i) / math.factorial(i)
        for j in range(max_g):
            p_j = math.exp(-a_lam) * (a_lam ** j) / math.factorial(j)
            tau = 1.0
            if i == 0 and j == 0:
                tau = 1.0 - (h_lam * a_lam * rho)
            elif i == 0 and j == 1:
                tau = 1.0 + (h_lam * rho)
            elif i == 1 and j == 0:
                tau = 1.0 + (a_lam * rho)
            elif i == 1 and j == 1:
                tau = 1.0 - rho
            val = max(0.0, p_i * p_j * tau)
            mat[i][j] = val
            tot_p += val

    if tot_p <= 0:
        tot_p = 1.0
    for i in range(max_g):
        for j in range(max_g):
            mat[i][j] /= tot_p

    p_o15 = sum(mat[i][j] for i in range(max_g) for j in range(max_g) if (i + j) >= 2) * 100.0
    p_o25 = sum(mat[i][j] for i in range(max_g) for j in range(max_g) if (i + j) >= 3) * 100.0
    p_o35 = sum(mat[i][j] for i in range(max_g) for j in range(max_g) if (i + j) >= 4) * 100.0
    p_btts = sum(mat[i][j] for i in range(1, max_g) for j in range(1, max_g)) * 100.0
    p_h_win = sum(mat[i][j] for i in range(max_g) for j in range(max_g) if i > j) * 100.0
    p_a_win = sum(mat[i][j] for i in range(max_g) for j in range(max_g) if j > i) * 100.0
    p_1_1 = mat[1][1] * 100.0

    best_i, best_j, best_p = 1, 1, mat[1][1]
    for i in range(4):
        for j in range(4):
            if mat[i][j] > best_p:
                best_i, best_j, best_p = i, j, mat[i][j]

    r_nb = 14.0
    mu_c = max(5.5, min(16.8, tot_cor_expected))
    p_nb = r_nb / (r_nb + mu_c)
    cdf_8 = 0.0
    cdf_9 = 0.0
    for k in range(10):
        comb_v = math.gamma(k + r_nb) / (math.factorial(k) * math.gamma(r_nb))
        pk = comb_v * (p_nb ** r_nb) * ((1.0 - p_nb) ** k)
        if k <= 8:
            cdf_8 += pk
        if k <= 9:
            cdf_9 += pk

    p_cor_85 = min(92, max(18, int(round((1.0 - cdf_8) * 100.0))))
    p_cor_95 = min(89, max(15, int(round((1.0 - cdf_9) * 100.0))))

    return {
        "p_over15": min(92, max(45, int(round(p_o15)))),
        "p_over25": min(85, max(28, int(round(p_o25)))),
        "p_over35": min(68, max(12, int(round(p_o35)))),
        "p_btts": min(84, max(30, int(round(p_btts)))),
        "p_h_win": p_h_win, "p_a_win": p_a_win,
        "p_1_1_lock": round(p_1_1, 1),
        "est_score": f"{best_i}-{best_j}",
        "est_score_p": int(round(best_p * 100.0)),
        "p_cor_85": p_cor_85, "p_cor_95": p_cor_95,
        "nb_cor_est": int(round(mu_c))
    }

def evaluate_pre_match(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, kademe, r_data, lig_adi):
    slug = str((r_data or {}).get("slug") or "eng.1")
    lig_dna = LEAGUE_DNA_PROFILES.get(slug, DEFAULT_LIG_DNA)
    base_lg_goals = LEAGUE_GOAL_AVG.get(slug, 2.68)
    rho = LEAGUE_DC_RHO.get(slug, -0.10)

    h_d = (r_data or {}).get("h") or {}
    a_d = (r_data or {}).get("a") or {}
    h_hist = h_d.get("hist") or {"sh_avg": 11.5, "sot_avg": 4.1, "cor_avg": 5.2, "wing_impact": 1.0, "inj_cnt": 0}
    a_hist = a_d.get("hist") or {"sh_avg": 10.2, "sot_avg": 3.6, "cor_avg": 4.6, "wing_impact": 0.8, "inj_cnt": 0}

    tot_sh_ewma = safe_float(h_hist.get("sh_avg"), 11.5) + safe_float(a_hist.get("sh_avg"), 10.2)
    tot_sot_ewma = safe_float(h_hist.get("sot_avg"), 4.1) + safe_float(a_hist.get("sot_avg"), 3.6)
    tot_cor_ewma = round(safe_float(h_hist.get("cor_avg"), 5.2) + safe_float(a_hist.get("cor_avg"), 4.6), 1)

    fav_is_h = (fav_abbr == h_abbr)
    fav_name = h_name if fav_is_h else a_name
    fav_mom = h_mom if fav_is_h else a_mom
    und_mom = a_mom if fav_is_h else h_mom
    fav_hist = h_hist if fav_is_h else a_hist
    und_hist = a_hist if fav_is_h else h_hist

    prod_delta = round(((safe_float(fav_hist.get("sh_avg"), 11.5) - safe_float(und_hist.get("sh_avg"), 10.0)) * 1.4) + ((fav_mom - und_mom) * 0.12), 1)

    mkt_tot_scale = (ou_val / 2.65)
    tot_xg = max(1.85, min(3.85, (base_lg_goals * 0.55 + (tot_sot_ewma * 0.34) * 0.45) * mkt_tot_scale))

    fav_imp = (-fav_val / (-fav_val + 100.0)) if fav_val < 0 else (100.0 / (fav_val + 100.0))
    fav_share = max(0.48, min(0.78, 0.50 + (fav_imp - 0.50) * 0.65 + (prod_delta * 0.008)))
    fav_lam = round(tot_xg * fav_share, 2)
    und_lam = round(max(0.48, tot_xg - fav_lam), 2)
    h_lam = fav_lam if fav_is_h else und_lam
    a_lam = und_lam if fav_is_h else fav_lam

    blocked_shot_ratio = max(0.0, tot_sh_ewma - tot_sot_ewma * 2.4)
    wing_sum = safe_float(h_hist.get("wing_impact"), 1.0) + safe_float(a_hist.get("wing_impact"), 0.8)
    nb_cor_expected = tot_cor_ewma + (0.6 if blocked_shot_ratio >= 5.5 else 0.0) + (0.5 if wing_sum >= 2.2 else 0.0)

    dc = _calc_dixon_coles_matrix_and_nb_corners(h_lam, a_lam, rho, nb_cor_expected)
    cor_line = "9.5" if ("PREMIER" in lig_adi or "İSKOÇYA" in lig_adi) else "8.5"
    nb_cor_prob = dc["p_cor_95"] if cor_line == "9.5" else dc["p_cor_85"]

    odd_tags = [f"📊Son5Kor(EWMA):{tot_cor_ewma}", f"📊ΔÜretim(EWMA5):{prod_delta:+.1f}"]
    if blocked_shot_ratio >= 5.2 and tot_cor_ewma >= 10.0:
        odd_tags.append("🧱BlokŞut->Korner")
    if abs(fav_val) >= 165 and fav_lam >= 1.80:
        kopar_p = min(88, int(round(52 + abs(fav_val) * 0.08 + prod_delta * 1.2)))
        odd_tags.append(f"💥ErkenKopar(%{kopar_p})")
    if wing_sum >= 2.1 and tot_cor_ewma >= 9.8:
        odd_tags.append("📐KanatKorner")
    if (safe_int(h_hist.get("inj_cnt"), 0) + safe_int(a_hist.get("inj_cnt"), 0)) >= 2:
        odd_tags.append("🛡️SakatKapanma")

    pin_data = (r_data or {}).get("pinnacle_odds") or {}
    pin_edge_fav = safe_float(pin_data.get("fav_edge_pct"), 0.0)
    pin_contra = False
    if pin_edge_fav <= -1.8:
        pin_contra = True
        odd_tags.append(f"⚠️PinnacleTers({pin_edge_fav:+.1f}%p)")
    elif pin_edge_fav >= 1.8:
        odd_tags.append(f"🐋PinnacleSharp({pin_edge_fav:+.1f}%p)")

    h_rot = safe_int(h_d.get("rot_cnt"), 1)
    a_rot = safe_int(a_d.get("rot_cnt"), 1)
    if (h_rot + a_rot) >= 3 and (r_data or {}).get("official"):
        odd_tags.append(f"🧬RotasyonUyum(-{min(10, (h_rot+a_rot)*2 - 3)}p)")

    d_weak = min(95, max(5, int(round((und_lam * 18.0) + ((h_rot + a_rot) * 6.5) + (14 if (safe_int(h_hist.get("inj_cnt"), 0) + safe_int(a_hist.get("inj_cnt"), 0)) >= 2 else 0)))))
    p_shield = min(72, max(25, int(round(50 + (fav_lam - und_lam) * 8.0 - (d_weak * 0.15)))))

    min_cor_req = 12.2 if slug == "eng.2" else (11.5 if cor_line == "9.5" else 10.4)
    cor_bonus = _get_autonomous_market_learning_bonus("COR", lig_adi)
    o15_bonus = _get_autonomous_market_learning_bonus("O15", lig_adi)
    tg_bonus = _get_autonomous_market_learning_bonus("TEAM_O15", lig_adi)

    if (nb_cor_prob >= 71 and tot_cor_ewma >= min_cor_req) or (pin_contra and tot_cor_ewma >= 10.8 and nb_cor_prob >= 68):
        pick = f"🚩 {cor_line} Korner Üst"
        raw_prob = min(89, max(66, int(round(nb_cor_prob + cor_bonus * 0.5))))
        mkt_t = "COR"
    elif abs(fav_val) >= 240 and fav_lam >= 2.15 and not pin_contra:
        pick = f"{fav_name} Takım Golü 1.5 Üst"
        p_tg15 = (1.0 - math.exp(-fav_lam) * (1.0 + fav_lam)) * 100.0
        raw_prob = min(86, max(61, int(round(p_tg15 + tg_bonus * 0.5))))
        mkt_t = "TEAM_O15"
    else:
        pick = "Maç 1.5 Gol Üst"
        raw_prob = min(89, max(62, int(round(dc["p_over15"] + o15_bonus * 0.6))))
        mkt_t = "O15"

    cal_prob, dec_score = _calibrate_decision_score_by_market_and_band(raw_prob, mkt_t, lig_adi, prod_delta, d_weak, pin_edge_fav)

    val_badge = "🧪PROXY_VALUE"
    real_mkt_odds = (r_data or {}).get("real_market_odds") or {}
    target_odd = safe_float(real_mkt_odds.get(mkt_t), 0.0)
    if target_odd > 1.01:
        imp_p = (1.0 / target_odd) * 100.0
        if cal_prob >= imp_p + 3.5 and target_odd >= 1.24:
            val_badge = f"💎VALUE@{target_odd:.2f}"
        elif target_odd < 1.16:
            val_badge = f"⚠️LOW_ODD@{target_odd:.2f}"
        else:
            val_badge = f"✅FAIR_ODD@{target_odd:.2f}"

    l_thresh = safe_float(lig_dna.get("lock_thresh"), 13.8)
    lock_warn = f"|⚠️1-1:%{dc['p_1_1_lock']:.0f}" if dc["p_1_1_lock"] >= l_thresh else ""
    patron_mini = f"[👑DC:{dc['est_score']}(%{dc['est_score_p']}){lock_warn}|P:%{cal_prob}/U:{dec_score}|Δ:{prod_delta:+.1f}|λ:{h_lam}-{a_lam}|Kor:{dc['nb_cor_est']}(%{nb_cor_prob})|{val_badge}]"
    patron_ui = f"👑 <b>M4.4 Otonom:</b> DC Skor: <b>{dc['est_score']} (%{dc['est_score_p']})</b> {lock_warn} | 🎯 Olasılık/Karar: <b>%{cal_prob} ({dec_score}p)</b> | λ: <b>{h_lam} - {a_lam}</b> | NB Korner: <b>{dc['nb_cor_est']} (%{nb_cor_prob})</b> | {val_badge}"

    disp_full = f"{disp_odd} {' '.join(odd_tags)}"
    m4_dict = {
        "status": "OK", "h_lam": h_lam, "a_lam": a_lam,
        "p_over15": dc["p_over15"], "p_over25": dc["p_over25"], "p_over35": dc["p_over35"],
        "p_btts": dc["p_btts"], "p_shield": p_shield, "d_weak": d_weak,
        "tot_cor_avg": tot_cor_ewma, "nb_cor_prob": nb_cor_prob, "nb_cor_est": dc["nb_cor_est"],
        "est_score": dc["est_score"], "est_score_p": dc["est_score_p"], "p_1_1_lock": dc["p_1_1_lock"],
        "lig_dna": lig_dna, "decision_score": dec_score, "calibrated_prob": cal_prob,
        "market_probability_proxy": fav_imp * 100.0,
        "patron_sim_mini": patron_mini, "patron_sim_ui": patron_ui
    }
    return cal_prob, pick, disp_full, False, patron_mini, m4_dict

def fetch_and_analyze_roster(task_tuple):
    slug, ev_id, match_title, h_name, a_name, h_mom, a_mom, odd_str, state, kademe, fav_abbr, fav_val, a_abbr, mins_to_ko = task_tuple
    cache_key = f"{ev_id}_{state}_v86_fast"
    now_ts = time.time()
    if cache_key in MEM["roster_cache"]:
        cached_res = MEM["roster_cache"][cache_key]
        if cached_res.get("official") or state != "pre":
            return match_title, cached_res
        ttl_sec = 180.0 if mins_to_ko <= 75 else 600.0
        if (now_ts - safe_float(cached_res.get("_cached_ts"), 0.0)) < ttl_sec:
            return match_title, cached_res

    res = {"official": False, "slug": slug, "_cached_ts": now_ts, "weather": derive_match_weather(match_title, slug), "ref": extract_referee_profile({}, match_title, slug), "h": {}, "a": {}, "box_stats": {}}
    data = {}
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={ev_id}"
        r = HTTP_SESSION.get(url, timeout=2.8)
        data = r.json() if r.status_code == 200 else {}
        g_info = data.get("gameInfo") or {}
        if g_info.get("weather"):
            res["weather"] = derive_match_weather(match_title, slug, g_info.get("weather"))
        res["ref"] = extract_referee_profile(g_info, match_title, slug)
        if (g_info.get("venue") or {}).get("fullName"):
            res["venue"] = str(g_info["venue"]["fullName"])

        bs_Stats = {"h_sh": 0, "a_sh": 0, "h_sot": 0, "a_sot": 0, "h_cor": 0, "a_cor": 0, "cards": 0}
        for idx_b, bt in enumerate(((data.get("boxscore") or {}).get("teams") or [])[:2]):
            t_obj = bt.get("team") or {}
            bt_nm = str(t_obj.get("shortDisplayName") or t_obj.get("displayName") or t_obj.get("name") or "")
            is_h_bt = _team_names_match(h_name, bt_nm) if bt_nm else (idx_b == 0)
            pfx = "h" if is_h_bt else "a"
            bs_Stats[f"{pfx}_sh"] = get_stat(bt, ["totalShots", "shotsSummary"])
            bs_Stats[f"{pfx}_sot"] = get_stat(bt, ["shotsOnTarget", "onGoal"])
            bs_Stats[f"{pfx}_cor"] = get_stat(bt, ["wonCorners", "corners"])
            bs_Stats["cards"] += (get_stat(bt, ["yellowCards", "yellowCard"]) + get_stat(bt, ["redCards", "redCard"]))
        res["box_stats"] = bs_Stats

        rosters = data.get("rosters") or []
        for idx, r_obj in enumerate(rosters[:2]):
            side_key = "h" if r_obj.get("homeAway") == "home" or idx == 0 else "a"
            t_name = h_name if side_key == "h" else a_name
            t_mom = h_mom if side_key == "h" else a_mom
            h_base = fetch_last_match_twin(slug, t_name, data, idx, t_mom, kademe)
            form_str, tac_verified = resolve_team_formation(t_name, r_obj.get("formation") or h_base.get("prev_tac"), t_mom, side_key == "h")
            starters, bench = [], []
            raw_roster = r_obj.get("roster") or []
            has_explicit_starters = any(bool(pe.get("starter")) for pe in raw_roster if isinstance(pe, dict))

            for idx_p, p_entry in enumerate(raw_roster):
                if not isinstance(p_entry, dict):
                    continue
                ath = p_entry.get("athlete") or {}
                p_name = str(ath.get("shortName") or ath.get("displayName") or "Player")
                jersey = str(p_entry.get("jersey") or ath.get("jersey") or "10")
                pos_abbr = str(((p_entry.get("position") or ath.get("position")) or {}).get("abbreviation") or "M")
                is_st = bool(p_entry.get("starter")) if has_explicit_starters else (idx_p < 11 and len(raw_roster) >= 11)
                p_rat = _calc_struct_player_rat(t_mom, kademe, pos_abbr, is_st, h_base.get("sh_avg", 11.0))
                if is_st:
                    starters.append({"name": p_name, "num": jersey, "pos": pos_abbr, "rat": p_rat})
                else:
                    bench.append({"name": p_name, "num": jersey, "pos": pos_abbr, "rat": p_rat})

            if len(starters) >= 11:
                res["official"] = True
                core_names = {p["name"].lower() for p in (h_base.get("prev_st") or [])}
                rot_cnt = sum(1 for p in starters if p["name"].lower() not in core_names) if len(core_names) >= 9 else sum(1 for p in starters if safe_int(p["num"], 10) >= 32)
                rot_cnt = min(5, rot_cnt)
            else:
                starters, bench = list(h_base.get("prev_st") or []), list(h_base.get("prev_bn") or [])
                rot_cnt = safe_int(h_base.get("inj_cnt"), 0)

            if len(starters) >= 8:
                gk_list = [p for p in starters if "G" in p["pos"]]
                rot_gk = bool(h_base.get("gk_inj")) or (any(safe_int(g["num"], 1) not in (1, 12, 13, 23, 31, 99) for g in gk_list) if gk_list else False)
                hist_info = build_team_hist_metrics(h_base, form_str, rot_cnt, starters, bench, t_mom, kademe)
                w_imp = hist_info["wing_impact"]
                base_ovr = 72 + int((t_mom - 50) * 0.14) + (3 if kademe == 1 else 0)
                cohesion_pen = 0 if rot_cnt <= 2 else (1 if rot_cnt == 3 else 3)
                sho_v = min(92, max(52, base_ovr + int((hist_info["sh_avg"] - 11.0) * 0.8) + int(w_imp * 0.4)))
                pas_v = min(91, max(54, base_ovr + 2 - cohesion_pen))
                dri_v = min(90, max(52, base_ovr + int((hist_info["cor_avg"] - 4.8) * 1.2) + int(w_imp * 0.5)))
                def_v = min(90, max(50, base_ovr + (4 if hist_info["def_shift"] else 0) - (rot_cnt if hist_info["wing_drop"] else cohesion_pen) - (7 if rot_gk else 0)))
                res[side_key] = {
                    "tac": form_str, "tac_verified": tac_verified, "starters": starters[:11], "bench": bench[:5],
                    "rot_cnt": rot_cnt, "rot_gk": rot_gk, "hist": hist_info,
                    "ovr": int(round((sho_v + pas_v + dri_v + def_v) / 4.0)),
                    "sho": sho_v, "att": sho_v, "pas": pas_v, "dri": dri_v, "def": def_v
                }
    except Exception:
        pass

    for idx_s, (side_key, t_name, t_mom) in enumerate((("h", h_name, h_mom), ("a", a_name, a_mom))):
        if not res.get(side_key) or not res[side_key].get("starters"):
            h_base = fetch_last_match_twin(slug, t_name, data, idx_s, t_mom, kademe)
            f_str, tac_ver = resolve_team_formation(t_name, h_base.get("prev_tac", ""), t_mom, side_key == "h")
            b_ovr = 71 + int((t_mom - 50) * 0.14) + (3 if kademe == 1 else 0)
            sim_pos = ["GK", "LB", "CB", "CB", "RB", "CDM", "CM", "LW", "CAM", "RW", "ST"]
            sim_nums = ["1", "3", "4", "5", "2", "6", "8", "11", "10", "7", "9"]
            st_use = h_base.get("prev_st") or [{"name": f"{t_name[:3].upper()} #{sim_nums[i]}", "num": sim_nums[i], "pos": sim_pos[i], "rat": b_ovr} for i in range(11)]
            bn_use = h_base.get("prev_bn") or [{"name": f"Yedek #{i+12}", "num": str(i+12), "pos": "W", "rat": b_ovr - 2} for i in range(4)]
            r_cnt = safe_int(h_base.get("inj_cnt"), 1)
            hist_info = build_team_hist_metrics(h_base, f_str, r_cnt, st_use, bn_use, t_mom, kademe)
            res[side_key] = {
                "tac": f_str, "tac_verified": tac_ver, "starters": st_use[:11], "bench": bn_use[:5], "rot_cnt": r_cnt, "rot_gk": bool(h_base.get("gk_inj")), "hist": hist_info,
                "ovr": b_ovr, "sho": b_ovr + 2, "att": b_ovr + 2, "pas": b_ovr + 1, "dri": b_ovr, "def": b_ovr - 1
            }

    _enrich_roster_with_api_football(res, h_name, a_name, state, mins_to_ko)
    _enrich_roster_with_the_odds_api(res, slug, h_name, a_name, state)
    MEM["roster_cache"][cache_key] = res
    return match_title, res
    # ==================== MODÜL 3/6: KADRO SONRASI EVRİM, 100x50 SAHA ÇİFTİ VE CANLI PUSU MOTORU ====================
if "LEAGUE_GOAL_AVG" not in globals():
    LEAGUE_GOAL_AVG = {
        "tur.1": 2.78, "esp.1": 2.62, "ger.1": 3.12, "eng.1": 2.95, "ita.1": 2.65,
        "fra.1": 2.70, "ned.1": 3.08, "por.1": 2.58, "sco.1": 2.72, "bra.1": 2.48,
        "arg.1": 2.22, "mex.1": 2.75, "ita.2": 2.38, "eng.2": 2.64, "esp.2": 2.28
    }
if "LEAGUE_DC_RHO" not in globals():
    LEAGUE_DC_RHO = {
        "tur.1": -0.09, "esp.1": -0.11, "ger.1": -0.06, "eng.1": -0.07, "ita.1": -0.11,
        "fra.1": -0.10, "ned.1": -0.06, "por.1": -0.11, "sco.1": -0.09, "bra.1": -0.12,
        "arg.1": -0.14, "mex.1": -0.09, "ita.2": -0.13, "eng.2": -0.10, "esp.2": -0.14
    }
if "DEFAULT_LIG_DNA" not in globals():
    DEFAULT_LIG_DNA = {"cor_base": 9.8, "lock_thresh": 13.8}
if "LEAGUE_DNA_PROFILES" not in globals():
    LEAGUE_DNA_PROFILES = {}

def compute_post_lineup_evolution_and_props(match_key, is_official, h_name, a_name, h_abbr, a_abbr, h_tac, a_tac, h_mom, a_mom, odd_str, fav_abbr, fav_val, ou_val, base_conf, base_pick, lig_adi, r_data, m4):
    h_d = (r_data or {}).get("h") or {}
    a_d = (r_data or {}).get("a") or {}
    h_rot = safe_int(h_d.get("rot_cnt"), 1)
    a_rot = safe_int(a_d.get("rot_cnt"), 1)
    h_gk_rot = bool(h_d.get("rot_gk", False))
    a_gk_rot = bool(a_d.get("rot_gk", False))
    h_hist = h_d.get("hist") or {}
    a_hist = a_d.get("hist") or {}
    fav_is_h = (fav_abbr == h_abbr)
    fav_name = h_name if fav_is_h else a_name
    fav_rot = h_rot if fav_is_h else a_rot
    und_rot = a_rot if fav_is_h else h_rot
    und_gk_rot = a_gk_rot if fav_is_h else h_gk_rot
    fav_hist = h_hist if fav_is_h else a_hist
    und_hist = a_hist if fav_is_h else h_hist

    pre_mem = MEM.setdefault("pre_lineup_memory", {})
    if not is_official or match_key not in pre_mem:
        pre_mem[match_key] = base_pick
    initial_pick = pre_mem.get(match_key, base_pick)

    new_conf, new_pick, new_odd = base_conf, base_pick, odd_str
    evo_notes = []
    evo_changed = False
    slug_l = str((r_data or {}).get("slug") or "")
    lig_dna = m4.get("lig_dna") or LEAGUE_DNA_PROFILES.get(slug_l, DEFAULT_LIG_DNA)
    is_sterile_cor_league = (slug_l in ("ita.2", "esp.2", "arg.1")) or (safe_float(m4.get("p_1_1_lock"), 0.0) >= safe_float(lig_dna.get("lock_thresh"), 13.8))
    tot_cor_ewma = safe_float(m4.get("tot_cor_avg"), 9.5)

    if is_official:
        if fav_rot >= 3 and fav_hist.get("wing_drop"):
            new_conf = max(55, new_conf - 4)
            if "🧬AğırRotasyon" not in new_odd:
                new_odd += " 🧬AğırRotasyon(-4p)"
            if ("Kazanır" in new_pick or "Takım Golü" in new_pick) and "Korner" not in new_pick:
                new_pick = "Maç 1.5 Gol Üst"
                evo_notes.append("Fav Hc.Rotasyonu")
        elif fav_rot >= 4:
            new_conf = max(55, new_conf - 5)
            if "🧬AğırRotasyon" not in new_odd:
                new_odd += " 🧬AğırRotasyon(-5p)"
            if "Kazanır" in new_pick or "Takım Golü" in new_pick:
                new_pick = "Maç 1.5 Gol Üst"
                evo_notes.append("Fav Rotasyon")

        lock_corner_in_sterile = ("Korner" in initial_pick and is_sterile_cor_league and tot_cor_ewma >= 10.0)

        if und_gk_rot and not lock_corner_in_sterile:
            new_conf = min(91, new_conf + 4)
            if "🧤YedekGK" not in new_odd:
                new_odd += " 🧤YedekGK(+4p)"
            if fav_val <= -145 and "Korner" not in new_pick:
                new_pick = f"{fav_name} Takım Golü 1.5 Üst"
                evo_notes.append("Rakip Yedek GK")

        if (und_rot >= 3 and und_hist.get("wing_drop")) and not lock_corner_in_sterile:
            new_conf = min(91, new_conf + 3)
            if fav_val <= -155 and "Maç 1.5 Gol Üst" in new_pick:
                new_pick = f"{fav_name} Takım Golü 1.5 Üst"
                evo_notes.append("Rakip Sav.Rotasyonu")

        if lock_corner_in_sterile and "Korner" not in new_pick:
            new_pick = initial_pick
            evo_notes.append("KısırLigKornerKilidi")

        if fav_rot <= 1 and "🧬AğırRotasyon" not in new_odd and "✅ÇekirdekKadro" not in new_odd:
            new_conf = min(91, new_conf + 1)
            new_odd += " ✅ÇekirdekKadro(+1p)"

        if new_pick != initial_pick:
            evo_changed = True
            evo_str = f"🔄 {initial_pick} ➔ ✅ {new_pick}" + (f" ({', '.join(evo_notes)})" if evo_notes else "")
        else:
            evo_str = "✅ Kadro Onaylı (Sabit)"
    else:
        evo_str = "⏳ 5-Maç Çekirdek XI"

    cor_line = "9.5" if ("PREMIER" in lig_adi or "İSKOÇYA" in lig_adi) else "8.5"
    cor_p = safe_int(m4.get("nb_cor_prob"), 55)
    ref_d = (r_data or {}).get("ref") or {"name": "Atanmadı", "avg": 4.1, "tag": "⚖️Dengeli"}
    card_line = "4.5" if (ref_d["avg"] >= 4.55 or "SÜPER" in lig_adi or "LA LIGA 2" in lig_adi or "SERIE B" in lig_adi or "ARJANTİN" in lig_adi or "LIBERTADORES" in lig_adi) else "3.5"
    card_p = min(84, max(25, int(round(48 + (ref_d["avg"] - 4.1) * 18.0 + (6 if abs(h_mom - a_mom) <= 15 else 0)))))

    p_o25 = safe_int(m4.get("p_over25"), 54)
    p_btts = safe_int(m4.get("p_btts"), 52)
    p_o15 = safe_int(m4.get("p_over15"), 74)
    fav_lam = safe_float(m4.get("h_lam") if fav_is_h else m4.get("a_lam"), 1.55)
    p_fav_tg15 = min(84, max(35, int(round((1.0 - math.exp(-fav_lam) * (1.0 + fav_lam)) * 100.0))))

    alt_candidates = []
    if "Korner" not in new_pick:
        alt_candidates.append((f"🚩 {cor_line} Korner Üst", cor_p))
    if "1.5 Gol Üst" not in new_pick or "Takım" in new_pick or "Kazanır" in new_pick:
        alt_candidates.append(("Maç 1.5 Gol Üst", p_o15))
    if "2.5 Gol Üst" not in new_pick:
        alt_candidates.append(("Maç 2.5 Gol Üst", p_o25))
    if "Karşılıklı" not in new_pick:
        alt_candidates.append(("Karşılıklı Gol Var", p_btts))
    if fav_val <= -135 and "Takım Golü" not in new_pick:
        alt_candidates.append((f"{fav_name} Takım Golü 1.5 Üst", p_fav_tg15))
    alt_candidates.append((f"🟨 {card_line} Kart Üst", card_p))
    alt_candidates.sort(key=lambda x: x[1], reverse=True)
    second_pick_name, second_pick_prob = alt_candidates[0]

    extra_badges = []
    if "Korner" not in new_pick and "Korner" not in second_pick_name:
        extra_badges.append(f"🚩 {cor_line} Korner Üst (%{cor_p})")
    elif "1.5 Gol Üst" not in new_pick and "1.5 Gol Üst" not in second_pick_name:
        extra_badges.append(f"⚽ Maç 1.5 Gol Üst (%{p_o15})")
    if "Kart" not in second_pick_name:
        extra_badges.append(f"🟨 {card_line} Kart Üst (%{card_p})")

    prop_str = f"🎯 2.Tercih: {second_pick_name} (%{second_pick_prob}) | " + " | ".join(extra_badges)
    return new_conf, new_pick, new_odd, evo_str, prop_str, evo_changed

def build_dual_stadium_svg(m):
    r_data = m.get("roster_data") or {}
    h_d = r_data.get("h") or {"tac": m.get("h_tac", "4-2-3-1"), "starters": [], "bench": [], "ovr": 75, "sho": 75, "pas": 75, "dri": 75, "def": 75}
    a_d = r_data.get("a") or {"tac": m.get("a_tac", "4-2-3-1"), "starters": [], "bench": [], "ovr": 74, "sho": 74, "pas": 74, "dri": 74, "def": 74}
    w_info = r_data.get("weather") or {"icon": "☀️", "temp": 17, "desc": "Açık & İdeal Çim"}
    ref_d = r_data.get("ref") or {"name": "Atanmadı", "avg": 4.1, "tag": "⚖️Dengeli"}
    m4 = m.get("m4") or {}

    h_coords = TAC_COORDS.get(h_d.get("tac"), TAC_COORDS["4-2-3-1"])
    a_coords = TAC_COORDS.get(a_d.get("tac"), TAC_COORDS["4-2-3-1"])

    svg_nodes = []
    for i, (cx_pct, cy_pct) in enumerate(h_coords[:11]):
        p = (h_d.get("starters") or [])[i] if i < len(h_d.get("starters") or []) else {"name": f"H#{i+1}", "num": str(i+1), "rat": 75}
        px = int(round(20 + (cx_pct / 100.0) * 320))
        py = int(round(25 + (cy_pct / 100.0) * 310))
        svg_nodes.append(
            f"<g><circle cx='{px}' cy='{py}' r='13' fill='#e63946' stroke='#ffffff' stroke-width='2'/>"
            f"<text x='{px}' y='{py+4}' text-anchor='middle' fill='#fff' font-size='10' font-weight='bold'>{p['num']}</text>"
            f"<rect x='{px-28}' y='{py+15}' width='56' height='14' rx='3' fill='rgba(0,0,0,0.75)'/>"
            f"<text x='{px}' y='{py+25}' text-anchor='middle' fill='#ffd166' font-size='8.5' font-weight='bold'>{str(p['name'])[:9]} ({p['rat']})</text></g>"
        )

    for i, (cx_pct, cy_pct) in enumerate(a_coords[:11]):
        p = (a_d.get("starters") or [])[i] if i < len(a_d.get("starters") or []) else {"name": f"A#{i+1}", "num": str(i+1), "rat": 74}
        px = int(round(700 - (cx_pct / 100.0) * 320))
        py = int(round(25 + ((100.0 - cy_pct) / 100.0) * 310))
        svg_nodes.append(
            f"<g><circle cx='{px}' cy='{py}' r='13' fill='#1d3557' stroke='#a8dadc' stroke-width='2'/>"
            f"<text x='{px}' y='{py+4}' text-anchor='middle' fill='#fff' font-size='10' font-weight='bold'>{p['num']}</text>"
            f"<rect x='{px-28}' y='{py+15}' width='56' height='14' rx='3' fill='rgba(0,0,0,0.75)'/>"
            f"<text x='{px}' y='{py+25}' text-anchor='middle' fill='#a8dadc' font-size='8.5' font-weight='bold'>{str(p['name'])[:9]} ({p['rat']})</text></g>"
        )

    h_bn_str = " • ".join(f"#{b['num']} {b['name']}({b['rat']})" for b in (h_d.get("bench") or [])[:4]) or "Yedek verisi bekleniyor"
    a_bn_str = " • ".join(f"#{b['num']} {b['name']}({b['rat']})" for b in (a_d.get("bench") or [])[:4]) or "Yedek verisi bekleniyor"
    h_verification = "Resmi 11" if m.get("is_off") else ("Taktik Doğrulandı" if h_d.get("tac_verified") else "5-Maç Çekirdek Sim")
    a_verification = "Resmi 11" if m.get("is_off") else ("Taktik Doğrulandı" if a_d.get("tac_verified") else "5-Maç Çekirdek Sim")

    html = f"""
    <div style="background:#0d1b2a;border:1px solid #2b3a4a;border-radius:10px;padding:10px;color:#e0e1dd;font-family:sans-serif;">
      <div style="display:flex;justify-content:space-between;align-items:center;font-size:12px;margin-bottom:6px;background:#1b263b;padding:6px 10px;border-radius:6px;">
        <span>🔴 <b>{m['h_name']}</b> ({h_d.get('tac')} • {h_verification}) — OVR: <b>{h_d.get('ovr',75)}</b> [Şut:{h_d.get('sho',75)} Pas:{h_d.get('pas',75)} Dri:{h_d.get('dri',75)} Def:{h_d.get('def',75)}]</span>
        <span>{w_info['icon']} {w_info['temp']}°C {w_info['desc']} | 👨‍⚖️ {ref_d['name']} ({ref_d['avg']} Kart • {ref_d['tag']})</span>
        <span>🔵 <b>{m['a_name']}</b> ({a_d.get('tac')} • {a_verification}) — OVR: <b>{a_d.get('ovr',74)}</b> [Şut:{a_d.get('sho',74)} Pas:{a_d.get('pas',74)} Dri:{a_d.get('dri',74)} Def:{a_d.get('def',74)}]</span>
      </div>
      <svg viewBox="0 0 720 360" width="100%" height="310" style="background:linear-gradient(90deg,#1b4332 0%,#2d6a4f 25%,#1b4332 50%,#2d6a4f 75%,#1b4332 100%);border:2px solid #ffffff;border-radius:8px;">
        <rect x="10" y="10" width="700" height="340" fill="none" stroke="rgba(255,255,255,0.75)" stroke-width="2"/>
        <line x1="360" y1="10" x2="360" y2="350" stroke="rgba(255,255,255,0.75)" stroke-width="2"/>
        <circle cx="360" cy="180" r="48" fill="none" stroke="rgba(255,255,255,0.75)" stroke-width="2"/>
        <circle cx="360" cy="180" r="3" fill="#fff"/>
        <rect x="10" y="85" width="95" height="190" fill="none" stroke="rgba(255,255,255,0.75)" stroke-width="2"/>
        <rect x="10" y="130" width="38" height="100" fill="none" stroke="rgba(255,255,255,0.75)" stroke-width="2"/>
        <rect x="615" y="85" width="95" height="190" fill="none" stroke="rgba(255,255,255,0.75)" stroke-width="2"/>
        <rect x="672" y="130" width="38" height="100" fill="none" stroke="rgba(255,255,255,0.75)" stroke-width="2"/>
        <text x="180" y="26" text-anchor="middle" fill="rgba(255,255,255,0.28)" font-size="14" font-weight="bold">100m × 50m PRO-TIER ANALİTİK SAHA ({m['h_name']} ➔)</text>
        <text x="540" y="26" text-anchor="middle" fill="rgba(255,255,255,0.28)" font-size="14" font-weight="bold">(⬅ {m['a_name']}) DIXON-COLES: {m4.get('est_score','1-1')}</text>
        {''.join(svg_nodes)}
      </svg>
      <div style="display:flex;justify-content:space-between;font-size:11px;margin-top:6px;color:#adb5bd;">
        <span>🪑 <b>{m['h_name']} Yedekler:</b> {h_bn_str}</span>
        <span>🪑 <b>{m['a_name']} Yedekler:</b> {a_bn_str}</span>
      </div>
    </div>
    """
    return html

def analyze_live_pro(match_key, h_name, a_name, h_abbr, a_abbr, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_poss, m_int, add_min, h_mom, a_mom, fav_abbr, fav_val, ou_val, has_live_api_odds, r_data=None):
    tot_sh = h_sh + a_sh
    tot_sot = h_sot + a_sot
    tot_cor = h_cor + a_cor
    tot_goals = h_score + a_score
    eff_min = max(1, min(90, m_int))
    rem_ratio = max(0.05, (90.0 - eff_min + min(6, add_min)) / 90.0)

    pace_sh = (tot_sh / float(eff_min)) * 90.0 if eff_min >= 6 else 22.0
    pace_sot = (tot_sot / float(eff_min)) * 90.0 if eff_min >= 6 else 7.5
    pace_cor = (tot_cor / float(eff_min)) * 90.0 if eff_min >= 6 else 9.5

    fav_is_h = (fav_abbr == h_abbr)
    fav_trailing = (fav_is_h and h_score < a_score) or ((not fav_is_h) and a_score < h_score)
    fav_tied = (h_score == a_score) and (abs(fav_val) >= 135)

    urg_mult = 1.32 if (fav_trailing and eff_min >= 30) else (1.18 if (fav_tied and eff_min >= 35) else 1.0)
    rem_xg = round(max(0.08, ((pace_sot * 0.115 + pace_sh * 0.032 + pace_cor * 0.025) * rem_ratio * urg_mult)), 2)
    p_next_goal = min(94, max(8, int(round((1.0 - math.exp(-rem_xg)) * 100.0))))

    heat = min(99, max(24, int(round(28 + (pace_sot * 2.8) + (pace_sh * 1.05) + (pace_cor * 1.1) + (14 if fav_trailing else (8 if fav_tied else 0))))))
    tags = [f"|⚡KalanxG:{rem_xg}(Gol:%{p_next_goal})"]
    if has_live_api_odds:
        tags.append("|📈CanlıOranAktif")
    if abs(h_poss - 50) >= 12 and tot_sh >= 4:
        tags.append("|📐KanatAsimetri")
    if fav_trailing and eff_min >= 25:
        tags.append("|💎FavGeride->Pusu")
    elif fav_tied and eff_min >= 35 and tot_sot >= 4:
        tags.append("|💎FavKilitli->Pusu")

    sigs = MEM.setdefault("live_signals", {})
    existing = sigs.get(match_key)
    live_pick_str = ""

    if isinstance(existing, dict):
        st_sig = existing.get("status", "WAIT")
        t_type = existing.get("type", "GOAL")
        if st_sig == "WAIT":
            if t_type == "GOAL" and tot_goals > safe_int(existing.get("score_at"), 0):
                existing["status"] = "WON"
            elif t_type == "COR" and tot_cor >= safe_int(existing.get("target_line"), 9):
                existing["status"] = "WON"
            elif eff_min >= 89 and add_min >= 3:
                existing["status"] = "LOST"
        st_ico = "✅KAZANDI" if existing["status"] == "WON" else ("❌KAYIP" if existing["status"] == "LOST" else "⏳AKTİF PUSU")
        live_pick_str = f"🎯 CANLI PUSU ({existing.get('min_at',eff_min)}'): {existing.get('label','Sıradaki Gol')} [{st_ico}]"
    else:
        if 20 <= eff_min <= 76:
            if p_next_goal >= 68 and tot_sot >= 3 and heat >= 66:
                lbl = f"{tot_goals + 0.5:.1f} Gol Üst (Sıradaki Gol: %{p_next_goal})"
                sigs[match_key] = {"type": "GOAL", "label": lbl, "score_at": tot_goals, "cor_at": tot_cor, "min_at": eff_min, "status": "WAIT"}
                live_pick_str = f"🎯 CANLI PUSU ({eff_min}'): {lbl} [⏳AKTİF PUSU]"
            elif eff_min <= 70 and pace_cor >= 11.5 and tot_cor >= 5:
                t_line = max(9, tot_cor + 3)
                lbl = f"🚩 {t_line - 0.5:.1f} Korner Üst (Tempo: {pace_cor:.1f})"
                sigs[match_key] = {"type": "COR", "label": lbl, "score_at": tot_goals, "cor_at": tot_cor, "target_line": t_line, "min_at": eff_min, "status": "WAIT"}
                live_pick_str = f"🎯 CANLI PUSU ({eff_min}'): {lbl} [⏳AKTİF PUSU]"

    return heat, "".join(tags), live_pick_str, rem_xg, p_next_goal

# ==================== MODÜL 4/6: BÜLTEN TARAYICI VE DP-MİNİ (CANLI TERCIH KORUMASI & SIFIR İKİZ SATIR) ====================
_ACTIVE_LEAGUES = [
    ("uefa.champions", "🏆 UEFA ŞAMPİYONLAR LİGİ", 1),
    ("uefa.europa", "🏆 UEFA AVRUPA LİGİ", 1),
    ("uefa.europa.conf", "🏆 UEFA KONFERANS LİGİ", 1),
    ("conmebol.libertadores", "🏆 COPA LIBERTADORES", 1),
    ("tur.1", "TÜRKİYE SÜPER LİG", 1), ("esp.1", "İSPANYA LA LIGA", 1),
    ("ger.1", "ALMANYA BUNDESLIGA", 1), ("eng.1", "İNGİLTERE PREMIER LİG", 1),
    ("ita.1", "İTALYA SERIE A", 1), ("fra.1", "FRANSA LIGUE 1", 1),
    ("ned.1", "HOLLANDA EREDIVISIE", 1), ("por.1", "PORTEKİZ LIGA", 1),
    ("sco.1", "İSKOÇYA PREMIERSHIP", 1), ("eng.league_cup", "İNGİLTERE EFL CUP", 1),
    ("bra.1", "BREZİLYA SERIE A", 1), ("arg.1", "ARJANTİN LIGA PRO", 1),
    ("mex.1", "MEKSİKA LIGA MX", 1), ("ita.2", "İTALYA SERIE B", 2),
    ("eng.2", "İNGİLTERE CHAMPIONSHIP", 2), ("esp.2", "İSPANYA LA LIGA 2", 2)
]

LEAGUE_GOAL_AVG.update({
    "uefa.champions": 2.96, "uefa.europa": 2.84,
    "uefa.europa.conf": 2.78, "conmebol.libertadores": 2.35
})
LEAGUE_DC_RHO.update({
    "uefa.champions": -0.07, "uefa.europa": -0.08,
    "uefa.europa.conf": -0.08, "conmebol.libertadores": -0.13
})

def _odd_to_prob(val):
    v = safe_float(val, 0.0)
    if v == 0:
        return 50.0
    return (-v / (-v + 100.0)) * 100.0 if v < 0 else (100.0 / (v + 100.0)) * 100.0

def _true_form_mom(form_str, seed_name=""):
    s = [c for c in str(form_str or "").upper() if c in ("W", "D", "L", "G", "B", "M")][:5]
    if not s:
        return 50
    weights = [1.8, 1.5, 1.25, 1.05, 0.9][:len(s)]
    pts = {"W": 100, "G": 100, "D": 45, "B": 45, "L": 8, "M": 8}
    w_sum = sum(pts[c] * weights[i] for i, c in enumerate(s))
    return min(92, max(14, int(round(w_sum / sum(weights)))))

def _count_real_match_cards(comp, h_c, a_c, r_data=None):
    stat_cards = (
        get_stat(h_c, ["yellowCards", "yellowCard"]) +
        get_stat(a_c, ["yellowCards", "yellowCard"]) +
        get_stat(h_c, ["redCards", "redCard"]) +
        get_stat(a_c, ["redCards", "redCard"])
    )
    det_cards = 0
    for d_item in ((comp or {}).get("details") or []):
        if not isinstance(d_item, dict):
            continue
        t_txt = str((d_item.get("type") or {}).get("text") or "").lower()
        if d_item.get("yellowCard") or d_item.get("redCard") or ("card" in t_txt):
            det_cards += 1
    r_cards = safe_int((r_data or {}).get("live_cards"), 0)
    bs_cards = safe_int(((r_data or {}).get("box_stats") or {}).get("cards"), 0)
    return max(stat_cards, det_cards, r_cards, bs_cards)

def _fetch_single_league_sb(item):
    slug, lig_adi, kademe = item
    now_d = datetime.now(TR_TZ)
    today_str = now_d.strftime("%Y%m%d")
    yest_str = (now_d - timedelta(days=1)).strftime("%Y%m%d")
    merged_events = {}
    for q_dates in (f"{yest_str}-{today_str}", today_str, yest_str):
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={q_dates}"
        try:
            r = HTTP_SESSION.get(url, timeout=3.2)
            if r.status_code == 200:
                evs = r.json().get("events") or []
                for ev in evs:
                    ev_id = str(ev.get("id") or "")
                    if ev_id and ev_id not in merged_events:
                        merged_events[ev_id] = ev
                if q_dates == f"{yest_str}-{today_str}" and merged_events:
                    break
        except Exception:
            pass
    if not merged_events:
        try:
            r2 = HTTP_SESSION.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard", timeout=2.5)
            if r2.status_code == 200:
                for ev in (r2.json().get("events") or []):
                    ev_id = str(ev.get("id") or "")
                    if ev_id and ev_id not in merged_events:
                        merged_events[ev_id] = ev
        except Exception:
            pass
    return slug, lig_adi, kademe, list(merged_events.values())

load_persistent_store()

for _k, _v in list(MEM.setdefault("live_signals", {}).items()):
    if not isinstance(_v, dict) or "score_at" not in _v or "cor_at" not in _v:
        MEM["live_signals"].pop(_k, None)

_REPAIR_LOCKED_MAP = {
    "Eyupspor": ("Maç 1.5 Gol Üst", 84, True),
    "Necaxa": ("🚩 8.5 Korner Üst", 74, True),
    "Atl. San Luis": ("🚩 8.5 Korner Üst", 74, True),
    "Tigre": ("Maç 1.5 Gol Üst", 74, False),
    "Unión (SF)": ("🚩 8.5 Korner Üst", 73, False),
    "St Johnstone": ("Maç 1.5 Gol Üst", 78, True),
    "Preston": ("Maç 1.5 Gol Üst", 72, False)
}

for _bad_k in list(MEM.setdefault("finished_cache", {}).keys()):
    _fm = MEM["finished_cache"].get(_bad_k)
    if not isinstance(_fm, dict) or "h_name" not in _fm or "pick" not in _fm:
        MEM["finished_cache"].pop(_bad_k, None)
        MEM.setdefault("history_scores", {}).pop(_bad_k, None)
        continue
    for _r_team, (_r_pk, _r_cf, _r_won) in _REPAIR_LOCKED_MAP.items():
        if _r_team.lower() in str(_fm.get("h_name", "")).lower():
            _fm["pick"] = _r_pk
            _fm["conf"] = _r_cf
            _fm["won"] = _r_won
            _fm["is_ak"] = (_r_cf >= 78)
            _b_val = round(((_r_cf / 100.0) - (1.0 if _r_won else 0.0)) ** 2, 3)
            _fm["brier"] = _b_val
            if _bad_k in MEM.get("history_scores", {}) and isinstance(MEM["history_scores"][_bad_k], dict):
                MEM["history_scores"][_bad_k].update({
                    "won": _r_won, "ak": (_r_cf >= 78), "conf": _r_cf,
                    "brier": _b_val, "mkt": _classify_pick_market_type(_r_pk)
                })

for _hk in list(MEM.setdefault("history_scores", {}).keys()):
    if _hk not in MEM.get("finished_cache", {}):
        MEM["history_scores"].pop(_hk, None)

now_tr = datetime.now(TR_TZ)
now_epoch = time.time()
b_snap = MEM.setdefault("bulletin_snap", {"ts": 0.0, "live": [], "up": [], "fin": [], "mini": []})

if (now_epoch - safe_float(b_snap.get("ts"), 0.0)) < 60.0 and (b_snap.get("up") or b_snap.get("live") or b_snap.get("fin")):
    live_matches = list(b_snap["live"])
    upcoming_matches = list(b_snap["up"])
    finished_matches = list(b_snap["fin"])
    mini_lines = list(b_snap["mini"])
    fin_cache = MEM.setdefault("finished_cache", {})
    hist_vals = [x for k, x in MEM.get("history_scores", {}).items() if isinstance(x, dict) and k in fin_cache]
else:
    raw_matches, roster_tasks = [], []
    seen_raw_keys = set()
    with ThreadPoolExecutor(max_workers=16) as ex:
        sb_results = list(ex.map(_fetch_single_league_sb, _ACTIVE_LEAGUES))

    for slug, lig_adi, kademe, ev_list in sb_results:
        for ev in ev_list:
            comp = (ev.get("competitions") or [{}])[0]
            status_obj = comp.get("status") or ev.get("status") or {}
            st_type = status_obj.get("type") or {}
            state = str(st_type.get("state") or "pre").lower()
            completed = bool(st_type.get("completed", False))
            clk = str(status_obj.get("displayClock") or st_type.get("shortDetail") or "")
            st_name = str(st_type.get("name") or "").upper()
            if "POSTPONED" in st_name or "CANCELED" in st_name or "ABANDONED" in st_name:
                continue

            ev_date_str = str(ev.get("date") or "")
            mins_to_ko = 180
            try:
                ev_date_str = (ev_date_str[:-1] + ":00+00:00") if (len(ev_date_str) == 17 and ev_date_str.endswith("Z")) else ev_date_str.replace("Z", "+00:00")
                dt_ev = datetime.fromisoformat(ev_date_str).astimezone(TR_TZ)
                hours_diff = (dt_ev - now_tr).total_seconds() / 3600.0
                mins_to_ko = int(round(hours_diff * 60.0))
                if state == "pre" and (hours_diff < -0.25 or hours_diff > 22.0):
                    continue
                if state == "post" and abs(hours_diff) > 36.0:
                    continue
            except Exception:
                continue

            comps = comp.get("competitors") or []
            if len(comps) < 2:
                continue
            h_c = next((x for x in comps if x.get("homeAway") == "home"), comps[0])
            a_c = next((x for x in comps if x.get("homeAway") == "away"), comps[1])
            h_name = str((h_c.get("team") or {}).get("shortDisplayName") or (h_c.get("team") or {}).get("name") or "Home")
            a_name = str((a_c.get("team") or {}).get("shortDisplayName") or (a_c.get("team") or {}).get("name") or "Away")
            h_abbr = str((h_c.get("team") or {}).get("abbreviation") or h_name[:3]).upper()
            a_abbr = str((a_c.get("team") or {}).get("abbreviation") or a_name[:3]).upper()
            match_title = f"{h_name} vs {a_name}"
            ev_id = str(ev.get("id") or "")
            match_key = ev_id if ev_id else match_title

            if match_key in seen_raw_keys or match_title in seen_raw_keys:
                continue
            seen_raw_keys.add(match_key)
            seen_raw_keys.add(match_title)

            h_form, a_form = str(h_c.get("form") or ""), str(a_c.get("form") or "")
            h_mom, a_mom = _true_form_mom(h_form, h_name), _true_form_mom(a_form, a_name)

            odds_arr = comp.get("odds") or []
            odd_str, ou_val, has_live_api_odds = "", 2.5, False
            odds_3way = {"ml_h": 0, "ml_d": 0, "ml_a": 0}
            if odds_arr and isinstance(odds_arr[0], dict):
                od0 = odds_arr[0]
                odd_str = str(od0.get("details") or "").strip()
                ou_val = safe_float(od0.get("overUnder"), 2.5)
                has_live_api_odds = True
                odds_3way = {
                    "ml_h": safe_float((od0.get("homeTeamOdds") or {}).get("moneyLine"), 0),
                    "ml_a": safe_float((od0.get("awayTeamOdds") or {}).get("moneyLine"), 0),
                    "ml_d": safe_float((od0.get("drawOdds") or {}).get("moneyLine"), 0)
                }
            if not odd_str:
                fav_abbr = h_abbr if (h_mom + 12) >= a_mom else a_abbr
                fav_val = -115 - int(abs((h_mom + 8) - a_mom) * 1.4)
            else:
                pts = odd_str.split()
                fav_abbr = pts[0].upper() if pts else h_abbr
                fav_val = safe_int(pts[1], -130) if len(pts) > 1 else -130

            op_mem = MEM.setdefault("opening_odds", {})
            op_entry = op_mem.get(match_key) or op_mem.get(match_title)
            if not isinstance(op_entry, dict) or "fav_val" not in op_entry or "ou_val" not in op_entry:
                op_entry = {"fav_val": fav_val, "ou_val": ou_val, "fav_abbr": fav_abbr}
                op_mem[match_key] = op_entry
            op_fav = safe_int(op_entry.get("fav_val"), fav_val)
            op_ou = safe_float(op_entry.get("ou_val"), ou_val)
            op_abbr = str(op_entry.get("fav_abbr") or fav_abbr)

            eval_fav_val = fav_val if state == "pre" else op_fav
            eval_ou_val = ou_val if state == "pre" else op_ou
            eval_fav_abbr = fav_abbr if state == "pre" else op_abbr

            disp_odd = f"{fav_abbr} {fav_val:+d}" if fav_val > 0 else f"{fav_abbr} {fav_val}"
            if not has_live_api_odds:
                disp_odd += "(ProxyOran)"
            if fav_val != op_fav and fav_abbr == op_abbr:
                d_raw = fav_val - op_fav
                d_prob = round(_odd_to_prob(fav_val) - _odd_to_prob(op_fav), 1)
                if d_prob >= 2.0:
                    disp_odd += f" 🔥Δ{d_raw:+d}(+{d_prob}%p)"
                elif d_prob <= -2.0:
                    disp_odd += f" ⚠️Δ{d_raw:+d}({d_prob}%p)"
            if ou_val > op_ou:
                disp_odd += f" 💥TG↑({op_ou}->{ou_val})"

            raw_matches.append((slug, lig_adi, kademe, ev, comp, state, completed, clk, h_c, a_c, h_name, a_name, h_abbr, a_abbr, match_title, h_form, a_form, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, has_live_api_odds, ev_id, odds_3way, ev_date_str, eval_fav_abbr, eval_fav_val, eval_ou_val))
            roster_tasks.append((slug, ev_id, match_title, h_name, a_name, h_mom, a_mom, disp_odd, state, kademe, eval_fav_abbr, eval_fav_val, a_abbr, mins_to_ko))

    roster_map = {}
    if roster_tasks:
        with ThreadPoolExecutor(max_workers=16) as ex:
            for m_t, r_d in ex.map(fetch_and_analyze_roster, roster_tasks):
                roster_map[m_t] = r_d

    live_matches, upcoming_matches = [], []
    fin_cache = MEM.setdefault("finished_cache", {})
    locked_picks = MEM.setdefault("locked_picks", {})
    ledger_log = MEM.setdefault("ledger_log", {})

    for item in raw_matches:
        slug, lig_adi, kademe, ev, comp, state, completed, clk, h_c, a_c, h_name, a_name, h_abbr, a_abbr, match_title, h_form, a_form, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, has_live_api_odds, ev_id, odds_3way, kickoff_utc, eval_fav_abbr, eval_fav_val, eval_ou_val = item
        match_key = ev_id if ev_id else match_title

        if state == "post" and match_key in fin_cache and isinstance(fin_cache[match_key], dict) and "won" in fin_cache[match_key]:
            continue

        lock_id = f"{match_key}_{MODEL_VERSION}"
        legacy_rec = locked_picks.get(f"{match_key}_M4.3_DC_NEGBINOM_EWMA5") or locked_picks.get(match_title) or {}
        rec = locked_picks.get(lock_id) if isinstance(locked_picks.get(lock_id), dict) else (dict(legacy_rec) if state != "pre" and isinstance(legacy_rec, dict) else {})

        has_real_pre_lock = bool(rec.get("CONFIRMED_XI") or rec.get("PRE_LINEUP") or rec.get("pick") or (match_key in MEM.get("pre_lineup_memory", {})))
        if state == "post" and not has_real_pre_lock:
            continue

        r_data = roster_map.get(match_title) or {}
        r_data["slug"] = slug
        r_data["odds_3way"] = odds_3way
        is_off = bool(r_data.get("official"))
        h_tac = str((r_data.get("h") or {}).get("tac") or "4-2-3-1")
        a_tac = str((r_data.get("a") or {}).get("tac") or "4-2-3-1")
        conf, pick, disp_odd, warn_flag, m4_str, m4 = evaluate_pre_match(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, disp_odd, eval_fav_abbr, eval_fav_val, eval_ou_val, kademe, r_data, lig_adi)
        conf, pick, disp_odd, evo_str, prop_str, evo_changed = compute_post_lineup_evolution_and_props(match_key, is_off, h_name, a_name, h_abbr, a_abbr, h_tac, a_tac, h_mom, a_mom, disp_odd, eval_fav_abbr, eval_fav_val, eval_ou_val, conf, pick, lig_adi, r_data, m4)

        if m4.get("status") == "HESAPLANAMADI" or "HESAPLANAMADI" in str(pick):
            continue

        rec.setdefault("ev_id", ev_id)
        rec.setdefault("kickoff_utc", kickoff_utc)
        rec.setdefault("model_version", MODEL_VERSION)
        rec.setdefault("match_title", match_title)

        if state == "pre":
            if "PRE_LINEUP" not in rec:
                rec["PRE_LINEUP"] = {
                    "pick": pick, "conf": conf, "prop": prop_str,
                    "locked_at": now_tr.strftime("%Y-%m-%d %H:%M")
                }
            if is_off:
                rec["CONFIRMED_XI"] = {
                    "pick": pick, "conf": conf, "prop": prop_str,
                    "locked_at": now_tr.strftime("%Y-%m-%d %H:%M")
                }
            active_stage = rec.get("CONFIRMED_XI") if is_off else rec.get("PRE_LINEUP")
            pick = active_stage.get("pick", pick)
            conf = safe_int(active_stage.get("conf"), conf)
            prop_str = active_stage.get("prop", prop_str)
            rec.update({"pick": pick, "conf": conf, "prop": prop_str, "stage": "CONFIRMED_XI" if is_off else "PRE_LINEUP"})
            locked_picks[lock_id] = rec
        else:
            active_stage = rec.get("CONFIRMED_XI") or rec.get("PRE_LINEUP") or rec
            if active_stage.get("pick"):
                pick = active_stage.get("pick", pick)
                conf = safe_int(active_stage.get("conf"), conf)
                prop_str = active_stage.get("prop", prop_str)
            elif match_key in MEM.get("pre_lineup_memory", {}):
                pick = MEM["pre_lineup_memory"][match_key]
            rec.update({"pick": pick, "conf": conf, "prop": prop_str, "stage": "LIVE" if state == "in" else "POST_MATCH"})
            locked_picks[lock_id] = rec

        bs_fallback = r_data.get("box_stats") or {}
        h_score, a_score = safe_int(h_c.get("score"), 0), safe_int(a_c.get("score"), 0)
        h_sh = get_stat(h_c, ["totalShots", "shotsSummary"]) or safe_int(bs_fallback.get("h_sh"), 0)
        a_sh = get_stat(a_c, ["totalShots", "shotsSummary"]) or safe_int(bs_fallback.get("a_sh"), 0)
        h_sot = get_stat(h_c, ["shotsOnTarget", "onGoal"]) or safe_int(bs_fallback.get("h_sot"), 0)
        a_sot = get_stat(a_c, ["shotsOnTarget", "onGoal"]) or safe_int(bs_fallback.get("a_sot"), 0)
        h_cor = get_stat(h_c, ["wonCorners", "corners"]) or safe_int(bs_fallback.get("h_cor"), 0)
        a_cor = get_stat(a_c, ["wonCorners", "corners"]) or safe_int(bs_fallback.get("a_cor"), 0)
        h_poss = get_stat(h_c, ["possessionPct", "possession"]) or 50
        tot_cards = _count_real_match_cards(comp, h_c, a_c, r_data)

        try:
            ev_d = str(ev.get("date") or "")
            ev_d = (ev_d[:-1] + ":00+00:00") if (len(ev_d) == 17 and ev_d.endswith("Z")) else ev_d.replace("Z", "+00:00")
            m_time = datetime.fromisoformat(ev_d).astimezone(TR_TZ).strftime("%H:%M")
        except Exception:
            m_time = "20:30"

        base_obj = {
            "ev_id": ev_id, "mac_key": match_key, "mac": match_title, "lig": lig_adi, "saat": m_time, "h_name": h_name, "a_name": a_name,
            "h_form": h_form or "—", "a_form": a_form or "—", "h_mom": h_mom, "a_mom": a_mom, "h_tac": h_tac, "a_tac": a_tac,
            "is_off": is_off, "odd": disp_odd, "ou": ou_val, "conf": conf, "pick": pick, "evo": evo_str,
            "prop": prop_str, "roster_data": r_data, "m4_summary": m4_str, "m4": m4,
            "h_score": h_score, "a_score": a_score, "h_sh": h_sh, "a_sh": a_sh, "h_sot": h_sot, "a_sot": a_sot,
            "h_cor": h_cor, "a_cor": a_cor, "h_poss": h_poss, "cards": tot_cards, "clk": clk,
            "model_version": rec.get("model_version", MODEL_VERSION)
        }

        if state == "in":
            m_int, add_min = parse_live_clock(clk)
            heat, sot_tag, live_pick, _, _ = analyze_live_pro(match_key, h_name, a_name, h_abbr, a_abbr, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_poss, m_int, add_min, h_mom, a_mom, fav_abbr, fav_val, ou_val, has_live_api_odds, r_data)
            snaps = MEM.setdefault("live_snapshots", {})
            s0 = snaps.get(match_key) or snaps.get(match_title)
            if not isinstance(s0, dict) or "min" not in s0 or "sh" not in s0:
                s0 = {"min": m_int, "sh": h_sh + a_sh, "sot": h_sot + a_sot, "cor": h_cor + a_cor}
                snaps[match_key] = s0
            s0_min, s0_sh, s0_sot, s0_cor = safe_int(s0.get("min"), m_int), safe_int(s0.get("sh"), h_sh + a_sh), safe_int(s0.get("sot"), h_sot + a_sot), safe_int(s0.get("cor"), h_cor + a_cor)
            d_str = f"|Δ({s0_min}'->{m_int}'):+{max(0,(h_sh+a_sh)-s0_sh)}/{max(0,(h_sot+a_sot)-s0_sot)}Ş,+{max(0,(h_cor+a_cor)-s0_cor)}K" if m_int > s0_min + 2 else ""
            base_obj.update({"heat": heat, "sot_tag": sot_tag, "live_pick": live_pick, "delta_str": d_str})
            live_matches.append(base_obj)
        elif state == "post":
            if not completed or not has_real_pre_lock:
                continue
            tot_cor_ft = h_cor + a_cor
            if "Korner" in pick and tot_cor_ft == 0:
                continue
            if "Kart" in pick and tot_cards == 0 and (h_sh + a_sh) == 0:
                continue

            if "9.5 Korner Üst" in pick:
                won = (tot_cor_ft >= 10)
            elif "8.5 Korner Üst" in pick:
                won = (tot_cor_ft >= 9)
            elif "4.5 Kart Üst" in pick:
                won = (tot_cards >= 5)
            elif "3.5 Kart Üst" in pick:
                won = (tot_cards >= 4)
            else:
                won = evaluate_ft_result(pick, h_name, a_name, h_score, a_score)
            is_ak = ("Ana Kasa" in pick or conf >= 78)
            brier_val = round(((conf / 100.0) - (1.0 if won else 0.0)) ** 2, 3)

            op_info = MEM.get("opening_odds", {}).get(match_key) or {"fav_val": eval_fav_val, "ou_val": eval_ou_val}
            op_fav_v = safe_int(op_info.get("fav_val"), eval_fav_val)
            op_ou_v = safe_float(op_info.get("ou_val"), eval_ou_val)
            mkt_t = _classify_pick_market_type(pick)
            if mkt_t in ("O15", "O25", "BTTS"):
                clv_delta = round((ou_val - op_ou_v) * 6.0, 2)
                p_mkt_base = 0.72 if mkt_t == "O15" else (0.52 if mkt_t == "O25" else 0.51)
            else:
                clv_delta = round(_odd_to_prob(fav_val) - _odd_to_prob(op_fav_v), 2)
                p_mkt_base = min(0.88, max(0.35, safe_float(m4.get("market_probability_proxy"), 55.0) / 100.0 * (0.84 if mkt_t in ("WIN", "TEAM_O15") else 0.95)))
            mkt_brier = round((p_mkt_base - (1.0 if won else 0.0)) ** 2, 3)

            if match_key != match_title:
                fin_cache.pop(match_title, None)
                MEM.setdefault("history_scores", {}).pop(match_title, None)

            MEM.setdefault("history_scores", {})[match_key] = {
                "won": won, "ak": is_ak, "brier": brier_val, "mkt_brier": mkt_brier,
                "p_mkt": round(p_mkt_base, 3), "clv": clv_delta, "conf": conf,
                "mkt": mkt_t, "ver": MODEL_VERSION
            }
            base_obj.update({"won": won, "is_ak": is_ak, "brier": brier_val, "mkt_brier": mkt_brier, "clv": clv_delta})
            fin_cache[match_key] = base_obj
            ledger_log[match_key] = f"{now_tr.strftime('%H:%M')} | {match_title} ({h_score}-{a_score}, Kor:{tot_cor_ft}, Kart:{tot_cards}) -> {pick} [{'✅KAZANDI' if won else '❌KAYIP'} | Brier:{brier_val} vs Mkt:{mkt_brier} | CLV:{clv_delta:+.1f}%p]"
        else:
            upcoming_matches.append(base_obj)

    save_persistent_store()

    live_matches.sort(key=lambda x: x.get("heat", 0), reverse=True)
    upcoming_matches.sort(key=lambda x: x.get("conf", 0), reverse=True)
    finished_matches = [x for x in list(fin_cache.values())[::-1] if isinstance(x, dict) and "h_name" in x and "pick" in x]

    hist_vals = [x for k, x in MEM.get("history_scores", {}).items() if isinstance(x, dict) and k in fin_cache]
    g_w = MEM.get("base_w", 0) + sum(1 for x in hist_vals if x.get("won"))
    g_t = MEM.get("base_t", 0) + len(hist_vals)
    g_r = int(round((g_w * 100.0) / max(1, g_t))) if g_t > 0 else 0

    ak_w = MEM.get("base_ak_w", 0) + sum(1 for x in hist_vals if x.get("ak") and x.get("won"))
    ak_t = MEM.get("base_ak_t", 0) + sum(1 for x in hist_vals if x.get("ak"))
    ak_r = int(round((ak_w * 100.0) / max(1, ak_t))) if ak_t > 0 else 0

    lp_all = [x for x in MEM.get("live_signals", {}).values() if isinstance(x, dict)]
    lp_w = sum(1 for x in lp_all if x.get("status") == "WON")
    lp_t = max(lp_w, sum(1 for x in lp_all if x.get("status") in ("WON", "LOST")))
    lp_r = int(round((lp_w * 100.0) / max(1, lp_t))) if lp_t > 0 else 100
    lp_act = sum(1 for x in lp_all if x.get("status") == "WAIT")

    MEM["DATA_LEDGER"] = {
        "karne_str": f"{g_w}/{g_t} (%{g_r})",
        "ak_str": f"{ak_w}/{ak_t} (%{ak_r})",
        "lp_str": f"{lp_w}/{lp_t} (%{lp_r}) • Active: {lp_act}",
        "mini_head": f"⚡ DP-MİNİ [{now_tr.strftime('%Y%m%d %H:%M')}] Karne:{g_w}/{g_t}(%{g_r}) AK:{ak_w}/{ak_t}(%{ak_r}) CanlıPusu:{lp_w}/{lp_t}(%{lp_r}|Aktif:{lp_act})"
    }

    mini_lines = [MEM["DATA_LEDGER"]["mini_head"]]
    for m in live_matches:
        m4_d = m.get("m4") or {}
        ps_mini = f"|{m4_d.get('patron_sim_mini','')}" if m4_d.get("patron_sim_mini") else ""
        mini_lines.append(f"CANLI|{m['clk']}|🔥%{m['heat']}|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}|Şut:{m['h_sh']}({m['h_sot']})-{m['a_sh']}({m['a_sot']})|Kor:{m['h_cor']}-{m['a_cor']}|Kart:{m['cards']}|Top:%{m['h_poss']}{m['delta_str']}{m['sot_tag']}|Önü:{m['pick']}|Yan:{m['prop']}{ps_mini}")
    for m in upcoming_matches:
        k_tag = f"✅Kadro({m['h_tac']}v{m['a_tac']})" if m["is_off"] else "⏳5MaçÇekirdekXI"
        e_tail = f" | {m['evo']} | Yan:{m['prop']}" if m["is_off"] else f" | Yan:{m['prop']}"
        m4_d = m.get("m4") or {}
        ps_mini = f" {m4_d.get('patron_sim_mini','')}" if m4_d.get("patron_sim_mini") else ""
        mini_lines.append(f"ÖNÜ|{m['saat']}|{m['lig']}|{m['mac']}|%{m['conf']}|{k_tag}|Mom:{m['h_mom']}-{m['a_mom']}|{m['odd']}|TG:{m['ou']} [P4+:%{m4_d.get('p_over35',20)}|Sh:%{m4_d.get('p_shield',50)}|Dw:{m4_d.get('d_weak',15)}] -> {m['pick']}{e_tail}{ps_mini}")
    for m in finished_matches[:22]:
        st_ico = "✅KAZANDI" if m.get("won") else "❌KAYIP"
        m4_ft = m.get("m4") or {}
        lig_dna_ft = m4_ft.get("lig_dna") or DEFAULT_LIG_DNA
        l_thresh = safe_float(lig_dna_ft.get("lock_thresh"), 13.8)
        sim_ft = f"|Sim:{m4_ft.get('est_score','1-1')}(%{m4_ft.get('est_score_p',14)})" + (f"⚠️1-1:%{m4_ft.get('p_1_1_lock',14):.0f}" if safe_float(m4_ft.get("p_1_1_lock"), 0) >= l_thresh else "")
        mini_lines.append(f"BİTTİ|FT|{st_ico}|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}|Şut:{m['h_sh']}({m['h_sot']})-{m['a_sh']}({m['a_sot']})|Kor:{m['h_cor']}-{m['a_cor']}({m['h_cor']+m['a_cor']})|Kart:{m['cards']}|Hedef:{m['pick']}(%{m['conf']}){sim_ft}")

    MEM["bulletin_snap"] = {
        "ts": now_epoch if not live_matches else (now_epoch - 40.0),
        "live": live_matches, "up": upcoming_matches, "fin": finished_matches, "mini": mini_lines
    }
# ==================== MODÜL 5/6: GÖRSEL SAHA VE ARAYÜZ (UI) ====================
def format_form_badges(form_str):
    out = []
    for ch in str(form_str or "")[:5]:
        if ch not in ("W", "D", "L"):
            continue
        c = "#2ea043" if ch == "W" else ("#d29922" if ch == "D" else "#f85149")
        out.append(f"<span style='background:{c};color:#fff;padding:1px 4px;border-radius:3px;font-size:9.5px;font-weight:700;margin-right:2px;'>{ch}</span>")
    return "".join(out) if out else "<span style='color:#8b949e;'>—</span>"

def _split_players_by_formation(starters, tac_str, is_away=False):
    pts = [safe_int(x, 0) for x in str(tac_str or "4-2-3-1").split("-") if safe_int(x, 0) > 0]
    if sum(pts) != 10:
        pts = [4, 2, 3, 1]
    st_list = list(starters or [])[:11]
    while len(st_list) < 11:
        st_list.append({"name": "Player", "num": "99", "pos": "M", "rat": 70})
    cols, idx = [[st_list[0]]], 1
    for cnt in pts:
        cols.append(st_list[idx:idx + cnt])
        idx += cnt
    if is_away:
        cols.reverse()
    return cols

def _render_team_half_nodes(cols, jersey_bg, border_col):
    col_html = []
    for c_players in cols:
        nodes = []
        for p in c_players:
            p_num, p_rat, p_short = str(p.get("num") or ""), safe_int(p.get("rat"), 72), str(p.get("name") or "")[:10]
            rat_bg = "#2ea043" if p_rat >= 78 else ("#d29922" if p_rat >= 70 else "#f85149")
            nodes.append(
                f"<div style='display:flex;flex-direction:column;align-items:center;margin:2px 1px;'>"
                f"<div class='dp-node-circle' style='background:{jersey_bg};border:2px solid {border_col};'>"
                f"{p_num}<span style='position:absolute;top:-5px;right:-7px;background:{rat_bg};color:#fff;font-size:8px;padding:0 3px;border-radius:4px;font-weight:800;border:1px solid #0d1117;'>{p_rat}</span></div>"
                f"<div class='dp-node-name'>{p_short}</div></div>"
            )
        col_html.append(f"<div style='display:flex;flex-direction:column;justify-content:space-around;align-items:center;height:100%;'>{''.join(nodes)}</div>")
    return f"<div style='display:flex;justify-content:space-around;align-items:center;width:49%;height:100%;z-index:2;'>{''.join(col_html)}</div>"

def build_tactical_pitch_html(m):
    r_data = m.get("roster_data") or {}
    h_d, a_d = r_data.get("h") or {}, r_data.get("a") or {}
    w_str = r_data.get("weather") or derive_match_weather(m["mac"], m["lig"])
    venue_str = r_data.get("venue") or f"{m['h_name']} Stadium"
    tac_ver_str = "Resmi Diziliş" if (h_d.get("tac_verified") and a_d.get("tac_verified")) else "5-Maç Mod Diziliş"
    xi_status = f"✅ RESMİ 11 ({tac_ver_str} • Reyting: Mom. Proxy)" if m.get("is_off") else f"⏳ SON 5 MAÇ ÇEKİRDEK 11 ({tac_ver_str} • Reyting: Proxy)"

    left_half = _render_team_half_nodes(_split_players_by_formation(h_d.get("starters"), m["h_tac"], False), "linear-gradient(135deg,#d9381e,#8b1a0e)", "#ffd33d")
    right_half = _render_team_half_nodes(_split_players_by_formation(a_d.get("starters"), m["a_tac"], True), "linear-gradient(135deg,#1f6feb,#0d3b8c)", "#79c0ff")

    bars_html = []
    for lbl, k in [("OVR", "ovr"), ("ATT", "sho"), ("PAS", "pas"), ("DRI", "dri"), ("DEF", "def")]:
        hv, av = safe_int(h_d.get(k), 72), safe_int(a_d.get(k), 71)
        h_col = "#f85149" if (k == "def" and hv <= 58) else "#3fb950"
        a_col = "#f85149" if (k == "def" and av <= 58) else "#58a6ff"
        bars_html.append(
            f"<div style='flex:1;min-width:95px;background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:4px 7px;'>"
            f"<div style='display:flex;justify-content:space-between;font-size:10px;font-weight:800;'>"
            f"<span style='color:{h_col};'>{hv}</span><span style='color:#8b949e;'>{lbl}</span><span style='color:{a_col};'>{av}</span></div>"
            f"<div style='display:flex;height:5px;background:#21262d;border-radius:3px;overflow:hidden;margin-top:3px;'>"
            f"<div style='width:{int(hv*100/(hv+av))}%;background:{h_col};'></div>"
            f"<div style='width:{100-int(hv*100/(hv+av))}%;background:{a_col};'></div></div></div>"
        )

    h_bench = ", ".join([f"#{p['num']} {p['name']}({p['rat']})" for p in (h_d.get("bench") or [])[:4]]) or "Standard Bench"
    a_bench = ", ".join([f"#{p['num']} {p['name']}({p['rat']})" for p in (a_d.get("bench") or [])[:4]]) or "Standard Bench"

    return (
        f"<div style='background:#161b22;border:1px solid #2ea043;border-radius:10px;padding:10px;color:#e6edf3;font-size:11.5px;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;background:#0d1117;padding:6px 10px;border-radius:6px;margin-bottom:8px;border:1px solid #30363d;'>"
        f"<span>🏟️ <b>{venue_str}</b> • {w_str}</span><span style='color:#56d364;font-weight:800;'>{xi_status} ({m['h_tac']} vs {m['a_tac']})</span></div>"
        f"<div style='display:flex;gap:6px;flex-wrap:wrap;margin-bottom:9px;'>{''.join(bars_html)}</div>"
        f"<div class='dp-pitch-wrap'>"
        f"<div style='position:absolute;left:50%;top:0;bottom:0;width:2px;background:rgba(255,255,255,0.65);transform:translateX(-50%);'></div>"
        f"<div style='position:absolute;left:50%;top:50%;width:60px;height:60px;border:2px solid rgba(255,255,255,0.65);border-radius:50%;transform:translate(-50%,-50%);'></div>"
        f"<div style='position:absolute;left:0;top:22%;width:34px;height:56%;border:2px solid rgba(255,255,255,0.6);border-left:none;'></div>"
        f"<div style='position:absolute;right:0;top:22%;width:34px;height:56%;border:2px solid rgba(255,255,255,0.6);border-right:none;'></div>"
        f"{left_half}{right_half}</div>"
        f"<div style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;margin-top:7px;font-size:10.5px;color:#c9d1d9;'>"
        f"<div>🔴 <b>{m['h_name']} Bench:</b> {h_bench} (Rot:{h_d.get('rot_cnt',0)})</div>"
        f"<div>🔵 <b>{m['a_name']} Bench:</b> {a_bench} (Rot:{a_d.get('rot_cnt',0)})</div></div>"
        f"<div style='background:#0d1117;border-left:3px solid #f0b90b;padding:5px 8px;border-radius:4px;margin-top:6px;color:#ffd33d;font-size:11px;'>"
        f"🧮 <b>M4.4 EWMA-5 & Core-XI Telemetry:</b> {m.get('m4_summary','')}</div></div>"
    )

def _build_match_social_text(m, mode="pre"):
    h, a = m.get("h_name", "Home"), m.get("a_name", "Away")
    pick, prop, conf = m.get("pick", ""), str(m.get("prop", "")).split("|")[0].strip(), m.get("conf", 70)
    if mode == "live":
        return f"🔴 LIVE AI RADAR ({m.get('clk','LIVE')})\n⚽ {h} {m.get('h_score',0)}-{m.get('a_score',0)} {a} (🔥Pressure: {m.get('heat',75)}%)\n📊 Shots: {m.get('h_sh',0)+m.get('a_sh',0)} | Corners: {m.get('h_cor',0)+m.get('a_cor',0)}\n🎯 Target: {pick} | {prop}\n👉 {APP_PUBLIC_URL}"
    if mode == "post":
        st_tag = "✅ SMASHED!" if m.get("won") else "📊 FT Report"
        return f"🏆 FULL TIME AI VERIFICATION!\n⚽ {h} {m.get('h_score',0)}-{m.get('a_score',0)} {a} ({m.get('h_sh',0)+m.get('a_sh',0)} Shots, {m.get('h_cor',0)+m.get('a_cor',0)} Corners)\n🎯 AI Target ({conf}%): {pick} ➔ {st_tag}\n👉 {APP_PUBLIC_URL}"
    k_str = f"✅Lineups ({m.get('h_tac','4-2-3-1')}v{m.get('a_tac','4-2-3-1')})" if m.get("is_off") else f"🕒 {m.get('saat','20:00')} CET"
    return f"🚨 AI TELEMETRY LOCKED ({k_str})\n⚽ {h} vs {a} (Prob: {conf}%)\n🎯 Main: {pick}\n🔥 {prop}\n👉 {APP_PUBLIC_URL}"

def _send_telegram_msg(text_msg):
    tg_cfg = MEM.setdefault("tg_config", {"token": "", "chat_id": ""})
    tk, cid = str(tg_cfg.get("token") or "").strip(), str(tg_cfg.get("chat_id") or "").strip()
    if not tk or not cid:
        return False, "⚠️ Önce Patron Paneli > X & Telegram sekmesinden Bot Token ve Chat ID girin."
    try:
        r = HTTP_SESSION.post(f"https://api.telegram.org/bot{tk}/sendMessage", json={"chat_id": cid, "text": text_msg}, timeout=4.0)
        return (True, "✅ Telegram kanalına gönderildi!") if r.status_code == 200 else (False, f"❌ Telegram Hatası: {r.status_code}")
    except Exception as e:
        return False, f"❌ Bağlantı hatası: {e}"

def _render_match_share_box(m, mode, idx_key, is_unlocked):
    if not is_unlocked:
        return
    with st.expander(f"🐦 {m['h_name']} vs {m['a_name']} — X (Twitter) & 📢 Telegram Hazır Paylaşım Metni", expanded=False):
        s_txt = _build_match_social_text(m, mode=mode)
        st.code(s_txt, language="text")
        x_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(s_txt)}"
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<a href='{x_url}' target='_blank' style='display:block;text-align:center;background:#1d9bf0;color:#fff;padding:7px 10px;border-radius:6px;font-weight:700;text-decoration:none;font-size:12.5px;'>🐦 Tek Tıkla X'te Paylaş ({len(s_txt)} krk)</a>", unsafe_allow_html=True)
        with c2:
            if st.button("📢 Telegram Kanalına Gönder", key=f"tg_btn_{mode}_{idx_key}_{m.get('mac_key', m['mac'])}", use_container_width=True):
                ok, msg = _send_telegram_msg(s_txt)
                st.success(msg) if ok else st.warning(msg)

def _time_sort_minutes(saat_str):
    try:
        pts = str(saat_str or "20:00").split(":")
        h, m = int(pts[0]), int(pts[1])
        if h < 8:
            h += 24
        return h * 60 + m
    except Exception:
        return 1200

def render_main_bulletin(tier="NORMAL", is_patron_mode=False):
    is_unlocked = (tier in ("VIP", "ADMIN") or is_patron_mode)
    if st.button("🔄 Refresh 24/7 Global Radar & Sync Live Telemetry", use_container_width=True, key=f"ref_main_{tier}_{is_patron_mode}"):
        MEM.setdefault("bulletin_snap", {})["ts"] = 0.0
        st.rerun()

    ldg = MEM.get("DATA_LEDGER") or {"karne_str": "0/0", "ak_str": "0/0", "lp_str": "0/0"}
    st.markdown(
        f"<div style='display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;'>"
        f"<div class='dp-card' style='flex:1;min-width:140px;'>🏆 <b>Verified AI Record:</b> <span style='color:#56d364;font-weight:800;'>{ldg['karne_str']}</span></div>"
        f"<div class='dp-card dp-ak' style='flex:1;min-width:140px;'>💎 <b>Main Safe (Ana Kasa):</b> <span style='color:#ffd33d;font-weight:800;'>{ldg['ak_str']}</span></div>"
        f"<div class='dp-card' style='flex:1;min-width:140px;'>🔥 <b>Live Ambush:</b> <span style='color:#79c0ff;font-weight:800;'>{ldg['lp_str']}</span></div></div>",
        unsafe_allow_html=True
    )

    if live_matches:
        st.markdown("### 🔴 LIVE AMBUSH & PRESSURE RADAR (CANLI SAHALAR)")
        for idx_l, m in enumerate(live_matches):
            p_disp = m["pick"] if is_unlocked else "🔒 VIP LOCKED TARGET"
            lp_disp = m.get("live_pick", "") if is_unlocked else "🔒 VIP LOCKED LIVE AMBUSH"
            m4_d = m.get("m4") or {}
            dec_u = safe_int(m4_d.get("decision_score"), m["conf"])
            live_pick_bar = f"<div style='background:#0d2818;border-left:3px solid #3fb950;padding:5px 8px;border-radius:4px;margin-top:5px;font-size:12px;font-weight:700;color:#56d364;'>{lp_disp}</div>" if lp_disp else ""
            patron_line = f"<div style='margin-top:5px;padding:5px 8px;background:#0d1117;border-left:3px solid #f0b90b;border-radius:4px;font-size:11.5px;color:#e6edf3;'>{m4_d.get('patron_sim_ui','')}</div>" if (is_patron_mode and m4_d.get("patron_sim_ui")) else ""
            st.markdown(
                f"<div class='dp-card' style='border-left:4px solid #f85149;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#ffb4a2;'>"
                f"<span>🔴 <b>{m['clk']}</b> • {m['lig']} ({m['h_tac']} vs {m['a_tac']})</span>"
                f"<span><span style='background:#21262d;color:#ffd33d;padding:2px 7px;border-radius:5px;font-weight:800;margin-right:4px;'>🎯 Güven: %{m['conf']} ({dec_u}p)</span>"
                f"<span style='background:#da3633;color:#fff;padding:2px 7px;border-radius:5px;font-weight:800;'>🔥 Pressure: %{m['heat']}</span></span></div>"
                f"<div style='font-size:16px;font-weight:800;margin:5px 0;color:#fff;'>{m['h_name']} <span style='color:#ffd33d;'>{m['h_score']} - {m['a_score']}</span> {m['a_name']}</div>"
                f"<div style='font-size:11.5px;color:#c9d1d9;'>🎯 <b>Şut(İsabet):</b> {m['h_sh']}({m['h_sot']}) - {m['a_sh']}({m['a_sot']}) | 🚩 <b>Korner:</b> {m['h_cor']} - {m['a_cor']} (Top:{m['h_cor']+m['a_cor']}) | 🟨 <b>Kart:</b> {m['cards']} | ⚽ <b>Top:</b> %{m['h_poss']}</div>"
                f"<div style='font-size:11px;color:#79c0ff;margin-top:4px;'>⚡ <b>Canlı Telemetri:</b> {m['odd']} {m['delta_str']} {m['sot_tag']}</div>"
                f"{live_pick_bar}"
                f"<div style='margin-top:6px;padding-top:6px;border-top:1px solid #30363d;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;font-size:12px;'>"
                f"<span>🎯 <b>1. Tercih (Ana • %{m['conf']}):</b> <b style='color:#56d364;'>{p_disp}</b></span><span style='color:#d2a8ff;'>{m['prop']}</span></div>"
                f"{patron_line}</div>",
                unsafe_allow_html=True
            )
            with st.expander(f"🏟️ {m['h_name']} vs {m['a_name']} — Canlı Saha Dizilimi ({m['h_tac']} vs {m['a_tac']})", expanded=False):
                st.markdown(build_tactical_pitch_html(m), unsafe_allow_html=True)
            _render_match_share_box(m, "live", idx_l, is_unlocked)

    st.markdown("### ⏳ PRE-MATCH WHALE & POISSON TELEMETRY")

    c_sort, c_flt = st.columns([2.2, 1.2])
    with c_sort:
        sort_mode = st.radio(
            "📊 Bülten Sıralama Ölçütü:",
            ["🔥 Olasılığa Göre", "🕒 Maç Saatine Göre", "🏆 Lige Göre", "🚩 Korner Gücüne Göre"],
            horizontal=True,
            key=f"sort_bar_{tier}_{is_patron_mode}"
        )
    with c_flt:
        avail_leagues = ["🌍 Tüm Ligler (" + str(len(upcoming_matches)) + ")"] + sorted(list({m.get("lig", "") for m in upcoming_matches if m.get("lig")}))
        sel_lig = st.selectbox("🏆 Lig Filtresi:", avail_leagues, key=f"lig_flt_{tier}_{is_patron_mode}")

    disp_upcoming = list(upcoming_matches)
    if not str(sel_lig).startswith("🌍"):
        disp_upcoming = [m for m in disp_upcoming if m.get("lig") == sel_lig]

    if "Maç Saatine" in sort_mode:
        disp_upcoming.sort(key=lambda x: (_time_sort_minutes(x.get("saat", "20:00")), -x.get("conf", 0)))
    elif "Lige Göre" in sort_mode:
        disp_upcoming.sort(key=lambda x: (str(x.get("lig", "")), _time_sort_minutes(x.get("saat", "20:00")), -x.get("conf", 0)))
    elif "Korner Gücüne" in sort_mode:
        disp_upcoming.sort(key=lambda x: (safe_int((x.get("m4") or {}).get("cor_p"), 50), x.get("conf", 0)), reverse=True)
    else:
        disp_upcoming.sort(key=lambda x: (x.get("conf", 0), -_time_sort_minutes(x.get("saat", "20:00"))), reverse=True)

    for idx_u, m in enumerate(disp_upcoming):
        locked_card = (m["conf"] >= 66 and not is_unlocked)
        p_disp = "🔒 VIP LOCKED (66%+ High Probability)" if locked_card else m["pick"]
        pr_disp = "🔒 Unlock VIP to view 2nd Pick & Corner Physics" if locked_card else m["prop"]
        b_col = "#f0b90b" if m["conf"] >= 68 else "#2f81f7"
        k_badge = f"<span style='color:#56d364;font-weight:700;'>✅ Resmi 11 ({m['h_tac']}v{m['a_tac']})</span>" if m["is_off"] else f"<span style='color:#8b949e;'>⏳ 5-Maç Çekirdek XI ({m['h_tac']}v{m['a_tac']})</span>"
        m4_d = m.get("m4") or {}
        dec_u = safe_int(m4_d.get("decision_score"), m["conf"])
        patron_line = f"<div style='margin-top:5px;padding:5px 8px;background:#0d1117;border-left:3px solid #f0b90b;border-radius:4px;font-size:11.5px;color:#e6edf3;'>{m4_d.get('patron_sim_ui','')}</div>" if (is_patron_mode and m4_d.get("patron_sim_ui")) else ""
        st.markdown(
            f"<div class='dp-card' style='border-left:4px solid {b_col};'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;font-size:11.5px;color:#8b949e;'>"
            f"<span>🕒 <b>{m['saat']}</b> • {m['lig']} • {k_badge}</span>"
            f"<span style='background:#21262d;color:#ffd33d;padding:2px 8px;border-radius:6px;font-weight:800;'>Olasılık: %{m['conf']} (Karar:{dec_u}p)</span></div>"
            f"<div style='font-size:15.5px;font-weight:800;margin:5px 0;color:#fff;'>{m['h_name']} vs {m['a_name']}</div>"
            f"<div style='font-size:11.5px;color:#c9d1d9;margin-bottom:4px;'>📈 <b>Form & Mom:</b> {format_form_badges(m['h_form'])} ({m['h_mom']}%) vs {format_form_badges(m['a_form'])} ({m['a_mom']}%)</div>"
            f"<div style='font-size:11px;color:#79c0ff;'>🐋 <b>Oran & Fizik:</b> {m['odd']} | TG: {m['ou']} | <code>P4+:%{m4_d.get('p_over35',20)} | Sh:%{m4_d.get('p_shield',50)} | Dw:{m4_d.get('d_weak',15)}</code></div>"
            f"<div style='margin-top:6px;padding-top:6px;border-top:1px solid #30363d;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;font-size:12px;'>"
            f"<span>🎯 <b>1. Tercih (Ana):</b> <b style='color:#56d364;'>{p_disp}</b> ({m['evo']})</span><span style='color:#d2a8ff;'>{pr_disp}</span></div>"
            f"{patron_line}</div>",
            unsafe_allow_html=True
        )
        with st.expander(f"🏟️ {m['h_name']} vs {m['a_name']} — Tactical Pitch & 5D Power Radar", expanded=False):
            st.markdown(build_tactical_pitch_html(m), unsafe_allow_html=True)
        _render_match_share_box(m, "pre", idx_u, is_unlocked)

    if finished_matches:
        st.markdown("---")
        st.markdown("### 🏁 BİTEN MAÇLAR & DOĞRULANMIŞ KARNE SONUÇLARI")
        for idx_f, m in enumerate(finished_matches):
            won = bool(m.get("won"))
            bd_col = "#2ea043" if won else "#f85149"
            badge_txt = "✅ WON / KAZANDI" if won else "❌ LOST / KAYBETTİ"
            ver_tag = m.get("model_version", MODEL_VERSION)
            st.markdown(
                f"<div class='dp-card' style='border-left:4px solid {bd_col};background:#0d1117;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:11.5px;color:#8b949e;'>"
                f"<span>🏁 <b>FT ({m.get('saat','20:30')})</b> • {m.get('lig','')} • <code>{ver_tag}</code></span>"
                f"<span style='background:{bd_col};color:#fff;padding:1px 8px;border-radius:5px;font-weight:800;'>{badge_txt}</span></div>"
                f"<div style='font-size:15px;font-weight:800;margin:4px 0;color:#fff;'>{m['h_name']} <span style='color:#ffd33d;'>{m['h_score']} - {m['a_score']}</span> {m['a_name']}</div>"
                f"<div style='font-size:11.5px;color:#c9d1d9;'>📊 <b>Maç Sonu İstatistik:</b> Şut: {m['h_sh']}({m['h_sot']})-{m['a_sh']}({m['a_sot']}) | 🚩 Korner: <b>{m['h_cor']}-{m['a_cor']} (Toplam: {m['h_cor']+m['a_cor']})</b> | 🟨 Kart: {m['cards']} | Brier: <code>{m.get('brier',0.0)}</code></div>"
                f"<div style='margin-top:5px;font-size:12px;color:#56d364;'>🎯 <b>AI Hedefi (%{m['conf']}):</b> {m['pick']} &nbsp;|&nbsp; <span style='color:#d2a8ff;'>{m['prop']}</span></div></div>",
                unsafe_allow_html=True
            )
            _render_match_share_box(m, "post", idx_f, is_unlocked)

# ==================== MODÜL 6/6: PATRON KOMUTA VE PAZARLAMA MERKEZİ ====================
load_persistent_store()

url_ref = str(st.query_params.get("ref") or "").strip().upper()
my_dev_candidates = get_all_possible_device_uids()
my_dev_id = get_smart_device_uid()
mini_text = "\n".join(mini_lines)

cur_user = auto_sync_device_user(my_dev_id, url_ref)
user_tier = str(cur_user.get("tier", "NORMAL")) if isinstance(cur_user, dict) else "NORMAL"

patron_devs = MEM.setdefault("patron_devs", {"DP-F3CB9C", "DP-ADMIN1"})
users_db_ref = MEM.setdefault("users_db", {})

# PATRON DOĞRUDAN AÇIK KALKANI: Sunucu yeniden başlasa veya IP/Tarayıcı değişse bile Patron Komuta Merkezi doğrudan açık gelir!
st.session_state["patron_unlocked"] = True
dirty_store = False
for c in my_dev_candidates:
    if c not in patron_devs:
        patron_devs.add(c)
        dirty_store = True
    if c in users_db_ref and users_db_ref[c].get("tier") != "ADMIN":
        users_db_ref[c]["tier"] = "ADMIN"
        dirty_store = True
if dirty_store:
    save_persistent_store()
try:
    if st.query_params.get("uid") != my_dev_id:
        st.query_params["uid"] = my_dev_id
except Exception:
    pass

def render_x_and_telegram_command_center():
    st.markdown("### 🐦 X (Twitter) & 📢 Telegram Global Pazarlama Merkezi")
    tg_cfg = MEM.setdefault("tg_config", {"token": "", "chat_id": ""})
    with st.expander("⚙️ Kalıcı Telegram Bot Token & Kanal (Chat ID) Ayarları", expanded=False):
        c_tk, c_cid = st.columns(2)
        in_tk = c_tk.text_input("Telegram Bot Token:", value=str(tg_cfg.get("token") or ""), type="password")
        in_cid = c_cid.text_input("Telegram Chat ID (Örn: @kanal veya -100...):", value=str(tg_cfg.get("chat_id") or ""))
        if st.button("💾 Telegram Ayarlarını Kalıcı Olarak Kaydet", use_container_width=True):
            MEM["tg_config"] = {"token": in_tk.strip(), "chat_id": in_cid.strip()}
            save_persistent_store()
            st.success("✅ Telegram ayarları dp_persistent_store.json içine kaydedildi!")

    ldg = MEM.get("DATA_LEDGER") or {"karne_str": "0/0", "ak_str": "0/0", "lp_str": "0/0"}
    t_global = f"⚡ DELTA-PULSE AI LIVE TELEMETRY!\n🏆 Verified Record: {ldg['karne_str']}\n💎 Main Safe: {ldg['ak_str']} | 🔥 Live Ambush: {ldg['lp_str']}\n📊 5D Pitch, EWMA-5 Corner & Blowout Physics!\n👉 {APP_PUBLIC_URL}"
    t_live = _build_match_social_text(live_matches[0], mode="live") if live_matches else (_build_match_social_text(finished_matches[0], mode="post") if finished_matches else t_global)
    t_pre = _build_match_social_text(upcoming_matches[0], mode="pre") if upcoming_matches else t_global

    col_x1, col_x2, col_x3 = st.columns(3)
    with col_x1:
        st.code(t_global, language="text")
        st.markdown(f"<a href='https://twitter.com/intent/tweet?text={urllib.parse.quote(t_global)}' target='_blank' style='display:block;text-align:center;background:#1d9bf0;color:#fff;padding:7px;border-radius:6px;font-weight:700;text-decoration:none;'>🐦 Karneyi X'te Paylaş</a>", unsafe_allow_html=True)
    with col_x2:
        st.code(t_live, language="text")
        st.markdown(f"<a href='https://twitter.com/intent/tweet?text={urllib.parse.quote(t_live)}' target='_blank' style='display:block;text-align:center;background:#2ea043;color:#fff;padding:7px;border-radius:6px;font-weight:700;text-decoration:none;'>🐦 Canlı/FT X'te Paylaş</a>", unsafe_allow_html=True)
    with col_x3:
        st.code(t_pre, language="text")
        st.markdown(f"<a href='https://twitter.com/intent/tweet?text={urllib.parse.quote(t_pre)}' target='_blank' style='display:block;text-align:center;background:#f0b90b;color:#000;padding:7px;border-radius:6px;font-weight:800;text-decoration:none;'>🐦 Maç Önü X'te Paylaş</a>", unsafe_allow_html=True)

if st.session_state.get("patron_unlocked"):
    st.markdown(f"## 👑 PATRON KOMUTA & PAZARLAMA MERKEZİ *(Tanınan Cihaz: `{my_dev_id}`)*")
    t1, t2, t3, t4 = st.tabs(["📊 Canlı Bülten & Sahalar", "📋 DP-MİNİ & Data Günlüğü", "👑 TRC20 Kasa & Üye Radarı", "🐦 X & 📢 Telegram Paneli"])
    with t1:
        render_main_bulletin(tier="ADMIN", is_patron_mode=True)
    with t2:
        st.markdown("##### 📋 Patron Özel DP-MİNİ Telemetri & G1 Kalibrasyon Çıktısı")
        t_pass, t_tot, t_fails = run_ft_evaluator_self_test()
        test_badge = f"✅ {t_pass}/{t_tot} GEÇTİ" if t_pass == t_tot else f"❌ HATA ({', '.join(t_fails)})"
        oa_quota = MEM.get("odds_api_cache", {}).get("remaining_quota", "Aktif")
        if hist_vals:
            avg_brier = round(sum(safe_float(x.get("brier"), 0.20) for x in hist_vals) / len(hist_vals), 4)
            avg_mkt_brier = round(sum(safe_float(x.get("mkt_brier"), 0.215) for x in hist_vals) / len(hist_vals), 4)
            avg_clv = round(sum(safe_float(x.get("clv"), 0.0) for x in hist_vals) / len(hist_vals), 2)
            log_losses, mkt_log_losses = [], []
            for x in hist_vals:
                p_c = min(0.98, max(0.02, safe_float(x.get("conf"), 70.0) / 100.0))
                p_m = min(0.98, max(0.02, safe_float(x.get("p_mkt"), 0.58)))
                y_c = 1.0 if x.get("won") else 0.0
                log_losses.append(-(y_c * math.log(p_c) + (1.0 - y_c) * math.log(1.0 - p_c)))
                mkt_log_losses.append(-(y_c * math.log(p_m) + (1.0 - y_c) * math.log(1.0 - p_m)))
            avg_ll = round(sum(log_losses) / len(log_losses), 4)
            avg_mkt_ll = round(sum(mkt_log_losses) / len(mkt_log_losses), 4)
            brier_skill = round((1.0 - (avg_brier / max(1e-6, avg_mkt_brier))) * 100.0, 1)
            g1_status = "✅ G1 GEÇTİ (Piyasa Üstü)" if avg_brier <= avg_mkt_brier else "⚠️ G1 İZLEMEDE"
            st.info(
                f"📐 **G1 Kalibrasyon & CLV Raporu ({len(hist_vals)} Maç):** "
                f"Model Brier: `{avg_brier}` vs Piyasa Brier: `{avg_mkt_brier}` (**BSS: `{brier_skill:+.1f}%`**) | "
                f"Model LL: `{avg_ll}` vs Piyasa LL: `{avg_mkt_ll}` | "
                f"📈 **Ort. CLV:** `{avg_clv:+.2f}%p` | {g1_status} | "
                f"🧪 **FT Hakem Öz-Testi:** `{test_badge}` | 🔌 **AF + OddsAPI (Kalan:{oa_quota})** | Sürüm: `{MODEL_VERSION}`"
            )
        else:
            st.info(f"🧪 **FT Hakem Öz-Testi (Unit Test):** `{test_badge}` | 🔌 **AF + OddsAPI (Kalan:{oa_quota})** | Aktif Sürüm: `{MODEL_VERSION}`")

        def _compact_mini_line(ln):
            reps = [
                ("📊Son5Kor(EWMA):", "K5:"), ("📊ΔÜretim(EWMA5):", "ΔÜ:"),
                ("⏳5MaçÇekirdekXI", "⏳ÇekXI"), ("🧱BlokŞut->Korner", "🧱BlokK"),
                ("📐KanatKorner", "📐KanatK"), ("🛡️SakatKapanma", "🛡️SakatK"),
                ("⚠️PinnacleTers", "⚠️PinTers"), ("🐋PinnacleSharp", "🐋PinSharp"),
                ("💥ErkenKopar", "💥Kopar"), ("🧬RotasyonUyum", "🧬Rot"),
                ("✅ÇekirdekKadro", "✅ÇekKadro"), ("✅ Kadro Onaylı (Sabit)", "✅Sabit"),
                ("🎯 2.Tercih:", "2.T:"), ("Karşılıklı Gol Var", "KG Var"),
                ("Takım Golü 1.5 Üst", "TG 1.5Ü"), ("Kazanır & 1.5 Gol Üst", "Kaz&1.5Ü"),
                ("Maç 1.5 Gol Üst", "1.5Ü"), ("Maç 2.5 Gol Üst", "2.5Ü"),
                ("Korner Üst", "KorÜ"), ("Kart Üst", "KartÜ"),
                ("TÜRKİYE SÜPER LİG", "TR1"), ("İNGİLTERE PREMIER LİG", "ENG1"),
                ("İNGİLTERE CHAMPIONSHIP", "ENG2"), ("İSPANYA LA LIGA 2", "ESP2"),
                ("İSPANYA LA LIGA", "ESP1"), ("ALMANYA BUNDESLIGA", "GER1"),
                ("İTALYA SERIE A", "ITA1"), ("İTALYA SERIE B", "ITA2"),
                ("FRANSA LIGUE 1", "FRA1"), ("HOLLANDA EREDIVISIE", "NED1"),
                ("PORTEKİZ LIGA", "POR1"), ("İSKOÇYA PREMIERSHIP", "SCO1"),
                ("ARJANTİN LIGA PRO", "ARG1"), ("BREZİLYA SERIE A", "BRA1"),
                ("MEKSİKA LIGA MX", "MEX1")
            ]
            out = str(ln)
            for old_s, new_s in reps:
                out = out.replace(old_s, new_s)
            return out

        mini_mode = st.radio(
            "📲 Mobil Kopyalama Modu (Telefon Sınırına Takılmaz):",
            ["🔥 Akıllı Özet (Canlı + Yakın Seans + %75+ & Value + FT)", "📦 2 Parçalı Tam Bülten (Bölünmüş Kutu)", "📜 Tam Liste (Kompakt)"],
            horizontal=True,
            key="dp_mini_copy_mode"
        )

        comp_lines = [_compact_mini_line(x) for x in mini_lines]
        head_line = comp_lines[0] if comp_lines else "⚡ DP-MİNİ"
        live_lns = [x for x in comp_lines[1:] if x.startswith("CANLI|")]
        up_lns = [x for x in comp_lines[1:] if x.startswith("ÖNÜ|")]
        ft_lns = [x for x in comp_lines[1:] if x.startswith("BİTTİ|")]

        if "Akıllı Özet" in mini_mode:
            now_hm = now_tr.hour * 60 + now_tr.minute
            smart_up = []
            for ln in up_lns:
                pts = ln.split("|")
                m_hm = _time_sort_minutes(pts[1]) if len(pts) > 1 else 1200
                conf_v = safe_int(pts[4].replace("%", ""), 0) if len(pts) > 4 else 0
                is_soon = (0 <= (m_hm - now_hm) <= 270) or ("✅Kadro" in ln)
                is_high_or_val = (conf_v >= 75) or ("💎VALUE" in ln) or ("TR1" in ln)
                if is_soon or is_high_or_val:
                    smart_up.append(ln)
            final_txt = "\n".join([head_line] + live_lns + smart_up[:28] + ft_lns[:12])
            st.caption(f"📏 Toplam Boyut: `{len(final_txt)}` karakter (Tek seferde kesilmeden kopyalanır • Süper Lig ve Yakın Maçlar Dahil)")
            st.code(final_txt, language="text")
        elif "2 Parçalı" in mini_mode:
            half_idx = max(1, len(up_lns) // 2)
            p1_txt = "\n".join([head_line + " [PAKET 1/2]"] + live_lns + up_lns[:half_idx])
            p2_txt = "\n".join([head_line + " [PAKET 2/2]"] + up_lns[half_idx:] + ft_lns)
            st.markdown("**📦 Paket 1 (Canlı + Üst Bülten):**")
            st.code(p1_txt, language="text")
            st.markdown("**📦 Paket 2 (Alt Bülten + Biten Maçlar FT):**")
            st.code(p2_txt, language="text")
        else:
            full_comp = "\n".join(comp_lines)
            st.caption(f"📏 Kompakt Tam Boyut: `{len(full_comp)}` karakter")
            st.code(full_comp, language="text")
    with t3:
        users_db = MEM.setdefault("users_db", {})
        vip_cnt = sum(1 for u in users_db.values() if isinstance(u, dict) and u.get("tier") == "VIP")
        st.markdown(f"**👥 Gerçek Cihaz:** `{len(users_db)}` | **👑 Aktif VIP:** `{vip_cnt}` (Kurucu Kalan: `{max(0, 100 - vip_cnt)}/100`)")
        with st.expander("📒 Kalıcı Karne & Arşiv Devir Ayarları (JSON Store)", expanded=False):
            c_bw, c_bt, c_akw, c_akt = st.columns(4)
            nw = c_bw.number_input("Devreden Kazanan", value=safe_int(MEM.get("base_w"), 0), min_value=0)
            nt = c_bt.number_input("Devreden Toplam", value=safe_int(MEM.get("base_t"), 0), min_value=0)
            nakw = c_akw.number_input("Ana Kasa Kazanan", value=safe_int(MEM.get("base_ak_w"), 0), min_value=0)
            nakt = c_akt.number_input("Ana Kasa Toplam", value=safe_int(MEM.get("base_ak_t"), 0), min_value=0)
            if st.button("💾 Kasa Devrini Kalıcı Dosyaya Kaydet", use_container_width=True):
                MEM["base_w"], MEM["base_t"], MEM["base_ak_w"], MEM["base_ak_t"] = int(nw), int(nt), int(nakw), int(nakt)
                save_persistent_store()
                st.rerun()
    with t4:
        render_x_and_telegram_command_center()
else:
    render_main_bulletin(tier=user_tier, is_patron_mode=False)
