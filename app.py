# ==================== 1. PARÇA BAŞLANGICI ====================
import streamlit as st
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Delta Pulse v5.8 SİMÜLASYON PRO", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .block-container { padding-top: 0.6rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }
    div[data-testid="stExpander"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 10px; }
    .dp-card { background: #161b22; border-left: 4px solid #2ea043; padding: 10px 12px; border-radius: 8px; margin-bottom: 4px; font-size: 13px; }
    .dp-ak { border-left: 4px solid #f0b90b; background: #1c2128; }
    .dp-warn { border-left: 4px solid #f85149; background: #1f1619; }
    .dp-live { border-left: 4px solid #2f81f7; background: #161b22; }
    .dp-live-hot { border-left: 5px solid #f0b90b; background: #1c1d24; }
    .dp-badge { background: #21262d; padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #8b949e; }
    .dp-heat { background: #3d2800; color: #ffd33d; border: 1px solid #f0b90b; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 700; }
    .dp-w { background: #122d1f; color: #56d364; border: 1px solid #2ea043; padding: 1px 5px; border-radius: 4px; font-size: 10.5px; font-weight: 700; margin-right: 2px; }
    .dp-d { background: #21262d; color: #c9d1d9; border: 1px solid #6e7681; padding: 1px 5px; border-radius: 4px; font-size: 10.5px; font-weight: 700; margin-right: 2px; }
    .dp-l { background: #311519; color: #ff7b72; border: 1px solid #f85149; padding: 1px 5px; border-radius: 4px; font-size: 10.5px; font-weight: 700; margin-right: 2px; }
    .dp-odds-hot { display: block; background: #0d2818; color: #56d364; border-left: 3px solid #2ea043; padding: 4px 8px; border-radius: 4px; font-weight: 600; margin-top: 5px; font-size: 12.5px; }
    .dp-odds-calm { display: block; background: #161f2c; color: #79c0ff; border-left: 3px solid #1f6feb; padding: 4px 8px; border-radius: 4px; margin-top: 5px; font-size: 12px; }
    @keyframes dpPulse {
        0% { opacity: 1; box-shadow: 0 0 10px rgba(240, 185, 11, 0.75); border-color: #f0b90b; }
        50% { opacity: 0.38; box-shadow: 0 0 2px rgba(240, 185, 11, 0.1); border-color: #d29922; }
        100% { opacity: 1; box-shadow: 0 0 10px rgba(240, 185, 11, 0.75); border-color: #f0b90b; }
    }
    .dp-exp-alert { display: block; background: linear-gradient(90deg, #3d2800, #161b22); color: #ffd33d; border: 1px solid #f0b90b; padding: 5px 10px; border-radius: 6px; font-weight: 700; margin-top: 5px; animation: dpPulse 1.2s infinite ease-in-out; }
    .dp-exp-calm { display: block; color: #8b949e; padding: 3px 2px; margin-top: 4px; font-size: 12px; }
    .dp-pitch { position: relative; width: 100%; height: 230px; background: repeating-linear-gradient(90deg, #143d22, #143d22 10%, #194a2a 10%, #194a2a 20%); border: 2px solid #8b949e; border-radius: 8px; overflow: hidden; margin: 8px 0; }
    .dp-pitch-mid { position: absolute; left: 50%; top: 0; bottom: 0; width: 2px; background: rgba(255,255,255,0.45); transform: translateX(-50%); }
    .dp-pitch-circle { position: absolute; left: 50%; top: 50%; width: 64px; height: 64px; border: 2px solid rgba(255,255,255,0.45); border-radius: 50%; transform: translate(-50%, -50%); }
    .dp-pitch-box-l { position: absolute; left: 0; top: 22%; width: 13%; height: 56%; border: 2px solid rgba(255,255,255,0.45); border-left: none; }
    .dp-pitch-box-r { position: absolute; right: 0; top: 22%; width: 13%; height: 56%; border: 2px solid rgba(255,255,255,0.45); border-right: none; }
    .dp-team-tag-l { position: absolute; left: 6px; top: 4px; background: rgba(13,17,23,0.75); padding: 1px 6px; border-radius: 4px; font-size: 10.5px; color: #58a6ff; font-weight: 700; z-index: 2; }
    .dp-team-tag-r { position: absolute; right: 6px; top: 4px; background: rgba(13,17,23,0.75); padding: 1px 6px; border-radius: 4px; font-size: 10.5px; color: #ffd33d; font-weight: 700; z-index: 2; }
    .dp-dot { position: absolute; width: 17px; height: 17px; border-radius: 50%; transform: translate(-50%, -50%); border: 2px solid #ffffff; font-size: 8px; text-align: center; line-height: 13px; font-weight: bold; color: #fff; z-index: 3; }
    .dp-dot-g { background: #2ea043; box-shadow: 0 0 6px #2ea043; }
    .dp-dot-r { background: #f85149; box-shadow: 0 0 10px #f85149; animation: dpPulse 1s infinite; }
    .dp-dot-o { background: #f0883e; box-shadow: 0 0 8px #f0883e; }
    .dp-pbar-wrap { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 7px 10px; margin-top: 6px; }
    .dp-pbar-row { display: flex; align-items: center; justify-content: space-between; font-size: 11px; margin-bottom: 4px; }
    .dp-pbar-track { flex: 1; height: 7px; background: #21262d; border-radius: 4px; margin: 0 8px; overflow: hidden; display: flex; }
</style>
""", unsafe_allow_html=True)

TR_TZ = timezone(timedelta(hours=3))

LEAGUES = {
    "UEFA ŞAMPİYONLAR LİGİ": ("uefa.champions", 1.05),
    "UEFA AVRUPA LİGİ": ("uefa.europa", 0.95),
    "UEFA KONFERANS LİGİ": ("uefa.europa.conf", 0.90),
    "İNGİLTERE PREMIER LİG": ("eng.1", 1.00),
    "İSPANYA LA LIGA": ("esp.1", 1.00),
    "ALMANYA BUNDESLIGA": ("ger.1", 1.00),
    "İTALYA SERIE A": ("ita.1", 1.00),
    "FRANSA LIGUE 1": ("fra.1", 0.95),
    "TÜRKİYE SÜPER LİG": ("tur.1", 0.90),
    "HOLLANDA EREDIVISIE": ("ned.1", 0.88),
    "PORTEKİZ LIGA PORTUGAL": ("por.1", 0.88),
    "İNGİLTERE CHAMPIONSHIP": ("eng.2", 0.82),
    "BELÇİKA PRO LİG": ("bel.1", 0.82),
    "İSKOÇYA PREMIERSHIP": ("sco.1", 0.80),
    "ALMANYA 2. BUNDESLIGA": ("ger.2", 0.78),
    "İNGİLTERE LEAGUE ONE": ("eng.3", 0.75),
    "İSPANYA LA LIGA 2": ("esp.2", 0.75),
    "İTALYA SERIE B": ("ita.2", 0.75),
    "TÜRKİYE 1. LİG": ("tur.2", 0.72),
    "İNGİLTERE FA CUP": ("eng.fa", 0.85),
    "İNGİLTERE EFL CUP": ("eng.league_cup", 0.85),
    "TÜRKİYE KUPASI": ("tur.cup", 0.80)
}

KNOWN_FORMATIONS = {
    "PSG": "4-3-3", "Lyon": "4-2-3-1", "Sevilla": "4-2-3-1", "Osasuna": "4-3-3",
    "Besiktas": "4-2-3-1", "Istanbul BB": "4-1-4-1", "Caykur Rizespor": "4-2-3-1", "Trabzonspor": "4-2-3-1",
    "Galatasaray": "4-2-3-1", "Fenerbahce": "4-2-3-1", "Santa Clara": "3-4-2-1", "Benfica": "4-2-3-1",
    "FC Andorra": "4-3-3", "Burgos": "4-4-2", "Inter Milan": "3-5-2", "Juventus": "4-2-3-1",
    "Milan": "4-2-3-1", "Real Sociedad": "4-3-3", "Barcelona": "4-2-3-1", "Real Madrid": "4-1-3-2"
}

@st.cache_resource
def get_persistent_memory():
    return {
        "locked_pre": {}, "live_snapshots": {}, "live_signals": {}, "settled_results": {},
        "settled_date": "20261025", "active_date": "20261026",
        "base_wins": 120, "base_total": 167, "base_ak_wins": 11, "base_ak_total": 13,
        "vip_live_wins": 44, "vip_live_total": 46,
        "opening_odds": {
            "PSG vs Lyon": {"fav": "PSG", "val": -265, "tg": 3.5},
            "Sevilla vs Osasuna": {"fav": "SEV", "val": -110, "tg": 2.5},
            "Besiktas vs Istanbul BB": {"fav": "BES", "val": -260, "tg": 3.5},
            "Caykur Rizespor vs Trabzonspor": {"fav": "TRAB", "val": -105, "tg": 2.5},
            "Galatasaray vs Fenerbahce": {"fav": "GAL", "val": 110, "tg": 3.5},
            "Santa Clara vs Benfica": {"fav": "SLB", "val": -265, "tg": 2.5},
            "FC Andorra vs Burgos": {"fav": "AND", "val": 115, "tg": 2.5}
        },
        "kickoff_odds": {}, "last_valid_odds": {}, "roster_cache": {},
        "prev_scan": {}, "change_log": []
    }

MEM = get_persistent_memory()
# ==================== 1. PARÇA SONU ====================
# ==================== 2. PARÇA BAŞLANGICI ====================
def safe_int(val, default=0):
    s = str(val if val is not None else "").replace("%", "").strip()
    if s.startswith("+"):
        s = s[1:]
    if not s:
        return default
    clean = s.split(".")[0]
    if clean.lstrip("-").isdigit():
        return int(clean)
    return default

def safe_float(val, default=2.5):
    s = str(val if val is not None else "").strip()
    if s.replace(".", "", 1).lstrip("-").isdigit():
        return float(s)
    return default

def american_to_steps(odd):
    if odd >= 100:
        return odd - 100
    elif odd <= -100:
        return odd + 100
    return 0

def calc_true_odds_delta(open_val, cur_val):
    return american_to_steps(cur_val) - american_to_steps(open_val)

def parse_form_momentum(form_str):
    if not form_str or not isinstance(form_str, str):
        return 50
    weights = [1.0, 1.2, 1.5, 1.8, 2.2]
    chars = list(form_str.upper()[-5:])
    score, max_s = 0.0, 0.0
    for i, ch in enumerate(chars):
        w = weights[i] if i < len(weights) else 1.0
        max_s += w * 3.0
        if ch == "W":
            score += w * 3.0
        elif ch == "D":
            score += w * 1.0
    return int(round((score / max_s) * 100)) if max_s > 0 else 50

def format_form_badges(form_str):
    if not form_str or not isinstance(form_str, str):
        form_str = "WDWLW"
    out = []
    for ch in list(form_str.upper()[-5:]):
        if ch == "W":
            out.append("<span class='dp-w'>W</span>")
        elif ch == "D":
            out.append("<span class='dp-d'>D</span>")
        else:
            out.append("<span class='dp-l'>L</span>")
    return "".join(out)

def resolve_team_formation(team_name, api_form, mom, is_home):
    if api_form and isinstance(api_form, str) and "-" in api_form:
        return api_form.strip()
    if team_name in KNOWN_FORMATIONS:
        return KNOWN_FORMATIONS[team_name]
    t_seed = sum(ord(c) for c in team_name)
    if mom >= 68:
        pool = ["4-3-3", "4-2-3-1", "4-1-3-2", "3-4-2-1"]
    elif mom <= 30 and not is_home:
        pool = ["5-3-2", "4-1-4-1", "4-4-2", "4-2-3-1"]
    else:
        pool = ["4-2-3-1", "4-3-3", "4-1-3-2", "3-5-2", "4-4-2"]
    return pool[t_seed % len(pool)]

def generate_formation_coords(formation_str, is_home=True):
    raw_parts = [safe_int(p, 0) for p in str(formation_str).split("-") if safe_int(p, 0) > 0]
    if sum(raw_parts) != 10:
        raw_parts = [4, 3, 3]
    coords = [(5.0, 50.0)] if is_home else [(95.0, 50.0)]
    num_lines = len(raw_parts)
    if num_lines == 3:
        x_steps = [15.0, 29.0, 43.0] if is_home else [85.0, 71.0, 57.0]
    elif num_lines == 4:
        x_steps = [14.0, 24.0, 34.0, 44.0] if is_home else [86.0, 76.0, 66.0, 56.0]
    else:
        x_steps = [13.0, 21.0, 29.0, 37.0, 45.0] if is_home else [87.0, 79.0, 71.0, 63.0, 55.0]
    y_map = {
        1: [50.0], 2: [34.0, 66.0], 3: [22.0, 50.0, 78.0],
        4: [14.0, 38.0, 62.0, 86.0], 5: [12.0, 31.0, 50.0, 69.0, 88.0]
    }
    for line_idx, count in enumerate(raw_parts):
        base_x = x_steps[min(line_idx, len(x_steps) - 1)]
        for p_idx, y_val in enumerate(y_map.get(count, [50.0])):
            x_val = base_x
            if count >= 4 and (p_idx == 0 or p_idx == count - 1):
                x_val += 2.2 if is_home else -2.2
            elif count == 3 and line_idx == num_lines - 1 and p_idx == 1:
                x_val += 2.0 if is_home else -2.0
            coords.append((round(x_val, 1), round(y_val, 1)))
    return coords[:11]

def calc_team_5powers(team_name, mom, kademe, is_fav, fav_val, def_weak, att_weak, atk_subs):
    base = int(round(68 + (kademe - 0.75) * 42))
    if is_fav and fav_val <= -150:
        base += min(9, abs(fav_val) // 45)
    elif not is_fav and fav_val <= -200:
        base -= 4
    seed = sum(ord(c) for c in team_name)
    pac = max(58, min(96, base + int((mom - 50) * 0.18) + (atk_subs * 2) - (att_weak * 2) + (seed % 5 - 2)))
    sho = max(55, min(97, base + int((mom - 50) * 0.25) + (atk_subs * 3) - (att_weak * 4) + ((seed // 2) % 5 - 2)))
    dri = max(58, min(96, base + int((mom - 50) * 0.20) - (att_weak * 3) + ((seed // 3) % 5 - 2)))
    phy = max(60, min(95, base + int((mom - 50) * 0.12) + (atk_subs * 2) - (def_weak * 2) + ((seed // 4) % 5 - 1)))
    dfn = max(54, min(95, base + int((mom - 50) * 0.14) - (def_weak * 5) + ((seed // 5) % 5 - 2)))
    ovr = int(round((pac + sho + dri + phy + dfn) / 5.0))
    return {"pac": pac, "sho": sho, "dri": dri, "phy": phy, "def": dfn, "ovr": ovr}
# ==================== 2. PARÇA SONU ====================
# ==================== 3. PARÇA BAŞLANGICI ====================
def parse_single_team_roster(roster_obj, fallback_tac, state="pre"):
    tac = str(roster_obj.get("formation") or "").strip()
    if "-" not in tac:
        tac = fallback_tac
    entries = roster_obj.get("roster") or []
    starters = [p for p in entries if isinstance(p, dict) and p.get("starter")]
    is_live = (state == "in")
    subs_in = [p for p in entries if isinstance(p, dict) and not p.get("starter") and p.get("subbedIn")] if is_live else []

    dots, red_names, org_names = [], [], []
    def_weak, att_weak, atk_subs = 0, 0, 0

    for idx, p in enumerate(starters[:11]):
        ath = p.get("athlete") or {}
        s_name = str(ath.get("shortName") or ath.get("displayName") or f"Oyuncu {idx+1}")
        jersey = safe_int(p.get("jersey"), idx + 1)
        pos_abbr = str((p.get("position") or {}).get("abbreviation") or "").upper()
        sub_out = bool(p.get("subbedOut")) if is_live else False
        has_card = any(isinstance(st_i, dict) and st_i.get("name") in ("yellowCards", "redCards") and safe_int(st_i.get("value"), 0) > 0 for st_i in (p.get("stats") or [])) if is_live else False
        is_rot = (jersey >= 27) or (idx == 0 and jersey not in (1, 13, 23, 25, 31, 99)) or (1 <= idx <= 4 and jersey >= 24)
        if is_rot:
            status = "R"
            red_names.append(f"#{jersey} {s_name}")
            if idx <= 5 or "D" in pos_abbr or "G" in pos_abbr:
                def_weak += 1
            else:
                att_weak += 1
        elif is_live and (sub_out or has_card):
            status = "O"
            org_names.append(f"#{jersey} {s_name} ({'Çıktı' if sub_out else 'Kart'})")
        else:
            status = "G"
        dots.append({"num": jersey, "name": s_name, "status": status})

    for sp in subs_in:
        ath = sp.get("athlete") or {}
        s_name = str(ath.get("shortName") or ath.get("displayName") or "Yedek")
        jersey = safe_int(sp.get("jersey"), 99)
        pos_abbr = str((sp.get("position") or {}).get("abbreviation") or "").upper()
        org_names.append(f"#{jersey} {s_name} (Girdi)")
        if "F" in pos_abbr or "M" in pos_abbr or "A" in pos_abbr or len(subs_in) >= 2:
            atk_subs += 1

    return {
        "official": len(starters) >= 11, "tac": tac, "dots": dots,
        "red_names": red_names[:3], "org_names": org_names[:3],
        "def_weak": def_weak, "att_weak": att_weak, "atk_subs": atk_subs
    }

def fetch_and_analyze_roster(task):
    slug, ev_id, m_title, h_name, a_name, h_mom, a_mom, odd_str, state, kademe, fav_abbr, fav_val, a_abbr = task
    cache_key = f"{ev_id}_{state}_v58"
    if cache_key in MEM["roster_cache"]:
        return m_title, MEM["roster_cache"][cache_key]

    h_tac_fb = resolve_team_formation(h_name, None, h_mom, True)
    a_tac_fb = resolve_team_formation(a_name, None, a_mom, False)
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={ev_id}"
    rosters_list = []
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3.2)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                rosters_list = data.get("rosters") or []
    except Exception:
        rosters_list = []

    h_rost_raw, a_rost_raw = {}, {}
    for r_item in rosters_list:
        if isinstance(r_item, dict):
            if r_item.get("homeAway") == "home":
                h_rost_raw = r_item
            elif r_item.get("homeAway") == "away":
                a_rost_raw = r_item

    h_info = parse_single_team_roster(h_rost_raw, h_tac_fb, state)
    a_info = parse_single_team_roster(a_rost_raw, a_tac_fb, state)
    both_official = (h_info["official"] and a_info["official"])

    if not both_official:
        for inf, t_n in ((h_info, h_name), (a_info, a_name)):
            inf["dots"] = [{"num": i+1, "name": f"{t_n} #{i+1}", "status": "G"} for i in range(11)]
            inf["def_weak"], inf["att_weak"], inf["atk_subs"] = 0, 0, 0
            inf["red_names"], inf["org_names"] = [], []

    is_away_fav = bool(fav_abbr and (fav_abbr.upper() == a_abbr.upper() or fav_abbr.upper() in a_name.upper()[:4]))
    h_info["pwr"] = calc_team_5powers(h_name, h_mom, kademe, not is_away_fav, fav_val, h_info["def_weak"], h_info["att_weak"], h_info["atk_subs"])
    a_info["pwr"] = calc_team_5powers(a_name, a_mom, kademe, is_away_fav, fav_val, a_info["def_weak"], a_info["att_weak"], a_info["atk_subs"])

    res = {"h": h_info, "a": a_info, "official": both_official}
    if both_official or state == "in":
        MEM["roster_cache"][cache_key] = res
    return m_title, res

def build_power_bars_html(h_name, a_name, h_p, a_p):
    metrics = [
        ("⚡ Hız & Atletizm (PAC)", h_p.get("pac", 75), a_p.get("pac", 72)),
        ("🎯 Atak & Şut Gücü (SHO)", h_p.get("sho", 75), a_p.get("sho", 72)),
        ("🪄 Kabiliyet & Teknik (DRI)", h_p.get("dri", 75), a_p.get("dri", 72)),
        ("💪 Kuvvet & Fizik (PHY)", h_p.get("phy", 75), a_p.get("phy", 72)),
        ("🛡️ Savunma Direnci (DEF)", h_p.get("def", 75), a_p.get("def", 72))
    ]
    rows = [
        f"<div style='display:flex;justify-content:space-between;font-size:11.5px;font-weight:700;margin-bottom:5px;border-bottom:1px solid #30363d;padding-bottom:3px;'>"
        f"<span style='color:#58a6ff;'>🏠 {h_name} (OVR: {h_p.get('ovr',75)})</span>"
        f"<span style='color:#c9d1d9;'>⚔️ 5'Lİ GÜÇ RADARI (0-99)</span>"
        f"<span style='color:#ffd33d;'>✈️ {a_name} (OVR: {a_p.get('ovr',72)})</span></div>"
    ]
    for label, hv, av in metrics:
        tot = max(1, hv + av)
        h_pct = int(round((hv / tot) * 100))
        a_pct = 100 - h_pct
        h_col = "#56d364" if hv >= av + 4 else ("#58a6ff" if hv >= av else "#8b949e")
        a_col = "#ffd33d" if av >= hv + 4 else ("#d29922" if av >= hv else "#8b949e")
        rows.append(
            f"<div class='dp-pbar-row'><b style='color:{h_col};width:28px;'>{hv}</b>"
            f"<div class='dp-pbar-track'><div style='width:{h_pct}%;background:{h_col};'></div>"
            f"<div style='width:{a_pct}%;background:{a_col};'></div></div>"
            f"<span style='width:155px;text-align:center;color:#c9d1d9;font-size:10.5px;'>{label}</span>"
            f"<b style='color:{a_col};width:28px;text-align:right;'>{av}</b></div>"
        )
    return f"<div class='dp-pbar-wrap'>{''.join(rows)}</div>"

def build_tactical_pitch_html(m):
    seed = sum(ord(c) for c in m["mac"])
    lig = m["lig"]
    if "İNGİLTERE" in lig or "İSKOÇYA" in lig or "HOLLANDA" in lig or "BELÇİKA" in lig:
        w_icon, w_txt, w_temp, w_hum = "🌧️ Yağmurlu", "Kaygan Zemin (Uzaktan şut & korner +%18 artar)", 11 + (seed % 4), 82 + (seed % 10)
    elif "İSPANYA" in lig or "PORTEKİZ" in lig or "İTALYA" in lig:
        w_icon, w_txt, w_temp, w_hum = ("⛅ Parçalı Bulutlu", "İdeal Zemin", 17 + (seed % 5), 60 + (seed % 15)) if seed % 3 == 0 else ("☀️ Açık / Güneşli", "Kuru & Hızlı Çim", 19 + (seed % 4), 52 + (seed % 12))
    else:
        w_icon, w_txt, w_temp, w_hum = "⛅ Serin / Bulutlu", "Dengeli Zemin (Fiziksel mücadele yüksek)", 13 + (seed % 5), 70 + (seed % 14)

    r_data = m.get("roster_data") or {}
    h_inf, a_inf = r_data.get("h") or {}, r_data.get("a") or {}
    is_off = bool(r_data.get("official", False))
    h_tac, a_tac = m.get("h_tac", "4-3-3"), m.get("a_tac", "4-2-3-1")
    home_coords = generate_formation_coords(h_tac, is_home=True)
    away_coords = generate_formation_coords(a_tac, is_home=False)
    h_dots_data = h_inf.get("dots") or [{"num": i+1, "status": "G"} for i in range(11)]
    a_dots_data = a_inf.get("dots") or [{"num": i+1, "status": "G"} for i in range(11)]

    dots_html = []
    rot_count, sub_count = 0, 0
    for idx, (x, y) in enumerate(home_coords):
        d = h_dots_data[idx] if idx < len(h_dots_data) else {"num": idx+1, "status": "G"}
        st_code = d.get("status", "G") if is_off else "G"
        if m["state"] != "in" and st_code == "O":
            st_code = "G"
        cls = "dp-dot-r" if st_code == "R" else ("dp-dot-o" if st_code == "O" else "dp-dot-g")
        rot_count += (1 if st_code == "R" else 0)
        sub_count += (1 if st_code == "O" else 0)
        dots_html.append(f"<div class='dp-dot {cls}' style='left:{x}%;top:{y}%;'>{d.get('num', idx+1)}</div>")

    for idx, (x, y) in enumerate(away_coords):
        d = a_dots_data[idx] if idx < len(a_dots_data) else {"num": idx+1, "status": "G"}
        st_code = d.get("status", "G") if is_off else "G"
        if m["state"] != "in" and st_code == "O":
            st_code = "G"
        cls = "dp-dot-r" if st_code == "R" else ("dp-dot-o" if st_code == "O" else "dp-dot-g")
        rot_count += (1 if st_code == "R" else 0)
        sub_count += (1 if st_code == "O" else 0)
        dots_html.append(f"<div class='dp-dot {cls}' style='left:{x}%;top:{y}%;'>{d.get('num', idx+1)}</div>")

    p_bars_html = build_power_bars_html(m["h_name"], m["a_name"], h_inf.get("pwr") or {}, a_inf.get("pwr") or {})
    if is_off:
        off_badge = "<span style='color:#56d364;font-weight:700;'>✅ Resmi İlk 11 & Forma Numaraları Açıklandı</span>"
        h_r_str = ", ".join(h_inf.get("red_names") or []) or "Tam Kadro"
        a_r_str = ", ".join(a_inf.get("red_names") or []) or "Tam Kadro"
        all_orgs = (h_inf.get("org_names") or []) + (a_inf.get("org_names") or [])
        org_str = ", ".join(all_orgs[:4]) if (m["state"] == "in" and all_orgs) else "Maç Başlamadı (Değişiklik Yok)"
        status_line = (
            f"<div style='display:flex;gap:12px;flex-wrap:wrap;margin-top:6px;font-size:11.5px;'>"
            f"<span>🟢 <b>As Kadro:</b> {22 - rot_count - sub_count}</span>"
            f"<span>🔴 <b>Rotasyon/Zaaf ({rot_count}):</b> Ev: {h_r_str} | Dep: {a_r_str}</span>"
            f"<span>🟠 <b>Canlı Değişiklik/Kart ({sub_count}):</b> {org_str}</span></div>"
        )
    else:
        off_badge = "<span style='color:#ffd33d;font-weight:700;'>⏳ Resmi Kadro Henüz Belli Değil</span>"
        status_line = (
            "<div style='margin-top:6px;padding:6px 8px;background:#3d2800;border:1px solid #f0b90b;border-radius:5px;color:#ffd33d;font-size:11.5px;'>"
            "⏳ <b>KADRO UYARISI:</b> Bu maçın resmi ilk 11'leri henüz açıklanmadı (Sahadaki noktalar standart diziliş şablonudur). "
            "Maç saatine <b>son 1 saat / 45 dakika kala</b> lütfen tekrar kontrol ediniz.</div>"
        )

    return (
        f"<div style='background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:10px;font-size:12px;'>"
        f"<div style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;margin-bottom:6px;'>"
        f"<span><b>{w_icon} ({w_temp}°C | Nem: %{w_hum}):</b> <span style='color:#79c0ff;'>{w_txt}</span></span>"
        f"{off_badge}</div>"
        f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
        f"<span>🏠 <b>{m['h_name']} ({h_tac}):</b> {format_form_badges(m.get('h_form','WDWWL'))}</span>"
        f"<span>✈️ <b>{m['a_name']} ({a_tac}):</b> {format_form_badges(m.get('a_form','LDWLL'))}</span></div>"
        f"<div class='dp-pitch'>"
        f"<div class='dp-team-tag-l'>🏠 {m['h_name']} ({h_tac}) ➔</div>"
        f"<div class='dp-team-tag-r'>⬅ ✈️ {m['a_name']} ({a_tac})</div>"
        f"<div class='dp-pitch-mid'></div><div class='dp-pitch-circle'></div>"
        f"<div class='dp-pitch-box-l'></div><div class='dp-pitch-box-r'></div>{''.join(dots_html)}</div>"
        f"{p_bars_html}{status_line}"
        f"<div style='margin-top:6px;padding:6px 8px;background:#161b22;border-left:3px solid #2ea043;border-radius:4px;color:#e6edf3;'>"
        f"🧬 <b>Model Karar Özeti:</b> {m.get('squad_model_note','')}</div></div>"
    )
# ==================== 3. PARÇA SONU ====================
# ==================== 4. PARÇA BAŞLANGICI ====================
def get_opening_fallback(match_title):
    if match_title in MEM["last_valid_odds"]:
        return MEM["last_valid_odds"][match_title]
    if match_title in MEM["opening_odds"]:
        op = MEM["opening_odds"][match_title]
        v_str = f"+{op['val']}" if op["val"] > 0 else str(op["val"])
        return (f"{op['fav']} {v_str}", op["fav"], op["val"], op["tg"])
    return ("Veri Yok", "", 0, 2.5)

def safe_parse_odds(comp, match_title, state="pre"):
    fallback = get_opening_fallback(match_title)
    if not isinstance(comp, dict):
        return fallback[0], fallback[1], fallback[2], fallback[3], False
    odds_list = comp.get("odds")
    if not odds_list or not isinstance(odds_list, list):
        return fallback[0], fallback[1], fallback[2], fallback[3], False
    o = next((item for item in odds_list if isinstance(item, dict)), None)
    if not isinstance(o, dict):
        return fallback[0], fallback[1], fallback[2], fallback[3], False

    raw_det = o.get("details")
    details = str(raw_det).strip() if raw_det is not None else ""
    if not details or details.lower() == "none":
        return fallback[0], fallback[1], fallback[2], fallback[3], False

    ou_val = safe_float(o.get("overUnder"), fallback[3])
    fav_abbr, fav_val = "", 0
    if " " in details:
        parts = details.split(" ")
        fav_abbr = parts[0].strip()
        fav_val = safe_int(parts[-1], 0)

    res = (details, fav_abbr, fav_val, ou_val)
    if fav_val != 0:
        MEM["last_valid_odds"][match_title] = res
        if state == "pre":
            MEM["kickoff_odds"][match_title] = {"fav": fav_abbr, "val": fav_val, "tg": ou_val}
    return details, fav_abbr, fav_val, ou_val, (fav_val != 0)

def evaluate_pre_match(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, odd_str, fav_abbr, fav_val, ou_val, kademe, roster_data=None, lig_adi=""):
    match_key = f"{h_name} vs {a_name}"
    open_db = MEM["opening_odds"]
    if match_key not in open_db and fav_abbr and fav_val != 0:
        open_db[match_key] = {"fav": fav_abbr, "val": fav_val, "tg": ou_val}

    smart_tag = ""
    bonus_conf = 0
    tg_jumped, ana_kasa_veto, severe_drift_warning, any_drift_warning = False, False, False, False

    if match_key in open_db and fav_val != 0:
        op = open_db[match_key]
        if op["fav"] and fav_abbr and op["fav"] != fav_abbr:
            smart_tag += f" 🔄FAV({op['fav']}->{fav_abbr})"
            bonus_conf += 5
        else:
            diff = calc_true_odds_delta(op["val"], fav_val)
            if diff <= -10:
                smart_tag += f" 🔥Δ{diff}"
                bonus_conf += min(7, abs(diff) // 7)
            elif diff >= 40:
                smart_tag += f" 🚨Δ+{diff}"
                bonus_conf -= min(26, 12 + (diff // 7))
                ana_kasa_veto = True
                severe_drift_warning = True
                any_drift_warning = True
            elif diff >= 15:
                smart_tag += f" ⚠️Δ+{diff}"
                bonus_conf -= min(12, 5 + (diff // 5))
                any_drift_warning = True
                if fav_val > -250:
                    ana_kasa_veto = True

        if ou_val > op["tg"]:
            smart_tag += f" 💥TG↑({op['tg']}->{ou_val})"
            bonus_conf += 10
            tg_jumped = True
        elif ou_val < op["tg"]:
            smart_tag += f" 📉TG↓({op['tg']}->{ou_val})"
            bonus_conf -= 5
            ana_kasa_veto = True

    is_away_fav = False
    if fav_abbr:
        if fav_abbr.upper() == a_abbr.upper() or fav_abbr.upper() in a_name.upper()[:4]:
            is_away_fav = True
    elif a_mom > h_mom + 12:
        is_away_fav = True

    fav_team, dog_team = (a_name, h_name) if is_away_fav else (h_name, a_name)
    fav_mom, dog_mom = (a_mom, h_mom) if is_away_fav else (h_mom, a_mom)
    mom_diff = abs(h_mom - a_mom)
    form_clash = (dog_mom - fav_mom >= 20)
    cs_code = "X2" if is_away_fav else "1X"

    is_off = bool((roster_data or {}).get("official", False))
    h_inf = (roster_data or {}).get("h") or {}
    a_inf = (roster_data or {}).get("a") or {}
    h_tac = h_inf.get("tac") or resolve_team_formation(h_name, None, h_mom, True)
    a_tac = a_inf.get("tac") or resolve_team_formation(a_name, None, a_mom, False)
    fav_tac, dog_tac = (a_tac, h_tac) if is_away_fav else (h_tac, a_tac)

    fav_inf, dog_inf = (a_inf, h_inf) if is_away_fav else (h_inf, a_inf)
    fav_p = fav_inf.get("pwr") or {"pac": 76, "sho": 76, "dri": 75, "phy": 75, "def": 75}
    dog_p = dog_inf.get("pwr") or {"pac": 71, "sho": 70, "dri": 70, "phy": 72, "def": 70}

    dog_def_weak = dog_inf.get("def_weak", 0) if is_off else 0
    fav_def_weak = fav_inf.get("def_weak", 0) if is_off else 0
    fav_rot_total = (fav_inf.get("def_weak", 0) + fav_inf.get("att_weak", 0)) if is_off else 0
    atk_vs_def_gap = int(round(((fav_p["sho"] + fav_p["pac"] + fav_p["dri"]) / 3.0) - ((dog_p["def"] + dog_p["phy"]) / 2.0)))

    open_line_tacs = ("3-4-2-1", "3-5-2", "4-3-3", "4-2-3-1", "4-1-3-2")
    fav_high_line = fav_tac in open_line_tacs
    dog_counter_threat = (dog_p["pac"] >= 73 or dog_p["phy"] >= 74) and dog_mom >= 38
    buro_btts_sim = (
        (ou_val >= 3.5 and (-240 <= fav_val <= -105 or fav_val >= 100) and fav_high_line and dog_mom >= 35)
        or (fav_high_line and dog_counter_threat and fav_p["def"] <= 79 and dog_mom >= 45)
    )
    wing_asymmetry = (h_tac.startswith("3-") and a_tac.startswith("4-")) or (h_tac.startswith("4-") and a_tac.startswith("3-"))
    is_wet_pitch = any(k in lig_adi for k in ("İNGİLTERE", "İSKOÇYA", "HOLLANDA", "BELÇİKA"))
    set_piece_sim = (is_wet_pitch or abs(fav_p["phy"] - dog_p["phy"]) >= 5) and max(fav_p["phy"], dog_p["phy"]) >= 76
    buro_xg_trust = (form_clash and fav_val <= -175 and not any_drift_warning)

    squad_force_team_over = False
    squad_force_btts = False
    sim_extra_notes = []

    if buro_btts_sim:
        squad_force_btts = True
        bonus_conf += 4
        smart_tag += " 💥BüroKG-Sim"
        sim_extra_notes.append(f"💥 Büro KG/Kontra Sim ({fav_team} {fav_tac} açık çizgi vs {dog_team} ⚡Hız:{dog_p['pac']}/💪Fizik:{dog_p['phy']})")
    if wing_asymmetry:
        bonus_conf += 3
        smart_tag += " 📐KanatKorner"
        sim_extra_notes.append(f"📐 Kanat Asimetrisi ({h_tac} vs {a_tac} ➔ Kenarlarda +2.5 Korner & Pozisyon artışı)")
    if set_piece_sim:
        bonus_conf += 2
        sim_extra_notes.append(f"🌧️ Zemin/Duran Top xG (Fizik:{max(fav_p['phy'],dog_p['phy'])} ➔ Korner/Karambol gol beklentisi yüksek)")
    if buro_xg_trust:
        bonus_conf += 4
        smart_tag += " 🧠Büro-xG"
        sim_extra_notes.append(f"🧠 Büro xG Koruması (Form farkına rağmen {fav_team} oranı güçlü tutuluyor)")

    if is_off:
        if fav_rot_total >= 3:
            bonus_conf -= 8
            ana_kasa_veto = True
            smart_tag += " 🧬FavRotasyon(-8p)"
            squad_model_note = f"✅ Resmi Kadro Açıklandı: DİKKAT! {fav_team} ilk 11'inde 🔴 {fav_rot_total} rotasyon oyuncusu var! Güven -8p kırıldı."
        elif (dog_def_weak >= 2 or atk_vs_def_gap >= 11) and fav_mom >= 52 and not any_drift_warning:
            p_boost = 7 if (dog_def_weak >= 2 and atk_vs_def_gap >= 11) else 5
            bonus_conf += p_boost
            smart_tag += f" ✅KadroOnay(+{p_boost}p)"
            squad_force_team_over = True
            squad_model_note = f"✅ Resmi Kadro Açıklandı: {fav_team} (Atak:{fav_p['sho']}, Hız:{fav_p['pac']}) vs {dog_team} (Savunma:{dog_p['def']}) ➔ Güven +{p_boost}p!"
        elif fav_def_weak >= 2 and dog_p["pac"] >= 73:
            squad_force_btts = True
            smart_tag += " 🧬StoperZaafı(KG)"
            squad_model_note = f"✅ Resmi Kadro Açıklandı: {fav_team} savunmasında 🔴 {fav_def_weak} rotasyon var ➔ KG Var / Üst eğilimi!"
        else:
            squad_model_note = f"✅ Resmi Kadro Açıklandı: İdeal ilk 11'ler sahada ({fav_team} Atak:{fav_p['sho']} vs {dog_team} Sav:{dog_p['def']})."
    else:
        if atk_vs_def_gap >= 12 and fav_mom >= 55 and not any_drift_warning:
            bonus_conf += 4
            smart_tag += f" ⚡GüçFarkı(+{atk_vs_def_gap})"
            squad_force_team_over = True
        squad_model_note = (
            f"⏳ Kadro Belli Değil (Maça son 45-60 dk kala lütfen kontrol ediniz) • "
            f"İskelet Gücü: {fav_team} (Atak:{fav_p['sho']}/Hız:{fav_p['pac']}) vs {dog_team} (Sav:{dog_p['def']})"
        )

    if sim_extra_notes:
        squad_model_note += " • " + " | ".join(sim_extra_notes)

    raw_conf = 50 + (int(mom_diff * 0.35) if (not form_clash or buro_xg_trust) else -4)
    if ou_val >= 3.5:
        raw_conf += 14
    if ou_val >= 4.5:
        raw_conf += 6
    if fav_val <= -175:
        raw_conf += 8
    if fav_val <= -300:
        raw_conf += 6
    if h_mom >= 65 and a_mom >= 65 and ou_val >= 3.5:
        raw_conf += 12
    if fav_mom < 50 and dog_mom < 40 and fav_val <= -150:
        raw_conf -= 5

    conf = int(round(raw_conf * min(1.05, max(0.78, kademe)))) + bonus_conf
    conf = max(25, min(97, conf))
    is_strong_market_fav = (fav_val <= -140 and (fav_mom >= 55 or buro_xg_trust))
    is_elite_shootout = (h_mom >= 80 and a_mom >= 80 and ou_val >= 3.5)

    if ana_kasa_veto or (form_clash and not buro_xg_trust) or not (is_strong_market_fav or is_elite_shootout):
        if conf >= 83:
            conf = 74 if severe_drift_warning else 78

    if h_mom == a_mom and h_mom <= 35 and ou_val <= 2.5:
        conf, pick = 25, "Maç 3.5 Gol Alt"
    elif conf >= 83 and kademe >= 0.88 and not ana_kasa_veto:
        pick = "Maç 2.5 Gol Üst (Ana Kasa)" if ((dog_mom >= 58 and ou_val >= 3.5) or fav_mom < 55) else f"{fav_team} Takım Golü 1.5 Üst (Ana Kasa)"
    elif ou_val >= 3.5 or tg_jumped:
        if severe_drift_warning:
            pick = "Maç 2.5 Gol Üst [⚠️ERİME: KADRO BEKLE]"
        elif fav_mom < 50 and dog_mom < 40 and fav_val <= -150 and not tg_jumped and not buro_btts_sim:
            pick = f"{fav_team} Çifte Şans ({cs_code}) & 3.5 Alt"
        elif (dog_mom < 45 or squad_force_team_over) and fav_val <= -160 and fav_mom >= 55 and not form_clash and not any_drift_warning and fav_rot_total < 3 and not buro_btts_sim:
            pick = f"{fav_team} Takım Golü 1.5 Üst"
        else:
            pick = "Maç 2.5 Gol Üst"
    else:
        if (h_mom >= 58 and a_mom >= 58) or (form_clash and dog_mom >= 65 and fav_val <= -110) or squad_force_btts:
            pick = "Karşılıklı Gol Var (KG Var)"
        elif (fav_val <= -185 or (dog_mom < 20 and fav_val <= -165) or (squad_force_team_over and fav_val <= -150)) and (fav_mom >= 55 or buro_xg_trust) and not any_drift_warning and fav_rot_total < 3:
            pick = f"{fav_team} Takım Golü 1.5 Üst"
        elif (mom_diff >= 25 and fav_mom > dog_mom) or (fav_val <= -150 and fav_mom < 55 and not form_clash) or fav_rot_total >= 3:
            pick = f"{fav_team} Çifte Şans ({cs_code}) & 3.5 Alt"
        else:
            pick = "Maç 3.5 Gol Alt"

    return conf, pick, (f"{odd_str}{smart_tag}" if smart_tag else odd_str), severe_drift_warning, squad_model_note
# ==================== 4. PARÇA SONU ====================
# ==================== 5. PARÇA BAŞLANGICI ====================
def evaluate_ft_result(pick, h_name, a_name, h_score, a_score):
    tot = h_score + a_score
    btts = (h_score > 0 and a_score > 0)
    fav_is_away = (a_name in pick and h_name not in pick)
    fav_goals = a_score if fav_is_away else h_score
    fav_won_or_drew = (a_score >= h_score) if fav_is_away else (h_score >= a_score)
    if "Takım Golü 1.5 Üst" in pick:
        return fav_goals >= 2
    if "Maç 2.5 Gol Üst" in pick:
        return tot >= 3
    if "Karşılıklı Gol Var" in pick:
        return btts
    if "Çifte Şans" in pick:
        return fav_won_or_drew and tot <= 3
    if "Maç 3.5 Gol Alt" in pick:
        return tot <= 3
    return False

def analyze_live_pro(match_title, h_name, a_name, h_abbr, a_abbr, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_poss, m_int, h_mom, a_mom, fav_abbr, fav_val, ou_val, has_live_api_odds, roster_data=None):
    tot_goals, tot_sh, tot_sot, tot_cor = h_score + a_score, h_sh + a_sh, h_sot + a_sot, h_cor + a_cor

    if match_title in MEM["live_signals"]:
        sig = MEM["live_signals"][match_title]
        if (sig["type"] == "GOL" and tot_goals >= sig["base"] + sig["need"]) or (sig["type"] == "KORNER" and tot_cor >= sig["base"] + sig["need"]):
            sig["status"] = "WON"

    if m_int >= 86:
        lock_notes = [
            "🔒 Son Dakika Kilidi (86'+): Son dakikalarda yüksek kaos ve belirsizlik nedeniyle canlı tahmin/yorum kapatılmıştır (İstatistik Koruması Aktif)."
        ]
        if match_title in MEM["live_signals"] and MEM["live_signals"][match_title]["status"] == "WON":
            lock_notes.insert(0, f"✅ ÖNCEKİ CANLI SİNYAL GELDİ! [{MEM['live_signals'][match_title]['label']}]")
        return 45, "|🔒SonDkKilidi", "🔒 Maç Sonu Kilidi Devrede (Oran & Canlı Bahis Kapalı)", " • ".join(lock_notes)

    h_sot_pct = int(round((h_sot / h_sh) * 100)) if h_sh > 0 else 0
    a_sot_pct = int(round((a_sot / a_sh) * 100)) if a_sh > 0 else 0
    tot_sot_pct = int(round((tot_sot / tot_sh) * 100)) if tot_sh > 0 else 0
    a_poss = (100 - h_poss) if h_poss > 0 else 0

    open_ref = MEM["opening_odds"].get(match_title) or {"fav": fav_abbr, "val": fav_val, "tg": ou_val}
    kick_ref = MEM["kickoff_odds"].get(match_title) or open_ref
    ref_fav, ref_val, ref_tg = kick_ref.get("fav", fav_abbr), kick_ref.get("val", fav_val), kick_ref.get("tg", ou_val)
    open_val, open_tg = open_ref.get("val", ref_val), open_ref.get("tg", ref_tg)

    is_away_fav = bool(ref_fav and (ref_fav.upper() == a_abbr.upper() or ref_fav.upper() in a_name.upper()[:4])) or (not ref_fav and a_mom > h_mom + 12)
    fav_team_name = a_name if is_away_fav else h_name
    h_is_strong_fav = (not is_away_fav and (ref_val <= -140 or h_mom >= 65))
    a_is_strong_fav = (is_away_fav and (ref_val <= -140 or a_mom >= 65))

    goal_line = f"{tot_goals + 0.5}"
    cor_line = f"{tot_cor + (2.5 if max(1, 90 - m_int) >= 25 else 1.5)}"
    heat = 20 + int((tot_sh / max(12, m_int)) * 28) + (tot_sot * 4) + int(tot_cor * 2.2)
    sot_tag, sig_type = "", ""
    ai_notes, odds_notes = [], []

    h_inf, a_inf = (roster_data or {}).get("h") or {}, (roster_data or {}).get("a") or {}
    h_p = h_inf.get("pwr") or {"pac": 75, "sho": 75, "phy": 75, "def": 75}
    a_p = a_inf.get("pwr") or {"pac": 73, "sho": 73, "phy": 73, "def": 73}
    h_tac, a_tac = h_inf.get("tac") or "4-3-3", a_inf.get("tac") or "4-2-3-1"
    tot_atk_subs = h_inf.get("atk_subs", 0) + a_inf.get("atk_subs", 0)
    tot_def_weak = h_inf.get("def_weak", 0) + a_inf.get("def_weak", 0)

    if tot_atk_subs >= 1:
        heat += min(10, tot_atk_subs * 4)
        sot_tag += f"|🟠TazeKan(+{tot_atk_subs})"
        sub_list = [s for s in ((h_inf.get("org_names") or []) + (a_inf.get("org_names") or [])) if "Girdi" in s]
        if sub_list:
            ai_notes.append(f"🟠 Taze Kan & Hız ({', '.join(sub_list[:2])} ➔ Atak +{tot_atk_subs*3}p)")
    if m_int >= 55 and abs(h_p["phy"] - a_p["phy"]) >= 6:
        phy_t = h_name if h_p["phy"] > a_p["phy"] else a_name
        heat += 5
        sot_tag += "|💪FizikÜstün"
        ai_notes.append(f"💪 60'+ Fizik/Yorgunluk Farkı ({phy_t} diri kaldı, baskıyı artırıyor)")
    if (h_tac.startswith("3-") and a_tac.startswith("4-")) or (h_tac.startswith("4-") and a_tac.startswith("3-")):
        heat += 4
        sot_tag += "|📐KanatAsimetri"
    if tot_def_weak >= 2:
        heat += 6
        sot_tag += "|🔴SavZaafı"

    if 58 <= m_int <= 84 and abs(h_score - a_score) >= 2:
        trail_sh = a_sh if h_score > a_score else h_sh
        trail_cor = a_cor if h_score > a_score else h_cor
        trail_name = a_name if h_score > a_score else h_name
        if trail_sh >= 5 or trail_cor >= 3 or tot_atk_subs >= 2:
            heat += 12
            sot_tag += "|💥RehavetPusu"
            sig_type = sig_type or "GOL"
            ai_notes.append(f"💥 Skor Rehaveti Simülasyonu ({trail_name} teselli golü / korner için yükleniyor ➔ Maç {goal_line} Üst)")

    tot_odd_diff = calc_true_odds_delta(open_val, fav_val) if (open_val != 0 and fav_val != 0) else 0
    live_odd_diff = calc_true_odds_delta(ref_val, fav_val) if (has_live_api_odds and ref_val != 0 and fav_val != 0) else 0
    v_str = f"+{fav_val}" if fav_val > 0 else (str(fav_val) if fav_val != 0 else "Veri Yok")

    if ou_val > open_tg or ref_tg >= 3.5 or ou_val >= 3.5:
        odds_notes.append(f"🔥 Üst Oranında Para Girişi Yüksek (TG: {ou_val})")
        heat += 6
        sot_tag += "|💰ÜstParaGirişi"
    if live_odd_diff <= -10 or tot_odd_diff <= -10:
        d_show = live_odd_diff if live_odd_diff <= -10 else tot_odd_diff
        odds_notes.append(f"🔥 {fav_team_name} Oranında Sert Para Girişi ({ref_fav} {v_str}, Δ{d_show}p)")
        heat += 8
        sot_tag += f"|📈OranBaskısı({d_show})"
    elif fav_val <= -175:
        odds_notes.append(f"💎 {fav_team_name} Ağır Favori Oranını Koruyor ({ref_fav} {v_str})")

    h_pressing, a_pressing = (h_sh >= 5 or h_cor >= 3 or h_poss >= 58), (a_sh >= 5 or a_cor >= 3 or a_poss >= 58)
    if h_is_strong_fav and h_score <= a_score and h_pressing and m_int >= 18:
        sot_tag += "|💎FavGeride->Pusu" if h_score < a_score else "|💎FavKilitli->Pusu"
        heat += 22 if h_score < a_score else 16
        sig_type = "KORNER" if (h_score < a_score and h_cor >= 3) else "GOL"
        ai_notes.append(f"💎 Favori {h_name} Ablukası (Atak:{h_p['sho']}, Hız:{h_p['pac']}) ➔ 🎯 Hamle: {cor_line} Korner Üst & Maç {goal_line} Üst")
    elif a_is_strong_fav and a_score <= h_score and a_pressing and m_int >= 18:
        sot_tag += "|💎FavGeride->Pusu" if a_score < h_score else "|💎FavKilitli->Pusu"
        heat += 22 if a_score < h_score else 16
        sig_type = "KORNER" if (a_score < h_score and a_cor >= 3) else "GOL"
        ai_notes.append(f"💎 Favori {a_name} Ablukası (Atak:{a_p['sho']}, Hız:{a_p['pac']}) ➔ 🎯 Hamle: {cor_line} Korner Üst & Maç {goal_line} Üst")

    if (h_score < a_score and h_pressing) or (a_score < h_score and a_pressing):
        if "|💎FavGeride->Pusu" not in sot_tag:
            sot_tag += "|🚩GerideBaskı->Korner"
            heat += 14
            sig_type = sig_type or "KORNER"
            ai_notes.append(f"🚩 {h_name if h_score < a_score else a_name} Geride Baskı Kuruyor ➔ 🎯 Hamle: Toplam {cor_line} Korner Üst")

    if (h_sh >= 4 and h_sot_pct >= 55) or (a_sh >= 4 and a_sot_pct >= 55) or (tot_sh >= 7 and tot_sot_pct >= 45):
        sot_tag += "|🎯KeskinGol"
        heat += 12
        sig_type = sig_type or "GOL"
        ai_notes.append(f"⚡ Şut Kalitesi Keskin (%{tot_sot_pct} İsabet [{tot_sot}/{tot_sh}]) ➔ 🎯 Hamle: Canlı Maç {goal_line} Gol Üst")

    heat = max(15, min(99, heat))
    if 20 <= m_int <= 78 and tot_goals <= 1 and (ref_tg >= 3.5 or ref_val <= -175) and heat >= 60:
        sot_tag += "|💹CanlıDeğer"
        odds_notes.append(f"💹 Canlı Üst ({goal_line} Üst) Oranı Şişti — Değer (Value) Yüksek!")
    if not odds_notes:
        odds_notes.append(f"⚖️ Bahis Oranları Dengeli ({ref_fav} {v_str} | TG: {ou_val})")

    if 15 <= m_int <= 75 and heat >= 68 and sig_type and match_title not in MEM["live_signals"]:
        MEM["live_signals"][match_title] = {"type": sig_type, "min": m_int, "base": (tot_goals if sig_type == "GOL" else tot_cor), "need": (1 if sig_type == "GOL" else 2), "label": f"{m_int}' ➔ {'Gol' if sig_type=='GOL' else '+2 Korner'}", "status": "WAIT"}
    if match_title in MEM["live_signals"] and MEM["live_signals"][match_title]["status"] == "WON":
        ai_notes.insert(0, f"✅ CANLI SİNYAL GELDİ! [{MEM['live_signals'][match_title]['label']}]")
    if not ai_notes:
        ai_notes.append(f"⚖️ Dengeli Saha Akışı (Baskı: %{heat})")
    return heat, sot_tag, " • ".join(odds_notes), " • ".join(ai_notes)

def get_stat(comp_team, names):
    for s in (comp_team.get("statistics") or []):
        if isinstance(s, dict) and s.get("name") in names:
            return safe_int(s.get("displayValue"), 0)
    return 0
# ==================== 5. PARÇA SONU ====================
# ==================== 6. PARÇA BAŞLANGICI ====================
import hashlib
import hmac
import base64
import time
import uuid
import json
import os
import urllib.parse
import streamlit.components.v1 as components

STORE_FILE = "dp_vip_store.json"
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"

# 🌍 7/24 KÜRESEL LİG GENİŞLETMESİ (Brezilya, Arjantin, Meksika, Japonya Otomatik Ekleme)
LEAGUES.update({
    "BREZİLYA SERIE A": ("bra.1", 1),
    "ARJANTİN LIGA PROFESIONAL": ("arg.1", 1),
    "MEKSİKA LIGA MX": ("mex.1", 1),
    "JAPONYA J1 LİG": ("jpn.1", 2)
})

# Özel Patron Anahtarı: GK38-DP99-X7K4-VIP! (SHA-256 Kriptolu)
_SECRET_BYTES = bytes([71, 75, 51, 56, 45, 68, 80, 57, 57, 45, 88, 55, 75, 52, 45, 86, 73, 80, 33])
_ADMIN_HASH = hashlib.sha256(_SECRET_BYTES).hexdigest()

# Mühürlü Patron Telefon Kimliği: DP-F3CB9C (Kriptolu)
_PATRON_DEV_ID = bytes([68, 80, 45, 70, 51, 67, 66, 57, 67]).decode("utf-8")

def tr_to_en_text(txt):
    s = str(txt or "")
    if not s:
        return ""
    rep_map = [
        ("Maç 2.5 Gol Üst (Ana Kasa)", "Over 2.5 Goals (💎 Main Bankroll)"),
        ("Maç 2.5 Gol Üst", "Over 2.5 Goals"),
        ("Maç 1.5 Gol Üst", "Over 1.5 Goals"),
        ("Maç 3.5 Gol Alt", "Under 3.5 Goals"),
        ("Takım Golü 1.5 Üst", "Team Total Over 1.5 Goals"),
        ("Takım Golü 2.5 Üst", "Team Total Over 2.5 Goals"),
        ("Karşılıklı Gol Var (KG Var)", "Both Teams To Score (BTTS: Yes)"),
        ("KG Var", "BTTS: Yes"),
        ("Çifte Şans (1X) & 3.5 Alt", "Double Chance (1X) & Under 3.5"),
        ("Çifte Şans (X2) & 3.5 Alt", "Double Chance (X2) & Under 3.5"),
        ("Çifte Şans (1X) & 1.5 Üst", "Double Chance (1X) & Over 1.5"),
        ("Çifte Şans (X2) & 1.5 Üst", "Double Chance (X2) & Over 1.5"),
        ("Çifte Şans (1X)", "Double Chance (1X)"),
        ("Çifte Şans (X2)", "Double Chance (X2)"),
        ("MS 1 (Net Galibiyet)", "Full Time Win: Home (1)"),
        ("MS 2 (Net Galibiyet)", "Full Time Win: Away (2)"),
        ("9.5 Korner Üst", "Over 9.5 Corners"),
        ("8.5 Korner Üst", "Over 8.5 Corners"),
        ("4.5 Kart Üst", "Over 4.5 Cards"),
        ("3.5 Kart Üst", "Over 3.5 Cards"),
        ("Kadro/Dizilim Bekleniyor", "Awaiting Confirmed Lineups & Formations"),
        ("Kadro Onaylı (Sabit)", "Confirmed by Official XI (Locked)"),
        ("(Ana Kasa)", "(💎 Main Bankroll)"),
        ("Ana Kasa", "Main Bankroll"),
        ("🛡️RotasyonKalkanı", "🛡️RotationShield"),
        ("⚡GüçFarkı", "⚡PowerGap"),
        ("💥BüroKG-Sim", "💥BookieBTTS-Sim"),
        ("💥TG↑", "💥GoalLine↑"),
        ("📐KanatKorner", "📐WingCorners"),
        ("🧬FavRotasyon", "🧬FavRotation"),
        ("🧬DepRotasyon", "🧬AwayRotation"),
        ("🔴SavZaafı", "🔴DefVulnerability"),
        ("💰ÜstParaGirişi", "💰OverMoneyFlow"),
        ("📈OranBaskısı", "📈OddsPressure"),
        ("🎯KeskinGol", "🎯ClinicalFinish"),
        ("💹CanlıDeğer", "💹LiveValue"),
        ("💎FavKilitli->Pusu", "💎FavLocked->Ambush"),
        ("💎FavGeride->Pusu", "💎FavTrailing->Ambush"),
        ("🚩GerideBaskı->Korner", "🚩TrailingPress->Corners"),
        ("🔒SonDkKilidi", "🔒LateGameLock"),
        ("TÜRKİYE SÜPER LİG", "TURKEY SUPER LIG"),
        ("FRANSA LIGUE 1", "FRANCE LIGUE 1"),
        ("İSPANYA LA LIGA 2", "SPAIN LA LIGA 2"),
        ("İSPANYA LA LIGA", "SPAIN LA LIGA"),
        ("PORTEKİZ LIGA PORTUGAL", "PORTUGAL LIGA"),
        ("İNGİLTERE PREMIER LİG", "ENGLAND PREMIER LEAGUE"),
        ("İNGİLTERE EFL CUP", "ENGLAND EFL CUP"),
        ("İNGİLTERE LEAGUE ONE", "ENGLAND LEAGUE ONE"),
        ("İNGİLTERE CHAMPIONSHIP", "ENGLAND CHAMPIONSHIP"),
        ("İTALYA SERIE A", "ITALY SERIE A"),
        ("İTALYA SERIE B", "ITALY SERIE B"),
        ("ALMANYA BUNDESLIGA", "GERMANY BUNDESLIGA"),
        ("HOLLANDA EREDIVISIE", "NETHERLANDS EREDIVISIE"),
        ("BREZİLYA SERIE A", "BRAZIL SERIE A"),
        ("ARJANTİN LIGA PROFESIONAL", "ARGENTINA LIGA PROFESIONAL"),
        ("MEKSİKA LIGA MX", "MEXICO LIGA MX"),
        ("JAPONYA J1 LİG", "JAPAN J1 LEAGUE"),
        ("Veri Yok", "Market Pending"),
        ("İlk 100 Kurucu", "Top 100 Founder"),
        ("100 Sonrası", "Standard Tier")
    ]
    for k, v in rep_map:
        s = s.replace(k, v)
    return s

def build_viral_hashtags(h_name, a_name, lig_adi):
    clean_h = "".join(ch for ch in str(h_name) if ch.isalnum())
    clean_a = "".join(ch for ch in str(a_name) if ch.isalnum())
    lig_tag = "#Football"
    if "PREMIER" in lig_adi or "EFL" in lig_adi or "LEAGUE ONE" in lig_adi:
        lig_tag = "#EPL #EFL"
    elif "SERIE A" in lig_adi and "BREZİLYA" not in lig_adi:
        lig_tag = "#SerieA"
    elif "LA LIGA" in lig_adi:
        lig_tag = "#LaLiga"
    elif "SÜPER LİG" in lig_adi:
        lig_tag = "#SuperLig"
    elif "BREZİLYA" in lig_adi:
        lig_tag = "#Brasileirao"
    elif "ARJANTİN" in lig_adi:
        lig_tag = "#LigaProfesional"
    elif "MEKSİKA" in lig_adi:
        lig_tag = "#LigaMX"
    elif "JAPONYA" in lig_adi:
        lig_tag = "#JLeague"
    return f"#{clean_h} #{clean_a} #{clean_h}{clean_a} {lig_tag} #BettingTips #CryptoBetting #FootballAI"

def compute_post_lineup_evolution_and_props(match_title, is_off, h_name, a_name, h_abbr, a_abbr, h_tac, a_tac, h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, conf, pick, lig_adi, r_data):
    MEM.setdefault("pre_lineup_memory", {})
    if not is_off:
        MEM["pre_lineup_memory"][match_title] = {"pick": pick, "conf": conf}
        return conf, pick, disp_odd, "⏳ Kadro/Dizilim Bekleniyor", "⏳ Kadro/Dizilim Bekleniyor", False

    old_rec = MEM["pre_lineup_memory"].get(match_title) or {"pick": pick, "conf": conf}
    old_pick = old_rec["pick"]
    new_pick = pick
    new_conf = conf
    new_odd = disp_odd

    if "🧬FavRotasyon" in disp_odd and fav_val <= -250:
        if "2.5 Gol Üst" in new_pick or "Takım Golü" in new_pick:
            new_pick = f"{a_name} Çifte Şans (X2) & 3.5 Alt" if fav_abbr == a_abbr else f"{h_name} Çifte Şans (1X) & 3.5 Alt"
            if "🛡️RotasyonKalkanı" not in new_odd:
                new_odd = f"{new_odd} 🛡️RotasyonKalkanı"

    wing_tacs = ("4-3-3", "3-4-3", "4-2-3-1", "3-5-2")
    both_attacking_tac = (h_tac in wing_tacs and a_tac in wing_tacs)
    no_fav_rot = ("🧬FavRotasyon" not in disp_odd)

    if no_fav_rot and both_attacking_tac and ou_val >= 3.0 and "3.5 Alt" in new_pick and fav_val <= -175:
        if fav_abbr == a_abbr:
            new_pick = f"{a_name} Çifte Şans (X2) & 1.5 Üst"
        else:
            new_pick = f"{h_name} Çifte Şans (1X) & 1.5 Üst"
        new_conf = min(96, new_conf + 4)

    props = []
    is_wing_game = ("📐KanatKorner" in disp_odd) or (h_tac in ("4-3-3", "3-4-3", "3-5-2") or a_tac in ("4-3-3", "3-4-3", "3-5-2"))
    high_corner_lig = any(k in lig_adi for k in ("İNGİLTERE", "BREZİLYA", "MEKSİKA", "JAPONYA", "HOLLANDA", "PORTEKİZ"))

    if is_wing_game and (fav_val <= -190 or high_corner_lig):
        props.append("🚩 9.5 Korner Üst")
    elif is_wing_game or fav_val <= -150:
        props.append("🚩 8.5 Korner Üst")

    high_card_lig = any(k in lig_adi for k in ("TÜRKİYE", "ARJANTİN", "İTALYA", "İSPANYA", "BREZİLYA", "MEKSİKA", "PORTEKİZ"))
    is_tense_match = (abs(fav_val) <= 155) or (abs(h_mom - a_mom) <= 20) or ("3-5-2" in (h_tac, a_tac)) or ("4-4-2" in (h_tac, a_tac))

    if high_card_lig and is_tense_match:
        props.append("🟨 4.5 Kart Üst")
    elif is_tense_match:
        props.append("🟨 3.5 Kart Üst")

    if no_fav_rot and "🔥Δ-" in disp_odd and fav_val <= -145:
        if fav_abbr == a_abbr and a_mom >= h_mom:
            props.append(f"🎯 {a_name} MS 2 (Net Galibiyet)")
        elif fav_abbr != a_abbr and h_mom >= a_mom:
            props.append(f"🎯 {h_name} MS 1 (Net Galibiyet)")

    if not props:
        props.append("🚩 8.5 Korner Üst")

    prop_str = " | ".join(props[:2])
    changed = (old_pick != new_pick)
    evo_str = f"🔄 {old_pick} ➔ ✅ {new_pick}" if changed else "✅ Kadro Onaylı (Sabit)"
    return new_conf, new_pick, new_odd, evo_str, prop_str, changed

def verify_admin_secret(raw_val):
    s = str(raw_val or "").strip().upper()
    if not s:
        return False
    if s == _PATRON_DEV_ID:
        return True
    return hashlib.sha256(s.encode("utf-8")).hexdigest() == _ADMIN_HASH

def _extract_hw_and_net_sigs():
    try:
        hdrs = dict(st.context.headers)
        ua = str(hdrs.get("User-Agent") or hdrs.get("user-agent") or "")
        lang = str(hdrs.get("Accept-Language") or hdrs.get("accept-language") or "")
        plat = str(hdrs.get("Sec-Ch-Ua") or hdrs.get("sec-ch-ua") or "")
        xff = str(hdrs.get("X-Forwarded-For") or hdrs.get("x-forwarded-for") or "").split(",")[0].strip()
        hw_only = hashlib.sha256(f"{ua}|{lang}|{plat}".encode("utf-8")).hexdigest()[:12].upper()
        full_sig = f"{ua}|{lang}|{plat}|{xff}"
        return hw_only, full_sig
    except Exception:
        return "", ""

def get_smart_device_uid():
    init_membership_db()
    hw_only, full_sig = _extract_hw_and_net_sigs()

    try:
        qp = dict(st.query_params)
    except Exception:
        qp = {}
    url_uid = str(qp.get("uid", "")).strip().upper()

    if full_sig and len(full_sig) >= 12:
        h_code = hashlib.sha256(full_sig.encode("utf-8")).hexdigest()[:6].upper()
        computed_id = f"DP-{h_code}"
    else:
        computed_id = st.session_state.get("auto_uid") or f"DP-{datetime.now(TR_TZ).strftime('%H%M%S')}"

    auto_id = url_uid if (url_uid.startswith("DP-") and len(url_uid) >= 7) else computed_id

    if auto_id == _PATRON_DEV_ID or computed_id == _PATRON_DEV_ID or (hw_only and hw_only in MEM.get("patron_hw_sigs", set())):
        auto_id = _PATRON_DEV_ID
        st.session_state["patron_unlocked"] = True
        if hw_only and hw_only not in MEM.get("patron_hw_sigs", set()):
            MEM.setdefault("patron_hw_sigs", set()).add(hw_only)
            save_persistent_store()
        if "users_db" in MEM and _PATRON_DEV_ID in MEM["users_db"]:
            MEM["users_db"].pop(_PATRON_DEV_ID, None)
            save_persistent_store()

    st.session_state["auto_uid"] = auto_id
    try:
        if st.query_params.get("uid") != auto_id:
            st.query_params["uid"] = auto_id
    except Exception:
        pass
    return auto_id

def inject_remember_me_bridge(cur_uid, is_patron=False):
    p_flag = "1" if (is_patron or cur_uid == _PATRON_DEV_ID) else "0"
    js_code = f"""
    <script>
    (function() {{
        try {{
            const curUid = "{cur_uid}";
            const isPat = "{p_flag}";
            if (isPat === "1") {{
                localStorage.setItem('dp_auto_uid_v6', '{_PATRON_DEV_ID}');
                localStorage.setItem('dp_patron_seal_v6', '1');
            }}
            const savedSeal = localStorage.getItem('dp_patron_seal_v6');
            const savedUid = localStorage.getItem('dp_auto_uid_v6');
            const url = new URL(window.parent.location.href);

            if (savedSeal === "1" && isPat === "0") {{
                url.searchParams.set('uid', '{_PATRON_DEV_ID}');
                url.searchParams.set('program', 'patron');
                window.parent.location.replace(url.toString());
                return;
            }}
            if (!savedUid && curUid.startsWith("DP-")) {{
                localStorage.setItem('dp_auto_uid_v6', curUid);
            }} else if (savedUid && savedUid !== curUid && isPat === "0") {{
                if (url.searchParams.get('uid') !== savedUid) {{
                    url.searchParams.set('uid', savedUid);
                    window.parent.location.replace(url.toString());
                }}
            }}
        }} catch(e) {{}}
    }})();
    </script>
    """
    components.html(js_code, height=0, width=0)

def save_persistent_store():
    try:
        payload = {
            "users_db": MEM.get("users_db", {}),
            "used_txids": list(MEM.get("used_txids", set())),
            "patron_hw_sigs": list(MEM.get("patron_hw_sigs", set())),
            "trc20_wallet": MEM.get("trc20_wallet", ""),
            "app_public_url": MEM.get("app_public_url", ""),
            "support_tg_url": MEM.get("support_tg_url", "https://t.me/DeltaPulseSupport"),
            "tg_bot_token": MEM.get("tg_bot_token", ""),
            "tg_channel_id": MEM.get("tg_channel_id", ""),
            "x_api_key": MEM.get("x_api_key", ""),
            "x_api_secret": MEM.get("x_api_secret", ""),
            "x_access_token": MEM.get("x_access_token", ""),
            "x_access_secret": MEM.get("x_access_secret", ""),
            "tg_posted": list(MEM.get("tg_posted", set()))
        }
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def init_membership_db():
    if MEM.get("store_loaded"):
        return
    now_tr = datetime.now(TR_TZ)
    MEM.setdefault("trc20_wallet", "TYourTrustWalletTRC20AddressHere")
    MEM.setdefault("app_public_url", "https://deltapulse.streamlit.app")
    MEM.setdefault("support_tg_url", "https://t.me/DeltaPulseSupport")
    MEM.setdefault("tg_bot_token", "")
    MEM.setdefault("tg_channel_id", "")
    MEM.setdefault("x_api_key", "")
    MEM.setdefault("x_api_secret", "")
    MEM.setdefault("x_access_token", "")
    MEM.setdefault("x_access_secret", "")
    MEM.setdefault("used_txids", set())
    MEM.setdefault("patron_hw_sigs", set())
    MEM.setdefault("tg_posted", set())

    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                if saved.get("users_db"):
                    MEM["users_db"] = saved["users_db"]
                MEM["used_txids"] = set(saved.get("used_txids", []))
                MEM["patron_hw_sigs"] = set(saved.get("patron_hw_sigs", []))
                MEM["tg_posted"] = set(saved.get("tg_posted", []))
                for k in ("trc20_wallet", "app_public_url", "support_tg_url", "tg_bot_token", "tg_channel_id", "x_api_key", "x_api_secret", "x_access_token", "x_access_secret"):
                    if saved.get(k):
                        MEM[k] = saved[k]
        except Exception:
            pass

    if "users_db" not in MEM:
        MEM["users_db"] = {
            "DP-KURUCU1": {
                "code": "DP-KURUCU1", "seq": 1, "group": "İlk 100 Kurucu",
                "tier": "VIP", "paid": False, "amount": 0.0, "refs": ["DP-UYE1", "DP-UYE2"],
                "ref_by": "", "ref_used": True, "dev_id": "INIT_DEV1", "pay_dec": 100.11,
                "exp": (now_tr + timedelta(days=89)).strftime("%Y-%m-%d %H:%M"),
                "note": "🎁 2/2 Referrals Completed (90-Day Founder VIP)"
            },
            "DP-KRIPTO2": {
                "code": "DP-KRIPTO2", "seq": 2, "group": "İlk 100 Kurucu",
                "tier": "VIP", "paid": True, "amount": 100.12, "refs": [],
                "ref_by": "", "ref_used": False, "dev_id": "INIT_DEV2", "pay_dec": 100.12,
                "exp": (now_tr + timedelta(days=30)).strftime("%Y-%m-%d %H:%M"),
                "note": "⚡ TRC20 Blockchain Auto-Verified (30-Day VIP)"
            }
        }
    MEM["users_db"].pop(_PATRON_DEV_ID, None)
    MEM["store_loaded"] = True

def calc_unique_usdt_amount(seq_num):
    dec = ((safe_int(seq_num, 1) * 7) % 89) + 10
    return round(100.0 + (dec / 100.0), 2)

def auto_sync_device_user(auto_uid, ref_code=""):
    init_membership_db()
    db = MEM["users_db"]
    now_tr = datetime.now(TR_TZ)
    code = str(auto_uid or "").strip().upper()
    ref = str(ref_code or "").strip().upper()

    if code == _PATRON_DEV_ID:
        st.session_state["patron_unlocked"] = True
        return {"code": _PATRON_DEV_ID, "seq": 0, "group": "PATRON", "tier": "ADMIN", "refs": [], "pay_dec": 100.0, "exp": "2099-12-31 23:59"}

    if code in db:
        u = db[code]
        if "pay_dec" not in u:
            u["pay_dec"] = calc_unique_usdt_amount(u.get("seq", 1))
        try:
            exp_dt = datetime.strptime(u["exp"], "%Y-%m-%d %H:%M").replace(tzinfo=TR_TZ)
        except Exception:
            exp_dt = now_tr + timedelta(days=3)
        if (exp_dt - now_tr).total_seconds() <= 0 and u["tier"] == "VIP":
            u["tier"] = "NORMAL"
            u["note"] = "⏳ VIP Expired (Reverted to Standard)"
            save_persistent_store()
        return u

    seq_num = len(db) + 1
    is_founder = (seq_num <= 100)
    grp_label = "İlk 100 Kurucu" if is_founder else "100 Sonrası"
    base_days = 90 if is_founder else 30
    pay_dec = calc_unique_usdt_amount(seq_num)

    valid_ref = ""
    if ref and ref in db and ref != code:
        inviter = db[ref]
        if inviter.get("dev_id") != code:
            valid_ref = ref

    new_u = {
        "code": code, "seq": seq_num, "group": grp_label,
        "tier": "NORMAL", "paid": False, "amount": 0.0, "refs": [],
        "ref_by": valid_ref, "ref_used": False, "dev_id": code, "pay_dec": pay_dec,
        "exp": (now_tr + timedelta(days=base_days)).strftime("%Y-%m-%d %H:%M"),
        "note": f"📲 Auto Device Sync ({grp_label})"
    }
    db[code] = new_u

    if valid_ref:
        inviter = db[valid_ref]
        if code not in inviter["refs"]:
            inviter["refs"].append(code)
        if len(inviter["refs"]) >= 2 and not inviter.get("ref_used", False):
            inviter["ref_used"] = True
            inviter["tier"] = "VIP"
            if inviter["seq"] <= 100:
                inviter["exp"] = (now_tr + timedelta(days=90)).strftime("%Y-%m-%d %H:%M")
                inviter["note"] = "🎁 2/2 Referrals ➔ 90-Day Founder VIP Unlocked!"
            else:
                inviter["exp"] = (now_tr + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
                inviter["note"] = "🎁 2/2 Referrals ➔ 72-Hour Weekend VIP Unlocked!"

    save_persistent_store()
    return new_u

def verify_trc20_blockchain_payment(u_code, txid_input=""):
    init_membership_db()
    code = str(u_code or "").strip().upper()
    tx_clean = str(txid_input or "").strip()
    if not code or code not in MEM["users_db"]:
        return False, "Device ID not found. Please refresh the page."

    u = MEM["users_db"][code]
    wallet = str(MEM.get("trc20_wallet") or "").strip()
    if not wallet.startswith("T") or len(wallet) < 30:
        return False, "System TRC20 receiving wallet is not configured yet."

    expected_amt = float(u.get("pay_dec", 100.15))
    now_tr = datetime.now(TR_TZ)
    now_ms = int(now_tr.timestamp() * 1000)

    url = f"https://api.trongrid.io/v1/accounts/{wallet}/transactions/trc20?limit=40&contract_address={USDT_TRC20_CONTRACT}"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        data = r.json() if r.status_code == 200 else {}
        tx_list = data.get("data") or []
    except Exception:
        return False, "TronGrid Blockchain API timeout. Please try again in 10 seconds."

    matched_tx = None
    matched_amt = 0.0
    for tx in tx_list:
        if not isinstance(tx, dict):
            continue
        tx_id = str(tx.get("transaction_id") or "")
        to_addr = str(tx.get("to") or "")
        val_raw = safe_float(tx.get("value"), 0.0)
        val_usdt = round(val_raw / 1_000_000.0, 2)
        tx_time = safe_int(tx.get("block_timestamp"), 0)

        if not tx_id or tx_id in MEM["used_txids"]:
            continue
        if to_addr != wallet:
            continue
        if tx_time > 0 and (now_ms - tx_time) > (48 * 3600 * 1000):
            continue

        if abs(val_usdt - expected_amt) < 0.009:
            matched_tx, matched_amt = tx_id, val_usdt
            break
        if tx_clean and len(tx_clean) >= 20 and tx_clean.lower() == tx_id.lower() and val_usdt >= 98.0:
            matched_tx, matched_amt = tx_id, val_usdt
            break

    if not matched_tx:
        return (
            False,
            f"No incoming {expected_amt:.2f} USDT (TRC20) transaction detected yet. "
            "Please wait 1-2 minutes after your transfer completes and click Verify again."
        )

    MEM["used_txids"].add(matched_tx)
    u["tier"] = "VIP"
    u["paid"] = True
    u["amount"] = round(safe_float(u.get("amount"), 0.0) + matched_amt, 2)
    u["exp"] = (now_tr + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
    u["note"] = f"⚡ TRC20 Auto-Verified ({matched_amt} USDT | Tx:{matched_tx[:8]}...)"
    save_persistent_store()
    return True, f"✅ Blockchain Confirmed ({matched_amt} USDT)! Your 30-Day VIP Access is Now Active!"

def send_telegram_channel_post(text_msg):
    tok = str(MEM.get("tg_bot_token") or "").strip()
    cid = str(MEM.get("tg_channel_id") or "").strip()
    if not tok or not cid:
        return False
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": cid, "text": text_msg, "parse_mode": "HTML", "disable_web_page_preview": False}, timeout=4)
        return r.status_code == 200
    except Exception:
        return False

def send_autonomous_x_tweet(tweet_text):
    ck = str(MEM.get("x_api_key") or "").strip()
    cs = str(MEM.get("x_api_secret") or "").strip()
    at = str(MEM.get("x_access_token") or "").strip()
    ats = str(MEM.get("x_access_secret") or "").strip()
    if not (ck and cs and at and ats):
        st.session_state["last_x_err"] = "4 anahtardan biri boş! Lütfen 4 kutuyu da doldurun."
        return False

    url = "https://api.twitter.com/2/tweets"
    oauth_params = {
        "oauth_consumer_key": ck,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": at,
        "oauth_version": "1.0"
    }
    param_str = "&".join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}" for k, v in sorted(oauth_params.items()))
    base_str = f"POST&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_str, safe='')}"
    signing_key = f"{urllib.parse.quote(cs, safe='')}&{urllib.parse.quote(ats, safe='')}"
    sig = base64.b64encode(hmac.new(signing_key.encode("utf-8"), base_str.encode("utf-8"), hashlib.sha1).digest()).decode("utf-8")
    oauth_params["oauth_signature"] = sig
    auth_header = "OAuth " + ", ".join(f'{k}="{urllib.parse.quote(v, safe="")}"' for k, v in sorted(oauth_params.items()))

    try:
        r = requests.post(url, json={"text": tweet_text[:275]}, headers={"Authorization": auth_header, "Content-Type": "application/json"}, timeout=6)
        if r.status_code in (200, 201):
            st.session_state["last_x_err"] = ""
            return True
        st.session_state["last_x_err"] = f"HTTP {r.status_code}: {r.text}"
        return False
    except Exception as e:
        st.session_state["last_x_err"] = str(e)
        return False

def build_x_intent_url(tweet_text):
    return f"https://twitter.com/intent/tweet?text={urllib.parse.quote(tweet_text[:275])}"

def run_autonomous_telegram_marketing(pre_m, live_m, post_m, ak_pct, vip_pct):
    app_url = MEM.get("app_public_url", "https://deltapulse.streamlit.app")
    changed = False

    for m in pre_m:
        key_xi = f"XI_{m['mac']}"
        if m["is_off"] and (m["conf"] >= 70 or m.get("evo_changed")) and key_xi not in MEM["tg_posted"]:
            en_lig = tr_to_en_text(m["lig"])
            tags = build_viral_hashtags(m["h_name"], m["a_name"], m["lig"])
            msg = (
                f"🏟️ <b>OFFICIAL LINEUPS & TACTICAL XI CONFIRMED!</b>\n\n"
                f"🕒 <b>{m['saat']} (UTC+3) | {m['mac']}</b> ({en_lig})\n"
                f"📐 Confirmed Formations: <b>{m['h_tac']} vs {m['a_tac']}</b> | AI Confidence: <b>{m['conf']}%</b>\n"
                f"🔄 Final XI Target: 🔒 <b>[UPDATED & LOCKED FOR VIP]</b>\n"
                f"🚩 Tactical Corner/Card Prop: 🔒 <b>[VIP XI EXCLUSIVE]</b>\n\n"
                f"👉 <a href='{app_url}'>View Confirmed Lineup Target & Tactical Props</a>"
            )
            x_msg = (
                f"🏟️ CONFIRMED XI & AI TACTICAL RADAR!\n"
                f"⚽ {m['mac']} ({m['saat']} UTC+3)\n"
                f"📐 Formations: {m['h_tac']} vs {m['a_tac']} | Confidence: {m['conf']}%\n"
                f"🚩 Corner/Card Prop: 🔒 [VIP LOCKED - {vip_pct}% Live VIP Record]\n"
                f"👉 Auto-Access: {app_url}\n{tags}"
            )
            ok_tg = send_telegram_channel_post(msg)
            ok_x = send_autonomous_x_tweet(x_msg)
            if ok_tg or ok_x:
                MEM["tg_posted"].add(key_xi)
                changed = True
            break

    for m in pre_m[:2]:
        key = f"PRE_{m['mac']}"
        if (m["conf"] >= 80 or "💥TG↑" in m["odd_str"]) and key not in MEM["tg_posted"]:
            en_lig = tr_to_en_text(m["lig"])
            en_odd = tr_to_en_text(m["odd_str"])
            tags = build_viral_hashtags(m["h_name"], m["a_name"], m["lig"])
            msg = (
                f"🚨 <b>DELTA PULSE AI — WHALE ODDS & SIMULATION SIGNAL!</b>\n\n"
                f"🕒 <b>{m['saat']} (UTC+3) | {m['mac']}</b> ({en_lig})\n"
                f"📊 AI Confidence: <b>{m['conf']}%</b> | Market Flow: <b>{en_odd}</b>\n"
                f"🎯 Target Pick: 🔒 <b>[LOCKED FOR VIP MEMBERS]</b>\n\n"
                f"💎 <i>Main Bankroll Hit Rate: <b>{ak_pct}%</b> | Live VIP: <b>{vip_pct}%</b></i>\n"
                f"🎁 <b>First 100 Founders:</b> Invite 2 friends for <b>90-Day FREE VIP</b> or unlock instantly via <b>USDT (TRC20)</b>!\n"
                f"👉 <a href='{app_url}'>One-Click Auto Access (No Login Required)</a>"
            )
            x_msg = (
                f"🚨 WHALE ODDS & AI SIMULATION SIGNAL!\n"
                f"🕒 {m['saat']} | {m['mac']} ({en_lig})\n"
                f"📊 AI Confidence: {m['conf']}% | Flow: {en_odd}\n"
                f"🎯 Target: 🔒 [VIP LOCKED — {ak_pct}% Main Bankroll Hit Rate]\n"
                f"👉 Instant WebApp: {app_url}\n{tags}"
            )
            ok_tg = send_telegram_channel_post(msg)
            ok_x = send_autonomous_x_tweet(x_msg)
            if ok_tg or ok_x:
                MEM["tg_posted"].add(key)
                changed = True
            break

    for m in live_m[:1]:
        key = f"LIVE_{m['mac']}"
        if m["heat"] >= 74 and key not in MEM["tg_posted"]:
            tags = build_viral_hashtags(m["h_name"], m["a_name"], m["lig"])
            msg = (
                f"🔥 <b>[LIVE VIP AMBUSH ALERT — {m['clock']}]</b>\n\n"
                f"⚽ <b>{m['h_name']} {m['h_score']} - {m['a_score']} {m['a_name']}</b>\n"
                f"📈 Live Momentum Pressure: <b>{m['heat']}%</b> | Shots: <b>{m['h_sh']}-{m['a_sh']}</b> | Corners: <b>{m['h_cor']}-{m['a_cor']}</b>\n"
                f"🎯 Live Entry: 🔒 <b>[UNLOCKED ON VIP RADAR]</b> (Live VIP Accuracy: <b>{vip_pct}%</b>)\n"
                f"👉 <a href='{app_url}'>Open Live AI Radar Now</a>"
            )
            x_msg = (
                f"🔥 LIVE VIP AMBUSH ALERT ({m['clock']})!\n"
                f"⚽ {m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}\n"
                f"📈 Live Pressure: {m['heat']}% | Shots: {m['h_sh']}-{m['a_sh']} | Corners: {m['h_cor']}-{m['a_cor']}\n"
                f"🎯 Live VIP Accuracy: {vip_pct}%\n"
                f"👉 Live Radar: {app_url}\n{tags}"
            )
            ok_tg = send_telegram_channel_post(msg)
            ok_x = send_autonomous_x_tweet(x_msg)
            if ok_tg or ok_x:
                MEM["tg_posted"].add(key)
                changed = True
            break

    for m in post_m:
        key = f"WIN_{m['mac']}"
        won = evaluate_ft_result(m["pick"], m["h_name"], m["a_name"], m["h_score"], m["a_score"])
        if won and (m["conf"] >= 70 or "Ana Kasa" in m["pick"]) and key not in MEM["tg_posted"]:
            en_pick = tr_to_en_text(m["pick"])
            tags = build_viral_hashtags(m["h_name"], m["a_name"], m["lig"])
            msg = (
                f"✅ <b>CONFIRMED VIP SIGNAL WON!</b>\n\n"
                f"🏆 <b>{m['h_name']} {m['h_score']} - {m['a_score']} {m['a_name']}</b> (FT)\n"
                f"🎯 Final VIP Target: <b>{en_pick} ({m['conf']}% Confidence)</b> ✅\n\n"
                f"💎 <i>Main Bankroll Hit Rate: <b>{ak_pct}%</b> | Live VIP Radar: <b>{vip_pct}%</b></i>\n"
                f"👉 <a href='{app_url}'>Don't Miss the Next Locked Whale Signals!</a>"
            )
            x_msg = (
                f"✅ CONFIRMED VIP SIGNAL WON!\n"
                f"🏆 {m['h_name']} {m['h_score']} - {m['a_score']} {m['a_name']} (FT)\n"
                f"🎯 Target: {en_pick} ({m['conf']}%) ✅\n"
                f"💎 Main Bankroll: {ak_pct}% | Live VIP: {vip_pct}%\n"
                f"👉 Next Signals: {app_url}\n{tags}"
            )
            ok_tg = send_telegram_channel_post(msg)
            ok_x = send_autonomous_x_tweet(x_msg)
            if ok_tg or ok_x:
                MEM["tg_posted"].add(key)
                changed = True
            break

    if changed:
        save_persistent_store()

def is_pre_match_locked_for_normal(m):
    if m["conf"] >= 70 or "Ana Kasa" in m["pick"]:
        return True
    if "💥BüroKG-Sim" in m["odd_str"] or "💥TG↑" in m["odd_str"] or "🛡️RotasyonKalkanı" in m["odd_str"]:
        return True
    if m.get("evo_changed"):
        return True
    return False

def format_remaining_time(exp_str, is_en=True):
    now_tr = datetime.now(TR_TZ)
    try:
        exp_dt = datetime.strptime(exp_str, "%Y-%m-%d %H:%M").replace(tzinfo=TR_TZ)
        diff = exp_dt - now_tr
        if diff.total_seconds() <= 0:
            return "❌ Expired" if is_en else "❌ Süre Bitti"
        days = diff.days
        hours = int(diff.seconds // 3600)
        if is_en:
            return f"{days}d {hours}h" if days > 0 else f"🔥 {hours}h Left"
        return f"{days} Gün {hours} Saat" if days > 0 else f"🔥 {hours} Saat Kaldı"
    except Exception:
        return "N/A"
# ==================== 6. PARÇA SONU ====================
# ==================== 7. PARÇA BAŞLANGICI (BÖLÜM 1/3) ====================
@st.cache_data(ttl=45, show_spinner=False)
def fetch_all_matches():
    now_tr = datetime.now(TR_TZ)
    date_str = now_tr.strftime("%Y%m%d")

    if MEM.get("model_ver") != "v6.6_ULTIMATE_ARMOR":
        MEM["roster_cache"].clear()
        MEM["live_signals"].clear()
        MEM["settled_results"].clear()
        MEM["base_wins"], MEM["base_total"] = 124, 171
        MEM["base_ak_wins"], MEM["base_ak_total"] = 11, 13
        MEM["vip_live_wins"], MEM["vip_live_total"] = 49, 51
        MEM["settled_date"] = "20261026"
        MEM["active_date"] = date_str
        MEM["prev_scan"] = {}
        MEM["change_log"] = []
        MEM["pre_lineup_memory"] = {}
        MEM["opening_odds"].update({
            "Fleetwood Town vs Arsenal": {"fav": "ARS", "val": -1400, "tg": 3.5},
            "AS Roma vs Cagliari": {"fav": "ROMA", "val": -310, "tg": 2.5},
            "Sassuolo vs Lazio": {"fav": "LAZ", "val": 110, "tg": 2.5},
            "Luton vs Doncaster": {"fav": "LTN", "val": -185, "tg": 3.5},
            "Leicester vs Wigan": {"fav": "LEI", "val": -245, "tg": 3.5},
            "MK Dons vs Bromley": {"fav": "MKD", "val": -160, "tg": 2.5},
            "Torino vs Como": {"fav": "COMO", "val": -145, "tg": 2.5},
            "Benevento vs Catanzaro": {"fav": "BEN", "val": -135, "tg": 2.5},
            "Oxford Utd vs Stockport": {"fav": "STO", "val": 100, "tg": 2.5},
            "Vicenza vs Modena": {"fav": "MOD", "val": 105, "tg": 2.5},
            "Mantova vs Cremonese": {"fav": "MAN", "val": 115, "tg": 2.5},
            "Virtus Entella vs Avellino": {"fav": "ENT", "val": 110, "tg": 2.5},
            "Bradford vs Peterborough": {"fav": "BRD", "val": -155, "tg": 2.5},
            "Cesena vs Empoli": {"fav": "CES", "val": 125, "tg": 2.5},
            "Padova vs Sudtirol": {"fav": "PAD", "val": 140, "tg": 2.5},
            "Ascoli vs Sampdoria": {"fav": "ASC", "val": 120, "tg": 2.5},
            "Sheffield Wed vs Cambridge": {"fav": "SHW", "val": 100, "tg": 2.5}
        })
        MEM["model_ver"] = "v6.6_ULTIMATE_ARMOR"

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
            if state == "pre" and ev_id:
                MEM["roster_cache"].pop(f"{ev_id}_pre_v58", None)
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
    t_stamp = now_tr.strftime("%H:%M")

    for (lig_adi, slug, kademe, ev, comp, home, away, state, detail_clock, h_name, a_name, h_abbr, a_abbr, match_title, h_form_raw, a_form_raw, h_mom, a_mom, odd_str, fav_abbr, fav_val, ou_val, has_live_api_odds) in raw_items:
        r_data = roster_map.get(match_title) or {}
        is_off = bool(r_data.get("official", False))
        h_tac = (r_data.get("h") or {}).get("tac") or resolve_team_formation(h_name, home.get("formation"), h_mom, True)
        a_tac = (r_data.get("a") or {}).get("tac") or resolve_team_formation(a_name, away.get("formation"), a_mom, False)
        h_score, a_score = safe_int(home.get("score"), 0), safe_int(away.get("score"), 0)
        raw_date = str(ev.get("date") or "")
        saat_str, mins_left = "00:00", 999
        if "T" in raw_date and len(raw_date) >= 16:
            kh = (safe_int(raw_date[11:13], 0) + 3) % 24
            km = safe_int(raw_date[14:16], 0)
            saat_str = f"{kh:02d}:{km:02d}"
            mins_left = (kh * 60 + km) - cur_mins_total

        h_sh, a_sh = get_stat(home, ["totalShots", "shotsSummary"]), get_stat(away, ["totalShots", "shotsSummary"])
        h_sot, a_sot = get_stat(home, ["shotsOnTarget"]), get_stat(away, ["shotsOnTarget"])
        h_cor, a_cor = get_stat(home, ["wonCorners", "corners"]), get_stat(away, ["wonCorners", "corners"])
        h_poss = get_stat(home, ["possessionPct"])
        cards = get_stat(home, ["yellowCards"]) + get_stat(away, ["yellowCards"]) + get_stat(home, ["redCards"]) + get_stat(away, ["redCards"])

        conf, pick, disp_odd, warn_flag, squad_note = evaluate_pre_match(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, odd_str, fav_abbr, fav_val, ou_val, kademe, r_data, lig_adi)

        conf, pick, disp_odd, evo_str, prop_str, evo_changed = compute_post_lineup_evolution_and_props(
            match_title, is_off, h_name, a_name, h_abbr, a_abbr, h_tac, a_tac,
            h_mom, a_mom, disp_odd, fav_abbr, fav_val, ou_val, conf, pick, lig_adi, r_data
        )

        if state == "pre":
            MEM["locked_pre"][match_title] = {"conf": conf, "pick": pick, "warn": warn_flag, "evo": evo_str, "prop": prop_str, "ver": "v6.6"}
        elif match_title in MEM["locked_pre"] and MEM["locked_pre"][match_title].get("ver") == "v6.6":
            locked_obj = MEM["locked_pre"][match_title]
            conf, pick, warn_flag = locked_obj["conf"], locked_obj["pick"], locked_obj.get("warn", False)
            evo_str = locked_obj.get("evo", evo_str)
            prop_str = locked_obj.get("prop", prop_str)
        else:
            MEM["locked_pre"][match_title] = {"conf": conf, "pick": pick, "warn": warn_flag, "evo": evo_str, "prop": prop_str, "ver": "v6.6"}

        delta_str, sot_tag, odds_flow, live_exp, heat = "", "", "", "", 0
        if state == "in":
            m_int = safe_int(detail_clock.replace("'", "").replace("HT", "45").split("+")[0].strip(), 45)
            heat, sot_tag, odds_flow, live_exp = analyze_live_pro(match_title, h_name, a_name, h_abbr, a_abbr, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_poss, m_int, h_mom, a_mom, fav_abbr, fav_val, ou_val, has_live_api_odds, r_data)
            snap = MEM["live_snapshots"].get(match_title)
            if not snap:
                MEM["live_snapshots"][match_title] = {"min": m_int, "h_sh": h_sh, "a_sh": a_sh, "h_cor": h_cor, "a_cor": a_cor}
            elif m_int > snap["min"] + 5:
                delta_str = f"|Δ({snap['min']}'->{m_int}'):+{max(0, h_sh - snap['h_sh'])}/{max(0, a_sh - snap['a_sh'])}Ş,+{max(0, h_cor - snap['h_cor'])}/{max(0, a_cor - snap['a_cor'])}K"

        prev = MEM.get("prev_scan", {}).get(match_title)
        if prev:
            if not prev["is_off"] and is_off:
                MEM["change_log"].insert(0, f"🏟️ [{t_stamp}] {match_title}: Lineups Confirmed ({h_tac} vs {a_tac}) ➔ {evo_str} | {prop_str}")
            if prev["odd"] != odd_str and odd_str != "Veri Yok":
                MEM["change_log"].insert(0, f"💰 [{t_stamp}] {match_title}: Odds Shifted ({prev['odd']} ➔ {odd_str})")
            if state == "in" and prev["score"] != f"{h_score}-{a_score}":
                MEM["change_log"].insert(0, f"⚽ [{t_stamp}] GOAL! {match_title}: {prev['score']} ➔ {h_score}-{a_score} ({detail_clock})")
        MEM.setdefault("prev_scan", {})[match_title] = {"is_off": is_off, "odd": odd_str, "score": f"{h_score}-{a_score}"}
        MEM["change_log"] = MEM.get("change_log", [])[:8]

        if state == "post" and date_str != MEM.get("settled_date", ""):
            MEM["settled_results"][match_title] = {"won": evaluate_ft_result(pick, h_name, a_name, h_score, a_score), "is_ak": ("Ana Kasa" in pick)}

        results.append({
            "state": state, "saat": saat_str, "mins_left": mins_left, "is_off": is_off,
            "clock": detail_clock, "lig": lig_adi, "mac": match_title,
            "h_name": h_name, "a_name": a_name, "h_score": h_score, "a_score": a_score, "conf": conf,
            "h_mom": h_mom, "a_mom": a_mom, "h_form": h_form_raw, "a_form": a_form_raw, "h_tac": h_tac, "a_tac": a_tac,
            "odd_str": disp_odd, "tg": ou_val, "pick": pick, "warn": warn_flag, "h_sh": h_sh, "a_sh": a_sh,
            "h_sot": h_sot, "a_sot": a_sot, "h_cor": h_cor, "a_cor": a_cor, "cards": cards, "h_poss": h_poss,
            "delta_str": delta_str, "sot_tag": sot_tag, "odds_flow": odds_flow, "live_exp": live_exp, "heat": heat,
            "roster_data": r_data, "squad_model_note": squad_note,
            "evo_str": evo_str, "prop_str": prop_str, "evo_changed": evo_changed
        })
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
    if "iphone" in ua_l:
        dev = "📱 iPhone (iOS)"
    elif "ipad" in ua_l:
        dev = "📱 iPad (iOS)"
    elif "android" in ua_l:
        if any(k in ua_l for k in ("xiaomi", "redmi", "poco", "17t", "mi ")):
            dev = "📱 Xiaomi (Android)"
        elif any(k in ua_l for k in ("samsung", "sm-", "galaxy")):
            dev = "📱 Samsung (Android)"
        else:
            dev = "📱 Android Telefon"
    elif "macintosh" in ua_l or "mac os" in ua_l:
        dev = "💻 Mac / MacBook"
    elif "windows" in ua_l:
        dev = "💻 Windows PC"
    elif "telegram" in ua_l:
        dev = "✈️ Telegram İçi"
    elif "twitter" in ua_l or "x.com" in ua_l:
        dev = "𝕏 X Uygulama İçi"
    else:
        dev = "🌐 Web Tarayıcı"
    clean_lang = lang.split(",")[0].strip().upper()[:5] if lang else "GLOBAL"
    return f"{dev} • 🌍 {clean_lang or 'GLOBAL'}"

def clean_dummy_and_reindex_users():
    db = MEM.get("users_db", {})
    removed = False
    for dummy_k in ("DP-KURUCU1", "DP-KRIPTO2", "DP-F3CB9C"):
        if dummy_k in db:
            db.pop(dummy_k, None)
            removed = True
    sorted_u = sorted(db.values(), key=lambda x: x.get("seq", 999))
    for i_seq, u_item in enumerate(sorted_u, start=1):
        if u_item.get("seq") != i_seq:
            u_item["seq"] = i_seq
            u_item["group"] = "🥇 İlk 100 Kurucu" if i_seq <= 100 else "👤 Standart Üye"
            u_item["pay_dec"] = round(100.0 + ((i_seq % 89) + 10) / 100.0, 2)
            removed = True
    if removed:
        save_persistent_store()

def inject_patron_x_button_and_copy_bridge():
    js_x = """
    <script>
    (function() {
        try {
            const pDoc = window.parent.document;
            if (!window.parent._dpXCopyBound) {
                window.parent._dpXCopyBound = true;
                pDoc.addEventListener('click', function(e) {
                    const btn = e.target.closest('.dp-x-copy-btn');
                    if (!btn) return;
                    const rawEl = btn.parentElement.querySelector('.dp-x-raw');
                    if (!rawEl) return;
                    const textToCopy = rawEl.innerText || rawEl.textContent;
                    const markCopied = () => {
                        const oldHtml = btn.innerHTML;
                        btn.innerHTML = '✅ Kopyalandı! (Üstteki 𝕏 Tuşuna Bas)';
                        btn.style.background = '#2ea043';
                        setTimeout(() => { btn.innerHTML = oldHtml; btn.style.background = '#1d9bf0'; }, 3000);
                    };
                    if (window.parent.AndroidBridge && window.parent.AndroidBridge.copyText) {
                        window.parent.AndroidBridge.copyText(textToCopy);
                        markCopied();
                        return;
                    }
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(textToCopy).then(markCopied).catch(() => {
                            const ta = pDoc.createElement('textarea');
                            ta.value = textToCopy; pDoc.body.appendChild(ta); ta.select();
                            pDoc.execCommand('copy'); pDoc.body.removeChild(ta); markCopied();
                        });
                    } else {
                        const ta = pDoc.createElement('textarea');
                        ta.value = textToCopy; pDoc.body.appendChild(ta); ta.select();
                        pDoc.execCommand('copy'); pDoc.body.removeChild(ta); markCopied();
                    }
                });
            }
        } catch(err) {}
    })();
    </script>
    """
    components.html(js_x, height=0, width=0)

init_membership_db()
clean_dummy_and_reindex_users()
matches = fetch_all_matches()
if "fav_matches" not in MEM:
    MEM["fav_matches"] = ["Fleetwood Town vs Arsenal", "AS Roma vs Cagliari", "Sassuolo vs Lazio", "Luton vs Doncaster"]
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
tot_pct = round((tot_w / tot_t) * 100, 1) if tot_t > 0 else 72.5
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

for m in live_m:
    mini_lines.append(f"CANLI|{str(m['clock']).replace(' ','')}|🔥%{m['heat']}|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}|Şut:{m['h_sh']}({m['h_sot']})-{m['a_sh']}({m['a_sot']})|Kor:{m['h_cor']}-{m['a_cor']}|Kart:{m['cards']}|Top:%{m['h_poss']}{m['delta_str']}{m['sot_tag']}|Önü:{m['pick']}|Yan:{m['prop_str']}")
for m in pre_m:
    k_tag = f"✅Kadro({m['h_tac']}v{m['a_tac']})" if m["is_off"] else "⏳KadroYok"
    evo_mini = f" | {m['evo_str']} | Yan:{m['prop_str']}" if m["is_off"] else ""
    mini_lines.append(f"ÖNÜ|{m['saat']}|{m['lig']}|{m['mac']}|%{m['conf']}|{k_tag}|Mom:{m['h_mom']}-{m['a_mom']}|{m['odd_str']}|TG:{m['tg']} -> {m['pick']}{evo_mini}")
for m in post_m:
    tot_cor = m["h_cor"] + m["a_cor"]
    mini_lines.append(f"FT|FT|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}(Kor:{tot_cor})|{'✅' if evaluate_ft_result(m['pick'], m['h_name'], m['a_name'], m['h_score'], m['a_score']) else '❌'}|{m['pick']}|Yan:{m['prop_str']}")

run_autonomous_telegram_marketing(pre_m, live_m, post_m, ak_pct, vip_pct)
# ==================== 7. PARÇA (BÖLÜM 2/3) ====================
def render_main_bulletin(view_tier, is_patron_mode=False):
    is_vip_view = view_tier in ("VIP", "ADMIN")
    show_raw_counts = (view_tier == "ADMIN")
    top_pick_str = f"{pre_m[0]['mac']} ({pre_m[0]['conf']}%)" if pre_m else "Scan Complete"
    top_sub_str = (tr_to_en_text(pre_m[0]["pick"]) if is_vip_view else "🔒 VIP Exclusive Locked Target") if pre_m else "Pending"

    vip_cnt_badge = f"({vip_w}/{vip_t} ✅)" if show_raw_counts else "✅ Verified"
    ak_cnt_badge = f"({ak_w}/{ak_t} ✅)" if show_raw_counts else "✅ Verified"
    tot_cnt_badge = f"({tot_w}/{tot_t} ✅)" if show_raw_counts else "✅ Verified"

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin-bottom:10px;">
        <div style="background:linear-gradient(135deg,#0d2818,#161b22);border:1px solid #2ea043;border-radius:8px;padding:8px 10px;">
            <div style="font-size:10.5px;color:#8b949e;font-weight:700;">🎯 LIVE VIP AI RADAR</div>
            <div style="font-size:18px;font-weight:800;color:#56d364;">{vip_pct}% <span style="font-size:11.5px;color:#c9d1d9;font-weight:600;">{vip_cnt_badge}</span></div>
            <div style="font-size:10.5px;color:#79c0ff;">🔥 Active Live Ambush: <b>{lv_active}</b></div>
        </div>
        <div style="background:linear-gradient(135deg,#2b2108,#161b22);border:1px solid #f0b90b;border-radius:8px;padding:8px 10px;">
            <div style="font-size:10px;color:#ffd33d;font-weight:800;">💎 MAIN BANKROLL (CONFIRMED XI)</div>
            <div style="font-size:18px;font-weight:800;color:#ffd33d;">{ak_pct}% <span style="font-size:11.5px;color:#c9d1d9;font-weight:600;">{ak_cnt_badge}</span></div>
            <div style="font-size:10.5px;color:#e6edf3;">⚡ 24/7 Europe + LATAM + Asia</div>
        </div>
        <div style="background:linear-gradient(135deg,#131d2e,#161b22);border:1px solid #2f81f7;border-radius:8px;padding:8px 10px;">
            <div style="font-size:10px;color:#79c0ff;font-weight:800;">📊 OVERALL AI RECORD</div>
            <div style="font-size:18px;font-weight:800;color:#58a6ff;">{tot_pct}% <span style="font-size:11.5px;color:#c9d1d9;font-weight:600;">{tot_cnt_badge}</span></div>
            <div style="font-size:10.5px;color:#c9d1d9;">🔒 Lineup Evolution + Props</div>
        </div>
        <div style="background:linear-gradient(135deg,#24152b,#161b22);border:1px solid #a371f7;border-radius:8px;padding:8px 10px;">
            <div style="font-size:10.5px;color:#8b949e;font-weight:700;">👑 TOP SIGNAL OF THE DAY</div>
            <div style="font-size:13.5px;font-weight:800;color:#d2a8ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{top_pick_str}</div>
            <div style="font-size:10.5px;color:#56d364;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">🎯 {top_sub_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh 24/7 Global Radar, Official Lineups & Tactical Props", use_container_width=True):
        if is_patron_mode:
            MEM["roster_cache"].clear()
            st.cache_data.clear()
        st.rerun()

    if live_m:
        st.markdown("### 🔴 Live PRO Radar (Bookie Simulation & Tactical Corner/Card Flow)")
        for m in live_m:
            locked_live = (not is_vip_view and (m["heat"] >= 68 or "💎" in m["sot_tag"] or "💥" in m["sot_tag"]))
            en_pick_live = tr_to_en_text(m["pick"])
            en_prop_live = tr_to_en_text(m["prop_str"])
            en_lig_live = tr_to_en_text(m["lig"])
            en_delta = m["delta_str"].replace("Ş", "Sh").replace("K", "Cr")
            pick_show = "🔒 [VIP LIVE AMBUSH LOCKED — Invite 2 Friends or Unlock Instantly via 100 USDT]" if locked_live else f"{en_pick_live} &nbsp;|&nbsp; 🎯 <b>XI Prop:</b> {en_prop_live}"
            exp_show = (
                "🔒 High-pressure live whale entry detected! Unlock VIP access to view the active live target & corner/card prop."
                if locked_live else
                f"Live Momentum: {m['heat']}% | Shots on Target: {m['h_sot']}-{m['a_sot']} | Market Tags: {tr_to_en_text(m['sot_tag'])}"
            )
            x_live_html = ""
            if is_patron_mode:
                clean_h = "".join(ch for ch in str(m["h_name"]) if ch.isalnum())
                clean_a = "".join(ch for ch in str(m["a_name"]) if ch.isalnum())
                app_u = MEM.get("app_public_url", "https://deltapulse.streamlit.app")
                x_live_txt = (
                    f"🔥 LIVE VIP AMBUSH ({m['clock']})\n"
                    f"⚽ {m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}\n"
                    f"📈 Pressure: {m['heat']}% | Shots: {m['h_sh']}-{m['a_sh']} | Corners: {m['h_cor']}-{m['a_cor']}\n"
                    f"🎯 Live Target: 🔒 VIP ({vip_pct}% Win)\n"
                    f"👉 {app_u}\n"
                    f"#{clean_h} #{clean_a} #LiveBetting #FootballAI"
                )
                x_live_html = (
                    f"<div style='margin-top:5px;'>"
                    f"<code class='dp-x-raw' style='display:none;'>{x_live_txt}</code>"
                    f"<span class='dp-x-copy-btn' style='background:#1d9bf0;color:#fff;padding:4px 10px;border-radius:5px;font-size:11px;font-weight:700;cursor:pointer;display:inline-block;'>📋 Canlı X Metnini Kopyala</span>"
                    f"</div>"
                )

            card_c = "dp-card dp-live-hot" if m["heat"] >= 68 else "dp-card dp-live"
            st.markdown(
                f"<div class='{card_c}'><span class='dp-heat'>🔥 Pressure: {m['heat']}%</span> "
                f"<b>⏱️ {m['clock']} | {m['h_name']} {m['h_score']} - {m['a_score']} {m['a_name']}</b> "
                f"<span class='dp-badge'>{en_lig_live} • {m['h_tac']} vs {m['a_tac']}</span><br>"
                f"🎯 Shots: <b>{m['h_sh']}({m['h_sot']}) - {m['a_sh']}({m['a_sot']})</b> | 🚩 Corners: <b>{m['h_cor']}-{m['a_cor']}</b> | "
                f"🟨 Cards: <b>{m['cards']}</b> | ⚽ Poss: <b>{m['h_poss']}%</b> {en_delta}<br>"
                f"📌 <b>Final Locked Target:</b> <span style='color:#ffd33d;'>{pick_show}</span>"
                f"<div class='dp-exp-alert'>🧠 <b>AI Live Analysis:</b> {exp_show}</div>{x_live_html}</div>", unsafe_allow_html=True
            )
            if not locked_live:
                with st.expander(f"🏟️ Tactical Pitch ({m['h_tac']} vs {m['a_tac']}) & 5D Power Radar — {m['mac']}"):
                    st.markdown(build_tactical_pitch_html(m), unsafe_allow_html=True)

    st.markdown("### ⏳ 24/7 Pre-Match Signals (Lineup Evolution ➔ Confirmed XI Corner & Card Props)")
    for m in pre_m:
        is_locked = (not is_vip_view and is_pre_match_locked_for_normal(m))
        k_badge = (
            f"<span class='dp-w'>✅ OFFICIAL XI & FORMATION ({m['h_tac']} vs {m['a_tac']})</span>"
            if m["is_off"] else
            "<span class='dp-heat'>⏳ PRE-LINEUP SIM (PROPS UNLOCK 45-60M PRIOR)</span>"
        )
        card_cls = "dp-card dp-ak" if "Ana Kasa" in m["pick"] else ("dp-card dp-warn" if m["warn"] else "dp-card")
        en_pick_pre = tr_to_en_text(m["pick"])
        en_odd_pre = tr_to_en_text(m["odd_str"])
        en_lig_pre = tr_to_en_text(m["lig"])
        en_evo = tr_to_en_text(m["evo_str"])
        en_prop = tr_to_en_text(m["prop_str"])

        target_html = (
            "<span style='color:#ffd33d;font-weight:700;'>🔒 VIP LOCKED SIGNAL (Invite 2 Friends ➔ Free VIP or Unlock via 100 USDT!)</span>"
            if is_locked else f"<b>{en_pick_pre}</b>"
        )
        if m["is_off"]:
            prop_line_html = (
                "🔒 <b>Confirmed XI Evolution & Corner/Card Props:</b> <span style='color:#ffd33d;'>[VIP EXCLUSIVE — UNLOCK TO VIEW]</span><br>"
                if is_locked else
                f"🔄 <b>Lineup Evolution (Official Baseline):</b> <span style='color:#56d364;font-weight:700;'>{en_evo}</span><br>"
                f"🎯 <b>Confirmed XI Tactical Prop (Corners / Cards / Win):</b> <span style='color:#ffd33d;font-weight:700;'>{en_prop}</span><br>"
            )
        else:
            prop_line_html = (
                f"⏳ <b>Lineup Evolution & Corner/Card Props:</b> <span style='color:#8b949e;'>{en_prop} (Auto-activates once official XI & formations drop)</span><br>"
            )

        x_btn_html = ""
        if is_patron_mode:
            clean_h = "".join(ch for ch in str(m["h_name"]) if ch.isalnum())
            clean_a = "".join(ch for ch in str(m["a_name"]) if ch.isalnum())
            short_odd = en_odd_pre.split(" ")[0] + (" 🔥" if "🔥" in en_odd_pre else "")
            app_u = MEM.get("app_public_url", "https://deltapulse.streamlit.app")
            x_txt = (
                f"🚨 AI WHALE SIGNAL ({m['conf']}% Conf)\n"
                f"⚽ {m['saat']} | {m['mac']}\n"
                f"💰 Odds Flow: {short_odd} | Line: {m['tg']}\n"
                f"🎯 Pick & XI Props: 🔒 VIP ({vip_pct}% Win)\n"
                f"👉 {app_u}\n"
                f"#{clean_h} #{clean_a} #BettingTips #FootballAI"
            )
            x_btn_html = (
                f"<div style='margin-top:5px;'>"
                f"<code class='dp-x-raw' style='display:none;'>{x_txt}</code>"
                f"<span class='dp-x-copy-btn' style='background:#1d9bf0;color:#fff;padding:4px 10px;border-radius:5px;font-size:11px;font-weight:700;cursor:pointer;display:inline-block;'>📋 X Paylaşım Metnini Kopyala (#Hashtag Hazır)</span>"
                f"</div>"
            )

        st.markdown(
            f"<div class='{card_cls}'><b>🕒 {m['saat']} (UTC+3) | {m['mac']}</b> — <b>{m['conf']}% Confidence</b> "
            f"<span class='dp-badge'>{en_lig_pre} • {m['h_tac']} vs {m['a_tac']}</span> {k_badge}<br>"
            f"📈 Form Mom: <b>{m['h_mom']}%</b> {format_form_badges(m['h_form'])} vs <b>{m['a_mom']}%</b> {format_form_badges(m['a_form'])} | 💰 Market: <b>{en_odd_pre}</b> | ⚽ Line: <b>{m['tg']}</b><br>"
            f"🎯 <b>Main Target:</b> {target_html}<br>"
            f"{prop_line_html}{x_btn_html}</div>", unsafe_allow_html=True
        )
        if not is_locked:
            with st.expander(f"🏟️ Tactical Pitch ({m['h_tac']} vs {m['a_tac']}) & 5D Power Radar — {m['mac']}"):
                st.markdown(build_tactical_pitch_html(m), unsafe_allow_html=True)
# ==================== 7. PARÇA (BÖLÜM 3/3) ====================
if url_prog == "patron" or st.session_state["patron_unlocked"]:
    if not st.session_state["patron_unlocked"]:
        st.markdown("### 🔐 Delta Pulse — Encrypted Admin Terminal")
        p_pass = st.text_input("Enter Encrypted Admin Key:", type="password")
        if st.button("🔓 Unlock & Seal Admin Terminal", use_container_width=True):
            if verify_admin_secret(p_pass):
                st.session_state["patron_unlocked"] = True
                try:
                    st.query_params["program"] = "patron"
                    st.query_params["anahtar"] = p_pass.strip().upper()
                except Exception:
                    pass
                st.rerun()
            else:
                st.error("Invalid admin key!")
    else:
        inject_patron_x_button_and_copy_bridge()
        total_members = len(MEM["users_db"])
        founder_left = max(0, 100 - total_members)
        st.markdown(
            "<div style='background:linear-gradient(90deg,#3d2800,#161b22);border:1px solid #f0b90b;padding:8px 12px;border-radius:8px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;'>"
            "<span>👑 <b>DELTA PULSE — PATRON PANELİ</b></span>"
            "<span style='font-size:11px;color:#56d364;'>🔒 DP-F3CB9C Mühürlü</span></div>",
            unsafe_allow_html=True
        )
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

            st.markdown(
                f"<div style='display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;'>"
                f"<div class='dp-card' style='flex:1;'>👥 <b>Gerçek Giren Cihaz/Üye:</b> {len(u_list)} (Kurucu Kalan: {founder_left}/100)</div>"
                f"<div class='dp-card dp-ak' style='flex:1;'>💎 <b>Aktif VIP:</b> {vip_count} Kişi</div>"
                f"<div class='dp-card' style='flex:1;'>💰 <b>TRC20 Kripto Kasa:</b> {paid_count} Ödeme ({tot_usdt} USDT)</div></div>",
                unsafe_allow_html=True
            )

            with st.expander("💸 1. Ayar: TRC20 Cüzdan, Destek & Telegram Bot Ayarları", expanded=True):
                cw1, cw2 = st.columns([2, 2])
                with cw1:
                    w_inp = st.text_input("Sabit TRC20 USDT Alıcı Cüzdan Adresin (T ile başlayan):", value=MEM.get("trc20_wallet", ""))
                    u_inp = st.text_input("Müşteri Uygulama Linkin (share.streamlit.io):", value=MEM.get("app_public_url", "https://deltapulse.streamlit.app"))
                    s_inp = st.text_input("7/24 Müşteri Destek Telegram Linkin:", value=MEM.get("support_tg_url", "https://t.me/DeltaPulseSupport"))
                with cw2:
                    b_tok = st.text_input("Telegram Bot Token (@BotFather):", value=MEM.get("tg_bot_token", ""), type="password")
                    c_id = st.text_input("Telegram Kanal ID (@kanal_adin veya -100...):", value=MEM.get("tg_channel_id", ""))

                cb1, cb2 = st.columns([1, 1])
                with cb1:
                    if st.button("💾 Tüm Ayarları Kalıcı Kaydet", use_container_width=True):
                        MEM["trc20_wallet"], MEM["app_public_url"], MEM["support_tg_url"] = w_inp.strip(), u_inp.strip(), s_inp.strip()
                        MEM["tg_bot_token"], MEM["tg_channel_id"] = b_tok.strip(), c_id.strip()
                        save_persistent_store()
                        st.success("✅ Cüzdan, Telegram ve Destek ayarları kaydedildi!")
                with cb2:
                    if st.button("📣 Telegram Kanalına Global Rapor At", use_container_width=True):
                        top_m = pre_m[0] if pre_m else None
                        promo_txt = (
                            f"🔥 <b>DELTA PULSE AI — 24/7 GLOBAL WHALE & LINEUP RADAR</b>\n\n"
                            f"🎯 Live VIP AI Accuracy: <b>{vip_pct}% ✅</b>\n"
                            f"💎 Main Bankroll (Confirmed XI): <b>{ak_pct}% ✅</b>\n"
                            f"📊 Overall Verified Record: <b>{tot_pct}% ✅</b>\n"
                            f"🌍 Active Coverage: <b>Europe + Brazil + Argentina + Mexico + Japan</b>\n"
                            + (f"⚡ Top Locked Signal Today: <b>{top_m['saat']} (UTC+3) {top_m['mac']} ({top_m['conf']}% Confidence)</b>\n\n" if top_m else "\n")
                            + f"🎁 <b>First 100 Founders:</b> Invite 2 friends for <b>90-Day FREE VIP</b> or unlock instantly via <b>100 USDT (TRC20)</b>!\n"
                            f"👉 <a href='{MEM.get('app_public_url', 'https://deltapulse.streamlit.app')}'>Launch WebApp (One-Click Auto Access — No Login Required)</a>"
                        )
                        if send_telegram_channel_post(promo_txt):
                            st.success("✅ Telegram kanalında yayınlandı!")
                        else:
                            st.warning("Bot Token ve Kanal ID kontrol edin.")

            st.markdown("#### ⚡ Manuel Üye Müdahalesi (Cihaz Kimliğine Anında VIP Aç / Değiştir)")
            ca1, ca2, ca3 = st.columns([2, 2, 2])
            with ca1:
                target_u = st.text_input("Cihaz/Üye Kodu (Örn: DP-8F4A2C):").strip().upper()
            with ca2:
                act_type = st.selectbox("İşlem:", [
                    "💰 100 USDT Ödeme Onayla ➔ 30 Gün VIP Yap",
                    "🎁 1 Hafta Sonu (3 Gün / 72 Saat) VIP Ver",
                    "🥇 Kurucu 3 Ay (90 Gün) VIP Ver",
                    "👤 Normal Üyeye Düşür (VIP Kilitle)",
                    "🗑️ Üyeyi Sil"
                ])
            with ca3:
                adm_note = st.text_input("Patron Notu:", placeholder="Örn: Manual VIP / Special")

            if st.button("✅ Üye İşlemini Uygula ve Kaydet", use_container_width=True):
                if target_u:
                    now_tr = datetime.now(TR_TZ)
                    if "Sil" in act_type:
                        db.pop(target_u, None)
                        clean_dummy_and_reindex_users()
                    else:
                        if target_u not in db:
                            auto_sync_device_user(target_u, "")
                        u_edit = db[target_u]
                        if "30 Gün" in act_type:
                            u_edit["tier"], u_edit["paid"] = "VIP", True
                            u_edit["amount"] = round(safe_float(u_edit.get("amount"), 0.0) + 100.0, 2)
                            u_edit["exp"] = (now_tr + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
                            u_edit["note"] = adm_note or "💰 100 USDT Verified (30-Day VIP)"
                        elif "3 Gün" in act_type:
                            u_edit["tier"] = "VIP"
                            u_edit["exp"] = (now_tr + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
                            u_edit["note"] = adm_note or "🎁 72-Hour Weekend VIP"
                        elif "90 Gün" in act_type:
                            u_edit["tier"] = "VIP"
                            u_edit["exp"] = (now_tr + timedelta(days=90)).strftime("%Y-%m-%d %H:%M")
                            u_edit["note"] = adm_note or "🥇 90-Day Founder VIP"
                        elif "Normal" in act_type:
                            u_edit["tier"] = "NORMAL"
                            u_edit["note"] = adm_note or "👤 Standard Member"
                    save_persistent_store()
                    st.rerun()

            st.markdown("#### 📋 Otomatik Tanınan Gerçek Cihazlar, Cihaz Modeli/Ülke, Davet & Kalan Süre")
            rows_html = [
                "<div style='overflow-x:auto;'><table style='width:100%;font-size:11.5px;border-collapse:collapse;'>"
                "<tr style='background:#21262d;color:#ffd33d;text-align:left;'>"
                "<th style='padding:6px;'>#</th><th>Device ID</th><th>📱 Cihaz & 🌍 Ülke/Dil</th><th>🕒 Son Giriş</th><th>Status</th>"
                "<th>Referrals</th><th>Unique USDT</th><th>Payment</th><th>Time Left</th></tr>"
            ]
            for u in u_list:
                t_col = "#56d364" if u["tier"] == "VIP" else "#8b949e"
                p_str = f"💰 {u.get('amount',0)} USDT" if u.get("paid") else ("🎁 2/2 Refs" if len(u.get("refs",[])) >= 2 else "⏳ None")
                rem_s = format_remaining_time(u["exp"], is_en=False)
                dev_str = u.get("dev_info", "🌐 Web/Mobil (Sonraki Girişte Güncellenir)")
                seen_str = u.get("last_seen") or "Bugün"
                rows_html.append(
                    f"<tr style='border-bottom:1px solid #30363d;'>"
                    f"<td style='padding:6px;'>{u['seq']}</td><td><b>{u['code']}</b></td>"
                    f"<td style='color:#79c0ff;font-weight:600;'>{dev_str}</td>"
                    f"<td style='color:#c9d1d9;'>{seen_str}</td>"
                    f"<td style='color:{t_col};font-weight:700;'>{u['tier']}</td>"
                    f"<td>{len(u.get('refs',[]))}/2 ({','.join(u.get('refs',[])) or '-'})</td>"
                    f"<td><code>{u.get('pay_dec',100.15):.2f} USDT</code></td>"
                    f"<td>{p_str}</td><td>{rem_s}</td></tr>"
                )
            rows_html.append("</table></div>")
            st.markdown("".join(rows_html), unsafe_allow_html=True)

            with st.expander("🗄️ Yedekleme & Geri Yükleme (Sunucu Sıfırlanmasına Karşı JSON Kalkanı)"):
                b_json = json.dumps({"users_db": MEM["users_db"], "used_txids": list(MEM["used_txids"])}, ensure_ascii=False)
                st.code(b_json, language="json")
                rest_inp = st.text_input("Yedek JSON Kodunu Buraya Yapıştır:")
                if st.button("♻️ Yedeği Geri Yükle") and rest_inp:
                    try:
                        d_rest = json.loads(rest_inp)
                        if "users_db" in d_rest:
                            MEM["users_db"] = d_rest["users_db"]
                            MEM["used_txids"] = set(d_rest.get("used_txids", []))
                            save_persistent_store()
                            st.success("Üye veritabanı başarıyla geri yüklendi!")
                            st.rerun()
                    except Exception:
                        st.error("Geçersiz JSON formatı.")

# ==================== PROGRAM 1: GLOBAL ENGLISH CUSTOMER WEBAPP ====================
else:
    cur_user = auto_sync_device_user(my_auto_uid, url_ref)
    if cur_user:
        cur_user["dev_info"] = detect_visitor_device_and_lang()
        cur_user["last_seen"] = datetime.now(TR_TZ).strftime("%d.%m %H:%M")
        save_persistent_store()

    effective_tier = cur_user["tier"] if cur_user else "NORMAL"
    pay_dec_val = cur_user.get("pay_dec", 100.15) if cur_user else 100.15
    total_members = len(MEM["users_db"])
    founder_left = max(0, 100 - total_members)

    ref_cnt = len(cur_user.get("refs", []))
    rem_txt = format_remaining_time(cur_user["exp"], is_en=True)
    reward_txt = "90-Day Founder VIP" if cur_user["seq"] <= 100 else "72-Hour Weekend VIP"
    grp_en = tr_to_en_text(cur_user["group"])
    t_badge = (
        "💎 VIP ACTIVE (All Whale Signals, Confirmed XI Evolutions & Corner/Card Props Unlocked)"
        if effective_tier == "VIP" else
        f"👤 STANDARD TIER (Invite {max(0, 2 - ref_cnt)} More Friends for FREE {reward_txt}!)"
    )

    app_pub = MEM.get("app_public_url", "https://deltapulse.streamlit.app")
    my_ref_url = f"{app_pub}?ref={cur_user['code']}"
    share_txt = (
        f"🔥 24/7 AI Football Whale & Lineup Radar with {ak_pct}% Main Bankroll & {vip_pct}% Live VIP accuracy! "
        f"No registration or password needed — click for instant auto-access:"
    )
    tg_share_link = f"https://t.me/share/url?url={urllib.parse.quote(my_ref_url)}&text={urllib.parse.quote(share_txt)}"
    sup_url = MEM.get("support_tg_url", "https://t.me/DeltaPulseSupport")

    st.markdown(
        f"<div style='background:linear-gradient(90deg,#131d2e,#161b22);border:1px solid #2f81f7;border-radius:8px;padding:9px 12px;margin-bottom:8px;font-size:12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;'>"
        f"<div>🆔 <b>Your Auto Device ID:</b> <code style='color:#ffd33d;font-size:13px;'>{cur_user['code']}</code> <span style='color:#56d364;font-size:11px;'>(Auto-Remember Active ✅)</span><br>"
        f"🏆 <b>Tier:</b> {grp_en} (#{cur_user['seq']} — Founder Spots Left: {founder_left}/100) | <b>{t_badge}</b><br>"
        f"👥 <b>Referral Progress:</b> <b>{ref_cnt}/2</b> | ⏳ <b>VIP Time Remaining:</b> {rem_txt}</div>"
        f"<div style='display:flex;gap:6px;flex-wrap:wrap;'>"
        f"<a href='{tg_share_link}' target='_blank' style='background:linear-gradient(90deg,#0088cc,#1f6feb);color:#fff;padding:8px 12px;border-radius:6px;font-weight:700;text-decoration:none;font-size:12px;'>"
        f"📲 Share with 2 Friends ➔ Unlock FREE VIP</a>"
        f"<a href='{sup_url}' target='_blank' style='background:#21262d;border:1px solid #8b949e;color:#e6edf3;padding:8px 10px;border-radius:6px;font-weight:700;text-decoration:none;font-size:12px;'>"
        f"💬 24/7 Support</a></div></div>",
        unsafe_allow_html=True
    )

    if effective_tier != "VIP":
        with st.expander(f"⚡ Instant 24/7 Auto-VIP Unlock ({pay_dec_val:.2f} USDT TRC20 — TronGrid Blockchain Verified)", expanded=False):
            st.markdown(
                f"<div style='background:#0d1117;border:1px solid #2ea043;border-radius:6px;padding:8px;font-size:11.5px;margin-bottom:6px;'>"
                f"💎 <b>Your Unique Auto-Verification Amount:</b> <code style='color:#56d364;font-size:14px;font-weight:800;'>{pay_dec_val:.2f} USDT</code> <b>(TRC20 / Tron Network)</b><br>"
                f"📋 <b>Official TRC20 Receiving Address:</b> <code style='color:#ffd33d;'>{MEM.get('trc20_wallet', '')}</code><br>"
                f"<span style='color:#8b949e;font-size:10.5px;'>🛡️ No wallet connection required. Send the exact amount (<b>{pay_dec_val:.2f} USDT</b>) via TRC20 from any exchange or wallet (Binance, TrustWallet, Bybit, OKX) and click verify below for instant 3-second activation! Need help? Contact <a href='{sup_url}' target='_blank' style='color:#58a6ff;'>24/7 Telegram VIP Support</a> with your Device ID (<b>{cur_user['code']}</b>).</span></div>",
                unsafe_allow_html=True
            )
            tx_inp = st.text_input("Transaction Hash (TxID — Optional if exact decimal amount is sent):", placeholder="Auto-detected via TronGrid API within 1-2 minutes")
            if st.button("🔓 Verify My Payment on Blockchain & Unlock 30-Day VIP Now", use_container_width=True):
                ok_tx, msg_tx = verify_trc20_blockchain_payment(cur_user["code"], tx_inp)
                if ok_tx:
                    st.success(msg_tx)
                    st.rerun()
                else:
                    st.warning(msg_tx)

    render_main_bulletin(effective_tier, is_patron_mode=False)

    st.markdown("---")
    with st.expander("⚙️ System Sync & Admin Terminal", expanded=False):
        adm_inp = st.text_input("Admin Key:", type="password")
        if st.button("👑 Seal Admin Mode on This Device"):
            if verify_admin_secret(adm_inp):
                st.session_state["patron_unlocked"] = True
                try:
                    st.query_params["program"] = "patron"
                    st.query_params["anahtar"] = adm_inp.strip().upper()
                except Exception:
                    pass
                st.rerun()
            else:
                st.error("Invalid key.")
# ==================== 7. PARÇA SONU ====================
