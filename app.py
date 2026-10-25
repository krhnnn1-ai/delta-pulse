# ==================== 1. PARÇA BAŞLANGICI ====================
import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Delta Pulse v5.1 LIVE PRO", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .block-container { padding-top: 0.6rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }
    div[data-testid="stExpander"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }
    .dp-card { background: #161b22; border-left: 4px solid #2ea043; padding: 10px 12px; border-radius: 8px; margin-bottom: 8px; font-size: 13px; }
    .dp-ak { border-left: 4px solid #f0b90b; background: #1c2128; }
    .dp-warn { border-left: 4px solid #f85149; background: #1f1619; }
    .dp-live { border-left: 4px solid #2f81f7; background: #161b22; }
    .dp-live-hot { border-left: 5px solid #f0b90b; background: #1c1d24; }
    .dp-badge { background: #21262d; padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #8b949e; }
    .dp-heat { background: #3d2800; color: #ffd33d; border: 1px solid #f0b90b; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 700; }
    @keyframes dpPulse {
        0% { opacity: 1; box-shadow: 0 0 10px rgba(240, 185, 11, 0.75); border-color: #f0b90b; }
        50% { opacity: 0.35; box-shadow: 0 0 2px rgba(240, 185, 11, 0.1); border-color: #d29922; }
        100% { opacity: 1; box-shadow: 0 0 10px rgba(240, 185, 11, 0.75); border-color: #f0b90b; }
    }
    .dp-exp-alert {
        display: inline-block;
        background: linear-gradient(90deg, #3d2800, #161b22);
        color: #ffd33d;
        border: 1px solid #f0b90b;
        padding: 5px 10px;
        border-radius: 6px;
        font-weight: 700;
        margin-top: 6px;
        animation: dpPulse 1.2s infinite ease-in-out;
    }
    .dp-exp-calm {
        display: inline-block;
        color: #8b949e;
        padding: 3px 0px;
        margin-top: 4px;
        font-size: 12px;
    }
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

@st.cache_resource
def get_persistent_memory():
    return {
        "locked_pre": {
            "Inter Milan vs Fiorentina": {"conf": 81, "pick": "Maç 2.5 Gol Üst", "warn": False},
            "Fortuna vs Excelsior": {"conf": 55, "pick": "Fortuna Çifte Şans (1X) & 3.5 Alt", "warn": False},
            "Hibernian vs Celtic": {"conf": 39, "pick": "Celtic Çifte Şans (X2) & 3.5 Alt", "warn": False}
        },
        "live_snapshots": {},
        "live_signals": {},
        "settled_results": {},
        "settled_date": "20261024",
        "base_wins": 88,
        "base_total": 128,
        "base_ak_wins": 9,
        "base_ak_total": 11,
        "opening_odds": {
            "Real Sociedad vs Levante": {"fav": "RSO", "val": -175, "tg": 3.5},
            "Inter Milan vs Fiorentina": {"fav": "INT", "val": -310, "tg": 3.5},
            "Union SG vs Cercle Brugge": {"fav": "USG", "val": -310, "tg": 3.5},
            "Barcelona vs Real Madrid": {"fav": "BAR", "val": -150, "tg": 4.5},
            "Hoffenheim vs Leverkusen": {"fav": "B04", "val": 110, "tg": 3.5},
            "Club Brugge vs Sint-Truidense": {"fav": "BRU", "val": -275, "tg": 3.5},
            "Freiburg vs Bayern": {"fav": "MUN", "val": -255, "tg": 3.5},
            "Udinese vs Milan": {"fav": "MIL", "val": -125, "tg": 2.5},
            "Marseille vs Le Havre AC": {"fav": "OLM", "val": -195, "tg": 3.5},
            "Liverpool vs Brighton": {"fav": "LIV", "val": 115, "tg": 3.5},
            "C Palace vs Newcastle": {"fav": "NEW", "val": 140, "tg": 3.5},
            "Lecce vs Juventus": {"fav": "JUV", "val": -205, "tg": 2.5},
            "Atalanta vs Frosinone": {"fav": "ATA", "val": -120, "tg": 3.5},
            "Genoa vs Venezia": {"fav": "GEN", "val": 110, "tg": 2.5},
            "Hull vs Brentford": {"fav": "BRE", "val": -145, "tg": 2.5},
            "Sporting vs Académico": {"fav": "SCP", "val": -425, "tg": 3.5},
            "Sparta vs Ajax": {"fav": "AJA", "val": -230, "tg": 3.5},
            "Rennes vs Strasbourg": {"fav": "REN", "val": -125, "tg": 3.5},
            "Toulouse vs Troyes": {"fav": "TOU", "val": -190, "tg": 2.5},
            "Athletic vs Getafe": {"fav": "ATH", "val": -175, "tg": 2.5},
            "Palermo vs Carrarese": {"fav": "PAL", "val": -215, "tg": 2.5},
            "Monaco vs Lille": {"fav": "MON", "val": 100, "tg": 2.5},
            "AZ Alkmaar vs FC Twente": {"fav": "AZ", "val": 115, "tg": 3.5},
            "Angers vs Lorient": {"fav": "LOR", "val": 150, "tg": 2.5},
            "Fortuna vs Excelsior": {"fav": "FOR", "val": 135, "tg": 2.5},
            "Man United vs Bournemouth": {"fav": "MAN", "val": 130, "tg": 2.5},
            "Konyaspor vs Genclerbirli": {"fav": "KNY", "val": -110, "tg": 2.5},
            "Hibernian vs Celtic": {"fav": "CEL", "val": -185, "tg": 3.5},
            "Sunderland vs Leeds": {"fav": "LEE", "val": 150, "tg": 2.5},
            "NEC vs FC Groningen": {"fav": "NEC", "val": 120, "tg": 3.5},
            "PSV vs Feyenoord": {"fav": "PSV", "val": 105, "tg": 3.5},
            "Motherwell vs Hearts": {"fav": "HOM", "val": 110, "tg": 2.5},
            "CD Sabadell vs Tenerife": {"fav": "CDS", "val": -110, "tg": 1.5},
            "Celta Vigo vs Betis": {"fav": "BET", "val": 125, "tg": 2.5},
            "Auxerre vs Le Mans": {"fav": "AUX", "val": 105, "tg": 2.5},
            "Nacional vs Braga": {"fav": "SCB", "val": -175, "tg": 2.5},
            "Rio Ave vs FC Famalicao": {"fav": "FCF", "val": 110, "tg": 2.5},
            "KAA Gent vs Anderlecht": {"fav": "GENT", "val": 135, "tg": 2.5},
            "Osnabruck vs Greuther Furth": {"fav": "OSN", "val": 115, "tg": 2.5},
            "Castellón vs Gijón": {"fav": "CAS", "val": -200, "tg": 2.5},
            "Verona vs Pisa": {"fav": "VER", "val": 125, "tg": 2.5},
            "Genk vs Standard Liege": {"fav": "GENK", "val": -135, "tg": 2.5},
            "Cádiz vs Ceuta": {"fav": "CAD", "val": -110, "tg": 2.5},
            "Estoril vs Moreirense": {"fav": "EPF", "val": -105, "tg": 2.5},
            "Holstein Kiel vs D Dresden": {"fav": "KSV", "val": 130, "tg": 2.5},
            "Albacete vs Eldense": {"fav": "ALB", "val": 140, "tg": 2.5}
        },
        "kickoff_odds": {},
        "last_valid_odds": {}
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
    parts = s.split(".")
    clean = parts[0]
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

def evaluate_pre_match(h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, odd_str, fav_abbr, fav_val, ou_val, kademe):
    match_key = f"{h_name} vs {a_name}"
    open_db = MEM["opening_odds"]

    if match_key not in open_db and fav_abbr and fav_val != 0:
        open_db[match_key] = {"fav": fav_abbr, "val": fav_val, "tg": ou_val}

    smart_tag = ""
    bonus_conf = 0
    tg_jumped = False
    ana_kasa_veto = False
    severe_drift_warning = False
    any_drift_warning = False

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

    fav_team = a_name if is_away_fav else h_name
    fav_mom = a_mom if is_away_fav else h_mom
    dog_mom = h_mom if is_away_fav else a_mom
    mom_diff = abs(h_mom - a_mom)
    form_clash = (dog_mom - fav_mom >= 20)
    cs_code = "X2" if is_away_fav else "1X"

    raw_conf = 50 + (int(mom_diff * 0.35) if not form_clash else -4)
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

    is_strong_market_fav = (fav_val <= -140 and fav_mom >= 55)
    is_elite_shootout = (h_mom >= 80 and a_mom >= 80 and ou_val >= 3.5)

    if ana_kasa_veto or form_clash or not (is_strong_market_fav or is_elite_shootout):
        if conf >= 83:
            conf = 74 if severe_drift_warning else 78

    if h_mom == a_mom and h_mom <= 35 and ou_val <= 2.5:
        conf = 25
        pick = "Maç 3.5 Gol Alt"
    elif conf >= 83 and kademe >= 0.88 and not ana_kasa_veto:
        if (dog_mom >= 58 and ou_val >= 3.5) or fav_mom < 55:
            pick = "Maç 2.5 Gol Üst (Ana Kasa)"
        else:
            pick = f"{fav_team} Takım Golü 1.5 Üst (Ana Kasa)"
    elif ou_val >= 3.5 or tg_jumped:
        if severe_drift_warning:
            pick = "Maç 2.5 Gol Üst [⚠️ERİME: KADRO BEKLE]"
        elif fav_mom < 50 and dog_mom < 40 and fav_val <= -150 and not tg_jumped:
            pick = f"{fav_team} Çifte Şans ({cs_code}) & 3.5 Alt"
        elif dog_mom < 45 and fav_val <= -165 and fav_mom >= 55 and not form_clash and not any_drift_warning:
            pick = f"{fav_team} Takım Golü 1.5 Üst"
        else:
            pick = "Maç 2.5 Gol Üst"
    else:
        if (h_mom >= 58 and a_mom >= 58) or (form_clash and dog_mom >= 65 and fav_val <= -110):
            pick = "Karşılıklı Gol Var (KG Var)"
        elif (fav_val <= -185 or (dog_mom < 20 and fav_val <= -165)) and fav_mom >= 55 and not form_clash and not any_drift_warning:
            pick = f"{fav_team} Takım Golü 1.5 Üst"
        elif (mom_diff >= 25 and fav_mom > dog_mom) or (fav_val <= -150 and fav_mom < 55 and not form_clash):
            pick = f"{fav_team} Çifte Şans ({cs_code}) & 3.5 Alt"
        else:
            pick = "Maç 3.5 Gol Alt"

    display_odd = f"{odd_str}{smart_tag}" if smart_tag else odd_str
    return conf, pick, display_odd, severe_drift_warning

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
# ==================== 2. PARÇA SONU ====================
# ==================== 3. PARÇA BAŞLANGICI ====================
def analyze_live_pro(match_title, h_name, a_name, h_abbr, a_abbr, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_poss, m_int, h_mom, a_mom, fav_abbr, fav_val, ou_val, has_live_api_odds):
    tot_goals = h_score + a_score
    tot_sh = h_sh + a_sh
    tot_sot = h_sot + a_sot
    tot_cor = h_cor + a_cor
    h_sot_pct = int(round((h_sot / h_sh) * 100)) if h_sh > 0 else 0
    a_sot_pct = int(round((a_sot / a_sh) * 100)) if a_sh > 0 else 0
    tot_sot_pct = int(round((tot_sot / tot_sh) * 100)) if tot_sh > 0 else 0
    a_poss = (100 - h_poss) if h_poss > 0 else 0

    base_ref = MEM["kickoff_odds"].get(match_title) or MEM["opening_odds"].get(match_title) or {"fav": fav_abbr, "val": fav_val, "tg": ou_val}
    ref_fav = base_ref.get("fav", fav_abbr)
    ref_val = base_ref.get("val", fav_val)
    ref_tg = base_ref.get("tg", ou_val)

    is_away_fav = False
    if ref_fav:
        if ref_fav.upper() == a_abbr.upper() or ref_fav.upper() in a_name.upper()[:4]:
            is_away_fav = True
    elif a_mom > h_mom + 12:
        is_away_fav = True

    fav_team_name = a_name if is_away_fav else h_name
    h_is_strong_fav = (not is_away_fav and (ref_val <= -140 or h_mom >= 65))
    a_is_strong_fav = (is_away_fav and (ref_val <= -140 or a_mom >= 65))

    goal_line = f"{tot_goals + 0.5}"
    rem_mins = max(1, 90 - m_int)
    cor_add = 2.5 if rem_mins >= 25 else 1.5
    cor_line = f"{tot_cor + cor_add}"

    heat = 20 + int((tot_sh / max(12, m_int)) * 28) + (tot_sot * 4) + int(tot_cor * 2.2)
    sot_tag = ""
    exp_list = []
    sig_type = ""

    if has_live_api_odds and ref_val != 0 and fav_val != 0:
        live_diff = calc_true_odds_delta(ref_val, fav_val)
        if live_diff <= -15:
            sot_tag += f"|📈CanlıOran({live_diff})"
            heat += 10
            exp_list.append(f"📈 CANLI ORAN BASKISI ({fav_team_name} canlı oranı {live_diff}p daha sertleşti!)")
        elif m_int >= 25 and tot_goals == 0 and ou_val >= ref_tg and ref_tg >= 2.5:
            sot_tag += f"|📈CanlıTG({ou_val})"
            heat += 8
            exp_list.append(f"📈 CANLI BAREM DİRENCİ (Dk {m_int}' 0-0 ama canlı barem {ou_val} seviyesinde tutuldu!)")

    h_pressing = (h_sh >= 5 or h_cor >= 3 or h_poss >= 58)
    a_pressing = (a_sh >= 5 or a_cor >= 3 or a_poss >= 58)

    if h_is_strong_fav and h_score <= a_score and h_pressing and m_int >= 18:
        if h_score < a_score:
            sot_tag += "|💎FavGeride->Pusu"
            heat += 22
            sig_type = "KORNER" if h_cor >= 3 else "GOL"
            exp_list.append(
                f"💎 ELMAS PUSU ({h_name} Favori Geride!): %{h_poss} top, {h_sh} şut, {h_cor} kornerle yükleniyor "
                f"➔ 🎯 HAMLE: Maç {goal_line} Gol Üst & Toplam {cor_line} Korner Üst"
            )
        elif m_int >= 25:
            sot_tag += "|💎FavKilitli->Pusu"
            heat += 16
            sig_type = "GOL"
            exp_list.append(
                f"💎 FAVORİ ABLUKASI ({h_name} {h_score}-{a_score}): %{h_poss} top, {h_sh}({h_sot}) şut, {h_cor} korner "
                f"➔ 🎯 HAMLE: {h_name} {h_score + 0.5} Gol Üst / Toplam {cor_line} Korner Üst"
            )
    elif a_is_strong_fav and a_score <= h_score and a_pressing and m_int >= 18:
        if a_score < h_score:
            sot_tag += "|💎FavGeride->Pusu"
            heat += 22
            sig_type = "KORNER" if a_cor >= 3 else "GOL"
            exp_list.append(
                f"💎 ELMAS PUSU ({a_name} Favori Geride!): %{a_poss} top, {a_sh} şut, {a_cor} kornerle yükleniyor "
                f"➔ 🎯 HAMLE: Maç {goal_line} Gol Üst & Toplam {cor_line} Korner Üst"
            )
        elif m_int >= 25:
            sot_tag += "|💎FavKilitli->Pusu"
            heat += 16
            sig_type = "GOL"
            exp_list.append(
                f"💎 FAVORİ ABLUKASI ({a_name} {h_score}-{a_score}): %{a_poss} top, {a_sh}({a_sot}) şut, {a_cor} korner "
                f"➔ 🎯 HAMLE: {a_name} {a_score + 0.5} Gol Üst / Toplam {cor_line} Korner Üst"
            )

    if (h_score < a_score and h_pressing) or (a_score < h_score and a_pressing):
        if "|💎FavGeride->Pusu" not in sot_tag:
            sot_tag += "|🚩GerideBaskı->Korner"
            heat += 14
            sig_type = sig_type or "KORNER"
            p_name = h_name if h_score < a_score else a_name
            p_sh = h_sh if h_score < a_score else a_sh
            p_cor = h_cor if h_score < a_score else a_cor
            exp_list.append(
                f"🚩 GERİDEKİ BASKISI ({p_name}): {p_sh} şut ve {p_cor} kornerle kanatları zorluyor "
                f"➔ 🎯 HAMLE: Toplam {cor_line} Korner Üst"
            )

    if (h_sh >= 4 and h_sot_pct >= 55) or (a_sh >= 4 and a_sot_pct >= 55) or (tot_sh >= 7 and tot_sot_pct >= 45):
        sot_tag += "|🎯KeskinGol"
        heat += 12
        sig_type = sig_type or "GOL"
        exp_list.append(
            f"⚡ KESKİN ŞUT (%{tot_sot_pct} İsabet [{tot_sot}/{tot_sh}]) ➔ 🎯 HAMLE: Canlı Maç {goal_line} Gol Üst"
        )
    elif (h_sh >= 8 and h_sot_pct <= 18) or (a_sh >= 8 and a_sot_pct <= 18):
        sot_tag += "|📐KörŞut->Korner"
        heat += 10
        sig_type = sig_type or "KORNER"
        dom_t = h_name if h_sh >= a_sh else a_name
        exp_list.append(
            f"📐 KÖR ŞUT BASKISI ({dom_t} çerçeveyi bulamıyor, toplar kornere gidiyor) ➔ 🎯 HAMLE: Toplam {cor_line} Korner Üst"
        )

    if 22 <= m_int <= 78 and tot_goals <= 1 and (ref_tg >= 3.5 or ref_val <= -175) and heat >= 62:
        sot_tag += "|💹DeğerFırsatı"
        heat += 7
        sig_type = sig_type or "GOL"
        exp_list.append(
            f"💹 DEĞER FIRSATI (VALUE): Maç önü beklentisi yüksek (TG:{ref_tg} / {ref_fav} {ref_val}); "
            f"Dk {m_int}' itibarıyla canlı oranlar şişti ama saha baskısı çok güçlü!"
        )

    heat = max(15, min(99, heat))

    if 15 <= m_int <= 75 and heat >= 68 and sig_type and match_title not in MEM["live_signals"]:
        if sig_type == "GOL":
            MEM["live_signals"][match_title] = {
                "type": "GOL", "min": m_int, "base": tot_goals, "need": 1,
                "label": f"{m_int}' ({h_score}-{a_score}) ➔ Maç {tot_goals + 0.5} Üst", "status": "WAIT"
            }
        else:
            MEM["live_signals"][match_title] = {
                "type": "KORNER", "min": m_int, "base": tot_cor, "need": 2,
                "label": f"{m_int}' ({h_cor}-{a_cor}K) ➔ +2 Korner", "status": "WAIT"
            }

    if match_title in MEM["live_signals"]:
        sig = MEM["live_signals"][match_title]
        if sig["type"] == "GOL" and tot_goals >= sig["base"] + sig["need"]:
            sig["status"] = "WON"
        elif sig["type"] == "KORNER" and tot_cor >= sig["base"] + sig["need"]:
            sig["status"] = "WON"
        if sig["status"] == "WON":
            exp_list.insert(0, f"✅ CANLI SİNYAL GELDİ! [{sig['label']}]")

    if not exp_list:
        if m_int >= 22 and tot_sh <= 4 and tot_sot <= 1:
            exp_list.append(f"🛡️ Düşük Tempo ({m_int}' itibarıyla {tot_sot} isabetli şut var, canlı üstten uzak dur)")
        else:
            exp_list.append(f"⚖️ Dengeli Akış (Baskı: %{heat} — Şut veya korner kırılması bekleniyor)")

    return heat, sot_tag, " • ".join(exp_list)

def calc_projected_score(m):
    h_m, a_m = m["h_mom"], m["a_mom"]
    tg = m["tg"]
    pick = m["pick"]
    away_fav = (m["a_name"] in pick) or (a_m > h_m + 15)

    if "3.5 Gol Alt" in pick and "Çifte Şans" not in pick:
        return ("1-1", "1-0") if h_m >= a_m else ("0-1", "1-1")
    elif "Çifte Şans" in pick:
        return ("1-2", "0-2") if "X2" in pick else ("2-0", "1-0")
    elif "Takım Golü 1.5 Üst" in pick:
        if away_fav:
            return ("1-3", "0-2") if tg >= 3.5 else ("0-2", "1-2")
        return ("3-1", "2-0") if tg >= 3.5 else ("2-0", "2-1")
    else:
        if h_m >= 60 and a_m >= 60:
            return ("1-2", "2-2") if away_fav else ("2-1", "2-2")
        return ("1-3", "1-2") if away_fav else ("3-1", "2-1")

def generate_card_comment_and_score(m):
    odd_s = m["odd_str"]
    h_m, a_m = m["h_mom"], m["a_mom"]
    notes = []

    if "🔥Δ-" in odd_s:
        d_val = odd_s.split("🔥Δ-")[1].split(" ")[0]
        notes.append(f"Sabah baz oranına göre favoriye -{d_val}p Akıllı Para girişi var")
    elif "🚨Δ+" in odd_s:
        d_val = odd_s.split("🚨Δ+")[1].split(" ")[0]
        notes.append(f"DİKKAT! Oranda +{d_val}p sert erime var, taraf/1.5 Üst bahsinden uzak dur")
    elif "⚠️Δ+" in odd_s:
        d_val = odd_s.split("⚠️Δ+")[1].split(" ")[0]
        notes.append(f"Oranda +{d_val}p gevşeme var, koruma çizgisinde kal")

    if "💥TG↑" in odd_s:
        notes.append("Toplam gol baremi yukarı kırıldı (Yüksek gol temposu)")
    elif "📉TG↓" in odd_s:
        notes.append("Gol baremi geri çekildi (Kontrollü tempo)")

    if abs(h_m - a_m) >= 28:
        strong_t = m["h_name"] if h_m > a_m else m["a_name"]
        notes.append(f"{strong_t} form momentumunda (+{abs(h_m - a_m)} fark) üstün")
    elif h_m >= 60 and a_m >= 60:
        notes.append(f"İki takım da yüksek hücum formunda ({h_m} vs {a_m})")
    elif max(h_m, a_m) < 50:
        notes.append(f"Hücum formları düşük ({h_m}-{a_m}), 1.5 Üst yerine koruma devrede")

    if not notes:
        notes.append("Oranlar ve form dengesi sabah başlangıç çizgisini koruyor")

    s1, s2 = calc_projected_score(m)
    return " • ".join(notes) + f" | 🎯 **Tahmini Skor:** `{s1} / {s2}`"

def build_autonomous_merkez_us_report(pre_m, live_m, tot_w, tot_t, tot_pct, ak_w, ak_t, lv_w, lv_t):
    lines = [
        f"### 🧠 Delta Pulse v5.1 LIVE PRO — Otonom Strateji Raporu "
        f"(`Karne: {tot_w}/{tot_t} %{tot_pct} | AK: {ak_w}/{ak_t} | CanlıPusu: {lv_w}/{lv_t}`)\n"
    ]

    if live_m:
        lines.append("#### 🔴 1. Canlı Baskı, Canlı Oran & Net Barem Pusulası")
        for lm in live_m:
            lines.append(
                f"* **🔥 [Baskı: %{lm['heat']}] {lm['clock']} | {lm['h_name']} {lm['h_score']}-{lm['a_score']} {lm['a_name']}** "
                f"(`Şut: {lm['h_sh']}({lm['h_sot']})-{lm['a_sh']}({lm['a_sot']})` | `Korner: {lm['h_cor']}-{lm['a_cor']}` {lm['delta_str']}) "
                f"➔ 🔮 **{lm['live_exp']}**"
            )
        lines.append("")

    ak_list = [m for m in pre_m if "Ana Kasa" in m["pick"]]
    smart_list = [m for m in pre_m if ("🔥Δ-" in m["odd_str"] or "💥TG↑" in m["odd_str"]) and "Ana Kasa" not in m["pick"]]

    lines.append("#### 💎 2. Ana Kasa & Akıllı Para (`🔥Δ-` / `💥TG↑`) Çekirdeği")
    for m in ak_list[:5]:
        s1, s2 = calc_projected_score(m)
        lines.append(f"* **[{m['saat']} | %{m['conf']}] {m['mac']}** (`{m['odd_str']}` | `Mom: {m['h_mom']}-{m['a_mom']}`) ➔ 🎯 **{m['pick']}** *(Skor: `{s1} / {s2}`)*")
    if smart_list:
        lines.append("\n**🔥 Gün İçi Para Girişi Alan En Güçlü Adaylar:**")
        for m in smart_list[:6]:
            s1, s2 = calc_projected_score(m)
            lines.append(f"* **[{m['saat']} | %{m['conf']}] {m['mac']}** (`{m['odd_str']}`) ➔ **{m['pick']}** *(Skor: `{s1}`)*")

    drift_list = [m for m in pre_m if ("🚨Δ+" in m["odd_str"] or "⚠️Δ+" in m["odd_str"] or m["warn"])]
    if drift_list:
        lines.append("\n#### 🚨 3. Otonom Erime Freni (Oranı Gevşeyen / Tuzak Maçlar)")
        for m in drift_list[:5]:
            lines.append(f"* **⚠️ [{m['saat']}] {m['mac']}** (`{m['odd_str']}` | Güven: `%{m['conf']}`): Favoriden para çıkışı tespit edildi. Takım 1.5 Üst veya taraf bahsine girilmemeli!")

    return "\n".join(lines)

def get_stat(comp_team, names):
    for s in (comp_team.get("statistics") or []):
        if isinstance(s, dict) and s.get("name") in names:
            return safe_int(s.get("displayValue"), 0)
    return 0

@st.cache_data(ttl=45)
def fetch_all_matches():
    now_tr = datetime.now(TR_TZ)
    date_str = now_tr.strftime("%Y%m%d")
    results = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for lig_adi, (slug, kademe) in LEAGUES.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={date_str}"
        try:
            r = requests.get(url, headers=headers, timeout=5)
            data = r.json() if r.status_code == 200 else {}
        except Exception:
            data = {}

        if not isinstance(data, dict):
            continue

        for ev in (data.get("events") or []):
            if not isinstance(ev, dict):
                continue
            comp_list = ev.get("competitions") or []
            comp = comp_list[0] if (len(comp_list) > 0 and isinstance(comp_list[0], dict)) else {}
            status_obj = (comp.get("status") or {}).get("type") or {}
            state = str(status_obj.get("state") or "pre")
            detail_clock = str(status_obj.get("shortDetail") or "")

            competitors = [c for c in (comp.get("competitors") or []) if isinstance(c, dict)]
            if len(competitors) < 2:
                continue
            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

            h_team = home.get("team") or {}
            a_team = away.get("team") or {}
            h_name = str(h_team.get("shortDisplayName") or "Ev")
            a_name = str(a_team.get("shortDisplayName") or "Dep")
            h_abbr = str(h_team.get("abbreviation") or "")
            a_abbr = str(a_team.get("abbreviation") or "")
            match_title = f"{h_name} vs {a_name}"

            h_score = safe_int(home.get("score"), 0)
            a_score = safe_int(away.get("score"), 0)
            h_mom = parse_form_momentum(home.get("form"))
            a_mom = parse_form_momentum(away.get("form"))
            odd_str, fav_abbr, fav_val, ou_val, has_live_api_odds = safe_parse_odds(comp, match_title, state)

            raw_date = str(ev.get("date") or "")
            saat_str = "00:00"
            if "T" in raw_date and len(raw_date) >= 16:
                utc_h = safe_int(raw_date[11:13], 0)
                utc_m = raw_date[14:16]
                saat_str = f"{(utc_h + 3) % 24:02d}:{utc_m}"

            h_sh = get_stat(home, ["totalShots", "shotsSummary"])
            a_sh = get_stat(away, ["totalShots", "shotsSummary"])
            h_sot = get_stat(home, ["shotsOnTarget"])
            a_sot = get_stat(away, ["shotsOnTarget"])
            h_cor = get_stat(home, ["wonCorners", "corners"])
            a_cor = get_stat(away, ["wonCorners", "corners"])
            h_poss = get_stat(home, ["possessionPct"])
            cards = (
                get_stat(home, ["yellowCards"]) + get_stat(away, ["yellowCards"]) +
                get_stat(home, ["redCards"]) + get_stat(away, ["redCards"])
            )

            conf, pick, disp_odd, warn_flag = evaluate_pre_match(
                h_name, a_name, h_abbr, a_abbr, h_mom, a_mom, odd_str, fav_abbr, fav_val, ou_val, kademe
            )

            if state == "pre":
                MEM["locked_pre"][match_title] = {"conf": conf, "pick": pick, "warn": warn_flag}
            elif match_title in MEM["locked_pre"]:
                conf = MEM["locked_pre"][match_title]["conf"]
                pick = MEM["locked_pre"][match_title]["pick"]
                warn_flag = MEM["locked_pre"][match_title].get("warn", False)

            delta_str = ""
            sot_tag = ""
            live_exp = ""
            heat = 0
            if state == "in":
                cur_min = detail_clock.replace("'", "").replace("HT", "45").split("+")[0].strip()
                m_int = safe_int(cur_min, 45)

                heat, sot_tag, live_exp = analyze_live_pro(
                    match_title, h_name, a_name, h_abbr, a_abbr, h_score, a_score,
                    h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_poss, m_int,
                    h_mom, a_mom, fav_abbr, fav_val, ou_val, has_live_api_odds
                )

                snap = MEM["live_snapshots"].get(match_title)
                if not snap:
                    MEM["live_snapshots"][match_title] = {
                        "min": m_int, "h_sh": h_sh, "a_sh": a_sh, "h_cor": h_cor, "a_cor": a_cor
                    }
                elif m_int > snap["min"] + 5:
                    d_hs = max(0, h_sh - snap["h_sh"])
                    d_as = max(0, a_sh - snap["a_sh"])
                    d_hc = max(0, h_cor - snap["h_cor"])
                    d_ac = max(0, a_cor - snap["a_cor"])
                    delta_str = f"|Δ({snap['min']}'->{m_int}'):+{d_hs}/{d_as}Ş,+{d_hc}/{d_ac}K"

            if state == "post":
                if match_title in MEM["live_signals"]:
                    sig = MEM["live_signals"][match_title]
                    if sig["type"] == "GOL" and (h_score + a_score) >= sig["base"] + sig["need"]:
                        sig["status"] = "WON"
                    elif sig["type"] == "KORNER" and (h_cor + a_cor) >= sig["base"] + sig["need"]:
                        sig["status"] = "WON"
                    elif sig["status"] == "WAIT":
                        sig["status"] = "LOST"

                if date_str != MEM.get("settled_date", ""):
                    won = evaluate_ft_result(pick, h_name, a_name, h_score, a_score)
                    MEM["settled_results"][match_title] = {"won": won, "is_ak": ("Ana Kasa" in pick)}

            results.append({
                "state": state, "saat": saat_str, "clock": detail_clock, "lig": lig_adi,
                "mac": match_title, "h_name": h_name, "a_name": a_name,
                "h_score": h_score, "a_score": a_score, "conf": conf,
                "h_mom": h_mom, "a_mom": a_mom, "odd_str": disp_odd, "tg": ou_val,
                "pick": pick, "warn": warn_flag, "h_sh": h_sh, "a_sh": a_sh,
                "h_sot": h_sot, "a_sot": a_sot, "h_cor": h_cor, "a_cor": a_cor,
                "cards": cards, "h_poss": h_poss, "delta_str": delta_str,
                "sot_tag": sot_tag, "live_exp": live_exp, "heat": heat
            })
    return results

matches = fetch_all_matches()

today_wins = sum(1 for v in MEM["settled_results"].values() if v["won"])
today_total = len(MEM["settled_results"])
today_ak_w = sum(1 for v in MEM["settled_results"].values() if v["is_ak"] and v["won"])
today_ak_t = sum(1 for v in MEM["settled_results"].values() if v["is_ak"])

tot_w = MEM["base_wins"] + today_wins
tot_t = MEM["base_total"] + today_total
tot_pct = int(round((tot_w / tot_t) * 100)) if tot_t > 0 else 0
ak_w = MEM["base_ak_wins"] + today_ak_w
ak_t = MEM["base_ak_total"] + today_ak_t

lv_settled = [s for s in MEM["live_signals"].values() if s["status"] in ("WON", "LOST")]
lv_w = sum(1 for s in lv_settled if s["status"] == "WON")
lv_t = len(lv_settled)
lv_active = sum(1 for s in MEM["live_signals"].values() if s["status"] == "WAIT")

now_str = datetime.now(TR_TZ).strftime("%Y%m%d %H:%M")
mini_lines = [
    f"⚡ DP-MİNİ [{now_str}] Karne:{tot_w}/{tot_t}(%{tot_pct}) AK:{ak_w}/{ak_t} CanlıPusu:{lv_w}/{lv_t}(Aktif:{lv_active})"
]

live_m = sorted([m for m in matches if m["state"] == "in"], key=lambda x: x["heat"], reverse=True)
pre_m = sorted([m for m in matches if m["state"] == "pre"], key=lambda x: x["conf"], reverse=True)
post_m = [m for m in matches if m["state"] == "post"]

for m in live_m:
    clk = str(m["clock"]).replace(" ", "")
    mini_lines.append(
        f"CANLI|{clk}|🔥%{m['heat']}|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}|"
        f"Şut:{m['h_sh']}({m['h_sot']})-{m['a_sh']}({m['a_sot']})|"
        f"Kor:{m['h_cor']}-{m['a_cor']}|Kart:{m['cards']}|Top:%{m['h_poss']}"
        f"{m['delta_str']}{m['sot_tag']}|Önü:{m['pick']}"
    )

for m in pre_m:
    mini_lines.append(
        f"ÖNÜ|{m['saat']}|{m['lig']}|{m['mac']}|%{m['conf']}|"
        f"Mom:{m['h_mom']}-{m['a_mom']}|{m['odd_str']}|TG:{m['tg']} -> {m['pick']}"
    )

for m in post_m:
    icon = "✅" if evaluate_ft_result(m["pick"], m["h_name"], m["h_name"] if m["a_name"] == "" else m["a_name"], m["h_score"], m["a_score"]) else "❌"
    mini_lines.append(f"FT|FT|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}|{icon}|{m['pick']}")

full_dp_text = "\n".join(mini_lines)

st.markdown(
    f"**📊 Karne:** `{tot_w}/{tot_t} (%{tot_pct})` | **💎 Ana Kasa:** `{ak_w}/{ak_t}` | "
    f"**🎯 Canlı Pusu:** `{lv_w}/{lv_t} (Aktif: {lv_active})` | **🔥 Canlı:** `{len(live_m)}`"
)

col_btn1, col_btn2 = st.columns([3, 1])
with col_btn1:
    if st.button("🧠 GEMİNİ v5.1 LIVE PRO RAPORUNU ÇIKAR", use_container_width=True):
        MEM["last_ai_report"] = build_autonomous_merkez_us_report(pre_m, live_m, tot_w, tot_t, tot_pct, ak_w, ak_t, lv_w, lv_t)
with col_btn2:
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if MEM.get("last_ai_report"):
    st.info(MEM["last_ai_report"])

with st.expander("📲 DP-MİNİ Ham Veri Kopyala"):
    st.code(full_dp_text, language="text")

if live_m:
    st.markdown("### 🔴 Canlı PRO Radar (Baskı Puanı & Canlı Değer Sıralı)")
    for m in live_m:
        is_hot_exp = any(k in m["live_exp"] for k in ["💎", "⚡", "🚩", "📐", "📈", "💹", "✅"])
        exp_cls = "dp-exp-alert" if is_hot_exp else "dp-exp-calm"
        card_c = "dp-card dp-live-hot" if m["heat"] >= 68 else "dp-card dp-live"
        st.markdown(
            f"<div class='{card_c}'><span class='dp-heat'>🔥 Baskı: %{m['heat']}</span> "
            f"<b>⏱️ {m['clock']} | {m['h_name']} {m['h_score']} - {m['a_score']} {m['a_name']}</b> "
            f"<span class='dp-badge'>{m['lig']}</span><br>"
            f"🎯 Şut: <b>{m['h_sh']}({m['h_sot']}) - {m['a_sh']}({m['a_sot']})</b> | 🚩 Korner: <b>{m['h_cor']}-{m['a_cor']}</b> | "
            f"🟨 Kart: <b>{m['cards']}</b> | ⚽ Top: <b>%{m['h_poss']}</b> {m['delta_str']} {m['sot_tag']}<br>"
            f"📌 <b>Kilitli Hedef:</b> {m['pick']}<br>"
            f"<div class='{exp_cls}'>🔮 <b>Canlı PRO:</b> {m['live_exp']}</div></div>",
            unsafe_allow_html=True
        )

st.markdown("### ⏳ Maç Önü v5.1 Otonom Sinyaller & Otomatik Yorumlar")
for m in pre_m:
    if "Ana Kasa" in m["pick"]:
        card_cls = "dp-card dp-ak"
    elif m["warn"]:
        card_cls = "dp-card dp-warn"
    else:
        card_cls = "dp-card"
    auto_comm = generate_card_comment_and_score(m)
    st.markdown(
        f"<div class='{card_cls}'><b>🕒 {m['saat']} | {m['mac']}</b> — <b>%{m['conf']} Güven</b> "
        f"<span class='dp-badge'>{m['lig']}</span><br>"
        f"📈 Mom: <b>%{m['h_mom']} vs %{m['a_mom']}</b> | 💰 Oran: <b>{m['odd_str']}</b> | ⚽ TG: <b>{m['tg']}</b><br>"
        f"🎯 <b>Net Hedef:</b> {m['pick']}<br>"
        f"💬 <span style='color:#8b949e;'>{auto_comm}</span></div>",
        unsafe_allow_html=True
    )
# ==================== 3. PARÇA SONU ====================
