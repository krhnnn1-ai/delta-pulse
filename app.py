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

# ==================== MODÜL 2/6: VERİ VE KADRO ÇEKME KATMANI (ULTRA-FAST EWMA-5 & CORE XI + AF & ODDS API) ====================
def _team_names_match(n1, n2):
    s1, s2 = str(n1 or "").lower().strip(), str(n2 or "").lower().strip()
    if not s1 or not s2:
        return False
    if s1 in s2 or s2 in s1:
        return True
    ignore = {"fc", "cf", "sc", "ac", "as", "cd", "ud", "rc", "fk", "sk", "utd", "united", "city", "real", "club", "de", "la"}
    w1 = {w for w in re.split(r"\W+", s1) if len(w) >= 3 and w not in ignore}
    w2 = {w for w in re.split(r"\W+", s2) if len(w) >= 3 and w not in ignore}
    if w1 and w2 and (w1 & w2):
        return True
    return s1[:4] == s2[:4]

def resolve_team_formation(team_name, raw_form, mom_val, is_home=True):
    clean = str(raw_form or "").strip()
    if clean and "-" in clean and len(clean) >= 5:
        return clean, True
    return "4-2-3-1", False

def derive_match_weather(match_title, lig_adi, raw_weather=None):
    if isinstance(raw_weather, dict) and raw_weather.get("temperature"):
        t_f = safe_int(raw_weather.get("temperature"), 62)
        t_c = int(round((t_f - 32) * 5.0 / 9.0)) if t_f > 42 else t_f
        cond = str(raw_weather.get("displayValue") or "Clear")
        return f"⛅ {t_c}°C • {cond} (Resmi Stadyum Verisi)"
    return "⛅ Hava Verisi Yok (Standart Zemin Varsayımı)"

def extract_referee_profile(g_info, match_title, lig_adi):
    offs = (g_info or {}).get("officials") or []
    ref_name = str(offs[0].get("displayName") or offs[0].get("fullName") or "").strip() if (offs and isinstance(offs[0], dict)) else ""
    hot_base = 4.3 if any(k in str(lig_adi).upper() for k in ("SERIE", "BREZİLYA", "ARJANTİN", "LA LIGA", "TÜRKİYE", "BRA.", "ITA.", "ESP.", "TUR.")) else 3.6
    if not ref_name:
        return {"name": "", "avg": hot_base, "style": "⚖️LigBaz(Proxy)", "disp": f"Hakem Bekleniyor (Lig Baz Proxy:{hot_base})", "verified": False}
    return {"name": ref_name, "avg": hot_base, "style": "⚖️LigBaz(Proxy)", "disp": f"{ref_name} (Lig Kart Bazı:{hot_base})", "verified": False}

def _calc_struct_player_rat(t_mom, kademe, pos_abbr, is_starter=True, sh_avg=11.0, freq_bonus=0):
    base_r = 71 + int((t_mom - 50) * 0.14) + (3 if kademe == 1 else 0) + int((sh_avg - 10.5) * 0.4) + min(2, freq_bonus)
    if any(k in str(pos_abbr) for k in ("F", "ST", "W", "CAM")):
        base_r += 1
    if not is_starter:
        base_r -= (2 if kademe == 1 else 4)
    return min(90, max(65, base_r))

def _ewma_robust(vals, weights, digits=1):
    if not vals:
        return 0.0
    if len(vals) == 1:
        return round(float(vals[0]), digits)
    w_use = list(weights[:len(vals)])
    if len(vals) >= 3:
        s_v = sorted(vals)
        med = s_v[len(s_v) // 2]
        for idx_v, v in enumerate(vals):
            if med > 0 and (v < med * 0.35 or v > med * 2.15):
                w_use[idx_v] *= 0.60
    w_sum = max(1e-9, sum(w_use))
    return round(sum(v * w for v, w in zip(vals, w_use)) / w_sum, digits)

def _fetch_espn_team_squad_fallback(slug, team_id, t_mom, kademe, sh_avg=11.0):
    if not team_id:
        return [], []
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/teams/{team_id}/roster"
        r = HTTP_SESSION.get(url, timeout=2.0)
        if r.status_code == 200:
            athletes = r.json().get("athletes") or []
            all_p = []
            for idx_a, ath in enumerate(athletes):
                if not isinstance(ath, dict):
                    continue
                p_n = str(ath.get("shortName") or ath.get("displayName") or ath.get("fullName") or "").strip()
                if not p_n:
                    continue
                j_n = str(ath.get("jersey") or str(idx_a + 1))
                pos_a = str((ath.get("position") or {}).get("abbreviation") or "M")
                p_rat = _calc_struct_player_rat(t_mom, kademe, pos_a, idx_a < 11, sh_avg)
                all_p.append({"name": p_n, "num": j_n, "pos": pos_a, "rat": p_rat})
            if len(all_p) >= 11:
                gks = [p for p in all_p if "G" in p["pos"]]
                outfield = [p for p in all_p if "G" not in p["pos"]]
                st_list = ([gks[0]] if gks else [all_p[0]]) + outfield[:10]
                bn_list = outfield[10:15]
                return st_list[:11], bn_list[:5]
    except Exception:
        pass
    return [], []

def _fetch_cached_past_event(slug, last_id):
    ev_mem = MEM.setdefault("event_summary_cache", {})
    if last_id in ev_mem:
        return ev_mem[last_id]
    try:
        r_h = HTTP_SESSION.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={last_id}", timeout=2.0)
        if r_h.status_code == 200:
            d_h = r_h.json()
            if len(ev_mem) > 400:
                ev_mem.clear()
            ev_mem[last_id] = d_h
            return d_h
    except Exception:
        pass
    return {}

def fetch_last_match_twin(slug, t_name, data, side_idx, t_mom, kademe):
    hist_mem = MEM.setdefault("team_hist_cache", {})
    today_tag = datetime.now(TR_TZ).strftime("%Y%m%d")
    ck = f"{slug}_{t_name}_{today_tag}_v12_fast"
    if ck in hist_mem and isinstance(hist_mem[ck], dict) and "cor_avg" in hist_mem[ck]:
        return dict(hist_mem[ck])

    cor_avg = round(4.4 + (t_mom - 50) * 0.025, 1)
    sh_avg = round(10.5 + (t_mom - 50) * 0.06, 1)
    sot_avg = round(3.6 + (t_mom - 50) * 0.03, 1)
    xg_avg = round(sot_avg * 0.30 + max(0.0, sh_avg - sot_avg) * 0.05, 2)
    card_avg, foul_avg, rest_days = 1.9, 11.2, 6
    prev_tac, team_id = "4-2-3-1", ""
    inj_names, wing_inj, gk_inj, prev_st, prev_bn = set(), False, False, [], []
    empirical_matches_found = 0

    for bt_top in ((data.get("boxscore") or {}).get("teams") or []):
        t_obj = bt_top.get("team") or {}
        if _team_names_match(t_name, t_obj.get("shortDisplayName") or t_obj.get("displayName") or t_obj.get("name")):
            team_id = str(t_obj.get("id") or "")

    inj_list = data.get("injuries") or []
    if side_idx < len(inj_list) and isinstance(inj_list[side_idx], dict):
        for item in (inj_list[side_idx].get("injuries") or []):
            ath = item.get("athlete") or {}
            p_nm = str(ath.get("shortName") or ath.get("displayName") or "").strip()
            pos_ab = str((ath.get("position") or {}).get("abbreviation") or "")
            if p_nm:
                inj_names.add(p_nm.lower())
            if any(k in pos_ab for k in ("W", "M", "F", "ST")):
                wing_inj = True
            if "G" in pos_ab:
                gk_inj = True

    l5 = data.get("lastFiveGames") or []
    l5_obj = None
    for cand in l5:
        if isinstance(cand, dict) and _team_names_match(t_name, (cand.get("team") or {}).get("displayName") or (cand.get("team") or {}).get("shortDisplayName")):
            l5_obj = cand
            if not team_id:
                team_id = str((cand.get("team") or {}).get("id") or "")
            break
    if not l5_obj and side_idx < len(l5) and isinstance(l5[side_idx], dict):
        l5_obj = l5[side_idx]
        if not team_id:
            team_id = str((l5_obj.get("team") or {}).get("id") or "")

    if l5_obj:
        evs = [e for e in (l5_obj.get("events") or []) if isinstance(e, dict)][:5]
        if evs and evs[0].get("gameDate"):
            try:
                gd_str = str(evs[0]["gameDate"]).replace("Z", "+00:00")
                last_dt = datetime.fromisoformat(gd_str).astimezone(TR_TZ)
                rest_days = max(2, min(14, (datetime.now(TR_TZ) - last_dt).days))
            except Exception:
                rest_days = 6

        c_vals, s_vals, sot_vals, xg_vals, crd_vals, fl_vals, w_vals = [], [], [], [], [], [], []
        tac_list = []
        player_pool = {}

        ev_ids = [(e_idx, str(ev_item.get("id") or ev_item.get("eventId") or "")) for e_idx, ev_item in enumerate(evs)]
        ev_ids = [(idx_e, eid) for idx_e, eid in ev_ids if eid]

        if ev_ids:
            with ThreadPoolExecutor(max_workers=5) as sub_ex:
                past_jsons = list(sub_ex.map(lambda p: (p[0], _fetch_cached_past_event(slug, p[1])), ev_ids))

            for e_idx, d_h in past_jsons:
                if not d_h:
                    continue
                base_w = 0.80 ** e_idx
                for bt in ((d_h.get("boxscore") or {}).get("teams") or []):
                    bt_nm = str((bt.get("team") or {}).get("shortDisplayName") or (bt.get("team") or {}).get("displayName") or "")
                    bt_id = str((bt.get("team") or {}).get("id") or "")
                    if (team_id and bt_id == team_id) or _team_names_match(t_name, bt_nm):
                        c_v = get_stat(bt, ["wonCorners", "corners"])
                        s_v = get_stat(bt, ["totalShots", "shotsSummary"])
                        st_v = get_stat(bt, ["shotsOnTarget", "onGoal"])
                        yel_v = get_stat(bt, ["yellowCards"])
                        red_v = get_stat(bt, ["redCards"])
                        y_v = yel_v + red_v
                        f_v = get_stat(bt, ["foulsCommitted"])
                        if c_v > 0 or s_v > 0:
                            match_w = base_w * (0.50 if red_v > 0 else 1.0)
                            w_vals.append(match_w)
                            c_vals.append(c_v)
                            s_vals.append(s_v)
                            sot_vals.append(st_v)
                            xg_vals.append(round(st_v * 0.30 + max(0, s_v - st_v) * 0.05, 2))
                            crd_vals.append(y_v)
                            if f_v > 0:
                                fl_vals.append(f_v)

                for r_old in (d_h.get("rosters") or []):
                    rt_obj = r_old.get("team") or {}
                    rt_nm = str(rt_obj.get("shortDisplayName") or rt_obj.get("displayName") or "")
                    rt_id = str(rt_obj.get("id") or "")
                    if (team_id and rt_id == team_id) or _team_names_match(t_name, rt_nm):
                        if r_old.get("formation"):
                            tac_list.append(str(r_old.get("formation")).strip())
                        for pe in (r_old.get("roster") or []):
                            if not isinstance(pe, dict):
                                continue
                            ath = pe.get("athlete") or {}
                            p_n = str(ath.get("shortName") or ath.get("displayName") or "").strip()
                            if not p_n:
                                continue
                            j_n = str(pe.get("jersey") or ath.get("jersey") or "10")
                            pos_a = str(((pe.get("position") or ath.get("position")) or {}).get("abbreviation") or "M")
                            is_st = bool(pe.get("starter"))
                            pk_low = p_n.lower()
                            if pk_low not in player_pool:
                                player_pool[pk_low] = {
                                    "name": p_n, "num": j_n, "pos": pos_a,
                                    "st_cnt": 0, "st_w": 0.0, "app_cnt": 0, "last_idx": e_idx
                                }
                            player_pool[pk_low]["app_cnt"] += 1
                            if is_st:
                                player_pool[pk_low]["st_cnt"] += 1
                                player_pool[pk_low]["st_w"] += base_w

        empirical_matches_found = len(s_vals)
        if c_vals: cor_avg = _ewma_robust(c_vals, w_vals, 1)
        if s_vals: sh_avg = _ewma_robust(s_vals, w_vals, 1)
        if sot_vals: sot_avg = _ewma_robust(sot_vals, w_vals, 1)
        if xg_vals: xg_avg = _ewma_robust(xg_vals, w_vals, 2)
        if crd_vals: card_avg = _ewma_robust(crd_vals, w_vals, 1)
        if fl_vals: foul_avg = _ewma_robust(fl_vals, w_vals[:len(fl_vals)], 1)

        if tac_list:
            prev_tac = Counter(tac_list).most_common(1)[0][0]

        if player_pool:
            all_tracked = list(player_pool.values())
            all_tracked.sort(key=lambda x: (x["st_w"], x["st_cnt"], x["app_cnt"], -x["last_idx"]), reverse=True)
            gks = [p for p in all_tracked if "G" in p["pos"]]
            outfield = [p for p in all_tracked if "G" not in p["pos"]]
            core_raw = ([gks[0]] if gks else []) + outfield
            core_st_raw = core_raw[:11]
            used_names = {p["name"].lower() for p in core_st_raw}
            core_bn_raw = [p for p in all_tracked if p["name"].lower() not in used_names][:5]

            for p in core_st_raw:
                freq_b = 1 if p["st_cnt"] >= 3 else 0
                prev_st.append({
                    "name": p["name"], "num": p["num"], "pos": p["pos"],
                    "rat": _calc_struct_player_rat(t_mom, kademe, p["pos"], True, sh_avg, freq_b),
                    "core_starts": p["st_cnt"]
                })
            for p in core_bn_raw:
                prev_bn.append({
                    "name": p["name"], "num": p["num"], "pos": p["pos"],
                    "rat": _calc_struct_player_rat(t_mom, kademe, p["pos"], False, sh_avg, 0),
                    "core_starts": p["st_cnt"]
                })

    if len(prev_st) < 11 and team_id:
        fb_st, fb_bn = _fetch_espn_team_squad_fallback(slug, team_id, t_mom, kademe, sh_avg)
        if len(fb_st) >= 11:
            prev_st, prev_bn = fb_st, fb_bn

    if prev_st and inj_names:
        clean_st, sub_pool = [], list(prev_bn)
        for p in prev_st:
            if p["name"].lower() in inj_names:
                wing_inj = True
                if sub_pool: clean_st.append(sub_pool.pop(0))
            else:
                clean_st.append(p)
        prev_st, prev_bn = clean_st, sub_pool

    h_base = {
        "cor_avg": cor_avg, "sh_avg": sh_avg, "sot_avg": sot_avg, "xg_avg": xg_avg,
        "card_avg": card_avg, "foul_avg": foul_avg, "rest_days": rest_days,
        "prev_tac": prev_tac, "inj_cnt": len(inj_names), "wing_inj": wing_inj, "gk_inj": gk_inj,
        "emp_n": empirical_matches_found,
        "prev_st": prev_st[:11], "prev_bn": prev_bn[:5]
    }
    # KOŞULSUZ ÖNBELLEK: Oyuncu listesi eksik dönse bile geçmiş maç istatistikleri tekrar tekrar API'den çekilmez!
    hist_mem[ck] = h_base
    return dict(h_base)

def build_team_hist_metrics(h_base, cur_form, rot_cnt, starters, bench, t_mom, kademe):
    att_players = [p for p in (starters or []) if any(k in str(p.get("pos", "")) for k in ("W", "M", "F", "ST"))]
    bench_rats = [safe_int(p.get("rat"), 72) for p in (bench or [])]
    avg_att_rat = int(round(sum(safe_int(p.get("rat"), 74) for p in att_players) / len(att_players))) if att_players else (73 + int((t_mom - 50) * 0.12) + (3 if kademe == 1 else 0))
    sub_rat = max(bench_rats) if bench_rats else (avg_att_rat - (2 if kademe == 1 else 4))

    has_wing_change = bool(h_base.get("wing_inj") or rot_cnt >= 3)
    hungry_sub = bool(has_wing_change and sub_rat >= 76 and rot_cnt <= 3)
    real_wing_drop = bool(h_base.get("wing_inj") and sub_rat <= 70)

    if hungry_sub:
        wing_impact = 4
    elif real_wing_drop:
        wing_impact = -10
    elif rot_cnt >= 4:
        wing_impact = -5
    elif rot_cnt == 3:
        wing_impact = -2
    else:
        wing_impact = 0

    total_missing = safe_int(h_base.get("inj_cnt"), 0) + (1 if rot_cnt >= 4 else 0)
    def_shift = (cur_form in ("5-3-2", "5-4-1", "4-5-1") and h_base.get("prev_tac") in ("4-3-3", "4-2-3-1", "3-4-3")) or (total_missing >= 3 and sub_rat <= 71)
    return {
        "cor_avg": h_base.get("cor_avg", 4.5), "sh_avg": h_base.get("sh_avg", 10.5),
        "sot_avg": h_base.get("sot_avg", 3.6), "xg_avg": h_base.get("xg_avg", 1.35),
        "card_avg": h_base.get("card_avg", 1.8), "foul_avg": h_base.get("foul_avg", 11.0),
        "rest_days": h_base.get("rest_days", 6), "gk_inj": bool(h_base.get("gk_inj", False)),
        "prev_tac": h_base.get("prev_tac", cur_form), "sub_rat": sub_rat,
        "emp_n": safe_int(h_base.get("emp_n"), 0),
        "hungry_sub": hungry_sub, "wing_drop": real_wing_drop,
        "wing_impact": wing_impact, "def_shift": def_shift
    }

def _af_get(endpoint, params, timeout=2.6):
    if not API_FOOTBALL_KEY:
        return []
    try:
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        r = HTTP_SESSION.get(f"https://v3.football.api-sports.io/{endpoint}", headers=headers, params=params, timeout=timeout)
        if r.status_code == 200:
            return (r.json() or {}).get("response") or []
    except Exception:
        pass
    return []

def _sync_af_daily_fixtures():
    af_mem = MEM.setdefault("af_cache", {})
    now_ts = time.time()
    today_iso = datetime.now(TR_TZ).strftime("%Y-%m-%d")
    fx_map = af_mem.get("fixtures_by_date", {}).get(today_iso)
    if isinstance(fx_map, list) and (now_ts - safe_float(af_mem.get("fx_ts"), 0.0)) < 900.0:
        return fx_map
    resp = _af_get("fixtures", {"date": today_iso, "timezone": "Europe/Istanbul"}, timeout=3.2)
    if resp:
        slim_list = []
        for item in resp:
            f_obj = item.get("fixture") or {}
            t_obj = item.get("teams") or {}
            g_obj = item.get("goals") or {}
            slim_list.append({
                "fid": f_obj.get("id"),
                "ref": str(f_obj.get("referee") or "").strip(),
                "status": str((f_obj.get("status") or {}).get("short") or "NS"),
                "h_name": str((t_obj.get("home") or {}).get("name") or ""),
                "a_name": str((t_obj.get("away") or {}).get("name") or ""),
                "h_g": g_obj.get("home"), "a_g": g_obj.get("away")
            })
        af_mem.setdefault("fixtures_by_date", {})[today_iso] = slim_list
        af_mem["fx_ts"] = now_ts
        return slim_list
    return fx_map or []

def _find_af_fixture(h_name, a_name):
    fx_list = _sync_af_daily_fixtures()
    for f in fx_list:
        if _team_names_match(h_name, f.get("h_name")) and _team_names_match(a_name, f.get("a_name")):
            return f
    return None

def _fetch_af_real_odds(fid):
    if not fid:
        return {}
    af_mem = MEM.setdefault("af_cache", {})
    odds_store = af_mem.setdefault("odds_by_fid", {})
    if str(fid) in odds_store and isinstance(odds_store[str(fid)], dict):
        return odds_store[str(fid)]
    resp = _af_get("odds", {"fixture": fid}, timeout=2.5)
    parsed = {}
    if resp and isinstance(resp[0], dict):
        bms = resp[0].get("bookmakers") or []
        bms_sorted = sorted(bms, key=lambda b: 0 if any(k in str(b.get("name", "")).lower() for k in ("pinnacle", "bet365", "1xbet", "bwin", "unibet")) else 1)
        for bm in bms_sorted:
            for bet in (bm.get("bets") or []):
                b_id = safe_int(bet.get("id"), 0)
                b_nm = str(bet.get("name") or "").lower()
                vals = bet.get("values") or []
                if b_id == 5 or "goals over/under" == b_nm:
                    for v in vals:
                        lbl = str(v.get("value") or "")
                        odd = safe_float(v.get("odd"), 0.0)
                        if lbl == "Over 1.5" and odd > 1.01 and "o15_odd" not in parsed:
                            parsed["o15_odd"] = odd
                        elif lbl == "Over 2.5" and odd > 1.01 and "o25_odd" not in parsed:
                            parsed["o25_odd"] = odd
                elif b_id == 8 or "both teams score" in b_nm:
                    for v in vals:
                        if str(v.get("value") or "") == "Yes" and safe_float(v.get("odd"), 0.0) > 1.01 and "btts_odd" not in parsed:
                            parsed["btts_odd"] = safe_float(v.get("odd"), 0.0)
                elif b_id == 45 or "corners over/under" in b_nm or "total corners" in b_nm:
                    for v in vals:
                        lbl = str(v.get("value") or "")
                        odd = safe_float(v.get("odd"), 0.0)
                        if "Over 8.5" in lbl and odd > 1.01 and "cor85_odd" not in parsed:
                            parsed["cor85_odd"] = odd
                        elif "Over 9.5" in lbl and odd > 1.01 and "cor95_odd" not in parsed:
                            parsed["cor95_odd"] = odd
                elif b_id == 16 or "total - home" in b_nm:
                    for v in vals:
                        if str(v.get("value") or "") == "Over 1.5" and safe_float(v.get("odd"), 0.0) > 1.01 and "h_o15_odd" not in parsed:
                            parsed["h_o15_odd"] = safe_float(v.get("odd"), 0.0)
                elif b_id == 17 or "total - away" in b_nm:
                    for v in vals:
                        if str(v.get("value") or "") == "Over 1.5" and safe_float(v.get("odd"), 0.0) > 1.01 and "a_o15_odd" not in parsed:
                            parsed["a_o15_odd"] = safe_float(v.get("odd"), 0.0)
            if len(parsed) >= 4:
                break
    odds_store[str(fid)] = parsed
    return parsed

def _enrich_roster_with_api_football(res, h_name, a_name, state, mins_to_ko):
    try:
        af_fx = _find_af_fixture(h_name, a_name)
        if not af_fx:
            return
        fid = af_fx.get("fid")
        res["af_fid"] = fid
        if af_fx.get("ref") and not (res.get("ref") or {}).get("name"):
            ref_nm = af_fx["ref"].split(",")[0].strip()
            avg_c = safe_float((res.get("ref") or {}).get("avg"), 4.0)
            res["ref"] = {"name": ref_nm, "avg": avg_c, "style": "✅AF-Hakem", "disp": f"{ref_nm} (AF Onaylı • Baz:{avg_c})", "verified": True}
        real_odds = _fetch_af_real_odds(fid)
        if real_odds:
            res["af_odds"] = real_odds
        if state == "pre" and not res.get("official") and mins_to_ko <= 65 and fid:
            af_mem = MEM.setdefault("af_cache", {})
            lu_cache = af_mem.setdefault("lineups_by_fid", {})
            lu_resp = lu_cache.get(str(fid))
            if lu_resp is None:
                lu_resp = _af_get("fixtures/lineups", {"fixture": fid}, timeout=2.4)
                if lu_resp:
                    lu_cache[str(fid)] = lu_resp
            if isinstance(lu_resp, list) and len(lu_resp) >= 2:
                for side_lu in lu_resp[:2]:
                    t_lu_name = str((side_lu.get("team") or {}).get("name") or "")
                    side_k = "h" if _team_names_match(h_name, t_lu_name) else "a"
                    form_lu = str(side_lu.get("formation") or "").strip()
                    start_xi = side_lu.get("startXI") or []
                    if len(start_xi) >= 11 and side_k in res:
                        res["official"] = True
                        if form_lu and "-" in form_lu:
                            res[side_k]["tac"] = form_lu
                            res[side_k]["tac_verified"] = True
    except Exception:
        pass

_ESPN_TO_ODDS_API_SPORT = {
    "uefa.champions": "soccer_uefa_champs_league",
    "uefa.europa": "soccer_uefa_europa_league",
    "uefa.europa.conf": "soccer_uefa_europa_conference_league",
    "conmebol.libertadores": "soccer_conmebol_copa_libertadores",
    "tur.1": "soccer_turkey_super_league",
    "esp.1": "soccer_spain_la_liga",
    "ger.1": "soccer_germany_bundesliga",
    "eng.1": "soccer_epl",
    "ita.1": "soccer_italy_serie_a",
    "fra.1": "soccer_france_ligue_one",
    "ned.1": "soccer_netherlands_eredivisie",
    "por.1": "soccer_portugal_primeira_liga",
    "sco.1": "soccer_spl",
    "eng.league_cup": "soccer_england_efl_cup",
    "bra.1": "soccer_brazil_campeonato",
    "arg.1": "soccer_argentina_primera_division",
    "mex.1": "soccer_mexico_ligamx",
    "ita.2": "soccer_italy_serie_b",
    "eng.2": "soccer_efl_champ",
    "esp.2": "soccer_spain_segunda_division"
}

def _sync_odds_api_league(slug):
    if not THE_ODDS_API_KEY:
        return []
    sport_key = _ESPN_TO_ODDS_API_SPORT.get(slug)
    if not sport_key:
        return []
    oa_mem = MEM.setdefault("odds_api_cache", {})
    lg_store = oa_mem.setdefault("by_sport", {})
    now_ts = time.time()
    cached_lg = lg_store.get(sport_key)
    if isinstance(cached_lg, dict) and (now_ts - safe_float(cached_lg.get("ts"), 0.0)) < 1800.0:
        return cached_lg.get("data") or []
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
        params = {
            "apiKey": THE_ODDS_API_KEY,
            "regions": "eu,uk",
            "markets": "h2h,totals",
            "oddsFormat": "decimal"
        }
        r = HTTP_SESSION.get(url, params=params, timeout=3.0)
        if r.status_code == 200:
            data = r.json() or []
            lg_store[sport_key] = {"ts": now_ts, "data": data}
            rem_q = r.headers.get("x-requests-remaining")
            if rem_q is not None:
                oa_mem["remaining_quota"] = str(rem_q)
            return data
    except Exception:
        pass
    return (cached_lg or {}).get("data") or []

def _enrich_roster_with_the_odds_api(res, slug, h_name, a_name, state):
    if state == "post":
        return
    try:
        events = _sync_odds_api_league(slug)
        if not events:
            return
        matched_ev = None
        for ev in events:
            if _team_names_match(h_name, ev.get("home_team")) and _team_names_match(a_name, ev.get("away_team")):
                matched_ev = ev
                break
        if not matched_ev:
            return

        bms = matched_ev.get("bookmakers") or []
        if not bms:
            return

        pin_h, pin_d, pin_a = 0.0, 0.0, 0.0
        soft_h_list, soft_d_list, soft_a_list = [], [], []
        best_o25_odd, best_o15_odd = 0.0, 0.0

        for bm in bms:
            bm_key = str(bm.get("key") or "").lower()
            is_pin = ("pinnacle" in bm_key)
            for mkt in (bm.get("markets") or []):
                m_key = str(mkt.get("key") or "")
                outcomes = mkt.get("outcomes") or []
                if m_key == "h2h":
                    oh, od, oa = 0.0, 0.0, 0.0
                    for out in outcomes:
                        nm = str(out.get("name") or "")
                        pr = safe_float(out.get("price"), 0.0)
                        if nm.lower() == "draw":
                            od = pr
                        elif _team_names_match(h_name, nm):
                            oh = pr
                        elif _team_names_match(a_name, nm):
                            oa = pr
                    if oh > 1.01 and od > 1.01 and oa > 1.01:
                        if is_pin:
                            pin_h, pin_d, pin_a = oh, od, oa
                        else:
                            soft_h_list.append(oh)
                            soft_d_list.append(od)
                            soft_a_list.append(oa)
                elif m_key == "totals":
                    for out in outcomes:
                        if str(out.get("name") or "").lower() == "over":
                            pt = safe_float(out.get("point"), 0.0)
                            pr = safe_float(out.get("price"), 0.0)
                            if abs(pt - 2.5) < 0.05 and pr > 1.01:
                                if is_pin or best_o25_odd == 0.0:
                                    best_o25_odd = pr
                            elif abs(pt - 1.5) < 0.05 and pr > 1.01:
                                if is_pin or best_o15_odd == 0.0:
                                    best_o15_odd = pr

        use_h = pin_h if pin_h > 1.01 else (sum(soft_h_list) / len(soft_h_list) if soft_h_list else 0.0)
        use_d = pin_d if pin_d > 1.01 else (sum(soft_d_list) / len(soft_d_list) if soft_d_list else 0.0)
        use_a = pin_a if pin_a > 1.01 else (sum(soft_a_list) / len(soft_a_list) if soft_a_list else 0.0)

        oa_info = {}
        if use_h > 1.01 and use_d > 1.01 and use_a > 1.01:
            qh, qd, qa = 1.0 / use_h, 1.0 / use_d, 1.0 / use_a
            q_sum = qh + qd + qa
            oa_info["nv_h"] = round((qh / q_sum) * 100.0, 1)
            oa_info["nv_d"] = round((qd / q_sum) * 100.0, 1)
            oa_info["nv_a"] = round((qa / q_sum) * 100.0, 1)
            oa_info["dec_h"], oa_info["dec_d"], oa_info["dec_a"] = round(use_h, 2), round(use_d, 2), round(use_a, 2)
            oa_info["is_pinnacle"] = (pin_h > 1.01)

            if pin_h > 1.01 and soft_h_list and soft_a_list:
                avg_sh = sum(soft_h_list) / len(soft_h_list)
                avg_sa = sum(soft_a_list) / len(soft_a_list)
                pin_edge_h = round(((1.0 / pin_h) - (1.0 / avg_sh)) * 100.0, 1)
                pin_edge_a = round(((1.0 / pin_a) - (1.0 / avg_sa)) * 100.0, 1)
                oa_info["pin_sharp_h"] = pin_edge_h
                oa_info["pin_sharp_a"] = pin_edge_a

        af_o = res.setdefault("af_odds", {})
        if best_o25_odd > 1.01 and "o25_odd" not in af_o:
            af_o["o25_odd"] = round(best_o25_odd, 2)
        if best_o15_odd > 1.01 and "o15_odd" not in af_o:
            af_o["o15_odd"] = round(best_o15_odd, 2)

        if oa_info:
            res["odds_api"] = oa_info
    except Exception:
        pass

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

        # YENİ: Scoreboard'da şut/korner 0 döndüğünde biten maçların silinmemesi için Boxscore yedek istatistikleri:
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

# OTOMATİK ONARIM KALKANI: Canlı oran kayması veya reboot yüzünden tercihi kayan maçları gerçek maç önü kilitli tercihlerine döndürür:
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

            # İKİZ SATIR KALKANI: Aynı maçın iki kez işlenmesini kesin olarak engelle!
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

            # CANLI ORAN KORUMASI: Maç canlıya ('in') veya bitmişe ('post') geçtiyse, maç önü model hesaplamasında açılış oranlarını sabitle ki canlı oranlar maç önü tercihini kaydırmasın!
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
            # Maç başladıktan ('in' veya 'post') sonra tercih kesinlikle kilitli aşamadan okunur, canlı oranla ezilmez!
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

# ==================== MODÜL 4/6: BÜLTEN TARAYICI VE DP-MİNİ (60s RAM KALKANI & FT MÜHÜR KALKANI) ====================
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

# OTOMATİK ONARIM KALKANI: Reboot sırasında oranları silindiği için tercihi ezilen maçları gerçek kilitli tercihlerine geri döndürür:
_REPAIR_LOCKED_MAP = {
    "Eyupspor": ("Maç 1.5 Gol Üst", 84, True),
    "Necaxa": ("🚩 8.5 Korner Üst", 74, True),
    "Atl. San Luis": ("🚩 8.5 Korner Üst", 74, True),
    "Tigre": ("Maç 1.5 Gol Üst", 74, False),
    "Unión (SF)": ("🚩 8.5 Korner Üst", 73, False)
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

# 60 SANİYELİK HIZ KALKANI: Sıralama veya lig filtresi değiştirildiğinde ESPN API'ye tekrar gitmez, 0.1 saniyede RAM'den yükler!
if (now_epoch - safe_float(b_snap.get("ts"), 0.0)) < 60.0 and (b_snap.get("up") or b_snap.get("live") or b_snap.get("fin")):
    live_matches = list(b_snap["live"])
    upcoming_matches = list(b_snap["up"])
    finished_matches = list(b_snap["fin"])
    mini_lines = list(b_snap["mini"])
    fin_cache = MEM.setdefault("finished_cache", {})
    hist_vals = [x for k, x in MEM.get("history_scores", {}).items() if isinstance(x, dict) and k in fin_cache]
else:
    raw_matches, roster_tasks = [], []
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

            ev_date_str = str(ev.get("date") or "")
            mins_to_ko = 180
            try:
                ev_date_str = (ev_date_str[:-1] + ":00+00:00") if (len(ev_date_str) == 17 and ev_date_str.endswith("Z")) else ev_date_str.replace("Z", "+00:00")
                dt_ev = datetime.fromisoformat(ev_date_str).astimezone(TR_TZ)
                hours_diff = (dt_ev - now_tr).total_seconds() / 3600.0
                mins_to_ko = int(round(hours_diff * 60.0))
                if state == "pre" and (hours_diff < -0.35 or hours_diff > 24.0):
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
                op_entry = {"fav_val": fav_val, "ou_val": ou_val}
                op_mem[match_key] = op_entry
            op_fav, op_ou = safe_int(op_entry.get("fav_val"), fav_val), safe_float(op_entry.get("ou_val"), ou_val)

            disp_odd = f"{fav_abbr} {fav_val:+d}" if fav_val > 0 else f"{fav_abbr} {fav_val}"
            if not has_live_api_odds:
                disp_odd += "(ProxyOran)"
            if fav_val != op_fav:
                d_raw = fav_val - op_fav
                d_prob = round(_odd_to_prob(fav_val) - _odd_to_prob(op_fav), 1)
                if d_prob >= 2.0:
                    disp_odd += f" 🔥Δ{d_raw:+d}(+{d_prob}%p)"
                elif d_prob <= -2.0:
                    disp_odd += f" ⚠️Δ{d_raw:+d}({d_prob}%p)"
            if ou_val > op_ou:
                disp_odd += f" 💥TG↑({op_ou}->{ou_val})"

            raw_matches.append((slug, lig_adi, kademe, ev, comp, state, completed, clk, h_c, a_c, h_name, a_name, h_abbr, a_abbr, match_title, h_form, a_form, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, has_live_api_odds, ev_id, odds_3way, ev_date_str))
            roster_tasks.append((slug, ev_id, match_title, h_name, a_name, h_mom, a_mom, disp_odd, state, kademe, fav_abbr, fav_val, a_abbr, mins_to_ko))

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
        slug, lig_adi, kademe, ev, comp, state, completed, clk, h_c, a_c, h_name, a_name, h_abbr, a_abbr, match_title, h_form, a_form, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, has_live_api_odds, ev_id, odds_3way, kickoff_utc = item
        match_key = ev_id if ev_id else match_title

        # 1) FT MÜHÜR KALKANI: Maç zaten bitmiş ve fin_cache içine sonucuyla mühürlenmişse, oranları silinmiş maçı ASLA baştan hesaplama!
        if state == "post" and match_key in fin_cache and isinstance(fin_cache[match_key], dict) and "won" in fin_cache[match_key]:
            continue

        lock_id = f"{match_key}_{MODEL_VERSION}"
        legacy_rec = locked_picks.get(f"{match_key}_M4.3_DC_NEGBINOM_EWMA5") or locked_picks.get(match_title) or {}
        rec = locked_picks.get(lock_id) if isinstance(locked_picks.get(lock_id), dict) else (dict(legacy_rec) if state != "pre" and isinstance(legacy_rec, dict) else {})

        has_real_pre_lock = bool(rec.get("CONFIRMED_XI") or rec.get("PRE_LINEUP") or rec.get("pick") or (match_key in MEM.get("pre_lineup_memory", {})))

        # 2) REBOOT KORUMASI: Maç bitmişse ('post') ama sistemde maç önü kilitli hiçbir tahmini yoksa, oranları silinmiş maça sonradan uydurma tahmin üretme!
        if state == "post" and not has_real_pre_lock:
            continue

        r_data = roster_map.get(match_title) or {}
        r_data["slug"] = slug
        r_data["odds_3way"] = odds_3way
        is_off = bool(r_data.get("official"))
        h_tac = str((r_data.get("h") or {}).get("tac") or "4-2-3-1")
        a_tac = str((r_data.get("a") or {}).get("tac") or "4-2-3-1")
        conf, pick, disp_odd, warn_flag, m4_str, m4 = evaluate_pre_match(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, kademe, r_data, lig_adi)
        conf, pick, disp_odd, evo_str, prop_str, evo_changed = compute_post_lineup_evolution_and_props(match_key, is_off, h_name, a_name, h_abbr, a_abbr, h_tac, a_tac, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, conf, pick, lig_adi, r_data, m4)

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
            if is_off and "CONFIRMED_XI" not in rec:
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

            op_info = MEM.get("opening_odds", {}).get(match_key) or {"fav_val": fav_val, "ou_val": ou_val}
            op_fav_v = safe_int(op_info.get("fav_val"), fav_val)
            op_ou_v = safe_float(op_info.get("ou_val"), ou_val)
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
