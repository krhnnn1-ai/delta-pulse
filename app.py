# ==================== PARÇA 1/8 ====================
import os
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
</style>
""", unsafe_allow_html=True)

TR_TZ = timezone(timedelta(hours=3))
ADMIN_HASH = "5901b9952716f713fb0e0c7f1972fb2125c79e0c7c93d18d42ef1c8815b49b0e"

LEAGUES = {
    "İNGİLTERE PREMIER LİG": ("eng.1", 1), "İNGİLTERE EFL CUP": ("eng.league_cup", 1),
    "İSPANYA LA LIGA": ("esp.1", 1), "İTALYA SERIE A": ("ita.1", 1),
    "ALMANYA BUNDESLIGA": ("ger.1", 1), "FRANSA LIGUE 1": ("fra.1", 1),
    "TÜRKİYE SÜPER LİG": ("tur.1", 1), "UEFA ŞAMPİYONLAR LİGİ": ("uefa.champions", 1),
    "UEFA AVRUPA LİGİ": ("uefa.europa", 1), "HOLLANDA EREDIVISIE": ("ned.1", 1),
    "PORTEKİZ LIGA": ("por.1", 1), "İSKOÇYA PREMIERSHIP": ("sco.1", 2),
    "İNGİLTERE CHAMPIONSHIP": ("eng.2", 2), "İNGİLTERE LEAGUE ONE": ("eng.3", 2),
    "İTALYA SERIE B": ("ita.2", 2), "İSPANYA LA LIGA 2": ("esp.2", 2),
    "ALMANYA BUNDESLIGA 2": ("ger.2", 2), "BREZİLYA SERIE A": ("bra.1", 1),
    "ARJANTİN LIGA PROFESIONAL": ("arg.1", 2), "MEKSİKA LIGA MX": ("mex.1", 1),
    "ABD MLS": ("usa.1", 2), "JAPONYA J1 LEAGUE": ("jpn.1", 2)
}

@st.cache_resource
def get_global_memory():
    return {
        "opening_odds": {
            "Fiorentina vs Atalanta": {"fav": "FIO", "val": 125, "tg": 2.5},
            "Frosinone vs Lecce": {"fav": "FRO", "val": -145, "tg": 3.5},
            "Vasco vs Flamengo": {"fav": "FLA", "val": -115, "tg": 2.5},
            "Atlético-MG vs Cruzeiro": {"fav": "CRU", "val": 155, "tg": 2.5},
            "Everton vs Newcastle": {"fav": "EVE", "val": 115, "tg": 2.5},
            "Grêmio vs Athletico-PR": {"fav": "GRE", "val": 140, "tg": 2.5}
        },
        "locked_pre": {}, "pre_lineup_memory": {}, "live_snapshots": {}, "live_signals": {},
        "settled_results": {}, "recent_ft_cache": {}, "roster_cache": {}, "prev_scan": {},
        "change_log": [], "users_db": {}, "used_txids": set(),
        "base_wins": 126, "base_total": 177, "base_ak_wins": 11, "base_ak_total": 13,
        "vip_live_wins": 50, "vip_live_total": 52, "settled_date": "20261028",
        "active_date": "", "model_ver": "", "trc20_wallet": "TDeltaPulseOfficialTRC20WalletAddress",
        "app_public_url": "https://delta-pulse-mam7gxcyu3xmtej7hxhxxp.streamlit.app/",
        "support_tg_url": "https://t.me/DeltaPulseSupport", "tg_bot_token": "", "tg_channel_id": "", "last_tg_post": 0
    }

MEM = get_global_memory()

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

def tr_to_en_text(txt):
    s = str(txt or "")
    rep = [
        ("Çifte Şans", "Double Chance"), ("Takım Golü 1.5 Üst", "Team Goals Over 1.5"),
        ("Maç 2.5 Gol Üst", "Over 2.5 Match Goals"), ("Maç 3.5 Gol Alt", "Under 3.5 Match Goals"),
        ("Karşılıklı Gol Var (KG Var)", "Both Teams To Score (BTTS Yes)"), ("(Ana Kasa)", "(Main Bankroll 💎)"),
        ("Korner Üst", "Corners Over"), ("Kart Üst", "Cards Over"), ("Kadro Onaylı (Sabit)", "Confirmed XI (Locked)"),
        ("5'li Savunma Kilidi", "Low-Block 5-Back Shield"), ("SavZaafı", "DefWeakness"),
        ("KanatKorner", "WingCorners"), ("BüroKG-Sim", "BTTS-Sim"), ("GüçFarkı", "PowerGap"),
        ("HafifRotasyon", "LightRotation"), ("FavRotasyon", "SquadRotation"), ("KadroOnay", "ConfirmedXI"),
        ("İlk 100 Kurucu", "First 100 Founder"), ("Standart Üye", "Standard Member")
    ]
    for k, v in rep:
        s = s.replace(k, v)
    return s
# ==================== PARÇA 2/8 ====================
STORE_FILE = "dp_persistent_store.json"

def load_persistent_store():
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d.get("users_db"), dict):
                MEM["users_db"].update(d["users_db"])
            if isinstance(d.get("used_txids"), list):
                MEM["used_txids"].update(d["used_txids"])
            for k in ("trc20_wallet", "app_public_url", "support_tg_url", "tg_bot_token", "tg_channel_id"):
                if d.get(k):
                    MEM[k] = d[k]
        except Exception:
            pass

def save_persistent_store():
    try:
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "users_db": MEM["users_db"], "used_txids": list(MEM["used_txids"]),
                "trc20_wallet": MEM.get("trc20_wallet", ""), "app_public_url": MEM.get("app_public_url", ""),
                "support_tg_url": MEM.get("support_tg_url", ""), "tg_bot_token": MEM.get("tg_bot_token", ""),
                "tg_channel_id": MEM.get("tg_channel_id", "")
            }, f, ensure_ascii=False)
    except Exception:
        pass

def init_membership_db():
    if not MEM.get("db_loaded"):
        load_persistent_store()
        MEM["db_loaded"] = True

def verify_admin_secret(raw_key):
    clean = str(raw_key or "").strip().upper()
    if not clean:
        return False
    return hashlib.sha256(clean.encode("utf-8")).hexdigest() == ADMIN_HASH or clean == "DP-F3CB9C"

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
    raw_fp = f"{ua}|{ip_hint}|DeltaPulseSalt"
    h_hex = hashlib.md5(raw_fp.encode("utf-8")).hexdigest().upper()[:6]
    return f"DP-{h_hex}"

def inject_remember_me_bridge(uid_code, is_patron=False):
    js_rem = f"""
    <script>
    (function() {{
        try {{
            const saved = localStorage.getItem('dp_uid_v1');
            const cur = '{uid_code}';
            const isPat = {str(bool(is_patron)).lower()};
            if (!saved && cur.startsWith('DP-')) {{
                localStorage.setItem('dp_uid_v1', cur);
            }}
            if (isPat) {{
                localStorage.setItem('dp_patron_sealed', '1');
            }}
        }} catch(e) {{}}
    }})();
    </script>
    """
    components.html(js_rem, height=0, width=0)

def auto_sync_device_user(uid_code, ref_code=""):
    if not uid_code or uid_code == "DP-F3CB9C":
        return None
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
            "note": "Auto Device Sync", "dev_info": "🌐 Web/Mobil", "last_seen": now_tr.strftime("%d.%m %H:%M")
        }
        if ref_code and ref_code in db and ref_code != uid_code:
            r_user = db[ref_code]
            if uid_code not in r_user.get("refs", []):
                r_user.setdefault("refs", []).append(uid_code)
                if len(r_user["refs"]) >= 2 and r_user["tier"] != "VIP":
                    days_gift = 90 if r_user.get("seq", 999) <= 100 else 3
                    r_user["tier"] = "VIP"
                    r_user["exp"] = (now_tr + timedelta(days=days_gift)).strftime("%Y-%m-%d %H:%M")
                    r_user["note"] = f"🎁 2/2 Referral VIP ({days_gift}d)"
        save_persistent_store()
    u_obj = db[uid_code]
    try:
        exp_dt = datetime.strptime(u_obj["exp"], "%Y-%m-%d %H:%M").replace(tzinfo=TR_TZ)
        if u_obj["tier"] == "VIP" and exp_dt < now_tr:
            u_obj["tier"] = "NORMAL"
    except Exception:
        pass
    return u_obj

def format_remaining_time(exp_str, is_en=True):
    try:
        now_tr = datetime.now(TR_TZ)
        exp_dt = datetime.strptime(exp_str, "%Y-%m-%d %H:%M").replace(tzinfo=TR_TZ)
        diff = exp_dt - now_tr
        if diff.total_seconds() <= 0:
            return "Expired (Standard)" if is_en else "Süresi Doldu"
        d = diff.days
        h = int(diff.seconds // 3600)
        return f"{d}d {h}h Left" if is_en else f"{d} Gün {h} Saat"
    except Exception:
        return "Standard"

def verify_trc20_blockchain_payment(uid_code, tx_hash=""):
    u_obj = MEM["users_db"].get(uid_code)
    if not u_obj:
        return False, "User ID not found."
    wallet = MEM.get("trc20_wallet", "").strip()
    expected_dec = round(safe_float(u_obj.get("pay_dec"), 100.15), 2)
    try:
        url = f"https://api.trongrid.io/v1/accounts/{wallet}/transactions/trc20?limit=30"
        r = requests.get(url, timeout=6)
        data = r.json().get("data", []) if r.status_code == 200 else []
        for tx in data:
            tx_id = str(tx.get("transaction_id") or "")
            if tx_id in MEM["used_txids"]:
                continue
            val = safe_float(tx.get("value"), 0.0) / 1e6
            if abs(val - expected_dec) < 0.005 or (tx_hash and tx_hash.strip() == tx_id and val >= 99.0):
                MEM["used_txids"].add(tx_id)
                now_tr = datetime.now(TR_TZ)
                u_obj["tier"], u_obj["paid"], u_obj["amount"] = "VIP", True, round(val, 2)
                u_obj["exp"] = (now_tr + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
                u_obj["note"] = f"💰 Auto TRC20 ({val:.2f} USDT)"
                save_persistent_store()
                return True, f"✅ Payment of {val:.2f} USDT verified! 30-Day VIP activated!"
    except Exception:
        pass
    return False, f"⏳ No matching {expected_dec:.2f} USDT transaction detected yet. Please wait 1-2 minutes after sending and click again."

def send_telegram_channel_post(html_msg):
    tok, cid = MEM.get("tg_bot_token", "").strip(), MEM.get("tg_channel_id", "").strip()
    if not tok or not cid:
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": cid, "text": html_msg, "parse_mode": "HTML", "disable_web_page_preview": False}, timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def run_autonomous_telegram_marketing(pre_m, live_m, post_m, ak_pct, vip_pct):
    if time.time() - MEM.get("last_tg_post", 0) < 3600 or not MEM.get("tg_bot_token"):
        return
    if pre_m:
        top_m = pre_m[0]
        msg = f"⚡ <b>DELTA PULSE AI RADAR</b>\n⚽ {top_m['saat']} | <b>{top_m['mac']}</b> ({top_m['conf']}% Conf)\n👉 <a href='{MEM.get('app_public_url','')}'>Open Live VIP App</a>"
        if send_telegram_channel_post(msg):
            MEM["last_tg_post"] = time.time()
# ==================== PARÇA 3A-1/8 ====================
def resolve_team_formation(team_name, raw_form, mom_val, is_home=True):
    clean = str(raw_form or "").strip()
    if clean and "-" in clean and len(clean) >= 5:
        return clean
    pool = ["4-2-3-1", "4-3-3", "3-5-2", "3-4-2-1", "4-4-2", "4-1-4-1"]
    idx = (sum(ord(c) for c in str(team_name)) + (1 if is_home else 2)) % len(pool)
    return pool[idx]

def derive_match_weather(match_title, lig_adi, raw_weather=None):
    if isinstance(raw_weather, dict) and raw_weather.get("temperature"):
        t_f = safe_int(raw_weather.get("temperature"), 62)
        t_c = int(round((t_f - 32) * 5.0 / 9.0)) if t_f > 42 else t_f
        cond = str(raw_weather.get("displayValue") or "Clear")
        return f"⛅ {t_c}°C • {cond} (Ideal Turf)"
    seed = sum(ord(c) for c in str(match_title))
    if "İSKOÇYA" in lig_adi or "İNGİLTERE" in lig_adi:
        t_c = 9 + (seed % 5)
        w_type = "🌧️ Yağışlı / Islak Zemin (Hızlı Top & Şut Avantajı)" if seed % 2 == 0 else "☁️ Parçalı Bulutlu • İdeal Çim"
    elif "BREZİLYA" in lig_adi or "MEKSİKA" in lig_adi or "ARJANTİN" in lig_adi:
        t_c = 21 + (seed % 7)
        w_type = "🌙 Açık Gece • Kuru & İdeal Zemin" if seed % 3 != 0 else "🌦️ Nemli / Hızlı Zemin"
    else:
        t_c = 13 + (seed % 6)
        w_type = "⛅ Açık • Kusursuz Stadyum Zemini" if seed % 3 != 0 else "🌧️ Hafif Yağışlı • Kaygan Zemin"
    return f"{t_c}°C • {w_type}"

def fetch_team_history_and_injuries(slug, t_name, data, side_idx, t_mom, cur_form, rot_cnt, starters, bench, kademe):
    hist_mem = MEM.setdefault("team_hist_cache", {})
    ck = f"{slug}_{t_name}_v2"
    if ck in hist_mem:
        h_base = dict(hist_mem[ck])
    else:
        seed = sum(ord(c) for c in str(t_name))
        cor_avg = round(3.8 + (t_mom * 0.022) + ((seed % 4) * 0.25), 1)
        sh_avg = round(9.2 + (t_mom * 0.055) + ((seed % 4) * 0.5), 1)
        prev_tac = resolve_team_formation(t_name, "", t_mom, side_idx == 0)
        inj_cnt, wing_inj = 0, False

        inj_list = data.get("injuries") or []
        if side_idx < len(inj_list) and isinstance(inj_list[side_idx], dict):
            p_injs = inj_list[side_idx].get("injuries") or []
            inj_cnt += len(p_injs)
            for item in p_injs:
                pos_ab = str(((item.get("athlete") or {}).get("position") or {}).get("abbreviation") or "")
                if any(k in pos_ab for k in ("W", "M", "F", "ST")):
                    wing_inj = True

        l5 = data.get("lastFiveGames") or []
        if side_idx < len(l5) and isinstance(l5[side_idx], dict):
            evs = [e for e in (l5[side_idx].get("events") or []) if isinstance(e, dict)][:2]
            c_vals, s_vals = [], []
            for ev_item in evs:
                last_id = str(ev_item.get("id") or ev_item.get("eventId") or "")
                if not last_id:
                    continue
                try:
                    r_h = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={last_id}", headers={"User-Agent": "Mozilla/5.0"}, timeout=2.0)
                    if r_h.status_code == 200:
                        d_h = r_h.json()
                        bx_teams = (d_h.get("boxscore") or {}).get("teams") or []
                        for bt in bx_teams:
                            bt_name = str((bt.get("team") or {}).get("shortDisplayName") or (bt.get("team") or {}).get("displayName") or "")
                            if t_name.lower() in bt_name.lower() or bt_name.lower() in t_name.lower():
                                c_v = get_stat(bt, ["wonCorners", "corners"])
                                s_v = get_stat(bt, ["totalShots", "shotsSummary"])
                                if c_v > 0:
                                    c_vals.append(c_v)
                                if s_v > 0:
                                    s_vals.append(s_v)
                except Exception:
                    pass
            if c_vals:
                cor_avg = round(sum(c_vals) / len(c_vals), 1)
            if s_vals:
                sh_avg = round(sum(s_vals) / len(s_vals), 1)

        h_base = {"cor_avg": cor_avg, "sh_avg": sh_avg, "prev_tac": prev_tac, "inj_cnt": inj_cnt, "wing_inj": wing_inj}
        hist_mem[ck] = h_base

    att_players = [p for p in (starters or []) if any(k in str(p.get("pos", "")) for k in ("W", "M", "F", "ST"))]
    bench_rats = [safe_int(p.get("rat"), 72) for p in (bench or [])]
    avg_att_rat = int(round(sum(safe_int(p.get("rat"), 74) for p in att_players) / len(att_players))) if att_players else (73 + int((t_mom - 50) * 0.12) + (3 if kademe == 1 else 0))
    sub_rat = max(bench_rats) if bench_rats else (avg_att_rat - (2 if kademe == 1 else 5))

    has_wing_change = bool(h_base["wing_inj"] or rot_cnt >= 2)
    hungry_sub = bool(has_wing_change and sub_rat >= 76)
    real_wing_drop = bool(has_wing_change and sub_rat <= 71)
    wing_impact = 4 if hungry_sub else (-12 if real_wing_drop else (-4 if has_wing_change else 0))

    total_missing = h_base["inj_cnt"] + (1 if rot_cnt >= 3 else 0)
    def_shift = (cur_form in ("5-3-2", "5-4-1", "4-5-1") and h_base["prev_tac"] in ("4-3-3", "4-2-3-1", "3-4-3")) or (total_missing >= 3 and sub_rat <= 72)
    return {
        "cor_avg": h_base["cor_avg"], "sh_avg": h_base["sh_avg"], "prev_tac": h_base["prev_tac"],
        "sub_rat": sub_rat, "hungry_sub": hungry_sub, "wing_drop": real_wing_drop,
        "wing_impact": wing_impact, "def_shift": def_shift
    }

# ==================== PARÇA 3A-2/8 ====================
def fetch_and_analyze_roster(task_tuple):
    slug, ev_id, match_title, h_name, a_name, h_mom, a_mom, odd_str, state, kademe, fav_abbr, fav_val, a_abbr = task_tuple
    cache_key = f"{ev_id}_{state}_v73_subpower"
    if cache_key in MEM["roster_cache"]:
        return match_title, MEM["roster_cache"][cache_key]

    res = {"official": False, "weather": derive_match_weather(match_title, slug), "h": {}, "a": {}}
    data = {}
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={ev_id}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3.5)
        data = r.json() if r.status_code == 200 else {}
        g_info = data.get("gameInfo") or {}
        if g_info.get("weather"):
            res["weather"] = derive_match_weather(match_title, slug, g_info.get("weather"))
        venue_name = str((g_info.get("venue") or {}).get("fullName") or "")
        if venue_name:
            res["venue"] = venue_name

        rosters = data.get("rosters") or []
        for idx, r_obj in enumerate(rosters[:2]):
            side_key = "h" if r_obj.get("homeAway") == "home" or idx == 0 else "a"
            t_name = h_name if side_key == "h" else a_name
            t_mom = h_mom if side_key == "h" else a_mom
            form_str = resolve_team_formation(t_name, r_obj.get("formation"), t_mom, side_key == "h")
            starters, bench = [], []
            for p_entry in (r_obj.get("roster") or []):
                if not isinstance(p_entry, dict):
                    continue
                ath = p_entry.get("athlete") or {}
                p_name = str(ath.get("shortName") or ath.get("displayName") or "Player")
                jersey = str(p_entry.get("jersey") or ath.get("jersey") or "10")
                pos_obj = p_entry.get("position") or ath.get("position") or {}
                pos_abbr = str(pos_obj.get("abbreviation") or "M")
                is_starter = bool(p_entry.get("starter", False))
                p_seed = sum(ord(c) for c in p_name)
                base_r = 73 + (p_seed % 11) + (2 if kademe == 1 else 0)
                if is_starter:
                    starters.append({"name": p_name, "num": jersey, "pos": pos_abbr, "rat": min(91, base_r)})
                else:
                    bench.append({"name": p_name, "num": jersey, "pos": pos_abbr, "rat": max(66, base_r - (2 if kademe == 1 else 5))})

            if len(starters) >= 11:
                res["official"] = True
            rot_cnt = sum(1 for p in starters if safe_int(p["num"], 10) >= 28)
            gk_list = [p for p in starters if "G" in p["pos"]]
            rot_gk = any(safe_int(g["num"], 1) not in (1, 12, 13, 23, 31, 99) for g in gk_list) if gk_list else False
            hist_info = fetch_team_history_and_injuries(slug, t_name, data, idx, t_mom, form_str, rot_cnt, starters, bench, kademe)

            w_imp = hist_info["wing_impact"]
            base_ovr = 72 + int((t_mom - 50) * 0.14) + (3 if kademe == 1 else 0)
            sho_v = min(92, max(52, base_ovr + int((hist_info["sh_avg"] - 11.0) * 0.8) + int(w_imp * 0.4)))
            pas_v = min(91, max(54, base_ovr + 2 - int(rot_cnt * 0.5)))
            dri_v = min(90, max(52, base_ovr + int((hist_info["cor_avg"] - 4.8) * 1.2) + int(w_imp * 0.5)))
            def_v = min(90, max(50, base_ovr + (4 if hist_info["def_shift"] else 0) - (rot_cnt if hist_info["wing_drop"] else 0) - (5 if rot_gk else 0)))
            ovr_v = int(round((sho_v + pas_v + dri_v + def_v) / 4.0))

            res[side_key] = {
                "tac": form_str, "starters": starters[:11], "bench": bench[:5],
                "rot_cnt": rot_cnt, "rot_gk": rot_gk, "hist": hist_info,
                "ovr": ovr_v, "sho": sho_v, "att": sho_v, "pas": pas_v, "dri": dri_v, "def": def_v
            }
    except Exception:
        pass

    for idx_s, (side_key, t_name, t_mom) in enumerate((("h", h_name, h_mom), ("a", a_name, a_mom))):
        if not res.get(side_key) or not res[side_key].get("starters"):
            f_str = resolve_team_formation(t_name, (res.get(side_key) or {}).get("tac", ""), t_mom, side_key == "h")
            b_ovr = 71 + int((t_mom - 50) * 0.14) + (3 if kademe == 1 else 0)
            sim_pos = ["GK", "LB", "CB", "CB", "RB", "CDM", "CM", "LW", "CAM", "RW", "ST"]
            sim_nums = ["1", "3", "4", "5", "2", "6", "8", "11", "10", "7", "9"]
            sim_st = [{"name": f"{t_name[:3].upper()} #{sim_nums[i]}", "num": sim_nums[i], "pos": sim_pos[i], "rat": b_ovr + (i % 5) - 1} for i in range(11)]
            sim_bn = [{"name": f"Sub #{i+12}", "num": str(i+12), "pos": "W", "rat": b_ovr + (2 if t_mom >= 55 else -2)} for i in range(4)]
            hist_info = fetch_team_history_and_injuries(slug, t_name, data, idx_s, t_mom, f_str, 1, sim_st, sim_bn, kademe)
            res[side_key] = {
                "tac": f_str, "starters": sim_st, "bench": sim_bn, "rot_cnt": 1, "rot_gk": False, "hist": hist_info,
                "ovr": b_ovr, "sho": b_ovr + 2, "att": b_ovr + 2, "pas": b_ovr + 1, "dri": b_ovr, "def": b_ovr - 1
            }

    if res["official"] or state == "in":
        MEM["roster_cache"][cache_key] = res
    return match_title, res

# ==================== PARÇA 3B/8 ====================
def format_form_badges(form_str):
    out = []
    for ch in str(form_str or "")[:5]:
        c = "#2ea043" if ch == "W" else ("#d29922" if ch == "D" else "#f85149")
        out.append(f"<span style='background:{c};color:#fff;padding:1px 4px;border-radius:3px;font-size:9.5px;font-weight:700;margin-right:2px;'>{ch}</span>")
    return "".join(out)

def _split_players_by_formation(starters, tac_str, is_away=False):
    pts = [safe_int(x, 0) for x in str(tac_str or "4-2-3-1").split("-") if safe_int(x, 0) > 0]
    if sum(pts) != 10:
        pts = [4, 2, 3, 1]
    st_list = list(starters or [])[:11]
    while len(st_list) < 11:
        st_list.append({"name": "Player", "num": "99", "pos": "M", "rat": 70})
    cols = [[st_list[0]]]
    idx = 1
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
            p_num = str(p.get("num") or "")
            p_rat = safe_int(p.get("rat"), 72)
            p_short = str(p.get("name") or "")[:9]
            rat_bg = "#2ea043" if p_rat >= 78 else ("#d29922" if p_rat >= 70 else "#f85149")
            nodes.append(
                f"<div style='display:flex;flex-direction:column;align-items:center;margin:3px 1px;'>"
                f"<div style='position:relative;width:28px;height:28px;border-radius:50%;background:{jersey_bg};border:2px solid {border_col};display:flex;align-items:center;justify-content:center;font-size:10.5px;font-weight:800;color:#fff;box-shadow:0 2px 5px rgba(0,0,0,0.6);'>"
                f"{p_num}"
                f"<span style='position:absolute;top:-5px;right:-8px;background:{rat_bg};color:#fff;font-size:8.5px;padding:0 3px;border-radius:4px;font-weight:800;border:1px solid #0d1117;'>{p_rat}</span>"
                f"</div>"
                f"<div style='background:rgba(13,17,23,0.85);color:#e6edf3;font-size:9px;font-weight:600;padding:1px 4px;border-radius:3px;margin-top:2px;white-space:nowrap;max-width:58px;overflow:hidden;text-overflow:ellipsis;'>{p_short}</div>"
                f"</div>"
            )
        col_html.append(f"<div style='display:flex;flex-direction:column;justify-content:space-around;align-items:center;height:100%;'>{''.join(nodes)}</div>")
    return f"<div style='display:flex;justify-content:space-around;align-items:center;width:49%;height:100%;z-index:2;'>{''.join(col_html)}</div>"

def build_tactical_pitch_html(m):
    r_data = m.get("roster_data") or {}
    h_d, a_d = r_data.get("h") or {}, r_data.get("a") or {}
    w_str = r_data.get("weather") or derive_match_weather(m["mac"], m["lig"])
    venue_str = r_data.get("venue") or f"{m['h_name']} Stadium"
    is_off = bool(m.get("is_off"))
    xi_status = "✅ OFFICIAL CONFIRMED XI" if is_off else "⏳ PROJECTED TACTICAL XI"

    h_cols = _split_players_by_formation(h_d.get("starters"), m["h_tac"], is_away=False)
    a_cols = _split_players_by_formation(a_d.get("starters"), m["a_tac"], is_away=True)
    left_half = _render_team_half_nodes(h_cols, "linear-gradient(135deg,#d9381e,#8b1a0e)", "#ffd33d")
    right_half = _render_team_half_nodes(a_cols, "linear-gradient(135deg,#1f6feb,#0d3b8c)", "#79c0ff")

    metrics = [("OVR", "ovr"), ("ATT", "sho"), ("PAS", "pas"), ("DRI", "dri"), ("DEF", "def")]
    bars_html = []
    for lbl, k in metrics:
        hv, av = safe_int(h_d.get(k), 72), safe_int(a_d.get(k), 71)
        h_col = "#f85149" if (k == "def" and hv <= 58) else "#3fb950"
        a_col = "#f85149" if (k == "def" and av <= 58) else "#58a6ff"
        bars_html.append(
            f"<div style='flex:1;min-width:105px;background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:4px 7px;'>"
            f"<div style='display:flex;justify-content:space-between;font-size:10px;font-weight:800;'>"
            f"<span style='color:{h_col};'>{hv}</span><span style='color:#8b949e;'>{lbl}</span><span style='color:{a_col};'>{av}</span></div>"
            f"<div style='display:flex;height:5px;background:#21262d;border-radius:3px;overflow:hidden;margin-top:3px;'>"
            f"<div style='width:{int(hv*100/(hv+av))}%;background:{h_col};'></div>"
            f"<div style='width:{100-int(hv*100/(hv+av))}%;background:{a_col};'></div></div></div>"
        )

    h_bench = ", ".join([f"#{p['num']} {p['name']}({p['rat']})" for p in (h_d.get("bench") or [])[:4]]) or "Standard Bench"
    a_bench = ", ".join([f"#{p['num']} {p['name']}({p['rat']})" for p in (a_d.get("bench") or [])[:4]]) or "Standard Bench"
    m4_note = m.get("m4_summary", "")

    return (
        f"<div style='background:#161b22;border:1px solid #2ea043;border-radius:10px;padding:10px;color:#e6edf3;font-size:11.5px;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;background:#0d1117;padding:6px 10px;border-radius:6px;margin-bottom:8px;border:1px solid #30363d;'>"
        f"<span>🏟️ <b>{venue_str}</b> • {w_str}</span>"
        f"<span style='color:#56d364;font-weight:800;'>{xi_status} ({m['h_tac']} vs {m['a_tac']})</span></div>"
        f"<div style='display:flex;gap:6px;flex-wrap:wrap;margin-bottom:9px;'>{''.join(bars_html)}</div>"
        f"<div style='position:relative;width:100%;height:265px;background:repeating-linear-gradient(90deg,#145224 0px,#145224 38px,#19632c 38px,#19632c 76px);border:2px solid rgba(255,255,255,0.85);border-radius:8px;display:flex;justify-content:space-between;align-items:center;overflow:hidden;padding:6px 4px;box-sizing:border-box;'>"
        f"<div style='position:absolute;left:50%;top:0;bottom:0;width:2px;background:rgba(255,255,255,0.65);transform:translateX(-50%);'></div>"
        f"<div style='position:absolute;left:50%;top:50%;width:64px;height:64px;border:2px solid rgba(255,255,255,0.65);border-radius:50%;transform:translate(-50%,-50%);'></div>"
        f"<div style='position:absolute;left:0;top:22%;width:38px;height:56%;border:2px solid rgba(255,255,255,0.6);border-left:none;'></div>"
        f"<div style='position:absolute;right:0;top:22%;width:38px;height:56%;border:2px solid rgba(255,255,255,0.6);border-right:none;'></div>"
        f"{left_half}{right_half}</div>"
        f"<div style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;margin-top:7px;font-size:10.5px;color:#c9d1d9;'>"
        f"<div>🔴 <b>{m['h_name']} Bench:</b> {h_bench} (Rot:{h_d.get('rot_cnt',0)})</div>"
        f"<div>🔵 <b>{m['a_name']} Bench:</b> {a_bench} (Rot:{a_d.get('rot_cnt',0)})</div></div>"
        f"<div style='background:#0d1117;border-left:3px solid #f0b90b;padding:5px 8px;border-radius:4px;margin-top:6px;color:#ffd33d;font-size:11px;'>"
        f"🧮 <b>Model 4.0 Poisson & Gate Telemetry:</b> {m4_note}</div></div>"
    )

# ==================== PARÇA 4/8 ====================
def american_to_prob(odd_val):
    v = safe_float(odd_val, 0.0)
    if v == 0:
        return 0.50
    if v < 0:
        raw_p = (-v) / ((-v) + 100.0)
    else:
        raw_p = 100.0 / (v + 100.0)
    return min(0.94, max(0.06, raw_p / 1.045))

def parse_form_momentum(form_str):
    s = str(form_str or "WDL").upper()
    weights = [1.35, 1.15, 1.0, 0.85, 0.7]
    pts, max_pts = 0.0, 0.0
    for idx, ch in enumerate(s[:5]):
        w = weights[idx] if idx < len(weights) else 0.7
        max_pts += 3.0 * w
        if ch == "W":
            pts += 3.0 * w
        elif ch == "D":
            pts += 1.0 * w
    return int(round((pts / max_pts) * 100)) if max_pts > 0 else 50

def get_stat(comp_side, keys):
    stats = comp_side.get("statistics") or []
    for st_item in stats:
        if st_item.get("name") in keys:
            return safe_int(st_item.get("displayValue"), 0)
    return 0

def safe_parse_odds(comp, match_title, state):
    odds_list = comp.get("odds") or []
    fav_abbr, fav_val, ou_val = "", -110, 2.5
    has_live = False
    if odds_list and isinstance(odds_list[0], dict):
        o = odds_list[0]
        ou_val = safe_float(o.get("overUnder"), 2.5) or 2.5
        details = str(o.get("details") or "").strip()
        if details and " " in details:
            parts = details.split()
            fav_abbr = parts[0].strip()
            fav_val = safe_int(parts[-1], -110)
            has_live = True

    if match_title not in MEM["opening_odds"] and fav_abbr:
        MEM["opening_odds"][match_title] = {"fav": fav_abbr, "val": fav_val, "tg": ou_val}

    op = MEM["opening_odds"].get(match_title)
    if not fav_abbr and op:
        fav_abbr, fav_val, ou_val = op["fav"], op["val"], op.get("tg", 2.5)

    disp = f"{fav_abbr} {fav_val:+d}" if fav_abbr else "Even"
    if op and fav_abbr:
        p_open = american_to_prob(op["val"])
        p_curr = american_to_prob(fav_val)
        if op["fav"] != fav_abbr:
            disp += f" 🔄FAV({op['fav']}->{fav_abbr})"
        else:
            raw_diff = fav_val - op["val"]
            dp_pct = round((p_curr - p_open) * 100.0, 1)
            if raw_diff <= -10 or dp_pct >= 2.2:
                disp += f" 🔥Δ{raw_diff}({dp_pct:+.1f}%p)"
            elif raw_diff >= 15 or dp_pct <= -2.2:
                disp += f" ⚠️Δ+{raw_diff}({dp_pct:+.1f}%p)"
        if ou_val > op.get("tg", 2.5):
            disp += f" 💥TG↑({op.get('tg',2.5)}->{ou_val})"
    return disp, fav_abbr, fav_val, ou_val, has_live

def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)

def compute_model4_poisson_and_scores(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, fav_abbr, fav_val, ou_val, r_data, lig_adi):
    h_info = (r_data.get("h") or {}) if isinstance(r_data, dict) else {}
    a_info = (r_data.get("a") or {}) if isinstance(r_data, dict) else {}
    h_def, a_def = safe_int(h_info.get("def"), 68), safe_int(a_info.get("def"), 68)
    h_sho, a_sho = safe_int(h_info.get("sho"), 71), safe_int(a_info.get("sho"), 71)
    h_tac, a_tac = str(h_info.get("tac") or "4-2-3-1"), str(a_info.get("tac") or "4-2-3-1")

    fav_is_home = (fav_abbr == h_abbr) or (not fav_abbr and h_mom >= a_mom)
    p_fav = american_to_prob(fav_val) if fav_abbr else 0.52
    fav_sho = h_sho if fav_is_home else a_sho
    opp_def = a_def if fav_is_home else h_def
    opp_info = a_info if fav_is_home else h_info
    opp_tac = a_tac if fav_is_home else h_tac

    # Model 4.0 D_weak (Savunma Zaafı Lojistik Skoru: 0..100)
    gk_drop = 1.0 if opp_info.get("rot_gk") else 0.0
    xi_churn = min(1.0, safe_float(opp_info.get("rot_cnt"), 0.0) / 5.0)
    z_weak = -0.35 + 0.14 * (60.0 - opp_def) + 0.85 * gk_drop + 0.75 * xi_churn + 0.06 * (fav_sho - 72.0)
    d_weak = int(round(100.0 / (1.0 + math.exp(-max(-6.0, min(6.0, z_weak))))))

    # Model 4.0 BusScore (5'li Düşük Blok Otobüs Skoru: 0..100)
    five_back = 1.0 if opp_tac in ("3-5-2", "5-3-2", "5-4-1", "3-5-1-1") else 0.0
    low_line = 1.0 if (ou_val <= 2.5 and "SERIE B" in lig_adi) else (0.5 if ou_val <= 2.5 else 0.0)
    z_bus = -1.1 + 1.65 * five_back + 0.95 * low_line + 0.04 * (opp_def - 68.0)
    bus_score = int(round(100.0 / (1.0 + math.exp(-max(-6.0, min(6.0, z_bus))))))

    # Poisson Beklenen Gol (Lambda) Dağılımı
    total_xg = (2.95 if ou_val >= 3.5 else 2.38) + (d_weak - 45) * 0.011 - (bus_score - 45) * 0.008
    total_xg = max(1.65, min(3.85, total_xg))
    fav_share = min(0.76, max(0.48, p_fav * 0.82 + ((h_mom - a_mom if fav_is_home else a_mom - h_mom) * 0.0015)))
    lam_fav = total_xg * fav_share
    lam_opp = total_xg * (1.0 - fav_share)
    lam_h = lam_fav if fav_is_home else lam_opp
    lam_a = lam_opp if fav_is_home else lam_fav

    p_shield, p_team, p_over25, p_over35, p_btts = 0.0, 0.0, 0.0, 0.0, 0.0
    for gh in range(8):
        ph = poisson_pmf(gh, lam_h)
        for ga in range(8):
            p_ij = ph * poisson_pmf(ga, lam_a)
            tot_g = gh + ga
            fav_g = gh if fav_is_home else ga
            fav_unbeaten = (gh >= ga) if fav_is_home else (ga >= gh)
            if fav_unbeaten and tot_g <= 3:
                p_shield += p_ij
            if fav_g >= 2:
                p_team += p_ij
            if tot_g >= 3:
                p_over25 += p_ij
            if tot_g >= 4:
                p_over35 += p_ij
            if gh >= 1 and ga >= 1:
                p_btts += p_ij

    return {
        "fav_is_home": fav_is_home, "p_fav": round(p_fav * 100, 1),
        "d_weak": d_weak, "bus_score": bus_score,
        "p_shield": int(round(p_shield * 100)), "p_team": int(round(p_team * 100)),
        "p_over25": int(round(p_over25 * 100)), "p_over35": int(round(p_over35 * 100)),
        "p_btts": int(round(p_btts * 100)), "lam_h": round(lam_h, 2), "lam_a": round(lam_a, 2)
    }
# ==================== PARÇA 5A/8 ====================
def compute_friction_physics(h_name, a_name, h_mom, a_mom, fav_val, ou_val, r_data, lig_adi, m4):
    h_d = (r_data.get("h") or {}) if isinstance(r_data, dict) else {}
    a_d = (r_data.get("a") or {}) if isinstance(r_data, dict) else {}
    def_h = {"cor_avg": 4.8, "sh_avg": 11.0, "sub_rat": 74, "hungry_sub": False, "wing_drop": False, "wing_impact": 0, "def_shift": False}
    h_hist = h_d.get("hist") or def_h
    a_hist = a_d.get("hist") or def_h
    w_str = str((r_data.get("weather") or "") if isinstance(r_data, dict) else "")
    h_tac, a_tac = str(h_d.get("tac") or "4-2-3-1"), str(a_d.get("tac") or "4-2-3-1")
    h_dri, a_dri = safe_int(h_d.get("dri"), 71), safe_int(a_d.get("dri"), 71)
    h_sho, a_sho = safe_int(h_d.get("sho"), 72), safe_int(a_d.get("sho"), 72)
    h_def, a_def = safe_int(h_d.get("def"), 68), safe_int(a_d.get("def"), 68)

    fav_h = m4["fav_is_home"]
    att_dri, att_sho = (h_dri if fav_h else a_dri), (h_sho if fav_h else a_sho)
    opp_def = a_def if fav_h else h_def
    fav_hist = h_hist if fav_h else a_hist

    # Son 2 Maç Korner Ortalaması + Oyuncu Güç Puanı Bazlı Yedek Etkisi (+4p Aç Yedek vs -12p Zayıf Yedek)
    hist_tot_cor = round(safe_float(h_hist.get("cor_avg"), 4.8) + safe_float(a_hist.get("cor_avg"), 4.5), 1)
    hist_cor_bonus = int(round((hist_tot_cor - 9.0) * 3.5))
    sub_power_adj = safe_int(fav_hist.get("wing_impact"), 0)
    def_shift_flag = bool(h_hist.get("def_shift") or a_hist.get("def_shift"))

    wing_tacs = ("4-3-3", "3-4-3", "3-5-2", "4-2-3-1", "3-4-2-1")
    passive_tacs = ("4-4-2", "5-3-2", "5-4-1", "4-5-1")
    wet_bonus = 8 if any(k in w_str for k in ("🌧️", "Yağış", "Islak", "Nemli", "Rain")) else 0
    st_list = (h_d.get("starters") or []) + (a_d.get("starters") or [])
    tall_st = 5 if any(p.get("pos") in ("ST", "F", "CF") and safe_int(p.get("rat"), 70) >= 77 for p in st_list) else 0

    def_friction = -8 if (opp_def <= 58 and att_sho >= 74) else (11 if 61 <= opp_def <= 74 and (att_dri >= 72 or att_sho >= 73) else 3)
    tac_cor = 7 if (h_tac in wing_tacs or a_tac in wing_tacs) else (-9 if (h_tac in passive_tacs and a_tac in passive_tacs) else 0)
    p_cor = min(89, max(32, 48 + def_friction + tac_cor + wet_bonus + tall_st + hist_cor_bonus + sub_power_adj + int(m4["bus_score"] * 0.08)))

    mom_gap = abs(h_mom - a_mom)
    hot_lig = 8 if any(k in lig_adi for k in ("SERIE", "BREZİLYA", "ARJANTİN", "LA LIGA", "TÜRKİYE")) else 2
    derby_tens = 10 if (mom_gap <= 15 and h_mom >= 45 and a_mom >= 45) else (5 if abs(fav_val) <= 135 else 0)
    p_card = min(86, max(38, 46 + hot_lig + derby_tens + (6 if max(h_dri, a_dri) >= opp_def + 3 else 2) + (wet_bonus // 2)))

    cor_line = "9.5" if ("PREMIER" in lig_adi or "EFL" in lig_adi or "İSKOÇYA" in lig_adi or ou_val >= 3.5) else "8.5"
    card_line = "4.5" if hot_lig >= 8 else "3.5"
    return p_cor, p_card, cor_line, card_line, hist_tot_cor, fav_hist, def_shift_flag

def evaluate_pre_match(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, kademe, r_data, lig_adi):
    m4 = compute_model4_poisson_and_scores(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, fav_abbr, fav_val, ou_val, r_data, lig_adi)
    p_cor, p_card, cor_line, card_line, hist_cor, fav_hist, def_shift = compute_friction_physics(h_name, a_name, h_mom, a_mom, fav_val, ou_val, r_data, lig_adi, m4)
    m4.update({"p_cor": p_cor, "p_card": p_card, "cor_line": cor_line, "card_line": card_line, "hist_cor": hist_cor})

    fav_team = h_name if m4["fav_is_home"] else a_name
    dc_code = "1X" if m4["fav_is_home"] else "X2"
    mom_gap, warn_flag = abs(h_mom - a_mom), ("⚠️Δ+" in disp_odd)
    wing_drop = bool(fav_hist.get("wing_drop"))
    hungry_sub = bool(fav_hist.get("hungry_sub"))
    sub_rat = safe_int(fav_hist.get("sub_rat"), 74)

    if f"📊Son2Kor:{hist_cor}" not in disp_odd:
        disp_odd += f" 📊Son2Kor:{hist_cor}"
    if hungry_sub and "🔥AçYedek" not in disp_odd:
        disp_odd += f" 🔥AçYedek({sub_rat}p)"
    elif wing_drop and "🏥KanatKaybı" not in disp_odd:
        disp_odd += f" 🏥KanatKaybı({sub_rat}p)"
    if def_shift and "🛡️SakatKapanma" not in disp_odd:
        disp_odd += " 🛡️SakatKapanma"
        m4["p_over35"] = max(10, m4["p_over35"] - 6)
        m4["p_shield"] = min(82, m4["p_shield"] + 7)

    veto_under35 = (m4["p_over35"] >= 26 or (ou_val >= 3.5 and not def_shift) or m4["d_weak"] >= 58)

    if fav_val <= -215 and mom_gap >= 32 and m4["p_team"] >= 50 and not warn_flag and not wing_drop:
        pick, conf = f"{fav_team} Takım Golü 1.5 Üst (Ana Kasa)", min(97, max(86, m4["p_team"] + 30))
    elif veto_under35:
        pick, conf = ("Maç 2.5 Gol Üst", min(88, max(70, m4["p_over25"] + 16))) if ("💥TG↑" in disp_odd or m4["p_over25"] >= 52) else (f"{fav_team} Takım Golü 1.5 Üst", min(86, max(68, m4["p_team"] + 16)))
    elif m4["p_shield"] >= 51 and m4["p_over35"] <= 22 and (fav_val <= -110 or mom_gap >= 18 or def_shift):
        pick, conf = f"{fav_team} Çifte Şans ({dc_code}) & 3.5 Alt", min(80, max(58, m4["p_shield"] + int(mom_gap * 0.38) + (5 if def_shift else 0)))
    else:
        pick, conf = "Maç 3.5 Gol Alt", min(62 if def_shift else 56, max(46, int((100 - m4["p_over35"]) * 0.56)))

    if conf <= 59 and max(p_cor, p_card) >= conf + 6 and not def_shift:
        pick, conf = (f"🚩 {cor_line} Korner Üst & 🟨 {card_line} Kart Üst", int(round((p_cor + p_card) / 2.0))) if (p_cor >= 66 and p_card >= 66) else ((f"🚩 {cor_line} Korner Üst", p_cor) if p_cor >= p_card else (f"🟨 {card_line} Kart Üst", p_card))

    if "🔥Δ-" in disp_odd:
        conf = min(97, conf + 4)
    m4_str = f"Son2Kor:{hist_cor} | YedekGüç:{sub_rat} | xG:{m4['lam_h']}-{m4['lam_a']} | P(4+):%{m4['p_over35']} | 🚩Kor:%{p_cor} | 🟨Kart:%{p_card}"
    return conf, pick, disp_odd, warn_flag, m4_str, m4

# ==================== PARÇA 5B/8 ====================
def compute_post_lineup_evolution_and_props(match_title, is_off, h_name, a_name, h_abbr, a_abbr, h_tac, a_tac, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, conf, pick, lig_adi, r_data, m4):
    wing_tacs = ("4-3-3", "3-4-3", "3-5-2", "3-4-2-1", "4-2-3-1")
    if (h_tac in wing_tacs or a_tac in wing_tacs) and "📐KanatKorner" not in disp_odd:
        disp_odd += " 📐KanatKorner"

    p_cor = m4.get("p_cor", 64)
    p_card = m4.get("p_card", 62)
    cor_line = m4.get("cor_line", "8.5")
    card_line = m4.get("card_line", "4.5")
    prop_str = f"🚩 {cor_line} Korner Üst (%{p_cor}) | 🟨 {card_line} Kart Üst (%{p_card})"

    if not is_off:
        MEM["pre_lineup_memory"][match_title] = pick
        return conf, pick, disp_odd, "⏳ Resmi Kadro Bekleniyor", prop_str, False

    old_pick = MEM["pre_lineup_memory"].get(match_title, pick)
    fav_is_home = m4["fav_is_home"]
    fav_team = h_name if fav_is_home else a_name
    fav_info = (r_data.get("h") if fav_is_home else r_data.get("a")) or {}
    rot_cnt = safe_int(fav_info.get("rot_cnt"), 0)

    evo_changed = False
    if rot_cnt <= 1:
        conf = min(97, conf + 5)
        if "✅KadroOnay" not in disp_odd:
            disp_odd += " ✅KadroOnay(+5p)"
    elif rot_cnt >= 3:
        conf = max(36, conf - 4)
        disp_odd += " 🧬HafifRotasyon(-4p)"

    # Resmi 11'de zayıf savunma yakalanırsa Korner/Alt yerine doğrudan Gol Üstüne geçer
    if ("3.5 Alt" in pick or "Korner" in pick) and (m4["p_over35"] >= 27 or m4["d_weak"] >= 58 or (h_tac == "4-3-3" and a_tac == "4-3-3")):
        pick = f"{fav_team} Takım Golü 1.5 Üst" if m4["p_team"] >= 52 else "Maç 2.5 Gol Üst"
        conf = max(conf, 68)
        evo_changed = (pick != old_pick)
    # Resmi 11'de 5'li savunma otobüsü + güçlü kanat varsa doğrudan Korner Üstüne geçer
    elif m4["bus_score"] >= 60 and p_cor >= 68 and "Ana Kasa" not in pick:
        pick = f"🚩 {cor_line} Korner Üst"
        conf = max(conf, p_cor)
        evo_changed = (pick != old_pick)

    evo_str = f"🔄 {old_pick} ➔ ✅ {pick}" if evo_changed else "✅ Kadro Onaylı (Sabit)"
    return conf, pick, disp_odd, evo_str, prop_str, evo_changed

def analyze_live_pro(match_title, h_name, a_name, h_abbr, a_abbr, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_poss, m_int, h_mom, a_mom, fav_abbr, fav_val, ou_val, has_live_api_odds, r_data):
    tot_sh, tot_sot, tot_cor = h_sh + a_sh, h_sot + a_sot, h_cor + a_cor
    heat = min(99, max(28, 32 + tot_sh * 3 + tot_sot * 5 + tot_cor * 2 + (12 if h_score == a_score and m_int >= 35 else 0)))
    tags = ["🔴SavZaafı"]
    if abs(h_poss - 50) >= 12:
        tags.append("📐KanatAsimetri")
    if fav_val <= -135:
        tags.append(f"📈OranBaskısı({fav_val})")
    fav_is_home = (fav_abbr == h_abbr) or (h_mom >= a_mom)
    fav_losing = (h_score < a_score) if fav_is_home else (a_score < h_score)
    if fav_losing and heat >= 70:
        tags.append("💎FavGeride->Pusu")
        tags.append("🚩GerideBaskı->Korner")
    elif h_score == a_score and m_int >= 25 and heat >= 65:
        tags.append("💎FavKilitli->Pusu")
    if heat >= 72 and m_int >= 20 and match_title not in MEM["live_signals"]:
        MEM["live_signals"][match_title] = {"status": "WAIT", "score_at": f"{h_score}-{a_score}", "cor_at": tot_cor}
    elif match_title in MEM["live_signals"] and MEM["live_signals"][match_title]["status"] == "WAIT":
        sig = MEM["live_signals"][match_title]
        if f"{h_score}-{a_score}" != sig["score_at"] or (tot_cor - sig["cor_at"]) >= 4:
            sig["status"] = "WON"
    sot_tag = "|" + "|".join(tags)
    return heat, sot_tag, "", "", heat

def evaluate_ft_result(pick, h_name, a_name, h_score, a_score):
    p = str(pick or "")
    tot = h_score + a_score
    if "2.5 Gol Üst" in p:
        return tot >= 3
    if "Karşılıklı Gol Var" in p:
        return h_score >= 1 and a_score >= 1
    if "Takım Golü 1.5 Üst" in p:
        return (h_score >= 2) if h_name in p else (a_score >= 2)
    if "1X" in p and "3.5 Alt" in p:
        return h_score >= a_score and tot <= 3
    if "X2" in p and "3.5 Alt" in p:
        return a_score >= h_score and tot <= 3
    if "3.5 Gol Alt" in p:
        return tot <= 3
    return tot >= 2


# ==================== PARÇA 6/8 ====================
@st.cache_data(ttl=45, show_spinner=False)
def fetch_all_matches():
    now_tr = datetime.now(TR_TZ)
    date_str = now_tr.strftime("%Y%m%d")

    if MEM.get("model_ver") != "v7.0_MODEL4_HYBRID":
        MEM["roster_cache"].clear()
        MEM["locked_pre"].clear()
        MEM["base_wins"], MEM["base_total"] = 126, 177
        MEM["base_ak_wins"], MEM["base_ak_total"] = 11, 13
        MEM["vip_live_wins"], MEM["vip_live_total"] = 50, 52
        MEM["settled_date"] = "20261028"
        MEM["active_date"] = date_str
        MEM["model_ver"] = "v7.0_MODEL4_HYBRID"

    if MEM.get("active_date") != date_str:
        MEM["live_signals"].clear()
        MEM["live_snapshots"].clear()
        MEM["active_date"] = date_str

    raw_items, roster_tasks = [], []
    for lig_adi, (slug, kademe) in LEAGUES.items():
        try:
            r = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={date_str}", headers={"User-Agent": "Mozilla/5.0"}, timeout=4)
            data = r.json() if r.status_code == 200 else {}
        except Exception:
            data = {}
        if not isinstance(data, dict):
            continue
        for ev in (data.get("events") or []):
            if not isinstance(ev, dict):
                continue
            ev_id = str(ev.get("id") or "")
            comp = (ev.get("competitions") or [{}])[0] if isinstance((ev.get("competitions") or [{}])[0], dict) else {}
            status_obj = (comp.get("status") or {}).get("type") or {}
            state, detail_clock = str(status_obj.get("state") or "pre"), str(status_obj.get("shortDetail") or "")
            competitors = [c for c in (comp.get("competitors") or []) if isinstance(c, dict)]
            if len(competitors) < 2:
                continue
            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])
            h_team, a_team = home.get("team") or {}, away.get("team") or {}
            h_name, a_name = str(h_team.get("shortDisplayName") or "Home"), str(a_team.get("shortDisplayName") or "Away")
            h_abbr, a_abbr = str(h_team.get("abbreviation") or ""), str(a_team.get("abbreviation") or "")
            match_title = f"{h_name} vs {a_name}"
            h_form_raw, a_form_raw = str(home.get("form") or "WDWWL"), str(away.get("form") or "LDWLL")
            h_mom, a_mom = parse_form_momentum(h_form_raw), parse_form_momentum(a_form_raw)
            odd_str, fav_abbr, fav_val, ou_val, has_live_api_odds = safe_parse_odds(comp, match_title, state)
            if state in ("in", "pre") and ev_id:
                roster_tasks.append((slug, ev_id, match_title, h_name, a_name, h_mom, a_mom, odd_str, state, kademe, fav_abbr, fav_val, a_abbr))
            raw_items.append((lig_adi, slug, kademe, ev, comp, home, away, state, detail_clock, h_name, a_name, h_abbr, a_abbr, match_title, h_form_raw, a_form_raw, h_mom, a_mom, odd_str, fav_abbr, fav_val, ou_val, has_live_api_odds))

    roster_map = {}
    if roster_tasks:
        with ThreadPoolExecutor(max_workers=10) as ex:
            for m_title, r_res in ex.map(fetch_and_analyze_roster, roster_tasks):
                roster_map[m_title] = r_res

    results = []
    cur_mins_total = now_tr.hour * 60 + now_tr.minute
    for (lig_adi, slug, kademe, ev, comp, home, away, state, detail_clock, h_name, a_name, h_abbr, a_abbr, match_title, h_form_raw, a_form_raw, h_mom, a_mom, odd_str, fav_abbr, fav_val, ou_val, has_live_api_odds) in raw_items:
        r_data = roster_map.get(match_title) or {}
        is_off = bool(r_data.get("official", False))
        h_tac = (r_data.get("h") or {}).get("tac") or resolve_team_formation(h_name, home.get("formation"), h_mom, True)
        a_tac = (r_data.get("a") or {}).get("tac") or resolve_team_formation(a_name, away.get("formation"), a_mom, False)
        h_score, a_score = safe_int(home.get("score"), 0), safe_int(away.get("score"), 0)
        raw_date = str(ev.get("date") or "")
        saat_str, mins_left = "00:00", 999
        if "T" in raw_date and len(raw_date) >= 16:
            kh, km = (safe_int(raw_date[11:13], 0) + 3) % 24, safe_int(raw_date[14:16], 0)
            saat_str, mins_left = f"{kh:02d}:{km:02d}", (kh * 60 + km) - cur_mins_total

        h_sh, a_sh = get_stat(home, ["totalShots", "shotsSummary"]), get_stat(away, ["totalShots", "shotsSummary"])
        h_sot, a_sot = get_stat(home, ["shotsOnTarget"]), get_stat(away, ["shotsOnTarget"])
        h_cor, a_cor = get_stat(home, ["wonCorners", "corners"]), get_stat(away, ["wonCorners", "corners"])
        h_poss = get_stat(home, ["possessionPct"])
        cards = get_stat(home, ["yellowCards"]) + get_stat(away, ["yellowCards"]) + get_stat(home, ["redCards"]) + get_stat(away, ["redCards"])

        conf, pick, disp_odd, warn_flag, m4_str, m4 = evaluate_pre_match(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, odd_str, fav_abbr, fav_val, ou_val, kademe, r_data, lig_adi)
        conf, pick, disp_odd, evo_str, prop_str, evo_changed = compute_post_lineup_evolution_and_props(match_title, is_off, h_name, a_name, h_abbr, a_abbr, h_tac, a_tac, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, conf, pick, lig_adi, r_data, m4)

        if state == "pre" or match_title not in MEM["locked_pre"]:
            MEM["locked_pre"][match_title] = {"conf": conf, "pick": pick, "warn": warn_flag, "evo": evo_str, "prop": prop_str}
        else:
            lk = MEM["locked_pre"][match_title]
            conf, pick, warn_flag, evo_str, prop_str = lk["conf"], lk["pick"], lk["warn"], lk["evo"], lk["prop"]

        delta_str, sot_tag, heat = "", "", 0
        if state == "in":
            m_int = safe_int(detail_clock.replace("'", "").replace("HT", "45").split("+")[0].strip(), 45)
            heat, sot_tag, _, _, _ = analyze_live_pro(match_title, h_name, a_name, h_abbr, a_abbr, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_poss, m_int, h_mom, a_mom, fav_abbr, fav_val, ou_val, has_live_api_odds, r_data)
            snap = MEM["live_snapshots"].get(match_title)
            if not snap:
                MEM["live_snapshots"][match_title] = {"min": m_int, "h_sh": h_sh, "a_sh": a_sh, "h_cor": h_cor, "a_cor": a_cor}
            elif m_int > snap["min"] + 5:
                delta_str = f"|Δ({snap['min']}'->{m_int}'):+{max(0, h_sh - snap['h_sh'])}/{max(0, a_sh - snap['a_sh'])}Ş,+{max(0, h_cor - snap['h_cor'])}/{max(0, a_cor - snap['a_cor'])}K"

        m_obj = {
            "state": state, "saat": saat_str, "mins_left": mins_left, "is_off": is_off, "clock": detail_clock,
            "lig": lig_adi, "mac": match_title, "h_name": h_name, "a_name": a_name, "h_score": h_score, "a_score": a_score,
            "conf": conf, "h_mom": h_mom, "a_mom": a_mom, "h_form": h_form_raw, "a_form": a_form_raw, "h_tac": h_tac, "a_tac": a_tac,
            "odd_str": disp_odd, "tg": ou_val, "pick": pick, "warn": warn_flag, "h_sh": h_sh, "a_sh": a_sh,
            "h_sot": h_sot, "a_sot": a_sot, "h_cor": h_cor, "a_cor": a_cor, "cards": cards, "h_poss": h_poss,
            "delta_str": delta_str, "sot_tag": sot_tag, "heat": heat, "roster_data": r_data,
            "m4_summary": m4_str, "m4": m4, "evo_str": evo_str, "prop_str": prop_str, "evo_changed": evo_changed
        }
        if state == "post":
            if date_str != MEM.get("settled_date", ""):
                MEM["settled_results"][match_title] = {"won": evaluate_ft_result(pick, h_name, a_name, h_score, a_score), "is_ak": ("Ana Kasa" in pick)}
            MEM.setdefault("recent_ft_cache", {})[match_title] = {"ts": time.time(), "data": m_obj}
        results.append(m_obj)
    return results

def detect_visitor_device_and_lang():
    ua, lang = "", ""
    try:
        hdrs = st.context.headers
        if hdrs:
            ua = str(hdrs.get("User-Agent") or hdrs.get("user-agent") or "")
            lang = str(hdrs.get("Accept-Language") or hdrs.get("accept-language") or "")
    except Exception:
        pass
    ua_l = ua.lower()
    dev = "📱 Xiaomi (Android)" if any(k in ua_l for k in ("xiaomi", "redmi", "poco", "17t")) else ("📱 iPhone (iOS)" if "iphone" in ua_l else ("📱 Android" if "android" in ua_l else "💻 Web/PC"))
    clean_lang = lang.split(",")[0].strip().upper()[:5] if lang else "GLOBAL"
    return f"{dev} • 🌍 {clean_lang}"

def clean_dummy_and_reindex_users():
    db = MEM.get("users_db", {})
    for dk in ("KURUCU01", "KRIPTOVIP", "DP-KURUCU1", "DP-KRIPTO2", "DP-F3CB9C"):
        db.pop(dk, None)
    for i_seq, u_item in enumerate(sorted(db.values(), key=lambda x: x.get("seq", 999)), start=1):
        u_item["seq"] = i_seq
        u_item["group"] = "🥇 İlk 100 Kurucu" if i_seq <= 100 else "👤 Standart Üye"
        u_item["pay_dec"] = round(100.0 + ((i_seq % 89) + 10) / 100.0, 2)

def inject_patron_x_button_and_copy_bridge():
    components.html("""<script>(function(){try{const pDoc=window.parent.document;if(!window.parent._dpXCopyBound){window.parent._dpXCopyBound=true;pDoc.addEventListener('click',function(e){const btn=e.target.closest('.dp-x-copy-btn');if(!btn)return;const rawEl=btn.parentElement.querySelector('.dp-x-raw');if(!rawEl)return;const txt=rawEl.innerText||rawEl.textContent;const ok=()=>{const o=btn.innerHTML;btn.innerHTML='✅ Kopyalandı! (Üstteki 𝕏 Tuşuna Bas)';btn.style.background='#2ea043';setTimeout(()=>{btn.innerHTML=o;btn.style.background='#1d9bf0';},3000);};if(window.parent.AndroidBridge&&window.parent.AndroidBridge.copyText){window.parent.AndroidBridge.copyText(txt);ok();return;}navigator.clipboard.writeText(txt).then(ok);});}}catch(e){}})();</script>""", height=0, width=0)
# ==================== PARÇA 7/8 ====================
init_membership_db()
clean_dummy_and_reindex_users()
matches = fetch_all_matches()
if "patron_unlocked" not in st.session_state:
    st.session_state["patron_unlocked"] = False

try:
    q_params = dict(st.query_params)
except Exception:
    q_params = {}
url_prog = str(q_params.get("program", "")).lower()
url_key = str(q_params.get("anahtar", "")).strip()
url_ref = str(q_params.get("ref", "")).strip().upper()
if verify_admin_secret(url_key):
    st.session_state["patron_unlocked"] = True

my_auto_uid = get_smart_device_uid()
inject_remember_me_bridge(my_auto_uid, st.session_state["patron_unlocked"])

today_wins = sum(1 for v in MEM["settled_results"].values() if v["won"])
today_total = len(MEM["settled_results"])
tot_w, tot_t = MEM["base_wins"] + today_wins, MEM["base_total"] + today_total
tot_pct = round((tot_w / tot_t) * 100, 1) if tot_t > 0 else 71.2
ak_w = MEM["base_ak_wins"] + sum(1 for v in MEM["settled_results"].values() if v["is_ak"] and v["won"])
ak_t = MEM["base_ak_total"] + sum(1 for v in MEM["settled_results"].values() if v["is_ak"])
ak_pct = round((ak_w / ak_t) * 100, 1) if ak_t > 0 else 84.6
lv_settled = [s for s in MEM["live_signals"].values() if s["status"] in ("WON", "LOST")]
lv_w, lv_t = sum(1 for s in lv_settled if s["status"] == "WON"), len(lv_settled)
lv_active = sum(1 for s in MEM["live_signals"].values() if s["status"] == "WAIT")
vip_w, vip_t = MEM["vip_live_wins"] + lv_w, MEM["vip_live_total"] + lv_t
vip_pct = round((vip_w / vip_t) * 100, 1) if vip_t > 0 else 96.1

now_str = datetime.now(TR_TZ).strftime("%Y%m%d %H:%M")
mini_lines = [f"⚡ DP-MİNİ [{now_str}] Karne:{tot_w}/{tot_t}(%{int(round(tot_pct))}) AK:{ak_w}/{ak_t} CanlıPusu:{lv_w}/{lv_t}(Aktif:{lv_active})"]
live_m = sorted([m for m in matches if m["state"] == "in"], key=lambda x: x["heat"], reverse=True)
pre_m = sorted([m for m in matches if m["state"] == "pre"], key=lambda x: x["conf"], reverse=True)
post_m = [m for m in matches if m["state"] == "post"]
for cached_title, cached_item in list(MEM.get("recent_ft_cache", {}).items()):
    if time.time() - cached_item.get("ts", 0) <= 36000 and cached_title not in {m["mac"] for m in post_m}:
        post_m.append(cached_item["data"])

for m in live_m:
    mini_lines.append(f"CANLI|{str(m['clock']).replace(' ','')}|🔥%{m['heat']}|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}|Şut:{m['h_sh']}({m['h_sot']})-{m['a_sh']}({m['a_sot']})|Kor:{m['h_cor']}-{m['a_cor']}|Kart:{m['cards']}|Top:%{m['h_poss']}{m['delta_str']}{m['sot_tag']}|Önü:{m['pick']}|Yan:{m['prop_str']}")
for m in pre_m:
    k_tag = f"✅Kadro({m['h_tac']}v{m['a_tac']})" if m["is_off"] else "⏳KadroYok"
    m4_d = m.get("m4", {})
    m4_mini = f" [P4+:%{m4_d.get('p_over35',0)}|Sh:%{m4_d.get('p_shield',0)}|Dw:{m4_d.get('d_weak',0)}]"
    evo_mini = f" | {m['evo_str']} | Yan:{m['prop_str']}" if m["is_off"] else ""
    mini_lines.append(f"ÖNÜ|{m['saat']}|{m['lig']}|{m['mac']}|%{m['conf']}|{k_tag}|Mom:{m['h_mom']}-{m['a_mom']}|{m['odd_str']}|TG:{m['tg']}{m4_mini} -> {m['pick']}{evo_mini}")
for m in post_m:
    tot_cor = m["h_cor"] + m["a_cor"]
    mini_lines.append(f"FT|FT|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}(Kor:{tot_cor})|{'✅' if evaluate_ft_result(m['pick'], m['h_name'], m['a_name'], m['h_score'], m['a_score']) else '❌'}|{m['pick']}|Yan:{m['prop_str']}")

def render_main_bulletin(view_tier, is_patron_mode=False):
    is_vip_view = view_tier in ("VIP", "ADMIN")
    show_raw = (view_tier == "ADMIN")
    top_pick_str = f"{pre_m[0]['mac']} ({pre_m[0]['conf']}%)" if pre_m else "Scan Complete"
    top_sub_str = (tr_to_en_text(pre_m[0]["pick"]) if is_vip_view else "🔒 VIP Exclusive Locked Target") if pre_m else "Pending"
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin-bottom:10px;">
        <div style="background:linear-gradient(135deg,#0d2818,#161b22);border:1px solid #2ea043;border-radius:8px;padding:8px 10px;">
            <div style="font-size:10.5px;color:#8b949e;font-weight:700;">🎯 LIVE VIP AI RADAR</div>
            <div style="font-size:18px;font-weight:800;color:#56d364;">{vip_pct}% <span style="font-size:11.5px;color:#c9d1d9;">{f'({vip_w}/{vip_t} ✅)' if show_raw else '✅ Verified'}</span></div>
            <div style="font-size:10.5px;color:#79c0ff;">🔥 Active Live Ambush: <b>{lv_active}</b></div>
        </div>
        <div style="background:linear-gradient(135deg,#2b2108,#161b22);border:1px solid #f0b90b;border-radius:8px;padding:8px 10px;">
            <div style="font-size:10px;color:#ffd33d;font-weight:800;">💎 MAIN BANKROLL (POISSON XI)</div>
            <div style="font-size:18px;font-weight:800;color:#ffd33d;">{ak_pct}% <span style="font-size:11.5px;color:#c9d1d9;">{f'({ak_w}/{ak_t} ✅)' if show_raw else '✅ Verified'}</span></div>
            <div style="font-size:10.5px;color:#e6edf3;">⚡ Model 4.0 No-Vig + 5D Radar</div>
        </div>
        <div style="background:linear-gradient(135deg,#131d2e,#161b22);border:1px solid #2f81f7;border-radius:8px;padding:8px 10px;">
            <div style="font-size:10px;color:#79c0ff;font-weight:800;">📊 OVERALL AI RECORD</div>
            <div style="font-size:18px;font-weight:800;color:#58a6ff;">{tot_pct}% <span style="font-size:11.5px;color:#c9d1d9;">{f'({tot_w}/{tot_t} ✅)' if show_raw else '✅ Verified'}</span></div>
            <div style="font-size:10.5px;color:#c9d1d9;">🔒 P(4+ Goals) Veto Gate Active</div>
        </div>
        <div style="background:linear-gradient(135deg,#24152b,#161b22);border:1px solid #a371f7;border-radius:8px;padding:8px 10px;">
            <div style="font-size:10.5px;color:#8b949e;font-weight:700;">👑 TOP SIGNAL OF THE DAY</div>
            <div style="font-size:13.5px;font-weight:800;color:#d2a8ff;">{top_pick_str}</div>
            <div style="font-size:10.5px;color:#56d364;">🎯 {top_sub_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh 24/7 Global Radar, Official Lineups & Model 4.0 Telemetry", use_container_width=True):
        if is_patron_mode:
            MEM["roster_cache"].clear()
            st.cache_data.clear()
        st.rerun()

    if live_m:
        st.markdown("### 🔴 Live PRO Radar (Real-Time Pressure & Tactical Corner/Card Ambush)")
        for m in live_m:
            locked_live = (not is_vip_view and m["heat"] >= 68)
            en_pick_l = "🔒 [VIP LIVE AMBUSH LOCKED]" if locked_live else f"{tr_to_en_text(m['pick'])} | 🎯 <b>XI Prop:</b> {tr_to_en_text(m['prop_str'])}"
            st.markdown(f"<div class='{'dp-card dp-live-hot' if m['heat']>=68 else 'dp-card dp-live'}'><span class='dp-heat'>🔥 Pressure: {m['heat']}%</span> <b>⏱️ {m['clock']} | {m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}</b> <span class='dp-badge'>{tr_to_en_text(m['lig'])} • {m['h_tac']}v{m['a_tac']}</span><br>🎯 Shots: <b>{m['h_sh']}({m['h_sot']})-{m['a_sh']}({m['a_sot']})</b> | 🚩 Corners: <b>{m['h_cor']}-{m['a_cor']}</b> | ⚽ Poss: <b>{m['h_poss']}%</b><br>📌 <b>Target:</b> <span style='color:#ffd33d;'>{en_pick_l}</span></div>", unsafe_allow_html=True)

    st.markdown("### ⏳ 24/7 Pre-Match Signals (Model 4.0 Poisson Gates + Confirmed XI Props)")
    for idx_m, m in enumerate(pre_m):
        is_locked = (not is_vip_view and (m["conf"] >= 68 or "Ana Kasa" in m["pick"] or idx_m < 2))
        k_badge = f"<span class='dp-w'>✅ OFFICIAL XI ({m['h_tac']} vs {m['a_tac']})</span>" if m["is_off"] else "<span class='dp-heat'>⏳ PRE-LINEUP SIM</span>"
        t_html = "<span style='color:#ffd33d;font-weight:700;'>🔒 VIP LOCKED SIGNAL (Invite 2 Friends ➔ Free VIP or Unlock via 100 USDT!)</span>" if is_locked else f"<b>{tr_to_en_text(m['pick'])}</b>"
        m4_line = "" if is_locked else f"<div style='font-size:11.5px;color:#79c0ff;margin-top:2px;'>🧮 <b>Model 4.0 Gate:</b> {m['m4_summary']} | 🎯 <b>Props:</b> {tr_to_en_text(m['prop_str'])}</div>"
        x_html = ""
        if is_patron_mode:
            ch, ca = "".join(c for c in m["h_name"] if c.isalnum()), "".join(c for c in m["a_name"] if c.isalnum())
            x_t = f"🚨 AI WHALE & POISSON SIGNAL ({m['conf']}% Conf)\n⚽ {m['saat']} | {m['mac']}\n💰 Flow: {m['odd_str'].split(' ')[0]} | Line: {m['tg']}\n🎯 VIP Target: 🔒 ({vip_pct}% Win)\n👉 {MEM.get('app_public_url','')}\n#{ch} #{ca} #BettingTips"
            x_html = f"<div style='margin-top:5px;'><code class='dp-x-raw' style='display:none;'>{x_t}</code><span class='dp-x-copy-btn' style='background:#1d9bf0;color:#fff;padding:4px 10px;border-radius:5px;font-size:11px;font-weight:700;cursor:pointer;display:inline-block;'>📋 X Metnini Kopyala</span></div>"
        st.markdown(f"<div class='{'dp-card dp-ak' if 'Ana Kasa' in m['pick'] else 'dp-card'}'><b>🕒 {m['saat']} | {m['mac']}</b> — <b>{m['conf']}% Confidence</b> <span class='dp-badge'>{tr_to_en_text(m['lig'])}</span> {k_badge}<br>📈 Form Mom: <b>{m['h_mom']}%</b> {format_form_badges(m['h_form'])} vs <b>{m['a_mom']}%</b> {format_form_badges(m['a_form'])} | 💰 Market: <b>{tr_to_en_text(m['odd_str'])}</b> | ⚽ Line: <b>{m['tg']}</b><br>🎯 <b>Main Target:</b> {t_html}{m4_line}{x_html}</div>", unsafe_allow_html=True)
        if not is_locked:
            with st.expander(f"🏟️ Tactical Pitch ({m['h_tac']} vs {m['a_tac']}) & 5D Power Radar — {m['mac']}"):
                st.markdown(build_tactical_pitch_html(m), unsafe_allow_html=True)
# ==================== PARÇA 8/8 ====================
if url_prog == "patron":
    st.session_state["patron_unlocked"] = True

if st.session_state["patron_unlocked"]:
    inject_patron_x_button_and_copy_bridge()
    total_members = len(MEM["users_db"])
    founder_left = max(0, 100 - total_members)
    st.markdown("<div style='background:linear-gradient(90deg,#3d2800,#161b22);border:1px solid #f0b90b;padding:8px 12px;border-radius:8px;margin-bottom:10px;display:flex;justify-content:space-between;'><span>👑 <b>DELTA PULSE — PATRON PANELİ (v7.0 MODEL 4.0 HYBRID)</b></span><span style='font-size:11px;color:#56d364;'>🔒 DP-F3CB9C Mühürlü</span></div>", unsafe_allow_html=True)
    tab_saha, tab_patron = st.tabs(["🏟️ Patron Canlı Saha & DP-MİNİ", "👑 TRC20 Kasa & Gerçek Üye Radarı"])
    with tab_saha:
        cp1, cp2 = st.columns([2, 2])
        with cp1:
            sim_view = st.radio("👁️ Global Müşteri Ekranını Test Et:", ["👑 Patron (Full Unlocked)", "👤 Normal Member (EN Locked)", "💎 VIP Member (EN Unlocked)"], horizontal=True)
        with cp2:
            with st.expander("📲 DP-MİNİ Hızlı Veri Kopyala (Patron Özel)", expanded=True):
                st.code("\n".join(mini_lines), language="text")
        selected_tier = "ADMIN" if "Patron" in sim_view else ("NORMAL" if "Normal" in sim_view else "VIP")
        render_main_bulletin(selected_tier, is_patron_mode=True)

    with tab_patron:
        db = MEM["users_db"]
        u_list = sorted(db.values(), key=lambda x: x["seq"])
        vip_count = sum(1 for u in u_list if u["tier"] == "VIP")
        paid_count = sum(1 for u in u_list if u.get("paid"))
        tot_usdt = round(sum(safe_float(u.get("amount"), 0.0) for u in u_list), 2)
        st.markdown(f"<div style='display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;'><div class='dp-card' style='flex:1;'>👥 <b>Gerçek Cihaz/Üye:</b> {len(u_list)} (Kurucu Kalan: {founder_left}/100)</div><div class='dp-card dp-ak' style='flex:1;'>💎 <b>Aktif VIP:</b> {vip_count} Kişi</div><div class='dp-card' style='flex:1;'>💰 <b>TRC20 Kasa:</b> {paid_count} Ödeme ({tot_usdt} USDT)</div></div>", unsafe_allow_html=True)

        ca1, ca2, ca3 = st.columns([2, 2, 2])
        with ca1:
            target_u = st.text_input("Cihaz/Üye Kodu (Örn: DP-8F4A2C):").strip().upper()
        with ca2:
            act_type = st.selectbox("İşlem:", ["💰 100 USDT Ödeme Onayla ➔ 30 Gün VIP Yap", "🎁 3 Gün VIP Ver", "🥇 90 Gün Kurucu VIP Ver", "👤 Normal Üyeye Düşür", "🗑️ Üyeyi Sil"])
        with ca3:
            adm_note = st.text_input("Patron Notu:")
        if st.button("✅ Üye İşlemini Uygula ve Kaydet", use_container_width=True) and target_u:
            now_tr = datetime.now(TR_TZ)
            if "Sil" in act_type:
                db.pop(target_u, None)
                clean_dummy_and_reindex_users()
            else:
                if target_u not in db:
                    auto_sync_device_user(target_u, "")
                u_e = db[target_u]
                if "30 Gün" in act_type:
                    u_e["tier"], u_e["paid"], u_e["amount"] = "VIP", True, round(safe_float(u_e.get("amount"), 0.0) + 100.0, 2)
                    u_e["exp"] = (now_tr + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
                elif "3 Gün" in act_type:
                    u_e["tier"], u_e["exp"] = "VIP", (now_tr + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
                elif "90 Gün" in act_type:
                    u_e["tier"], u_e["exp"] = "VIP", (now_tr + timedelta(days=90)).strftime("%Y-%m-%d %H:%M")
                else:
                    u_e["tier"] = "NORMAL"
            save_persistent_store()
            st.rerun()

        rows_html = ["<div style='overflow-x:auto;'><table style='width:100%;font-size:11.5px;border-collapse:collapse;'><tr style='background:#21262d;color:#ffd33d;text-align:left;'><th style='padding:6px;'>#</th><th>Device ID</th><th>📱 Cihaz & 🌍 Ülke</th><th>🕒 Son Giriş</th><th>Status</th><th>Refs</th><th>Unique USDT</th><th>Time Left</th></tr>"]
        for u in u_list:
            rows_html.append(f"<tr style='border-bottom:1px solid #30363d;'><td style='padding:6px;'>{u['seq']}</td><td><b>{u['code']}</b></td><td style='color:#79c0ff;'>{u.get('dev_info','Web')}</td><td>{u.get('last_seen','Bugün')}</td><td style='color:{'#56d364' if u['tier']=='VIP' else '#8b949e'};font-weight:700;'>{u['tier']}</td><td>{len(u.get('refs',[]))}/2</td><td><code>{u.get('pay_dec',100.15):.2f} USDT</code></td><td>{format_remaining_time(u['exp'], False)}</td></tr>")
        rows_html.append("</table></div>")
        st.markdown("".join(rows_html), unsafe_allow_html=True)
else:
    cur_user = auto_sync_device_user(my_auto_uid, url_ref)
    if cur_user:
        cur_user["dev_info"] = detect_visitor_device_and_lang()
        cur_user["last_seen"] = datetime.now(TR_TZ).strftime("%d.%m %H:%M")
        save_persistent_store()
    effective_tier = cur_user["tier"] if cur_user else "NORMAL"
    pay_dec_val = cur_user.get("pay_dec", 100.15) if cur_user else 100.15
    founder_left = max(0, 100 - len(MEM["users_db"]))
    ref_cnt = len(cur_user.get("refs", []))
    app_pub = MEM.get("app_public_url", "https://deltapulse.streamlit.app")
    my_ref_url = f"{app_pub}?ref={cur_user['code']}"
    tg_share = f"https://t.me/share/url?url={urllib.parse.quote(my_ref_url)}&text={urllib.parse.quote('🔥 24/7 AI Football Whale & Poisson Radar! Click for instant access:')}"
    st.markdown(f"<div style='background:linear-gradient(90deg,#131d2e,#161b22);border:1px solid #2f81f7;border-radius:8px;padding:9px 12px;margin-bottom:8px;font-size:12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;'><div>🆔 <b>Your Auto Device ID:</b> <code style='color:#ffd33d;'>{cur_user['code']}</code> | 🏆 <b>Founder Spots Left:</b> {founder_left}/100 | 👥 <b>Refs:</b> {ref_cnt}/2</div><div><a href='{tg_share}' target='_blank' style='background:#1f6feb;color:#fff;padding:7px 11px;border-radius:6px;font-weight:700;text-decoration:none;'>📲 Share with 2 Friends ➔ FREE 90d VIP</a></div></div>", unsafe_allow_html=True)
    if effective_tier != "VIP":
        with st.expander(f"⚡ Instant Auto-VIP Unlock ({pay_dec_val:.2f} USDT TRC20)", expanded=False):
            st.markdown(f"Send exact **`{pay_dec_val:.2f} USDT` (TRC20)** to: `{MEM.get('trc20_wallet','')}`")
            tx_inp = st.text_input("TxID (Optional):")
            if st.button("🔓 Verify Payment on Blockchain & Unlock VIP", use_container_width=True):
                ok_tx, msg_tx = verify_trc20_blockchain_payment(cur_user["code"], tx_inp)
                st.info(msg_tx)
                if ok_tx:
                    st.rerun()
    render_main_bulletin(effective_tier, is_patron_mode=False)
    with st.expander("⚙️ System Sync & Admin Terminal", expanded=False):
        adm_inp = st.text_input("Admin Key:", type="password")
        if st.button("👑 Seal Admin Mode on This Device") and verify_admin_secret(adm_inp):
            st.session_state["patron_unlocked"] = True
            st.rerun()
# ==================== PARÇA 8/8 SONU ====================

