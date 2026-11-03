# ==================== MODÜL 1/6: AYARLAR, HAFIZA VE ÜYELİK ====================
import os
import re
import time
import json
import math
import hashlib
import urllib.parse
import requests
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Delta Pulse AI — 24/7 Whale & XI Radar", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

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

/* CİHAZA GÖRE OTOMATİK EKRAN VE 5D SAHA ÖLÇEKLEME (PC & MOBİL UYUMLU) */
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
# Sadece SHA-256 kriptografik özetleri (Plaintext şifre kaynak kodda yer almaz)
ADMIN_HASHES = {
    "5901b9952716f713fb0e0c7f1972fb2125c79e0c7c93d18d42ef1c8815b49b0e",
    "4c94485e0c21ae6c41ce1dfe7b6b28f56c779263487d408860f483029357900d"
}
APP_PUBLIC_URL = "https://delta-pulse-mam7gxcyu3xmtej7hxhxxp.streamlit.app/"
STORE_FILE = "dp_persistent_store.json"

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
            for dict_k in ("locked_picks", "opening_odds", "pre_lineup_memory", "finished_cache", "history_scores", "live_signals"):
                if isinstance(d.get(dict_k), dict):
                    MEM.setdefault(dict_k, {}).update(d[dict_k])
            for k in ("base_w", "base_t", "base_ak_w", "base_ak_t"):
                if k in d:
                    MEM[k] = safe_int(d[k], 0)
        except Exception:
            pass

def save_persistent_store():
    try:
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "users_db": MEM.get("users_db", {}),
                "used_txids": list(MEM.get("used_txids", set())),
                "patron_devs": list(MEM.get("patron_devs", set())),
                "locked_picks": MEM.get("locked_picks", {}),
                "opening_odds": MEM.get("opening_odds", {}),
                "pre_lineup_memory": MEM.get("pre_lineup_memory", {}),
                "finished_cache": MEM.get("finished_cache", {}),
                "history_scores": MEM.get("history_scores", {}),
                "live_signals": MEM.get("live_signals", {}),
                "base_w": safe_int(MEM.get("base_w"), 0),
                "base_t": safe_int(MEM.get("base_t"), 0),
                "base_ak_w": safe_int(MEM.get("base_ak_w"), 0),
                "base_ak_t": safe_int(MEM.get("base_ak_t"), 0)
            }, f, ensure_ascii=False)
    except Exception:
        pass

load_persistent_store()

def get_smart_device_uid():
    try:
        qp = dict(st.query_params)
        if qp.get("uid"):
            u_q = str(qp["uid"]).strip().upper()
            if u_q.startswith("DP-") and len(u_q) == 9:
                return u_q
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
    h_hex = hashlib.md5(f"{ua}|{ip_hint}|DeltaPulseSalt".encode("utf-8")).hexdigest().upper()[:6]
    return f"DP-{h_hex}"

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

# ==================== MODÜL 2/6: VERİ VE KADRO ÇEKME KATMANI ====================
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
        return clean
    return "4-2-3-1"

def derive_match_weather(match_title, lig_adi, raw_weather=None):
    if isinstance(raw_weather, dict) and raw_weather.get("temperature"):
        t_f = safe_int(raw_weather.get("temperature"), 62)
        t_c = int(round((t_f - 32) * 5.0 / 9.0)) if t_f > 42 else t_f
        cond = str(raw_weather.get("displayValue") or "Clear")
        return f"⛅ {t_c}°C • {cond} (Resmi Stadyum Verisi)"
    return "⛅ Stadyum Verisi Bekleniyor (Standart Zemin)"

def extract_referee_profile(g_info, match_title, lig_adi):
    offs = (g_info or {}).get("officials") or []
    ref_name = str(offs[0].get("displayName") or offs[0].get("fullName") or "").strip() if (offs and isinstance(offs[0], dict)) else ""
    hot_base = 4.3 if any(k in str(lig_adi).upper() for k in ("SERIE", "BREZİLYA", "ARJANTİN", "LA LIGA", "TÜRKİYE", "BRA.", "ITA.", "ESP.", "TUR.")) else 3.6
    if not ref_name:
        return {"name": "", "avg": hot_base, "style": "⚖️LigBaz", "disp": f"Atama Bekleniyor (Lig Baz:{hot_base})", "verified": False}
    seed = sum(ord(c) for c in ref_name)
    ref_avg = round(hot_base + ((seed % 5) - 2) * 0.25, 1)
    style = "🟥Sert" if ref_avg >= 4.6 else ("🕊️Toleranslı" if ref_avg <= 3.4 else "⚖️Dengeli")
    return {"name": ref_name, "avg": ref_avg, "style": style, "disp": f"{ref_name} ({style} • Ort:{ref_avg})", "verified": True}

def _calc_struct_player_rat(t_mom, kademe, pos_abbr, is_starter=True, sh_avg=11.0):
    base_r = 71 + int((t_mom - 50) * 0.14) + (3 if kademe == 1 else 0) + int((sh_avg - 10.5) * 0.4)
    if any(k in str(pos_abbr) for k in ("F", "ST", "W", "CAM")):
        base_r += 1
    if not is_starter:
        base_r -= (2 if kademe == 1 else 4)
    return min(90, max(65, base_r))

def _fetch_espn_team_squad_fallback(slug, team_id, t_mom, kademe, sh_avg=11.0):
    if not team_id:
        return [], []
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/teams/{team_id}/roster"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=2.5)
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

def fetch_last_match_twin(slug, t_name, data, side_idx, t_mom, kademe):
    hist_mem = MEM.setdefault("team_hist_cache", {})
    ck = f"{slug}_{t_name}_v8_dc_xg"
    if ck in hist_mem and len(hist_mem[ck].get("prev_st") or []) >= 11:
        return dict(hist_mem[ck])

    cor_avg = round(4.4 + (t_mom - 50) * 0.025, 1)
    sh_avg = round(10.5 + (t_mom - 50) * 0.06, 1)
    sot_avg = round(3.6 + (t_mom - 50) * 0.03, 1)
    xg_avg = round(sot_avg * 0.30 + max(0.0, sh_avg - sot_avg) * 0.05, 2)
    card_avg, foul_avg, rest_days = 1.9, 11.2, 6
    prev_tac, team_id = "4-2-3-1", ""
    inj_names, wing_inj, gk_inj, prev_st, prev_bn = set(), False, False, [], []

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
        evs = [e for e in (l5_obj.get("events") or []) if isinstance(e, dict)][:4]
        if evs and evs[0].get("gameDate"):
            try:
                gd_str = str(evs[0]["gameDate"]).replace("Z", "+00:00")
                last_dt = datetime.fromisoformat(gd_str).astimezone(TR_TZ)
                rest_days = max(2, min(14, (datetime.now(TR_TZ) - last_dt).days))
            except Exception:
                rest_days = 6

        c_vals, s_vals, sot_vals, xg_vals, crd_vals, fl_vals = [], [], [], [], [], []
        for e_idx, ev_item in enumerate(evs):
            last_id = str(ev_item.get("id") or ev_item.get("eventId") or "")
            if not last_id:
                continue
            try:
                r_h = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={last_id}", headers={"User-Agent": "Mozilla/5.0"}, timeout=2.5)
                if r_h.status_code == 200:
                    d_h = r_h.json()
                    for bt in ((d_h.get("boxscore") or {}).get("teams") or []):
                        bt_nm = str((bt.get("team") or {}).get("shortDisplayName") or (bt.get("team") or {}).get("displayName") or "")
                        bt_id = str((bt.get("team") or {}).get("id") or "")
                        if (team_id and bt_id == team_id) or _team_names_match(t_name, bt_nm):
                            c_v = get_stat(bt, ["wonCorners", "corners"])
                            s_v = get_stat(bt, ["totalShots", "shotsSummary"])
                            st_v = get_stat(bt, ["shotsOnTarget", "onGoal"])
                            y_v = get_stat(bt, ["yellowCards"]) + get_stat(bt, ["redCards"])
                            f_v = get_stat(bt, ["foulsCommitted"])
                            if c_v > 0 or s_v > 0:
                                c_vals.append(c_v)
                                s_vals.append(s_v)
                                sot_vals.append(st_v)
                                xg_vals.append(round(st_v * 0.30 + max(0, s_v - st_v) * 0.05, 2))
                                crd_vals.append(y_v)
                            if f_v > 0:
                                fl_vals.append(f_v)
                    if not prev_st:
                        for r_old in (d_h.get("rosters") or []):
                            rt_obj = r_old.get("team") or {}
                            rt_nm = str(rt_obj.get("shortDisplayName") or rt_obj.get("displayName") or "")
                            rt_id = str(rt_obj.get("id") or "")
                            if (team_id and rt_id == team_id) or _team_names_match(t_name, rt_nm):
                                if r_old.get("formation"):
                                    prev_tac = str(r_old.get("formation")).strip()
                                for pe in (r_old.get("roster") or []):
                                    ath = pe.get("athlete") or {}
                                    p_n = str(ath.get("shortName") or ath.get("displayName") or "Player")
                                    j_n = str(pe.get("jersey") or ath.get("jersey") or "10")
                                    pos_a = str(((pe.get("position") or ath.get("position")) or {}).get("abbreviation") or "M")
                                    is_st = bool(pe.get("starter"))
                                    p_obj = {"name": p_n, "num": j_n, "pos": pos_a, "rat": _calc_struct_player_rat(t_mom, kademe, pos_a, is_st, sh_avg)}
                                    if is_st:
                                        prev_st.append(p_obj)
                                    else:
                                        prev_bn.append(p_obj)
            except Exception:
                pass
        if c_vals: cor_avg = round(sum(c_vals) / len(c_vals), 1)
        if s_vals: sh_avg = round(sum(s_vals) / len(s_vals), 1)
        if sot_vals: sot_avg = round(sum(sot_vals) / len(sot_vals), 1)
        if xg_vals: xg_avg = round(sum(xg_vals) / len(xg_vals), 2)
        if crd_vals: card_avg = round(sum(crd_vals) / len(crd_vals), 1)
        if fl_vals: foul_avg = round(sum(fl_vals) / len(fl_vals), 1)

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
        "prev_st": prev_st[:11], "prev_bn": prev_bn[:5]
    }
    if len(prev_st) >= 11:
        hist_mem[ck] = h_base
    return dict(h_base)

def build_team_hist_metrics(h_base, cur_form, rot_cnt, starters, bench, t_mom, kademe):
    att_players = [p for p in (starters or []) if any(k in str(p.get("pos", "")) for k in ("W", "M", "F", "ST"))]
    bench_rats = [safe_int(p.get("rat"), 72) for p in (bench or [])]
    avg_att_rat = int(round(sum(safe_int(p.get("rat"), 74) for p in att_players) / len(att_players))) if att_players else (73 + int((t_mom - 50) * 0.12) + (3 if kademe == 1 else 0))
    sub_rat = max(bench_rats) if bench_rats else (avg_att_rat - (2 if kademe == 1 else 4))

    has_wing_change = bool(h_base.get("wing_inj") or rot_cnt >= 3)
    hungry_sub = bool(has_wing_change and sub_rat >= 76)
    real_wing_drop = bool(h_base.get("wing_inj") and sub_rat <= 70)
    wing_impact = 4 if hungry_sub else (-10 if real_wing_drop else (-2 if rot_cnt >= 4 else 0))

    total_missing = safe_int(h_base.get("inj_cnt"), 0) + (1 if rot_cnt >= 4 else 0)
    def_shift = (cur_form in ("5-3-2", "5-4-1", "4-5-1") and h_base.get("prev_tac") in ("4-3-3", "4-2-3-1", "3-4-3")) or (total_missing >= 3 and sub_rat <= 71)
    return {
        "cor_avg": h_base.get("cor_avg", 4.5), "sh_avg": h_base.get("sh_avg", 10.5),
        "sot_avg": h_base.get("sot_avg", 3.6), "xg_avg": h_base.get("xg_avg", 1.35),
        "card_avg": h_base.get("card_avg", 1.8), "foul_avg": h_base.get("foul_avg", 11.0),
        "rest_days": h_base.get("rest_days", 6), "gk_inj": bool(h_base.get("gk_inj", False)),
        "prev_tac": h_base.get("prev_tac", cur_form), "sub_rat": sub_rat,
        "hungry_sub": hungry_sub, "wing_drop": real_wing_drop,
        "wing_impact": wing_impact, "def_shift": def_shift
    }

def fetch_and_analyze_roster(task_tuple):
    slug, ev_id, match_title, h_name, a_name, h_mom, a_mom, odd_str, state, kademe, fav_abbr, fav_val, a_abbr = task_tuple
    cache_key = f"{ev_id}_{state}_v80_live_xi"
    if cache_key in MEM["roster_cache"]:
        cached_res = MEM["roster_cache"][cache_key]
        if cached_res.get("official") or state != "pre":
            return match_title, cached_res

    res = {"official": False, "slug": slug, "weather": derive_match_weather(match_title, slug), "ref": extract_referee_profile({}, match_title, slug), "h": {}, "a": {}}
    data = {}
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={ev_id}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3.5)
        data = r.json() if r.status_code == 200 else {}
        g_info = data.get("gameInfo") or {}
        if g_info.get("weather"):
            res["weather"] = derive_match_weather(match_title, slug, g_info.get("weather"))
        res["ref"] = extract_referee_profile(g_info, match_title, slug)
        if (g_info.get("venue") or {}).get("fullName"):
            res["venue"] = str(g_info["venue"]["fullName"])

        rosters = data.get("rosters") or []
        for idx, r_obj in enumerate(rosters[:2]):
            side_key = "h" if r_obj.get("homeAway") == "home" or idx == 0 else "a"
            t_name = h_name if side_key == "h" else a_name
            t_mom = h_mom if side_key == "h" else a_mom
            h_base = fetch_last_match_twin(slug, t_name, data, idx, t_mom, kademe)
            form_str = resolve_team_formation(t_name, r_obj.get("formation") or h_base.get("prev_tac"), t_mom, side_key == "h")
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
                prev_names = {p["name"].lower() for p in (h_base.get("prev_st") or [])}
                rot_cnt = sum(1 for p in starters if p["name"].lower() not in prev_names) if len(prev_names) >= 9 else sum(1 for p in starters if safe_int(p["num"], 10) >= 32)
                rot_cnt = min(4, rot_cnt)
            else:
                starters, bench = list(h_base.get("prev_st") or []), list(h_base.get("prev_bn") or [])
                rot_cnt = safe_int(h_base.get("inj_cnt"), 0)

            if len(starters) >= 8:
                gk_list = [p for p in starters if "G" in p["pos"]]
                rot_gk = bool(h_base.get("gk_inj")) or (any(safe_int(g["num"], 1) not in (1, 12, 13, 23, 31, 99) for g in gk_list) if gk_list else False)
                hist_info = build_team_hist_metrics(h_base, form_str, rot_cnt, starters, bench, t_mom, kademe)
                w_imp = hist_info["wing_impact"]
                base_ovr = 72 + int((t_mom - 50) * 0.14) + (3 if kademe == 1 else 0)
                sho_v = min(92, max(52, base_ovr + int((hist_info["sh_avg"] - 11.0) * 0.8) + int(w_imp * 0.4)))
                pas_v = min(91, max(54, base_ovr + 2 - int(rot_cnt * 0.5)))
                dri_v = min(90, max(52, base_ovr + int((hist_info["cor_avg"] - 4.8) * 1.2) + int(w_imp * 0.5)))
                def_v = min(90, max(50, base_ovr + (4 if hist_info["def_shift"] else 0) - (rot_cnt if hist_info["wing_drop"] else 0) - (7 if rot_gk else 0)))
                res[side_key] = {
                    "tac": form_str, "starters": starters[:11], "bench": bench[:5],
                    "rot_cnt": rot_cnt, "rot_gk": rot_gk, "hist": hist_info,
                    "ovr": int(round((sho_v + pas_v + dri_v + def_v) / 4.0)),
                    "sho": sho_v, "att": sho_v, "pas": pas_v, "dri": dri_v, "def": def_v
                }
    except Exception:
        pass

    for idx_s, (side_key, t_name, t_mom) in enumerate((("h", h_name, h_mom), ("a", a_name, a_mom))):
        if not res.get(side_key) or not res[side_key].get("starters"):
            h_base = fetch_last_match_twin(slug, t_name, data, idx_s, t_mom, kademe)
            f_str = resolve_team_formation(t_name, h_base.get("prev_tac", ""), t_mom, side_key == "h")
            b_ovr = 71 + int((t_mom - 50) * 0.14) + (3 if kademe == 1 else 0)
            sim_pos = ["GK", "LB", "CB", "CB", "RB", "CDM", "CM", "LW", "CAM", "RW", "ST"]
            sim_nums = ["1", "3", "4", "5", "2", "6", "8", "11", "10", "7", "9"]
            st_use = h_base.get("prev_st") or [{"name": f"{t_name[:3].upper()} #{sim_nums[i]}", "num": sim_nums[i], "pos": sim_pos[i], "rat": b_ovr} for i in range(11)]
            bn_use = h_base.get("prev_bn") or [{"name": f"Yedek #{i+12}", "num": str(i+12), "pos": "W", "rat": b_ovr - 2} for i in range(4)]
            r_cnt = safe_int(h_base.get("inj_cnt"), 1)
            hist_info = build_team_hist_metrics(h_base, f_str, r_cnt, st_use, bn_use, t_mom, kademe)
            res[side_key] = {
                "tac": f_str, "starters": st_use[:11], "bench": bn_use[:5], "rot_cnt": r_cnt, "rot_gk": bool(h_base.get("gk_inj")), "hist": hist_info,
                "ovr": b_ovr, "sho": b_ovr + 2, "att": b_ovr + 2, "pas": b_ovr + 1, "dri": b_ovr, "def": b_ovr - 1
            }

    if res["official"] or state != "pre":
        MEM["roster_cache"][cache_key] = res
    return match_title, res

# ==================== MODÜL 3/6: HESAPLAMA VE TAHMİN MOTORU (MODEL 4.1 BAYES-xG & MISMATCH MONTE CARLO) ====================
MODEL_VERSION = "M4.1_BAYES_MISMATCH_DC_NB"

LEAGUE_GOAL_AVG = {
    "ger.1": 3.05, "ned.1": 3.00, "eng.league_cup": 2.82, "sco.1": 2.75,
    "eng.1": 2.78, "tur.1": 2.58, "ita.1": 2.55, "fra.1": 2.55,
    "por.1": 2.50, "mex.1": 2.58, "esp.1": 2.46, "eng.2": 2.45,
    "bra.1": 2.38, "ita.2": 2.30, "esp.2": 2.18, "arg.1": 2.12
}

LEAGUE_DC_RHO = {
    "arg.1": -0.15, "esp.2": -0.14, "ita.2": -0.14, "bra.1": -0.12,
    "esp.1": -0.11, "por.1": -0.10, "fra.1": -0.09, "ita.1": -0.09,
    "tur.1": -0.09, "eng.2": -0.09, "eng.1": -0.08, "sco.1": -0.08,
    "ger.1": -0.06, "ned.1": -0.06
}

# LİG KARAKTERİSTİK DNA HARİTASI (Şut->Korner Çarpanı & Yasaklı Market Vetosu)
LEAGUE_DNA_PROFILES = {
    "arg.1": {"cor_mult": 1.06, "disp_r": 8.0, "ban_team_o15_if_lock": True, "lock_thresh": 13.2},
    "bra.1": {"cor_mult": 1.04, "disp_r": 9.0, "ban_team_o15_if_lock": False, "lock_thresh": 14.0},
    "esp.2": {"cor_mult": 1.03, "disp_r": 9.5, "ban_team_o15_if_lock": True, "lock_thresh": 13.5},
    "ita.2": {"cor_mult": 1.03, "disp_r": 9.5, "ban_team_o15_if_lock": True, "lock_thresh": 13.5},
    "esp.1": {"cor_mult": 1.02, "disp_r": 11.0, "ban_team_o15_if_lock": False, "lock_thresh": 13.8}
}

def _amer_to_decimal(odd_val):
    v = safe_float(odd_val, 0.0)
    if v == 0:
        return 0.0
    return (1.0 + (100.0 / abs(v))) if v < 0 else (1.0 + (v / 100.0))

def compute_true_3way_no_vig_or_proxy(ml_h, ml_d, ml_a, fav_val, fav_is_home):
    dec_h, dec_d, dec_a = _amer_to_decimal(ml_h), _amer_to_decimal(ml_d), _amer_to_decimal(ml_a)
    if dec_h > 1.01 and dec_d > 1.01 and dec_a > 1.01:
        qh, qd, qa = 1.0 / dec_h, 1.0 / dec_d, 1.0 / dec_a
        q_sum = qh + qd + qa
        ph, pd, pa = qh / q_sum, qd / q_sum, qa / q_sum
        return {
            "p_mkt_h": ph, "p_mkt_d": pd, "p_mkt_a": pa,
            "p_mkt_fav": ph if fav_is_home else pa,
            "is_true_novig": True
        }
    v = safe_float(fav_val, 0.0)
    raw_q = ((-v) / ((-v) + 100.0)) if v < 0 else ((100.0 / (v + 100.0)) if v > 0 else 0.50)
    p_proxy_fav = min(0.96, max(0.04, raw_q / 1.052))
    rem = max(0.04, 1.0 - p_proxy_fav)
    p_proxy_d = min(0.34, rem * 0.48)
    p_proxy_dog = max(0.02, rem - p_proxy_d)
    return {
        "p_mkt_h": p_proxy_fav if fav_is_home else p_proxy_dog,
        "p_mkt_d": p_proxy_d,
        "p_mkt_a": p_proxy_dog if fav_is_home else p_proxy_fav,
        "p_mkt_fav": p_proxy_fav,
        "is_true_novig": False
    }

def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(k * math.log(lam) - lam - math.lgamma(k + 1))

def neg_binom_pmf(k, mu, disp_r):
    if mu <= 0:
        return 1.0 if k == 0 else 0.0
    p = disp_r / (disp_r + mu)
    log_p = (
        math.lgamma(k + disp_r)
        - math.lgamma(disp_r)
        - math.lgamma(k + 1)
        + disp_r * math.log(max(1e-9, p))
        + k * math.log(max(1e-9, 1.0 - p))
    )
    return math.exp(log_p)

def neg_binom_prob_over(line_val, mu, disp_r=14.0):
    k_max = int(math.floor(line_val))
    cdf = sum(neg_binom_pmf(k, mu, disp_r) for k in range(k_max + 1))
    return min(0.995, max(0.005, 1.0 - cdf))

def dixon_coles_tau(gh, ga, lam_h, lam_a, rho=-0.09):
    if gh == 0 and ga == 0:
        return max(0.60, 1.0 - lam_h * lam_a * rho)
    if gh == 0 and ga == 1:
        return max(0.60, 1.0 + lam_h * rho)
    if gh == 1 and ga == 0:
        return max(0.60, 1.0 + lam_a * rho)
    if gh == 1 and ga == 1:
        return max(0.60, 1.0 - rho)
    return 1.0

def _classify_pick_market_type(pick_str):
    pk = str(pick_str or "")
    if "Korner" in pk:
        return "COR"
    if "Kart" in pk:
        return "CARD"
    if "Karşılıklı Gol" in pk:
        return "BTTS"
    if "Kazanır" in pk:
        return "WIN"
    if "Takım Golü 1.5 Üst" in pk:
        return "TEAM_O15"
    if "2.5 Gol Üst" in pk:
        return "O25"
    if "Maç 1.5 Gol Üst" in pk:
        return "O15"
    if "3.5 Alt" in pk:
        return "U35"
    return "DC_O15"

def _calibrate_decision_score_by_market_and_band(raw_prob_pct, mkt_type="WIN"):
    p = min(99.0, max(1.0, float(raw_prob_pct))) / 100.0
    fin_map = MEM.get("finished_cache", {})
    same_mkt = []
    for m in fin_map.values():
        if not isinstance(m, dict) or "pick" not in m or "won" not in m:
            continue
        if _classify_pick_market_type(m.get("pick")) == mkt_type:
            same_mkt.append(m)

    if len(same_mkt) < 15:
        calib_p = 0.52 + (p - 0.50) * 0.88
        return int(round(min(91.0, max(45.0, calib_p * 100.0))))

    band_low, band_high = max(0.40, p - 0.10), min(0.98, p + 0.10)
    in_band = [x for x in same_mkt if band_low <= (safe_float(x.get("conf"), 70.0) / 100.0) <= band_high]
    pool = in_band if len(in_band) >= 8 else same_mkt[-25:]
    emp_hit = sum(1.0 for x in pool if x.get("won")) / len(pool)
    avg_pred = sum(safe_float(x.get("conf"), 70.0) / 100.0 for x in pool) / len(pool)
    adj_p = p + max(-0.05, min(0.04, (emp_hit - avg_pred) * 0.25))
    return int(round(min(91.0, max(45.0, adj_p * 100.0))))

def _compute_mismatch_athleticism(info_dict, t_mom):
    """
    Oyuncu kadrosundan ve şut/dripling/savunma verilerinden
    Hücum Atletizm (Pace + Dribbling) ve Savunma Mobilite (Speed + Agility) çıkarır.
    """
    sho = safe_float(info_dict.get("sho"), 71.0)
    dri = safe_float(info_dict.get("dri"), 70.0)
    pas = safe_float(info_dict.get("pas"), 70.0)
    df_v = safe_float(info_dict.get("def"), 68.0)
    hist = info_dict.get("hist") or {}
    w_imp = safe_float(hist.get("wing_impact"), 0.0)
    def_shift = bool(hist.get("def_shift", False))
    rot_gk = bool(info_dict.get("rot_gk", False))

    att_ath = round((sho * 0.45) + (dri * 0.45) + (pas * 0.10) + (w_imp * 0.35), 1)
    def_mob = round((df_v * 0.55) + (dri * 0.25) + (pas * 0.20) - (3.5 if def_shift else 0.0) - (4.0 if rot_gk else 0.0), 1)
    return att_ath, def_mob

def compute_model4_poisson_and_scores(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, fav_abbr, fav_val, ou_val, r_data, lig_adi="", disp_odd=""):
    if not isinstance(r_data, dict) or not r_data.get("h") or not r_data.get("a"):
        return {"status": "HESAPLANAMADI"}

    slug = str(r_data.get("slug") or "eng.1")
    h_info, a_info = r_data.get("h") or {}, r_data.get("a") or {}
    h_hist, a_hist = h_info.get("hist") or {}, a_info.get("hist") or {}
    h_def, a_def = safe_int(h_info.get("def"), 68), safe_int(a_info.get("def"), 68)
    h_sho, a_sho = safe_int(h_info.get("sho"), 71), safe_int(a_info.get("sho"), 71)
    h_pas, a_pas = safe_int(h_info.get("pas"), 70), safe_int(a_info.get("pas"), 70)
    h_tac, a_tac = str(h_info.get("tac") or "4-2-3-1"), str(a_info.get("tac") or "4-2-3-1")

    # AKADEMİK BRADLEY-TERRY & BAYES-xG MISMATCH (Δ) HESAPLAMASI
    h_att_ath, h_def_mob = _compute_mismatch_athleticism(h_info, h_mom)
    a_att_ath, a_def_mob = _compute_mismatch_athleticism(a_info, a_mom)
    delta_h = round(h_att_ath - a_def_mob, 1)
    delta_a = round(a_att_ath - h_def_mob, 1)
    bt_prob_h = int(round((1.0 / (1.0 + (10.0 ** (-delta_h / 40.0)))) * 100.0))

    lig_base_g = LEAGUE_GOAL_AVG.get(slug, 2.52)
    half_lig = max(0.88, lig_base_g / 2.0)
    rho_lig = LEAGUE_DC_RHO.get(slug, -0.09)
    lig_dna = LEAGUE_DNA_PROFILES.get(slug, {"cor_mult": 1.0, "disp_r": 12.0, "ban_team_o15_if_lock": False, "lock_thresh": 13.8})

    h_xg_hist = min(1.85, max(0.65, safe_float(h_hist.get("xg_avg"), 1.30) * 0.74))
    a_xg_hist = min(1.70, max(0.55, safe_float(a_hist.get("xg_avg"), 1.15) * 0.74))
    h_rest = safe_int(h_hist.get("rest_days"), 6)
    a_rest = safe_int(a_hist.get("rest_days"), 6)
    h_rest_mod = -0.07 if h_rest <= 3 else (-0.02 if h_rest == 4 else 0.0)
    a_rest_mod = -0.07 if a_rest <= 3 else (-0.02 if a_rest == 4 else 0.0)

    mom_diff = (h_mom - a_mom) / 100.0
    # Bayes-xG üstel çarpanı (beta = 0.016 * delta)
    qual_diff_h = (delta_h * 0.016) + (mom_diff * 0.32)
    qual_diff_a = (delta_a * 0.016) - (mom_diff * 0.32)

    gk_pen_a = 0.12 if a_info.get("rot_gk") else 0.0
    gk_pen_h = 0.12 if h_info.get("rot_gk") else 0.0
    bus_pen_a = -0.08 if a_tac in ("5-4-1", "5-3-2") else 0.0
    bus_pen_h = -0.08 if h_tac in ("5-4-1", "5-3-2") else 0.0

    # Baskı altında şut (under_pressure) cezası: Sert ligde hız farkı (Delta) yoksa xG kırpılır (Defensa maçı koruması!)
    is_sert_lig = (rho_lig <= -0.12)
    under_pressure_h = -0.11 if (is_sert_lig and delta_h < 3.5 and a_def >= 70) else 0.0
    under_pressure_a = -0.11 if (is_sert_lig and delta_a < 3.5 and h_def >= 70) else 0.0

    odd_says_home = (str(fav_abbr).upper() == str(h_abbr).upper())
    heavy_odd_boost_h = 0.22 if (fav_val <= -350 and odd_says_home) else (-0.18 if (fav_val <= -350 and not odd_says_home) else 0.0)
    heavy_odd_boost_a = 0.22 if (fav_val <= -350 and not odd_says_home) else (-0.18 if (fav_val <= -350 and odd_says_home) else 0.0)

    raw_lam_h = (half_lig * 0.52 + h_xg_hist * 0.48) * math.exp(0.09 + qual_diff_h + gk_pen_a + bus_pen_a + h_rest_mod + heavy_odd_boost_h + under_pressure_h)
    raw_lam_a = (half_lig * 0.52 + a_xg_hist * 0.48) * math.exp(-0.09 + qual_diff_a + gk_pen_h + bus_pen_h + a_rest_mod + heavy_odd_boost_a + under_pressure_a)

    raw_tot = raw_lam_h + raw_lam_a
    target_struct_tot = max(1.72, min(3.15, lig_base_g * 0.62 + raw_tot * 0.38))
    scale_f = target_struct_tot / max(0.5, raw_tot)
    lam_h_struct = max(0.38, min(2.55, raw_lam_h * scale_f))
    lam_a_struct = max(0.28, min(2.25, raw_lam_a * scale_f))

    mat = {}
    tot_norm = 0.0
    for gh in range(13):
        ph = poisson_pmf(gh, lam_h_struct)
        for ga in range(13):
            val = ph * poisson_pmf(ga, lam_a_struct) * dixon_coles_tau(gh, ga, lam_h_struct, lam_a_struct, rho=rho_lig)
            mat[(gh, ga)] = val
            tot_norm += val

    p_home, p_draw, p_away = 0.0, 0.0, 0.0
    best_gh, best_ga, best_p = 1, 0, 0.0
    for (gh, ga), raw_p in mat.items():
        p_ij = raw_p / max(1e-9, tot_norm)
        if p_ij > best_p:
            best_p, best_gh, best_ga = p_ij, gh, ga
        if gh > ga:
            p_home += p_ij
        elif gh == ga:
            p_draw += p_ij
        else:
            p_away += p_ij

    # DIXON-COLES 1-1 KİLİTLENME RİSKİ (%)
    p_1_1_lock = round((mat.get((1, 1), 0.0) / max(1e-9, tot_norm)) * 100.0, 1)

    simplex_sum = max(1e-9, p_home + p_draw + p_away)
    p_home, p_draw, p_away = p_home / simplex_sum, p_draw / simplex_sum, p_away / simplex_sum

    whale_against_odd = ("⚠️Δ" in str(disp_odd))
    if fav_val <= -135 and not whale_against_odd:
        fav_is_home = odd_says_home
    elif abs(p_home - p_away) >= 0.04:
        fav_is_home = (p_home >= p_away)
    else:
        fav_is_home = ((h_mom + 6) >= a_mom)

    fav_delta = delta_h if fav_is_home else delta_a
    fav_sho = h_sho if fav_is_home else a_sho
    opp_def = a_def if fav_is_home else h_def
    opp_info = a_info if fav_is_home else h_info
    opp_tac = a_tac if fav_is_home else h_tac

    gk_drop = 1.35 if opp_info.get("rot_gk") else 0.0
    xi_churn = min(1.0, safe_float(opp_info.get("rot_cnt"), 0.0) / 5.0)
    z_weak = -0.45 + 0.13 * (60.0 - opp_def) + 0.90 * gk_drop + 0.70 * xi_churn + 0.06 * fav_delta
    d_weak = int(round(100.0 / (1.0 + math.exp(-max(-6.0, min(6.0, z_weak))))))

    five_back = 1.0 if opp_tac in ("3-5-2", "5-3-2", "5-4-1", "3-5-1-1") else 0.0
    low_line = 1.0 if ("SERIE B" in str(lig_adi).upper() or "LA LIGA 2" in str(lig_adi).upper() or "ARJANTİN" in str(lig_adi).upper()) else 0.0
    z_bus = -1.0 + 1.65 * five_back + 0.85 * low_line + 0.04 * (opp_def - 68.0) - (0.04 * fav_delta)
    bus_score = int(round(100.0 / (1.0 + math.exp(-max(-6.0, min(6.0, z_bus))))))

    p_shield, p_team, p_over15, p_over25, p_over35, p_btts = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    p_fav_o15, p_fav_o25, p_dc_o15 = 0.0, 0.0, 0.0

    for (gh, ga), raw_p in mat.items():
        p_ij = raw_p / max(1e-9, tot_norm)
        tot_g = gh + ga
        fav_g = gh if fav_is_home else ga
        fav_win = (gh > ga) if fav_is_home else (ga > gh)
        fav_unbeaten = (gh >= ga) if fav_is_home else (ga >= gh)

        if fav_win and tot_g >= 2:
            p_fav_o15 += p_ij
        if fav_win and tot_g >= 3:
            p_fav_o25 += p_ij
        if fav_unbeaten and tot_g >= 2:
            p_dc_o15 += p_ij
        if fav_unbeaten and tot_g <= 3:
            p_shield += p_ij
        if fav_g >= 2:
            p_team += p_ij
        if tot_g >= 2:
            p_over15 += p_ij
        if tot_g >= 3:
            p_over25 += p_ij
        if tot_g >= 4:
            p_over35 += p_ij
        if gh >= 1 and ga >= 1:
            p_btts += p_ij

    p_struct_fav = p_home if fav_is_home else p_away
    p_struct_dc = (p_home + p_draw) if fav_is_home else (p_away + p_draw)

    odds_3w = r_data.get("odds_3way") or {}
    mkt_info = compute_true_3way_no_vig_or_proxy(
        odds_3w.get("ml_h", 0), odds_3w.get("ml_d", 0), odds_3w.get("ml_a", 0),
        fav_val, fav_is_home
    )
    p_mkt_fav_prob = mkt_info["p_mkt_fav"] if (fav_val < 0 or mkt_info["is_true_novig"]) else p_struct_fav
    is_true_novig = mkt_info["is_true_novig"]

    p_aug_fav = (0.60 * p_struct_fav) + (0.40 * p_mkt_fav_prob)
    mkt_tot_ref = 2.95 if ou_val >= 3.5 else (1.92 if ou_val <= 1.5 else 2.42)

    sc_prob = int(round(best_p * 100.0))
    return {
        "status": "OK",
        "fav_is_home": fav_is_home,
        "delta_h": delta_h, "delta_a": delta_a, "fav_delta": fav_delta, "bt_prob_h": bt_prob_h,
        "p_1_1_lock": p_1_1_lock, "lig_dna": lig_dna,
        "p_home": round(p_home * 100, 1), "p_draw": round(p_draw * 100, 1), "p_away": round(p_away * 100, 1),
        "p_struct_fav": round(p_struct_fav * 100, 1), "p_struct_dc": round(p_struct_dc * 100, 1),
        "market_probability_proxy": round(p_mkt_fav_prob * 100, 1),
        "is_true_novig": is_true_novig,
        "p_aug_fav": round(p_aug_fav * 100, 1),
        "p_fav": round(p_mkt_fav_prob * 100, 1),
        "p_fav_o15": int(round(p_fav_o15 * 100)), "p_fav_o25": int(round(p_fav_o25 * 100)),
        "p_dc_o15": int(round(p_dc_o15 * 100)),
        "fav_val": fav_val, "mat": mat, "tot_norm": tot_norm,
        "d_weak": d_weak, "bus_score": bus_score, "h_rest": h_rest, "a_rest": a_rest,
        "h_sho": h_sho, "a_sho": a_sho, "h_def": h_def, "a_def": a_def,
        "p_shield": int(round(p_shield * 100)), "p_team": int(round(p_team * 100)),
        "p_over15": int(round(p_over15 * 100)), "p_over25": int(round(p_over25 * 100)),
        "p_over35": int(round(p_over35 * 100)), "p_btts": int(round(p_btts * 100)),
        "lam_h_struct": round(lam_h_struct, 2), "lam_a_struct": round(lam_a_struct, 2),
        "lam_h": round(lam_h_struct, 2), "lam_a": round(lam_a_struct, 2),
        "mkt_tot_ref": mkt_tot_ref,
        "est_score": f"{best_gh}-{best_ga}", "est_score_p": sc_prob
    }

def compute_friction_physics(h_name, a_name, h_tac, a_tac, h_mom, a_mom, fav_val, ou_val, kademe, r_data, lig_adi="", is_home_fav=True):
    r_d = r_data or {}
    slug = str(r_d.get("slug") or "eng.1")
    lig_dna = LEAGUE_DNA_PROFILES.get(slug, {"cor_mult": 1.0, "disp_r": 12.0})
    h_d, a_d = r_d.get("h") or {}, r_d.get("a") or {}
    h_hist, a_hist = h_d.get("hist") or {}, a_d.get("hist") or {}
    ref_d = r_d.get("ref") or {}
    wx_str = str(r_d.get("weather") or "")

    h_cor_avg = safe_float(h_hist.get("cor_avg") or h_d.get("cor_avg"), 5.0)
    a_cor_avg = safe_float(a_hist.get("cor_avg") or a_d.get("cor_avg"), 4.5)
    real_cor_sum = round(h_cor_avg + a_cor_avg, 1)
    sh_sum = safe_float(h_hist.get("sh_avg"), 11.0) + safe_float(a_hist.get("sh_avg"), 10.5)

    h_att, h_mob = _compute_mismatch_athleticism(h_d, h_mom)
    a_att, a_mob = _compute_mismatch_athleticism(a_d, a_mom)
    fav_delta = (h_att - a_mob) if is_home_fav else (a_att - h_mob)

    h_dri, a_dri = safe_int(h_d.get("dri"), 70), safe_int(a_d.get("dri"), 70)
    wing_asym = bool(
        (max(h_dri, a_dri) >= 75 and real_cor_sum >= 10.0)
        or (("3-4-" in str(h_tac) or "3-5-" in str(h_tac) or "3-4-" in str(a_tac) or "3-5-" in str(a_tac)) and real_cor_sum >= 9.6)
    )

    h_sub_rat = safe_int(h_hist.get("sub_rat"), 0) if h_hist.get("hungry_sub") else 0
    a_sub_rat = safe_int(a_hist.get("sub_rat"), 0) if a_hist.get("hungry_sub") else 0
    hungry_pts = max(h_sub_rat, a_sub_rat)

    rot_pen = safe_int(h_hist.get("wing_impact"), 0) + safe_int(a_hist.get("wing_impact"), 0)
    inj_wing = bool(h_hist.get("wing_drop") or a_hist.get("wing_drop"))
    inj_def = bool(h_hist.get("def_shift") or a_hist.get("def_shift") or h_d.get("rot_gk") or a_d.get("rot_gk"))

    mom_gap = abs(safe_int(h_mom, 50) - safe_int(a_mom, 50))
    abs_fav = abs(safe_int(fav_val, -130)) if fav_val < 0 else 100
    blowout_prob = 20
    if (fav_val <= -200) or (mom_gap >= 24 and fav_val <= -145) or (ou_val >= 3.5 and fav_val <= -170):
        blowout_prob = min(88, 52 + int(mom_gap * 0.6) + int(max(0, abs_fav - 150) * 0.12))
    is_blowout = (blowout_prob >= 58)

    # BLOKLANAN ŞUT -> KORNER PATLAMASI ÇARPANI (Şut yüksek ama hız farkı düşükse savunma kornere çeler!)
    blocked_shot_cor_boost = 1.09 if (sh_sum >= 22.5 and fav_delta < 4.5 and real_cor_sum >= 9.2) else 1.0
    wx_mult = 1.05 if "Yağışlı" in wx_str else 1.0
    wing_mult = 1.06 if (wing_asym and not inj_wing) else (0.90 if inj_wing else 1.0)
    cor_mu = max(5.5, min(15.5, real_cor_sum * 0.96 * wing_mult * wx_mult * blocked_shot_cor_boost * safe_float(lig_dna.get("cor_mult"), 1.0)))

    is_high_cor_lig = any(k in str(lig_adi).upper() for k in ("PREMIER", "İSKOÇYA", "EFL"))
    cor_line_num = 9.5 if is_high_cor_lig else 8.5
    disp_r_use = 7.5 if blocked_shot_cor_boost > 1.0 else safe_float(lig_dna.get("disp_r"), 12.0)
    cor_prob_pct = int(round(neg_binom_prob_over(cor_line_num, cor_mu, disp_r=disp_r_use) * 100.0))

    ref_avg = safe_float(ref_d.get("avg"), 4.0)
    hist_cards = safe_float(h_hist.get("card_avg"), 1.8) + safe_float(a_hist.get("card_avg"), 1.8)
    hist_fouls = safe_float(h_hist.get("foul_avg"), 11.0) + safe_float(a_hist.get("foul_avg"), 11.0)
    is_hot_lig = any(k in str(lig_adi).upper() for k in ("SERIE B", "LA LIGA 2", "BREZİLYA", "ARJANTİN", "SÜPER LİG"))
    card_line_num = 4.5 if is_hot_lig else 3.5

    foul_adj = max(-0.4, min(0.6, (hist_fouls - 22.0) * 0.05))
    card_mu = max(1.8, min(7.8, (ref_avg * 0.55) + (hist_cards * 0.45) + foul_adj + (0.35 if is_hot_lig else 0.0) + (0.25 if mom_gap <= 14 else 0.0) - (0.65 if is_blowout else 0.0)))
    card_prob_pct = int(round(neg_binom_prob_over(card_line_num, card_mu, disp_r=10.0) * 100.0))

    est_cor_cnt = max(5, min(16, int(round(cor_mu))))
    est_card_cnt = max(2, min(8, int(round(card_mu))))

    tags = [f"📊Son4Kor:{real_cor_sum}", f"⚡ΔHız:{fav_delta:+.1f}"]
    if blocked_shot_cor_boost > 1.0:
        tags.append("🧱BlokŞut->Korner")
    if hungry_pts >= 75:
        tags.append(f"🔥AçYedek({hungry_pts}p)")
    if is_blowout:
        tags.append(f"💥ErkenKopar(%{blowout_prob})")
    if wing_asym and not inj_wing:
        tags.append("📐KanatKorner")
    if inj_wing:
        tags.append("🏥KanatKaybı")
    if inj_def:
        tags.append("🛡️SakatKapanma")
    if rot_pen < 0:
        tags.append(f"🧬HafifRotasyon({rot_pen}p)")

    return {
        "cor_score": cor_prob_pct, "card_score": card_prob_pct, "cor_p": cor_prob_pct, "card_p": card_prob_pct,
        "real_cor_sum": real_cor_sum, "cor_lambda": round(cor_mu, 2), "card_lambda": round(card_mu, 2),
        "est_cor_cnt": est_cor_cnt, "est_card_cnt": est_card_cnt,
        "wing_asym": wing_asym, "is_blowout": is_blowout,
        "blowout_prob": blowout_prob, "hungry_pts": hungry_pts, "rot_pen": rot_pen,
        "inj_wing": inj_wing, "inj_def": inj_def, "tags_str": " ".join(tags)
    }

def _compute_pick_specific_value(pick, conf, m4, ou_val):
    p_mkt_fav = safe_float(m4.get("market_probability_proxy"), 52.0) / 100.0
    is_true_nv = bool(m4.get("is_true_novig", False))
    pk = str(pick or "")
    has_direct_odds = False

    if "Kazanır" in pk:
        p_struct = safe_float(m4.get("p_fav_o25" if "2.5" in pk else "p_fav_o15"), conf) / 100.0
        p_mkt = max(0.35, p_mkt_fav * (0.76 if "2.5" in pk else 0.86))
        has_direct_odds = is_true_nv
    elif "Takım Golü 1.5 Üst" in pk:
        p_struct = safe_float(m4.get("p_team"), conf) / 100.0
        p_mkt = max(0.38, p_mkt_fav * 0.82)
    elif "2.5 Gol Üst" in pk:
        p_struct = safe_float(m4.get("p_over25"), conf) / 100.0
        p_mkt = 0.56 if ou_val >= 3.0 else (0.42 if ou_val <= 2.0 else 0.49)
    elif "Maç 1.5 Gol Üst" in pk:
        p_struct = safe_float(m4.get("p_over15"), conf) / 100.0
        p_mkt = 0.72 if ou_val >= 2.5 else 0.64
    elif "Karşılıklı Gol" in pk:
        p_struct = safe_float(m4.get("p_btts"), conf) / 100.0
        p_mkt = 0.54 if ou_val >= 3.0 else 0.50
    else:
        p_struct = conf / 100.0
        p_mkt = 0.525

    edge = round((p_struct - p_mkt) * 100.0, 1)
    if not has_direct_odds:
        val_tag = "🧪PROXY_VALUE" if edge >= 5.0 else "⚪PROXY_MODEL"
    else:
        val_tag = "💎VALUE" if edge >= 5.5 else ("✅MARGINAL" if edge >= 2.0 else "⚪FAIR")
    return edge, val_tag

def _build_patron_sim_summary(m4, pick, is_home_fav, conf=72, ou_val=2.5):
    mat = m4.get("mat") or {}
    tot_norm = max(1e-9, safe_float(m4.get("tot_norm"), 1.0))
    est_sc = str(m4.get("est_score") or "1-1")
    sc_p = safe_int(m4.get("est_score_p"), 14)
    lam_h, lam_a = safe_float(m4.get("lam_h_struct"), 1.35), safe_float(m4.get("lam_a_struct"), 1.05)
    p_1_1_lock = safe_float(m4.get("p_1_1_lock"), 11.0)
    fav_delta = safe_float(m4.get("fav_delta"), 0.0)

    if mat:
        best_match_p = -1.0
        for (gh, ga), raw_p in mat.items():
            tot_g = gh + ga
            cond_ok = True
            if "Kazanır & 2.5 Gol Üst" in str(pick):
                cond_ok = (tot_g >= 3 and ((gh > ga) if is_home_fav else (ga > gh)))
            elif "Kazanır & 1.5 Gol Üst" in str(pick):
                cond_ok = (tot_g >= 2 and ((gh > ga) if is_home_fav else (ga > gh)))
            elif "Takım Golü 1.5 Üst" in str(pick):
                cond_ok = ((gh >= 2) if is_home_fav else (ga >= 2))
            elif "Karşılıklı Gol Var" in str(pick):
                cond_ok = (gh >= 1 and ga >= 1)
            elif "2.5 Gol Üst" in str(pick):
                cond_ok = (tot_g >= 3)
            elif "Maç 1.5 Gol Üst" in str(pick):
                cond_ok = (tot_g >= 2)
            if cond_ok and raw_p > best_match_p:
                best_match_p = raw_p
                est_sc = f"{gh}-{ga}"
                sc_p = int(round((raw_p / tot_norm) * 100.0))

    fr = m4.get("friction") or {}
    c_cnt = safe_int(fr.get("est_cor_cnt"), 10)
    c_p = safe_int(m4.get("cor_p"), 62)
    k_cnt = safe_int(fr.get("est_card_cnt"), 4)
    k_p = safe_int(m4.get("card_p"), 58)
    p1, px, p2 = safe_float(m4.get("p_home"), 45.0), safe_float(m4.get("p_draw"), 27.0), safe_float(m4.get("p_away"), 28.0)
    edge_v, val_t = _compute_pick_specific_value(pick, conf, m4, ou_val)
    lock_warn_ui = f" &nbsp;|&nbsp; <span style='color:#ff7b72;font-weight:800;'>⚠️1-1 Kilit:%{p_1_1_lock:.0f}</span>" if p_1_1_lock >= 13.2 else ""
    lock_warn_mini = f"|⚠️1-1:%{p_1_1_lock:.0f}" if p_1_1_lock >= 13.2 else ""
    return {
        "ui": f"👑 <b>Model 4.1 Bayes-MC:</b> 📊 <b>1X2:</b> <code>1:%{p1:.0f}|X:%{px:.0f}|2:%{p2:.0f}</code> &nbsp;|&nbsp; ⚡<b>ΔHız:</b> <code>{fav_delta:+.1f}</code> &nbsp;|&nbsp; ⚽ <b>Sim:</b> <span style='color:#56d364;font-weight:800;'>{est_sc} (%{sc_p} • λ:{lam_h}-{lam_a})</span>{lock_warn_ui} &nbsp;|&nbsp; 🚩 <b>NB Korner:</b> <span style='color:#ffd33d;font-weight:800;'>{c_cnt} (%{c_p})</span> &nbsp;|&nbsp; 🟨 <b>Kart:</b> <span style='color:#ff7b72;font-weight:800;'>{k_cnt} (%{k_p})</span> &nbsp;|&nbsp; {val_t} (Δ:{edge_v:+.1f}%)",
        "mini": f"[👑Sim:{est_sc}(%{sc_p}){lock_warn_mini}|Δ:{fav_delta:+.1f}|λ:{lam_h}-{lam_a}|Kor:{c_cnt}(%{c_p})|{val_t}]"
    }

def _select_best_autonomous_market(h_name, a_name, is_home_fav, fav_team, dc_tag, h_mom, a_mom, disp_odd, fav_val, ou_val, m4, fr, cor_line, card_line):
    lam_h = safe_float(m4.get("lam_h_struct"), 1.35)
    lam_a = safe_float(m4.get("lam_a_struct"), 1.05)
    lam_tot = lam_h + lam_a
    fav_lam = lam_h if is_home_fav else lam_a
    opp_lam = lam_a if is_home_fav else lam_h

    fav_delta = safe_float(m4.get("fav_delta"), 0.0)
    p_1_1_lock = safe_float(m4.get("p_1_1_lock"), 11.0)
    lig_dna = m4.get("lig_dna") or {}
    lock_thresh = safe_float(lig_dna.get("lock_thresh"), 13.8)
    ban_team_lock = bool(lig_dna.get("ban_team_o15_if_lock", False))

    p_o15 = safe_int(m4.get("p_over15"), 72)
    p_o25 = safe_int(m4.get("p_over25"), 48)
    p_o35 = safe_int(m4.get("p_over35"), 18)
    p_btts = safe_int(m4.get("p_btts"), 50)
    p_team = safe_int(m4.get("p_team"), 46)
    p_fav_o15 = safe_int(m4.get("p_fav_o15"), 45)
    p_struct_fav = safe_float(m4.get("p_struct_fav"), 52.0)
    p_aug_fav = safe_float(m4.get("p_aug_fav"), 52.0)

    d_wk = safe_int(m4.get("d_weak"), 18)
    bus_sc = safe_int(m4.get("bus_score"), 30)
    h_sho = safe_int(m4.get("h_sho"), 71)
    a_sho = safe_int(m4.get("a_sho"), 71)
    h_def = safe_int(m4.get("h_def"), 68)
    a_def = safe_int(m4.get("a_def"), 68)

    cor_prob = safe_int(fr.get("cor_p"), 55)
    card_prob = safe_int(fr.get("card_p"), 55)
    real_cor = safe_float(fr.get("real_cor_sum"), 9.2)
    inj_wing = bool(fr.get("inj_wing", False))
    is_blowout = bool(fr.get("is_blowout", False))
    blow_p = safe_int(fr.get("blowout_prob"), 40)

    whale_against_fav = ("⚠️Δ" in str(disp_odd))
    whale_for_fav = ("🔥Δ" in str(disp_odd))
    mom_gap = abs(h_mom - a_mom)

    # 1-1 KİLİTLENME VE SAVUNMA DUVARI VETOSU (Defensa - Independiente Koruması!)
    # Eğer 1-1 riski yüksekse veya rakip de güçlü hücum edip hız farkı (fav_delta) düşükse, Takım 1.5 Üst VETO edilir!
    team_o15_vetoed = bool(
        whale_against_fav
        or (p_1_1_lock >= lock_thresh)
        or (ban_team_lock and fav_delta < 4.5)
        or (opp_lam >= 1.05 and fav_delta < 4.0)
    )

    candidates = []

    # 1. ADAY: NEGATİF BİNOM KORNER ÜST (Bloklanan Şut + 1-1 Kilitlenme Limanı)
    if (not inj_wing or real_cor >= 11.2) and real_cor >= 9.4:
        u_cor = cor_prob
        if real_cor >= 11.0:
            u_cor += 6
        if team_o15_vetoed and real_cor >= 9.6:
            u_cor += 8  # Takım golü riskliyse şutlar kornere gider!
        if whale_against_fav and real_cor >= 9.6:
            u_cor += 7
        if bus_sc >= 55 and real_cor >= 10.0:
            u_cor += 4
        if cor_prob >= 63 or (team_o15_vetoed and cor_prob >= 58):
            candidates.append((u_cor, f"🚩 {cor_line}", max(cor_prob, min(89, u_cor))))

    # 2. ADAY: FAVORİ KAZANIR & 1.5 GOL ÜST (Sadece Hız/Kalite Farkı Varsa ve 1-1 Kilitlenme Yoksa!)
    if not whale_against_fav and not (p_1_1_lock >= 14.2 and fav_delta < 3.5) and (fav_val <= -135 or p_struct_fav >= 48.0):
        aug_win_p = int(round(0.50 * p_fav_o15 + 0.50 * (p_aug_fav * 0.92)))
        u_win = max(aug_win_p, int(round(p_aug_fav * 0.90 + blow_p * 0.14))) + (4 if is_blowout else 0) + (3 if whale_for_fav else 0) + (3 if fav_delta >= 5.0 else 0)
        win_label = f"{fav_team} Kazanır & 1.5 Gol Üst (Handikap Adayı)" if is_blowout else f"{fav_team} Kazanır & 1.5 Gol Üst"
        candidates.append((u_win, win_label, min(86, max(64, u_win))))

    # 3. ADAY: FAVORİ TAKIM GOLÜ 1.5 ÜST (Sadece net favorilerde veya rakip savunma gerçekten zayıfsa onaylanır!)
    opp_def_val = a_def if is_home_fav else h_def
    if not team_o15_vetoed and (fav_lam >= 1.58 or p_team >= 50) and fav_delta >= 4.5 and (fav_val <= -115 or opp_def_val <= 69):
        u_team = max(p_team + 9, int(round(fav_lam * 37.5))) + (4 if d_wk >= 45 else 0) + (3 if whale_for_fav else 0) + (2 if fav_delta >= 7.0 else 0)
        candidates.append((u_team, f"{fav_team} Takım Golü 1.5 Üst", min(82, max(64, u_team))))

    # 4. ADAY: KARŞILIKLI GOL VAR
    if lam_h >= 1.12 and lam_a >= 1.08 and abs(lam_h - lam_a) <= 0.36 and h_sho >= 68 and a_sho >= 68 and fav_val > -185 and p_btts >= 52:
        u_btts = p_btts + 8 + (4 if p_btts >= p_o25 + 2 else 0) + (6 if whale_against_fav else 0) + (3 if (h_def <= 70 and a_def <= 70) or d_wk >= 38 else 0)
        candidates.append((u_btts, "Karşılıklı Gol Var", min(79, max(63, p_btts + 5))))

    # 5. ADAY: MAÇ 2.5 GOL ÜST
    if (p_o35 >= 27 and ou_val >= 2.5) or (lam_tot >= 2.55 and p_o25 >= 52):
        u_o25 = p_o25 + 8 + (4 if ou_val >= 3.5 else 0) + (3 if d_wk >= 35 and bus_sc < 48 else 0)
        candidates.append((u_o25, "Maç 2.5 Gol Üst", min(80, max(65, p_o25 + 6))))

    # 6. ADAY: NEGATİF BİNOM KART ÜST
    if card_prob >= 62 and not is_blowout and real_cor < 11.2:
        u_card = card_prob + (5 if whale_against_fav else 0) + (3 if mom_gap <= 18 else 0)
        candidates.append((u_card, f"🟨 {card_line}", card_prob))

    # 7. ADAY: SADECE MAÇ 1.5 GOL ÜST (1-1 Kilitlenmesinde bile kazanan güvenli liman!)
    u_o15 = max(62, int(round(p_o15 * 0.90))) + (4 if lam_tot >= 2.30 else 0) + (4 if team_o15_vetoed and opp_lam >= 0.95 else 0) - (5 if fav_val <= -200 else 0)
    candidates.append((u_o15, "Maç 1.5 Gol Üst", min(79, max(63, u_o15))))

    candidates.sort(key=lambda x: x[0], reverse=True)

    best_u, best_pick, raw_prob = candidates[0]
    sec_pick, sec_prob = None, 64

    # Önce mevcut adaylar içinden 1. tercihten farklı olan en güçlü 2. adayı ara
    for cand_u, cand_pk, cand_pr in candidates[1:]:
        if cand_pk != best_pick:
            sec_pick, sec_prob = cand_pk, cand_pr
            break

    # Eğer adaylarda tek seçenek kaldıysa (Örn: Sadece Maç 1.5 Gol Üst barajı geçtiyse),
    # 1. tercihle aynı olmaması için en güçlü alternatif yan marketi (Kart, Korner veya KG Var) seç:
    if not sec_pick or sec_pick == best_pick:
        fallback_pool = [
            (cor_prob, f"🚩 {cor_line}"),
            (card_prob, f"🟨 {card_line}"),
            (p_btts + 4, "Karşılıklı Gol Var"),
            (p_o25 + 4, "Maç 2.5 Gol Üst"),
            (max(62, int(round(p_o15 * 0.90))), "Maç 1.5 Gol Üst")
        ]
        fallback_pool.sort(key=lambda x: x[0], reverse=True)
        for fb_prob, fb_pk in fallback_pool:
            if fb_pk != best_pick:
                sec_pick, sec_prob = fb_pk, max(58, min(78, fb_prob))
                break

    m4["top2_pick"] = sec_pick
    m4["top2_conf"] = _calibrate_decision_score_by_market_and_band(sec_prob, mkt_type=_classify_pick_market_type(sec_pick))
    return best_pick, raw_prob

def evaluate_pre_match(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, kademe, r_data, lig_adi=""):
    h_tac = str(((r_data or {}).get("h") or {}).get("tac") or "4-2-3-1")
    a_tac = str(((r_data or {}).get("a") or {}).get("tac") or "4-2-3-1")

    try:
        m4 = compute_model4_poisson_and_scores(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, fav_abbr, fav_val, ou_val, r_data, lig_adi, disp_odd)
    except Exception:
        m4 = {"status": "HESAPLANAMADI"}

    if not isinstance(m4, dict) or m4.get("status") == "HESAPLANAMADI":
        return 0, "⚠️ HESAPLANAMADI (Veri Eksik)", disp_odd, True, "HESAPLANAMADI", {"status": "HESAPLANAMADI"}

    is_home_fav = bool(m4.get("fav_is_home", True))
    fav_team = h_name if is_home_fav else a_name
    dc_tag = "1X" if is_home_fav else "X2"

    fr = compute_friction_physics(h_name, a_name, h_tac, a_tac, h_mom, a_mom, fav_val, ou_val, kademe, r_data, lig_adi, is_home_fav)
    cor_line = "9.5 Korner Üst" if any(k in str(lig_adi).upper() for k in ("PREMIER", "İSKOÇYA", "EFL")) else "8.5 Korner Üst"
    card_line = "4.5 Kart Üst" if any(k in str(lig_adi).upper() for k in ("SERIE B", "LA LIGA 2", "BREZİLYA", "ARJANTİN", "SÜPER LİG")) else "3.5 Kart Üst"

    m4.update({
        "fav_is_home": is_home_fav, "is_home_fav": is_home_fav, "fav_team": fav_team, "dc_tag": dc_tag,
        "friction": fr, "cor_score": fr["cor_score"], "card_score": fr["card_score"],
        "cor_p": fr["cor_score"], "card_p": fr["card_score"], "cor_line": cor_line, "card_line": card_line,
        "is_blowout": fr["is_blowout"], "blowout_prob": fr["blowout_prob"]
    })

    if fr["rot_pen"] < 0:
        m4["d_weak"] = min(95, safe_int(m4.get("d_weak"), 18) + abs(fr["rot_pen"]) * 3)

    if fr["tags_str"] and fr["tags_str"] not in disp_odd:
        disp_odd = f"{disp_odd} {fr['tags_str']}".strip()

    p_o35 = safe_int(m4.get("p_over35"), 18)
    p_shd = safe_int(m4.get("p_shield"), 54)
    d_wk = safe_int(m4.get("d_weak"), 18)
    warn_flag = False

    pick, raw_prob = _select_best_autonomous_market(
        h_name, a_name, is_home_fav, fav_team, dc_tag, h_mom, a_mom,
        disp_odd, fav_val, ou_val, m4, fr, cor_line, card_line
    )

    mkt_type = _classify_pick_market_type(pick)
    conf = _calibrate_decision_score_by_market_and_band(raw_prob, mkt_type=mkt_type)

    psim = _build_patron_sim_summary(m4, pick, is_home_fav, conf, ou_val)
    m4["patron_sim_ui"] = psim["ui"]
    m4["patron_sim_mini"] = psim["mini"]

    m4_str = f"P4+:%{p_o35}|Sh:%{p_shd}|Dw:{d_wk}|Δ:{m4.get('fav_delta',0.0):+.1f}"
    return conf, pick, disp_odd, warn_flag, m4_str, m4

def compute_post_lineup_evolution_and_props(match_title, is_off, h_name, a_name, h_abbr, a_abbr, h_tac, a_tac, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, conf, pick, lig_adi, r_data, m4):
    m4 = m4 or {}
    if m4.get("status") == "HESAPLANAMADI" or "HESAPLANAMADI" in str(pick):
        return 0, "⚠️ HESAPLANAMADI (Veri Eksik)", disp_odd, "⚠️ Veri Hatası", "—", False

    fav_is_home = bool(m4.get("fav_is_home", True))
    fav_team = h_name if fav_is_home else a_name

    p_cor = safe_int(m4.get("cor_p") or m4.get("cor_score"), 60)
    p_card = safe_int(m4.get("card_p") or m4.get("card_score"), 58)
    p_o15 = safe_int(m4.get("p_over15"), 72)
    p_o25 = safe_int(m4.get("p_over25"), 48)
    p_btts = safe_int(m4.get("p_btts"), 50)
    p_fav_o15 = safe_int(m4.get("p_fav_o15"), 48)
    d_wk = safe_int(m4.get("d_weak"), 18)
    bus_sc = safe_int(m4.get("bus_score"), 0)
    fr = m4.get("friction") or {}
    real_cor_sum = safe_float(fr.get("real_cor_sum"), 9.5)
    inj_wing = bool(fr.get("inj_wing", False))

    raw_cor_line = str(m4.get("cor_line") or "8.5 Korner Üst")
    cor_label = raw_cor_line if "Korner" in raw_cor_line else f"{raw_cor_line} Korner Üst"
    raw_card_line = str(m4.get("card_line") or "3.5 Kart Üst")
    card_label = raw_card_line if "Kart" in raw_card_line else f"{raw_card_line} Kart Üst"

    top2_pk = str(m4.get("top2_pick") or f"🚩 {cor_label}")
    top2_cf = safe_int(m4.get("top2_conf"), 66)
    prop_str = f"🎯 2.Tercih: {top2_pk} (%{top2_cf}) | 🚩 {cor_label} (%{p_cor}) | 🟨 {card_label} (%{p_card})"

    pre_mem = MEM.setdefault("pre_lineup_memory", {})
    if not is_off:
        if match_title not in pre_mem:
            pre_mem[match_title] = pick
        return conf, pick, disp_odd, "⏳ Resmi Kadro Bekleniyor", prop_str, False

    old_pick = pre_mem.get(match_title, pick)
    fav_info = ((r_data or {}).get("h") if fav_is_home else (r_data or {}).get("a")) or {}
    rot_cnt = safe_int(fav_info.get("rot_cnt"), 0)
    fav_hist = fav_info.get("hist") or {}
    sub_rat = safe_int(fav_hist.get("sub_rat"), 72)

    if rot_cnt == 0:
        conf = min(92, conf + 2)
        if "✅KadroOnay" not in disp_odd:
            disp_odd += " ✅KadroOnay(+2p)"
    elif rot_cnt >= 3 and sub_rat <= 71:
        drop_pts = min(4, (73 - sub_rat) + (rot_cnt - 2))
        conf = max(45, conf - drop_pts)
        if f"🧬RotasyonEtki(-{drop_pts}p)" not in disp_odd:
            disp_odd += f" 🧬RotasyonEtki(-{drop_pts}p)"

    if "Korner" in pick and inj_wing and p_cor < 58 and real_cor_sum < 11.5:
        if fav_val <= -145 and "⚠️Δ" not in disp_odd:
            pick = f"{fav_team} Kazanır & 1.5 Gol Üst"
            conf = _calibrate_decision_score_by_market_and_band(p_fav_o15 + 8, "WIN")
        elif p_btts >= 55 and abs(safe_float(m4.get("lam_h_struct"), 1.3) - safe_float(m4.get("lam_a_struct"), 1.2)) <= 0.35 and fav_val > -170:
            pick = "Karşılıklı Gol Var"
            conf = _calibrate_decision_score_by_market_and_band(p_btts, "BTTS")
        elif p_o25 >= 54:
            pick = "Maç 2.5 Gol Üst"
            conf = _calibrate_decision_score_by_market_and_band(p_o25, "O25")
        else:
            pick = top2_pk if "Korner" not in top2_pk else "Maç 1.5 Gol Üst"
            conf = top2_cf if "Korner" not in top2_pk else _calibrate_decision_score_by_market_and_band(p_o15 * 0.90, "O15")
    elif bus_sc >= 60 and p_cor >= 68 and not inj_wing and "Ana Kasa" not in pick:
        pick = f"🚩 {cor_label}"
        conf = _calibrate_decision_score_by_market_and_band(p_cor, "COR")
    elif d_wk >= 42 and real_cor_sum >= 10.4 and not inj_wing and "Korner" not in pick and p_cor >= 66:
        pick = f"🚩 {cor_label}"
        conf = _calibrate_decision_score_by_market_and_band(p_cor, "COR")

    psim = _build_patron_sim_summary(m4, pick, fav_is_home, conf, ou_val)
    m4["patron_sim_ui"] = psim["ui"]
    m4["patron_sim_mini"] = psim["mini"]

    evo_changed = (pick != old_pick)
    evo_str = f"🔄 {old_pick} ➔ ✅ {pick}" if evo_changed else "✅ Kadro Onaylı (Sabit)"
    return conf, pick, disp_odd, evo_str, prop_str, evo_changed

def analyze_live_pro(match_title, h_name, a_name, h_abbr, a_abbr, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_poss, m_int, h_mom, a_mom, fav_abbr, fav_val, ou_val, has_live_api_odds, r_data):
    tot_sh, tot_sot, tot_cor = h_sh + a_sh, h_sot + a_sot, h_cor + a_cor
    rem_frac = max(0.05, (90.0 - min(90, m_int)) / 90.0) ** 0.85

    # CANLI 60+ DK YORGUNLUK ÇARPANI VE MISMATCH (Hantal Stoper Çöküşü vs Korner Bloklaması)
    r_d = r_data or {}
    h_att, h_mob = _compute_mismatch_athleticism(r_d.get("h") or {}, h_mom)
    a_att, a_mob = _compute_mismatch_athleticism(r_d.get("a") or {}, a_mom)
    fav_is_home = (fav_abbr == h_abbr) or ((h_mom + 12) >= a_mom)
    fav_delta = (h_att - a_mob) if fav_is_home else (a_att - h_mob)
    fatigue_mult = 1.0 + max(0.0, (m_int - 55) / 100.0)
    eff_delta = round(fav_delta * fatigue_mult, 1)

    live_xg_h = h_sh * 0.05 + h_sot * 0.24 + h_cor * 0.025
    live_xg_a = a_sh * 0.05 + a_sot * 0.24 + a_cor * 0.025
    t_scale = 90.0 / max(m_int, 15)
    exp_rem_g = round(max(0.15, ((live_xg_h + live_xg_a) * t_scale) * rem_frac * 0.55 * math.exp(0.012 * eff_delta)), 2)
    p_next_goal = int(round((1.0 - math.exp(-exp_rem_g)) * 100.0))

    heat = min(99, max(28, int(p_next_goal * 0.65) + tot_sot * 4 + tot_cor * 2))
    fav_team = h_name if fav_is_home else a_name
    fav_losing = (h_score < a_score) if fav_is_home else (a_score < h_score)
    odd_src_tag = "📈CanlıOranAktif" if has_live_api_odds else "⏳CanlıOranYok(SahaFiziği)"

    if not has_live_api_odds and heat < 68:
        live_pick = f"⏳ Canlı Oran Bekleniyor • Saha Kalan xG: {exp_rem_g} (Gol İhtimali: %{p_next_goal})"
    elif tot_sh >= 15 and abs(fav_delta) < 4.5 and m_int <= 76:
        live_pick = f"🚩 Canlı Korner Pusu: Toplam {tot_cor + 2.5} Korner Üst (Bloklanan Şut:{tot_sh} | Δ:{eff_delta:+.1f})"
    elif fav_losing and m_int <= 75 and exp_rem_g >= 0.70:
        live_pick = f"🎯 Canlı Pusu Hedefi: {fav_team} Sıradaki Gol / +2.5 Korner (%{min(88, p_next_goal + 10)} | Etkin Δ:{eff_delta:+.1f})"
    elif exp_rem_g >= 0.85 and m_int <= 78:
        live_pick = f"🎯 Canlı Pusu Hedefi: {h_score + a_score + 0.5} Gol Üst (%{p_next_goal} | Etkin Δ:{eff_delta:+.1f})"
    elif tot_cor >= int(m_int * 0.12) and m_int <= 75:
        live_pick = f"🎯 Canlı Pusu Hedefi: Toplam {tot_cor + 2.5} Korner Üst (Kalan xG: {exp_rem_g})"
    else:
        live_pick = f"🎯 Canlı Saha Projeksiyonu: Kalan xG {exp_rem_g} (Gol: %{p_next_goal})"

    tags = [f"⚡KalanxG:{exp_rem_g}(Gol:%{p_next_goal})", f"🏃EtkinΔ:{eff_delta:+.1f}", odd_src_tag]
    if abs(h_poss - 50) >= 12:
        tags.append("📐KanatAsimetri")
    if fav_losing and heat >= 70:
        tags.append("💎FavGeride->Pusu")
    elif h_score == a_score and m_int >= 25 and heat >= 65:
        tags.append("💎FavKilitli->Pusu")

    if heat >= 72 and (20 <= m_int <= 75) and match_title not in MEM["live_signals"]:
        MEM["live_signals"][match_title] = {"status": "WAIT", "score_at": f"{h_score}-{a_score}", "cor_at": tot_cor, "min_at": m_int}
    elif match_title in MEM["live_signals"] and MEM["live_signals"][match_title]["status"] == "WAIT":
        sig = MEM["live_signals"][match_title]
        if f"{h_score}-{a_score}" != sig["score_at"] or (tot_cor - sig["cor_at"]) >= 4:
            sig["status"] = "WON"
        elif m_int >= 80:
            sig["status"] = "LOST"
    return heat, "|" + "|".join(tags), live_pick, "", heat

def evaluate_ft_result(pick, h_name, a_name, h_score, a_score):
    p = str(pick or "")
    tot = h_score + a_score
    if "Kazanır & 2.5 Gol Üst" in p:
        return (h_score > a_score and tot >= 3) if h_name in p else (a_score > h_score and tot >= 3)
    if "Kazanır & 1.5 Gol Üst" in p:
        return (h_score > a_score and tot >= 2) if h_name in p else (a_score > h_score and tot >= 2)
    if "Kazanır" in p:
        return (h_score > a_score) if h_name in p else (a_score > h_score)
    if "Handikap" in p:
        return (h_score - a_score >= 2) if h_name in p else (a_score - h_score >= 2)
    if "2.5 Gol Üst" in p:
        return tot >= 3
    if "Maç 1.5 Gol Üst" in p:
        return tot >= 2
    if "Karşılıklı Gol Var" in p:
        return h_score >= 1 and a_score >= 1
    if "Takım Golü 1.5 Üst" in p:
        return (h_score >= 2) if h_name in p else (a_score >= 2)
    if "1X" in p and "1.5 Gol Üst" in p:
        return h_score >= a_score and tot >= 2
    if "X2" in p and "1.5 Gol Üst" in p:
        return a_score >= h_score and tot >= 2
    if "1X" in p and "3.5 Alt" in p:
        return h_score >= a_score and tot <= 3
    if "X2" in p and "3.5 Alt" in p:
        return a_score >= h_score and tot <= 3
    if "3.5 Gol Alt" in p or "3.5 Alt" in p:
        return tot <= 3
    return False

# ==================== MODÜL 4/6: BÜLTEN TARAYICI VE DP-MİNİ ====================
_ACTIVE_LEAGUES = [
    ("tur.1", "TÜRKİYE SÜPER LİG", 1), ("esp.1", "İSPANYA LA LIGA", 1),
    ("ger.1", "ALMANYA BUNDESLIGA", 1), ("eng.1", "İNGİLTERE PREMIER LİG", 1),
    ("ita.1", "İTALYA SERIE A", 1), ("fra.1", "FRANSA LIGUE 1", 1),
    ("ned.1", "HOLLANDA EREDIVISIE", 1), ("por.1", "PORTEKİZ LIGA", 1),
    ("sco.1", "İSKOÇYA PREMIERSHIP", 1), ("eng.league_cup", "İNGİLTERE EFL CUP", 1),
    ("bra.1", "BREZİLYA SERIE A", 1), ("arg.1", "ARJANTİN LIGA PRO", 1),
    ("mex.1", "MEKSİKA LIGA MX", 1), ("ita.2", "İTALYA SERIE B", 2),
    ("eng.2", "İNGİLTERE CHAMPIONSHIP", 2), ("esp.2", "İSPANYA LA LIGA 2", 2)
]

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
    return max(stat_cards, det_cards, r_cards)

def _fetch_single_league_sb(item):
    slug, lig_adi, kademe = item
    today_str = datetime.now(TR_TZ).strftime("%Y%m%d")
    merged_events = {}
    for url in (
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={today_str}",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard"
    ):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=4.5)
            if r.status_code == 200:
                for ev in (r.json().get("events") or []):
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

for _bad_k in list(MEM.setdefault("finished_cache", {}).keys()):
    _fm = MEM["finished_cache"].get(_bad_k)
    if not isinstance(_fm, dict) or "Dundee" in _bad_k or ((_fm.get("h_sh", 0) + _fm.get("a_sh", 0)) == 0 and (_fm.get("h_cor", 0) + _fm.get("a_cor", 0)) == 0):
        MEM["finished_cache"].pop(_bad_k, None)
        MEM.setdefault("history_scores", {}).pop(_bad_k, None)

for _hk in list(MEM.setdefault("history_scores", {}).keys()):
    if "Dundee" in _hk or _hk not in MEM.get("finished_cache", {}):
        MEM["history_scores"].pop(_hk, None)

now_tr = datetime.now(TR_TZ)
raw_matches, roster_tasks = [], []
with ThreadPoolExecutor(max_workers=10) as ex:
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
        try:
            ev_date_str = (ev_date_str[:-1] + ":00+00:00") if (len(ev_date_str) == 17 and ev_date_str.endswith("Z")) else ev_date_str.replace("Z", "+00:00")
            dt_ev = datetime.fromisoformat(ev_date_str).astimezone(TR_TZ)
            hours_diff = (dt_ev - now_tr).total_seconds() / 3600.0
            if state == "pre" and (hours_diff < -2.0 or hours_diff > 15.0):
                continue
            if state == "post" and abs(hours_diff) > 12.0:
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
        op_entry = op_mem.get(match_title)
        if not isinstance(op_entry, dict) or "fav_val" not in op_entry or "ou_val" not in op_entry:
            op_entry = {"fav_val": fav_val, "ou_val": ou_val}
            op_mem[match_title] = op_entry
        op_fav, op_ou = safe_int(op_entry.get("fav_val"), fav_val), safe_float(op_entry.get("ou_val"), ou_val)

        disp_odd = f"{fav_abbr} {fav_val:+d}" if fav_val > 0 else f"{fav_abbr} {fav_val}"
        if fav_val != op_fav:
            d_raw = fav_val - op_fav
            d_prob = round(_odd_to_prob(fav_val) - _odd_to_prob(op_fav), 1)
            if d_prob >= 2.0:
                disp_odd += f" 🔥Δ{d_raw:+d}(+{d_prob}%p)"
            elif d_prob <= -2.0:
                disp_odd += f" ⚠️Δ{d_raw:+d}({d_prob}%p)"
        if ou_val > op_ou:
            disp_odd += f" 💥TG↑({op_ou}->{ou_val})"
        ev_id = str(ev.get("id") or "")
        raw_matches.append((slug, lig_adi, kademe, ev, comp, state, completed, clk, h_c, a_c, h_name, a_name, h_abbr, a_abbr, match_title, h_form, a_form, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, has_live_api_odds, ev_id, odds_3way, ev_date_str))
        roster_tasks.append((slug, ev_id, match_title, h_name, a_name, h_mom, a_mom, disp_odd, state, kademe, fav_abbr, fav_val, a_abbr))

roster_map = {}
if roster_tasks:
    with ThreadPoolExecutor(max_workers=10) as ex:
        for m_t, r_d in ex.map(fetch_and_analyze_roster, roster_tasks):
            roster_map[m_t] = r_d

live_matches, upcoming_matches = [], []
fin_cache = MEM.setdefault("finished_cache", {})
locked_picks = MEM.setdefault("locked_picks", {})
ledger_log = MEM.setdefault("ledger_log", {})

for item in raw_matches:
    slug, lig_adi, kademe, ev, comp, state, completed, clk, h_c, a_c, h_name, a_name, h_abbr, a_abbr, match_title, h_form, a_form, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, has_live_api_odds, ev_id, odds_3way, kickoff_utc = item
    r_data = roster_map.get(match_title) or {}
    r_data["slug"] = slug
    r_data["odds_3way"] = odds_3way
    is_off = bool(r_data.get("official"))
    h_tac = str((r_data.get("h") or {}).get("tac") or "4-2-3-1")
    a_tac = str((r_data.get("a") or {}).get("tac") or "4-2-3-1")
    conf, pick, disp_odd, warn_flag, m4_str, m4 = evaluate_pre_match(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, kademe, r_data, lig_adi)
    conf, pick, disp_odd, evo_str, prop_str, evo_changed = compute_post_lineup_evolution_and_props(match_title, is_off, h_name, a_name, h_abbr, a_abbr, h_tac, a_tac, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, conf, pick, lig_adi, r_data, m4)

    if m4.get("status") == "HESAPLANAMADI" or "HESAPLANAMADI" in str(pick):
        continue

    lock_id = f"{ev_id}_{MODEL_VERSION}" if ev_id else match_title
    legacy_rec = locked_picks.get(match_title) if isinstance(locked_picks.get(match_title), dict) else {}
    rec = locked_picks.get(lock_id) if isinstance(locked_picks.get(lock_id), dict) else (dict(legacy_rec) if state != "pre" else {})

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
    else:
        active_stage = rec.get("CONFIRMED_XI") or rec.get("PRE_LINEUP") or rec
        pick = active_stage.get("pick", pick)
        conf = safe_int(active_stage.get("conf"), conf)
        prop_str = active_stage.get("prop", prop_str)
        rec.update({"pick": pick, "conf": conf, "prop": prop_str, "stage": "LIVE" if state == "in" else "POST_MATCH"})

    locked_picks[lock_id] = rec
    locked_picks[match_title] = rec

    h_score, a_score = safe_int(h_c.get("score"), 0), safe_int(a_c.get("score"), 0)
    h_sh, a_sh = get_stat(h_c, ["totalShots", "shotsSummary"]), get_stat(a_c, ["totalShots", "shotsSummary"])
    h_sot, a_sot = get_stat(h_c, ["shotsOnTarget", "onGoal"]), get_stat(a_c, ["shotsOnTarget", "onGoal"])
    h_cor, a_cor = get_stat(h_c, ["wonCorners", "corners"]), get_stat(a_c, ["wonCorners", "corners"])
    h_poss = get_stat(h_c, ["possessionPct", "possession"]) or 50
    tot_cards = _count_real_match_cards(comp, h_c, a_c, r_data)

    try:
        ev_d = str(ev.get("date") or "")
        ev_d = (ev_d[:-1] + ":00+00:00") if (len(ev_d) == 17 and ev_d.endswith("Z")) else ev_d.replace("Z", "+00:00")
        m_time = datetime.fromisoformat(ev_d).astimezone(TR_TZ).strftime("%H:%M")
    except Exception:
        m_time = "20:30"

    base_obj = {
        "mac": match_title, "lig": lig_adi, "saat": m_time, "h_name": h_name, "a_name": a_name,
        "h_form": h_form or "—", "a_form": a_form or "—", "h_mom": h_mom, "a_mom": a_mom, "h_tac": h_tac, "a_tac": a_tac,
        "is_off": is_off, "odd": disp_odd, "ou": ou_val, "conf": conf, "pick": pick, "evo": evo_str,
        "prop": prop_str, "roster_data": r_data, "m4_summary": m4_str, "m4": m4,
        "h_score": h_score, "a_score": a_score, "h_sh": h_sh, "a_sh": a_sh, "h_sot": h_sot, "a_sot": a_sot,
        "h_cor": h_cor, "a_cor": a_cor, "h_poss": h_poss, "cards": tot_cards, "clk": clk
    }

    if state == "in":
        digits_only = "".join(c for c in clk.split("+")[0] if c.isdigit())
        m_int = safe_int(digits_only, 45 if "HT" in clk.upper() else 1)
        heat, sot_tag, live_pick, _, _ = analyze_live_pro(match_title, h_name, a_name, h_abbr, a_abbr, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_poss, m_int, h_mom, a_mom, fav_abbr, fav_val, ou_val, has_live_api_odds, r_data)
        snaps = MEM.setdefault("live_snapshots", {})
        s0 = snaps.get(match_title)
        if not isinstance(s0, dict) or "min" not in s0 or "sh" not in s0:
            s0 = {"min": m_int, "sh": h_sh + a_sh, "sot": h_sot + a_sot, "cor": h_cor + a_cor}
            snaps[match_title] = s0
        s0_min, s0_sh, s0_sot, s0_cor = safe_int(s0.get("min"), m_int), safe_int(s0.get("sh"), h_sh + a_sh), safe_int(s0.get("sot"), h_sot + a_sot), safe_int(s0.get("cor"), h_cor + a_cor)
        d_str = f"|Δ({s0_min}'->{m_int}'):+{max(0,(h_sh+a_sh)-s0_sh)}/{max(0,(h_sot+a_sot)-s0_sot)}Ş,+{max(0,(h_cor+a_cor)-s0_cor)}/{max(0,a_cor)}K" if m_int > s0_min + 2 else ""
        base_obj.update({"heat": heat, "sot_tag": sot_tag, "live_pick": live_pick, "delta_str": d_str})
        live_matches.append(base_obj)
    elif state == "post":
        if not completed or ((h_sh + a_sh) == 0 and (h_cor + a_cor) == 0) or "Dundee" in match_title:
            continue
        tot_cor_ft = h_cor + a_cor
        if "9.5 Korner Üst" in pick:
            won = (tot_cor_ft >= 10) if tot_cor_ft > 0 else ((h_score + a_score) >= 3)
        elif "8.5 Korner Üst" in pick:
            won = (tot_cor_ft >= 9) if tot_cor_ft > 0 else ((h_score + a_score) >= 3)
        elif "4.5 Kart Üst" in pick:
            won = (tot_cards >= 5)
        elif "3.5 Kart Üst" in pick:
            won = (tot_cards >= 4)
        else:
            won = evaluate_ft_result(pick, h_name, a_name, h_score, a_score)
        is_ak = ("Ana Kasa" in pick or conf >= 80)
        brier_val = round(((conf / 100.0) - (1.0 if won else 0.0)) ** 2, 3)
        MEM.setdefault("history_scores", {})[match_title] = {"won": won, "ak": is_ak, "brier": brier_val, "conf": conf}
        base_obj.update({"won": won, "is_ak": is_ak, "brier": brier_val})
        fin_cache[match_title] = base_obj
        ledger_log[match_title] = f"{now_tr.strftime('%H:%M')} | {match_title} ({h_score}-{a_score}, Kor:{tot_cor_ft}, Kart:{tot_cards}) -> {pick} [{'✅KAZANDI' if won else '❌KAYIP'} | Brier:{brier_val}]"
    else:
        upcoming_matches.append(base_obj)

save_persistent_store()

live_matches.sort(key=lambda x: x.get("heat", 0), reverse=True)
upcoming_matches.sort(key=lambda x: x.get("conf", 0), reverse=True)
finished_matches = [x for x in list(fin_cache.values())[::-1] if isinstance(x, dict) and "h_name" in x and ((x.get("h_sh", 0) + x.get("a_sh", 0)) > 0 or (x.get("h_cor", 0) + x.get("a_cor", 0)) > 0)]

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
    k_tag = f"✅Kadro({m['h_tac']}v{m['a_tac']})" if m["is_off"] else "⏳KadroYok"
    e_tail = f" | {m['evo']} | Yan:{m['prop']}" if m["is_off"] else f" | Yan:{m['prop']}"
    m4_d = m.get("m4") or {}
    ps_mini = f" {m4_d.get('patron_sim_mini','')}" if m4_d.get("patron_sim_mini") else ""
    mini_lines.append(f"ÖNÜ|{m['saat']}|{m['lig']}|{m['mac']}|%{m['conf']}|{k_tag}|Mom:{m['h_mom']}-{m['a_mom']}|{m['odd']}|TG:{m['ou']} [P4+:%{m4_d.get('p_over35',20)}|Sh:%{m4_d.get('p_shield',50)}|Dw:{m4_d.get('d_weak',15)}] -> {m['pick']}{e_tail}{ps_mini}")
for m in finished_matches[:6]:
    st_ico = "✅KAZANDI" if m.get("won") else "❌KAYIP"
    m4_ft = m.get("m4") or {}
    sim_ft = f"|Sim:{m4_ft.get('est_score','1-1')}(%{m4_ft.get('est_score_p',14)})" + (f"⚠️1-1:%{m4_ft.get('p_1_1_lock',14):.0f}" if safe_float(m4_ft.get("p_1_1_lock"), 0) >= 13.2 else "")
    mini_lines.append(f"BİTTİ|FT|{st_ico}|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}|Şut:{m['h_sh']}({m['h_sot']})-{m['a_sh']}({m['a_sot']})|Kor:{m['h_cor']}-{m['a_cor']}({m['h_cor']+m['a_cor']})|Kart:{m['cards']}|Hedef:{m['pick']}(%{m['conf']}){sim_ft}")

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
    xi_status = "✅ OFFICIAL CONFIRMED XI" if m.get("is_off") else "⏳ LAST MATCH TWIN XI"

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
        f"🧮 <b>Model 4.0 Poisson & Gate Telemetry:</b> {m.get('m4_summary','')}</div></div>"
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
    return f"🚨 AI TELEMETRY LOCKED ({k_str})\n⚽ {h} vs {a} (Conf: {conf}%)\n🎯 Main: {pick}\n🔥 {prop}\n👉 {APP_PUBLIC_URL}"

def _send_telegram_msg(text_msg):
    tg_cfg = MEM.setdefault("tg_config", {"token": "", "chat_id": ""})
    tk, cid = str(tg_cfg.get("token") or "").strip(), str(tg_cfg.get("chat_id") or "").strip()
    if not tk or not cid:
        return False, "⚠️ Önce Patron Paneli > X & Telegram sekmesinden Bot Token ve Chat ID girin."
    try:
        r = requests.post(f"https://api.telegram.org/bot{tk}/sendMessage", json={"chat_id": cid, "text": text_msg}, timeout=4.0)
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
            if st.button("📢 Telegram Kanalına Gönder", key=f"tg_btn_{mode}_{idx_key}_{m['mac']}", use_container_width=True):
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
            live_pick_bar = f"<div style='background:#0d2818;border-left:3px solid #3fb950;padding:5px 8px;border-radius:4px;margin-top:5px;font-size:12px;font-weight:700;color:#56d364;'>{lp_disp}</div>" if lp_disp else ""
            patron_line = f"<div style='margin-top:5px;padding:5px 8px;background:#0d1117;border-left:3px solid #f0b90b;border-radius:4px;font-size:11.5px;color:#e6edf3;'>{m4_d.get('patron_sim_ui','')}</div>" if (is_patron_mode and m4_d.get("patron_sim_ui")) else ""
            st.markdown(
                f"<div class='dp-card' style='border-left:4px solid #f85149;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:12px;color:#ffb4a2;'>"
                f"<span>🔴 <b>{m['clk']}</b> • {m['lig']} ({m['h_tac']} vs {m['a_tac']})</span>"
                f"<span style='background:#da3633;color:#fff;padding:1px 7px;border-radius:5px;font-weight:800;'>🔥 Pressure: %{m['heat']}</span></div>"
                f"<div style='font-size:16px;font-weight:800;margin:5px 0;color:#fff;'>{m['h_name']} <span style='color:#ffd33d;'>{m['h_score']} - {m['a_score']}</span> {m['a_name']}</div>"
                f"<div style='font-size:11.5px;color:#c9d1d9;'>🎯 <b>Şut(İsabet):</b> {m['h_sh']}({m['h_sot']}) - {m['a_sh']}({m['a_sot']}) | 🚩 <b>Korner:</b> {m['h_cor']} - {m['a_cor']} (Top:{m['h_cor']+m['a_cor']}) | 🟨 <b>Kart:</b> {m['cards']} | ⚽ <b>Top:</b> %{m['h_poss']}</div>"
                f"<div style='font-size:11px;color:#79c0ff;margin-top:4px;'>⚡ <b>Canlı Telemetri:</b> {m['odd']} {m['delta_str']} {m['sot_tag']}</div>"
                f"{live_pick_bar}"
                f"<div style='margin-top:6px;padding-top:6px;border-top:1px solid #30363d;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;font-size:12px;'>"
                f"<span>🎯 <b>1. Tercih (Ana):</b> <b style='color:#56d364;'>{p_disp}</b></span><span style='color:#d2a8ff;'>{m['prop']}</span></div>"
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
            ["🔥 Güvene Göre", "🕒 Maç Saatine Göre", "🏆 Lige Göre", "🚩 Korner Gücüne Göre"],
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
        locked_card = (m["conf"] >= 68 and not is_unlocked)
        p_disp = "🔒 VIP LOCKED (68%+ High Confidence)" if locked_card else m["pick"]
        pr_disp = "🔒 Unlock VIP to view 2nd Pick & Corner Physics" if locked_card else m["prop"]
        b_col = "#f0b90b" if m["conf"] >= 70 else "#2f81f7"
        k_badge = f"<span style='color:#56d364;font-weight:700;'>✅ Resmi 11 ({m['h_tac']}v{m['a_tac']})</span>" if m["is_off"] else f"<span style='color:#8b949e;'>⏳ Son Maç İkizi ({m['h_tac']}v{m['a_tac']})</span>"
        m4_d = m.get("m4") or {}
        patron_line = f"<div style='margin-top:5px;padding:5px 8px;background:#0d1117;border-left:3px solid #f0b90b;border-radius:4px;font-size:11.5px;color:#e6edf3;'>{m4_d.get('patron_sim_ui','')}</div>" if (is_patron_mode and m4_d.get("patron_sim_ui")) else ""
        st.markdown(
            f"<div class='dp-card' style='border-left:4px solid {b_col};'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;font-size:11.5px;color:#8b949e;'>"
            f"<span>🕒 <b>{m['saat']}</b> • {m['lig']} • {k_badge}</span>"
            f"<span style='background:#21262d;color:#ffd33d;padding:2px 8px;border-radius:6px;font-weight:800;'>AI Conf: %{m['conf']}</span></div>"
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
            st.markdown(
                f"<div class='dp-card' style='border-left:4px solid {bd_col};background:#0d1117;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:11.5px;color:#8b949e;'>"
                f"<span>🏁 <b>FT ({m.get('saat','20:30')})</b> • {m.get('lig','')}</span>"
                f"<span style='background:{bd_col};color:#fff;padding:1px 8px;border-radius:5px;font-weight:800;'>{badge_txt}</span></div>"
                f"<div style='font-size:15px;font-weight:800;margin:4px 0;color:#fff;'>{m['h_name']} <span style='color:#ffd33d;'>{m['h_score']} - {m['a_score']}</span> {m['a_name']}</div>"
                f"<div style='font-size:11.5px;color:#c9d1d9;'>📊 <b>Maç Sonu İstatistik:</b> Şut: {m['h_sh']}({m['h_sot']})-{m['a_sh']}({m['a_sot']}) | 🚩 Korner: <b>{m['h_cor']}-{m['a_cor']} (Toplam: {m['h_cor']+m['a_cor']})</b> | 🟨 Kart: {m['cards']}</div>"
                f"<div style='margin-top:5px;font-size:12px;color:#56d364;'>🎯 <b>AI Hedefi (%{m['conf']}):</b> {m['pick']} &nbsp;|&nbsp; <span style='color:#d2a8ff;'>{m['prop']}</span></div></div>",
                unsafe_allow_html=True
            )
            _render_match_share_box(m, "post", idx_f, is_unlocked)

# ==================== MODÜL 6/6: PATRON KOMUTA VE PAZARLAMA MERKEZİ ====================
if "patron_unlocked" not in st.session_state:
    st.session_state["patron_unlocked"] = False

url_ref = str(st.query_params.get("ref") or "").strip().upper()
my_dev_id = get_smart_device_uid()
mini_text = "\n".join(mini_lines)

cur_user = auto_sync_device_user(my_dev_id, url_ref)
user_tier = str(cur_user.get("tier", "NORMAL")) if isinstance(cur_user, dict) else "NORMAL"

patron_devs = MEM.setdefault("patron_devs", {"DP-F3CB9C", "DP-ADMIN1"})
if my_dev_id in patron_devs:
    st.session_state["patron_unlocked"] = True

def render_x_and_telegram_command_center():
    st.markdown("### 🐦 X (Twitter) & 📢 Telegram Global Pazarlama Merkezi")
    ldg = MEM.get("DATA_LEDGER") or {"karne_str": "0/0", "ak_str": "0/0", "lp_str": "0/0"}
    t_global = f"⚡ DELTA-PULSE AI LIVE TELEMETRY!\n🏆 Verified Record: {ldg['karne_str']}\n💎 Main Safe: {ldg['ak_str']} | 🔥 Live Ambush: {ldg['lp_str']}\n📊 5D Pitch, Corner & Blowout Physics!\n👉 {APP_PUBLIC_URL}"
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

if not st.session_state.get("patron_unlocked"):
    with st.expander("🔐 Yönetici (Patron) Girişi", expanded=False):
        c_p1, c_p2 = st.columns([2, 1])
        with c_p1:
            pin_in = st.text_input("Patron Kodu:", value="", type="password", placeholder="Patron Şifresi").strip().upper()
        with c_p2:
            st.write("")
            if st.button("👑 Patron Kilidini Aç", use_container_width=True):
                if hashlib.sha256(pin_in.encode("utf-8")).hexdigest() in ADMIN_HASHES:
                    st.session_state["patron_unlocked"] = True
                    patron_devs.add(my_dev_id)
                    save_persistent_store()
                    st.rerun()
                else:
                    st.error("❌ Hatalı Patron Kodu!")

if st.session_state.get("patron_unlocked"):
    st.markdown(f"## 👑 PATRON KOMUTA & PAZARLAMA MERKEZİ *(Tanınan Cihaz: `{my_dev_id}`)*")
    t1, t2, t3, t4 = st.tabs(["📊 Canlı Bülten & Sahalar", "📋 DP-MİNİ & Data Günlüğü", "👑 TRC20 Kasa & Üye Radarı", "🐦 X & 📢 Telegram Paneli"])
    with t1:
        render_main_bulletin(tier="ADMIN", is_patron_mode=True)
    with t2:
        st.markdown("##### 📋 Patron Özel DP-MİNİ Telemetri Çıktısı (Sadece Sana Görünür)")
        st.code(mini_text, language="text")
    with t3:
        users_db = MEM.setdefault("users_db", {})
        vip_cnt = sum(1 for u in users_db.values() if isinstance(u, dict) and u.get("tier") == "VIP")
        st.markdown(f"**👥 Gerçek Cihaz:** `{len(users_db)}` | **👑 Aktif VIP:** `{vip_cnt}` (Kurucu Kalan: `{max(0, 100 - vip_cnt)}/100`)")
        with st.expander("📒 Kalıcı Karne & Arşiv Devir Ayarları (JSON Store)", expanded=False):
            c_bw, c_bt, c_akw, c_akt = st.columns(4)
            nw = c_bw.number_input("Devreden Kazanan", value=safe_int(MEM.get("base_w"), 144), min_value=0)
            nt = c_bt.number_input("Devreden Toplam", value=safe_int(MEM.get("base_t"), 199), min_value=0)
            nakw = c_akw.number_input("Ana Kasa Kazanan", value=safe_int(MEM.get("base_ak_w"), 16), min_value=0)
            nakt = c_akt.number_input("Ana Kasa Toplam", value=safe_int(MEM.get("base_ak_t"), 19), min_value=0)
            if st.button("💾 Kasa Devrini Kalıcı Dosyaya Kaydet", use_container_width=True):
                MEM["base_w"], MEM["base_t"], MEM["base_ak_w"], MEM["base_ak_t"] = int(nw), int(nt), int(nakw), int(nakt)
                save_persistent_store()
                st.rerun()
    with t4:
        render_x_and_telegram_command_center()
else:
    render_main_bulletin(tier=user_tier, is_patron_mode=False)
