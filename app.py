import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# ==========================================
# PARÇA 1: SAYFA AYARLARI VE 22 LİG HAVUZU
# ==========================================
st.set_page_config(page_title="Delta Pulse v4.8", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .block-container { padding-top: 0.6rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }
    div[data-testid="stExpander"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }
    .dp-card { background: #161b22; border-left: 4px solid #2ea043; padding: 10px 12px; border-radius: 8px; margin-bottom: 8px; font-size: 13px; }
    .dp-ak { border-left: 4px solid #f0b90b; background: #1c2128; }
    .dp-warn { border-left: 4px solid #f85149; background: #1f1619; }
    .dp-live { border-left: 4px solid #2f81f7; background: #161b22; }
    .dp-badge { background: #21262d; padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #8b949e; }
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
# ==========================================
# PARÇA 2: KALICI HAFIZA VE 00:02 BAZ ORANLAR
# ==========================================
@st.cache_resource
def get_persistent_memory():
    return {
        "locked_pre": {},
        "live_snapshots": {},
        "settled_results": {},
        "base_wins": 16,
        "base_total": 21,
        "base_ak_wins": 3,
        "base_ak_total": 3,
        "opening_odds": {
            "Sporting vs LASK Linz": {"fav": "SCP", "val": -525, "tg": 3.5},
            "Betis vs Feyenoord": {"fav": "BET", "val": -180, "tg": 3.5},
            "Real Madrid vs RB Leipzig": {"fav": "RMA", "val": -400, "tg": 4.5},
            "Aston Villa vs Viking FK": {"fav": "AVL", "val": -450, "tg": 3.5},
            "Club Brugge vs Lens": {"fav": "BRU", "val": 100, "tg": 3.5},
            "Como vs Man United": {"fav": "COMO", "val": 115, "tg": 3.5},
            "Inter Milan vs Shakhtar": {"fav": "INT", "val": -475, "tg": 3.5},
            "Levante vs Athletic": {"fav": "ATH", "val": 115, "tg": 2.5},
            "Bayern vs Arsenal": {"fav": "MUN", "val": 105, "tg": 2.5},
            "Reading vs Leyton Orient": {"fav": "REA", "val": -185, "tg": 2.5},
            "Lille vs Galatasaray": {"fav": "LILL", "val": 115, "tg": 2.5}
        }
    }

MEM = get_persistent_memory()

def american_to_steps(odd):
    """Amerikan oranındaki +100/-100 sıfır geçişini gerçek puana çevirir."""
    if odd >= 100:
        return odd - 100
    elif odd <= -100:
        return odd + 100
    return 0

def calc_true_odds_delta(open_val, cur_val):
    """Negatif sonuç = Oran düştü (Akıllı Para), Pozitif sonuç = Oran yükseldi (Gevşeme/Erime)."""
    return american_to_steps(cur_val) - american_to_steps(open_val)

def parse_form_momentum(form_str):
    if not form_str:
        return 50
    weights = [1.0, 1.2, 1.5, 1.8, 2.2]
    chars = list(form_str.upper()[-5:])
    score, max_s = 0.0, 0.0
    for i, ch in enumerate(chars):
        w = weights[i] if i < len(weights) else 1.0
        max_s += w * 3.0
        if ch == 'W':
            score += w * 3.0
        elif ch == 'D':
            score += w * 1.0
    return int(round((score / max_s) * 100)) if max_s > 0 else 50

def parse_odds(comp):
    odds_list = comp.get("odds", [])
    if not odds_list:
        return "Veri Yok", "", 0, 2.5
    o = odds_list[0]
    details = o.get("details", "") or "Veri Yok"
    ou = o.get("overUnder", 2.5)
    try:
        ou_val = float(ou)
    except Exception:
        ou_val = 2.5

    fav_abbr, fav_val = "", 0
    if details and details != "Veri Yok" and " " in details:
        parts = details.split(" ")
        fav_abbr = parts[0].strip()
        try:
            fav_val = int(float(parts[-1]))
        except Exception:
            fav_val = 0
    return details, fav_abbr, fav_val, ou_val
    # ==========================================
# PARÇA 3: v4.8 OTONOM MERKEZ ÜS KARAR MOTORU
# ==========================================
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

    if match_key in open_db and fav_val != 0:
        op = open_db[match_key]
        # 1. Favori El Değiştirmesi (Flip)
        if op["fav"] and fav_abbr and op["fav"] != fav_abbr:
            smart_tag += f" 🔄FAV({op['fav']}->{fav_abbr})"
            bonus_conf += 5
        else:
            # 2. Gerçek Oran Farkı (Sıfır Geçişi Düzeltmeli)
            diff = calc_true_odds_delta(op["val"], fav_val)
            if diff <= -10:
                smart_tag += f" 🔥Δ{diff}"
                bonus_conf += min(7, abs(diff) // 7)
            elif diff >= 40:
                # SPORTING KURALI: 40+ Puanlık Sert Erime -> Ana Kasa Veto & Ağır Puan Kırpma!
                smart_tag += f" 🚨Δ+{diff}"
                bonus_conf -= min(26, 12 + (diff // 7))
                ana_kasa_veto = True
                severe_drift_warning = True
            elif diff >= 15:
                # Orta Ölçekli Gevşeme (Betis / Aston Villa / Como)
                smart_tag += f" ⚠️Δ+{diff}"
                bonus_conf -= min(12, 5 + (diff // 5))
                if fav_val > -250:
                    ana_kasa_veto = True

        # 3. Toplam Gol Baremi Sıçraması (Bayern - Arsenal Kuralı)
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

    raw_conf = 50 + int(mom_diff * 0.35)
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

    conf = int(round(raw_conf * min(1.05, max(0.78, kademe)))) + bonus_conf
    conf = max(25, min(97, conf))

    # Sahte Ana Kasa Freni (+100/-110 Oran Koruması) VE Erime Vetosu
    is_strong_market_fav = (fav_val <= -140)
    is_elite_shootout = (h_mom >= 80 and a_mom >= 80 and ou_val >= 3.5)

    if ana_kasa_veto or not (is_strong_market_fav or is_elite_shootout):
        if conf >= 83:
            conf = 74 if severe_drift_warning else 78

    # OTONOM TAHMİN ATAMA MOTORU
    if h_mom == a_mom and h_mom <= 35 and ou_val <= 2.5:
        conf = 25
        pick = "Maç Önü PAS (3.5 Alt / İY 1.5 Alt)"
    elif conf >= 83 and kademe >= 0.88 and not ana_kasa_veto:
        if fav_val <= -350 and fav_mom >= 75 and dog_mom <= 72:
            pick = f"{fav_team} Takım Golü 2.5 Üst / Maç 3.5 Üst (Ana Kasa)"
        else:
            pick = f"KG Var & 2.5 Üst / {fav_team} 1.5 Üst (Ana Kasa)"
    elif ou_val >= 3.5 or tg_jumped:
        if severe_drift_warning:
            pick = f"{fav_team} 1.5 Üst / Maç 2.5 Üst [⚠️ERİME: KADRO BEKLE]"
        elif fav_val <= -170:
            pick = f"{fav_team} Takım Golü 1.5 Üst & Maç 2.5 Üst"
        elif mom_diff >= 28 and fav_mom >= 70:
            pick = f"{fav_team} Takım Golü 1.5 Üst"
        else:
            pick = "Maç 2.5 Gol Üst / KG Var"
    else:
        if kademe >= 0.95 and (h_mom >= 60 and a_mom >= 60):
            conf = max(conf, 74)
            pick = "KG Var / Maç 2.5 Gol Üst"
        elif fav_val <= -170:
            pick = f"{fav_team} Takım Golü 1.5 Üst"
        elif mom_diff >= 25:
            cs_code = "X2" if is_away_fav else "1X"
            pick = f"{fav_team} Çifte Şans ({cs_code}) & 3.5 Alt"
        elif kademe <= 0.78:
            pick = "İlk Yarı 1.5 Alt & Maç 3.5 Alt"
        else:
            pick = "KG Var / İlk Yarı 1.5 Alt"

    display_odd = f"{odd_str}{smart_tag}" if smart_tag else odd_str
    return conf, pick, display_odd, severe_drift_warning

def evaluate_ft_result(pick, h_name, a_name, h_score, a_score):
    tot = h_score + a_score
    btts = (h_score > 0 and a_score > 0)
    fav_is_away = (a_name in pick and h_name not in pick)
    fav_goals = a_score if fav_is_away else h_score
    fav_won_or_drew = (a_score >= h_score) if fav_is_away else (h_score >= a_score)

    if "PAS" in pick or ("3.5 Alt" in pick and "Çifte Şans" not in pick):
        return tot <= 3
    if "2.5 Üst / Maç 3.5 Üst" in pick:
        return fav_goals >= 3 or tot >= 4
    if "KG Var & 2.5 Üst /" in pick:
        return (btts and tot >= 3) or fav_goals >= 2
    if "1.5 Üst" in pick and "İlk Yarı" not in pick:
        return fav_goals >= 2 or tot >= 3
    if "Maç 2.5 Gol Üst / KG Var" in pick or "KG Var / Maç 2.5" in pick:
        return tot >= 3 or btts
    if "Çifte Şans" in pick:
        return fav_won_or_drew and tot <= 3
    return tot <= 3 or btts
    # ==========================================
# PARÇA 4: CANLI TÜNEL (SOT% KESKİNLİK) & EKRAN
# ==========================================
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
            if r.status_code != 200:
                continue
            data = r.json()
        except Exception:
            continue

        for ev in data.get("events", []):
            comp = ev.get("competitions", [{}])[0]
            status_obj = comp.get("status", {}).get("type", {})
            state = status_obj.get("state", "pre")
            detail_clock = status_obj.get("shortDetail", "")

            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

            h_name = home.get("team", {}).get("shortDisplayName", "Ev")
            a_name = away.get("team", {}).get("shortDisplayName", "Dep")
            h_abbr = home.get("team", {}).get("abbreviation", "")
            a_abbr = away.get("team", {}).get("abbreviation", "")
            match_title = f"{h_name} vs {a_name}"

            h_score = int(home.get("score", 0) or 0)
            a_score = int(away.get("score", 0) or 0)

            h_mom = parse_form_momentum(home.get("form", ""))
            a_mom = parse_form_momentum(away.get("form", ""))
            odd_str, fav_abbr, fav_val, ou_val = parse_odds(comp)

            try:
                dt_utc = datetime.fromisoformat(ev.get("date", "").replace("Z", "+00:00"))
                saat_str = dt_utc.astimezone(TR_TZ).strftime("%H:%M")
            except Exception:
                saat_str = "00:00"

            def get_stat(comp_team, names):
                for s in comp_team.get("statistics", []):
                    if s.get("name") in names:
                        try:
                            return int(float(s.get("displayValue", "0").replace("%", "")))
                        except Exception:
                            return 0
                return 0

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
            if state == "in":
                cur_min = detail_clock.replace("'", "").replace("HT", "45").split("+")[0].strip()
                try:
                    m_int = int(cur_min)
                except Exception:
                    m_int = 1

                h_sot_pct = int((h_sot / h_sh) * 100) if h_sh > 0 else 0
                a_sot_pct = int((a_sot / a_sh) * 100) if a_sh > 0 else 0
                if (h_sh >= 6 and h_sot_pct >= 45) or (a_sh >= 6 and a_sot_pct >= 45):
                    sot_tag = "|🎯KeskinGol"
                elif (h_sh >= 8 and h_sot_pct <= 15) or (a_sh >= 8 and a_sot_pct >= 15):
                    sot_tag = "|📐KörŞut->Korner"

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
                won = evaluate_ft_result(pick, h_name, a_name, h_score, a_score)
                MEM["settled_results"][match_title] = {"won": won, "is_ak": ("Ana Kasa" in pick)}

            results.append({
                "state": state, "saat": saat_str, "clock": detail_clock, "lig": lig_adi,
                "mac": match_title, "h_name": h_name, "a_name": a_name,
                "h_score": h_score, "a_score": a_score, "conf": conf,
                "h_mom": h_mom, "a_mom": a_mom, "odd_str": disp_odd, "tg": ou_val,
                "pick": pick, "warn": warn_flag, "h_sh": h_sh, "a_sh": a_sh,
                "h_sot": h_sot, "a_sot": a_sot, "h_cor": h_cor, "a_cor": a_cor,
                "cards": cards, "h_poss": h_poss, "delta_str": delta_str, "sot_tag": sot_tag
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

now_str = datetime.now(TR_TZ).strftime("%Y%m%d %H:%M")
mini_lines = [f"⚡ DP-MİNİ [{now_str}] Karne:{tot_w}/{tot_t}(%{tot_pct}) AK:{ak_w}/{ak_t}"]

live_m = [m for m in matches if m["state"] == "in"]
pre_m = sorted([m for m in matches if m["state"] == "pre"], key=lambda x: x["conf"], reverse=True)
post_m = [m for m in matches if m["state"] == "post"]

for m in live_m:
    clk = m["clock"].replace(" ", "")
    mini_lines.append(
        f"CANLI|{clk}|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}|"
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
    icon = "✅" if evaluate_ft_result(m["pick"], m["h_name"], m["a_name"], m["h_score"], m["a_score"]) else "❌"
    mini_lines.append(f"FT|FT|{m['h_name']} {m['h_score']}-{m['a_score']} {m['a_name']}|{icon}|{m['pick']}")

st.markdown("##### 📲 GEMİNİ'YE TEK TIKLA AKTAR (Sağ Üstteki Kopyala İkonuna Dokun)")
st.code("\n".join(mini_lines), language="text")

st.markdown(f"**📊 Aktif Karne:** `{tot_w}/{tot_t} (%{tot_pct})` | **💎 Ana Kasa:** `{ak_w}/{ak_t}` | **🔥 Canlı:** `{len(live_m)}` | **⏳ Maç Önü:** `{len(pre_m)}`")

if live_m:
    st.markdown("### 🔴 Canlı Tünel & Keskinlik Radar")
    for m in live_m:
        st.markdown(
            f"<div class='dp-card dp-live'><b>⏱️ {m['clock']} | {m['h_name']} {m['h_score']} - {m['a_score']} {m['a_name']}</b> "
            f"<span class='dp-badge'>{m['lig']}</span><br>"
            f"🎯 Şut: <b>{m['h_sh']}({m['h_sot']}) - {m['a_sh']}({m['a_sot']})</b> | 🚩 Korner: <b>{m['h_cor']}-{m['a_cor']}</b> | "
            f"🟨 Kart: <b>{m['cards']}</b> | ⚽ Top: <b>%{m['h_poss']}</b> {m['delta_str']} {m['sot_tag']}<br>"
            f"📌 <b>Kilitli Hedef:</b> {m['pick']}</div>",
            unsafe_allow_html=True
        )

st.markdown("### ⏳ Maç Önü v4.8 Otonom Sinyaller (Akıllı Para & Erime Freni)")
for m in pre_m:
    if "Ana Kasa" in m["pick"]:
        card_cls = "dp-card dp-ak"
    elif m["warn"]:
        card_cls = "dp-card dp-warn"
    else:
        card_cls = "dp-card"
    st.markdown(
        f"<div class='{card_cls}'><b>🕒 {m['saat']} | {m['mac']}</b> — <b>%{m['conf']} Güven</b> "
        f"<span class='dp-badge'>{m['lig']}</span><br>"
        f"📈 Mom: <b>%{m['h_mom']} vs %{m['a_mom']}</b> | 💰 Oran: <b>{m['odd_str']}</b> | ⚽ TG: <b>{m['tg']}</b><br>"
        f"🎯 <b>Hedef:</b> {m['pick']}</div>",
        unsafe_allow_html=True
    )
