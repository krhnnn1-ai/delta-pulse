# -*- coding: utf-8 -*-
import json, os, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import streamlit as st

st.set_page_config(page_title="Delta Pulse v4.5 Cloud", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.dp-card {background:#161b22; border:1px solid #30363d; border-radius:10px; padding:14px; margin-bottom:10px;}
.dp-ak {background:#1c2128; border-left:5px solid #f0b90b; border-radius:8px; padding:12px; margin-bottom:8px;}
.dp-live {border-left:5px solid #ff4b4b;}
.dp-pre {border-left:5px solid #2f81f7;}
.dp-ft-ok {border-left:5px solid #2ea043;}
.dp-ft-no {border-left:5px solid #da3633;}
</style>
""", unsafe_allow_html=True)

MEMORY_FILE = "delta_pulse_hafiza.json"
TR_TZ = timezone(timedelta(hours=3))
CHRONO_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]
ARCHETYPE_WEIGHTS = {
    "MUTLAK_FAVORI": 1.00, "CIFT_YONLU_MOMENTUM": 0.98, "RAKIP_COKUSU": 0.96,
    "PIYASA_BASKISI": 0.90, "SIMETRIK_DENGE": 0.88, "KARA_DELIK": 0.75,
}

LEAGUES = {
    "eng.1": ("İNGİLTERE PREMIER LİG", 0.92),
    "esp.1": ("İSPANYA LA LIGA", 0.90),
    "ger.1": ("ALMANYA BUNDESLIGA", 0.88),
    "ita.1": ("İTALYA SERIE A", 0.87),
    "fra.1": ("FRANSA LIGUE 1", 0.84),
    "tur.1": ("TÜRKIYE SÜPER LIG", 0.81),
    "eng.2": ("İNGİLTERE CHAMPIONSHIP", 0.80),
    "ger.2": ("ALMANYA BUNDESLIGA 2", 0.79),
    "tur.2": ("TÜRKIYE 1. LİG", 0.75),
}

LOCKED_PRE_CACHE = {
    "Brighton vs C Palace": ("Brighton Takım Golü 1.5 Üst (Ana Kasa)", 88),
    "Leverkusen vs Freiburg": ("KG Var & 2.5 Üst / Leverkusen 1.5 Üst (Ana Kasa)", 87),
    "Real Madrid vs Sevilla": ("Real Madrid Takım Golü 2.5 Üst / Maç 3.5 Üst (Ana Kasa)", 85),
    "Nottm Forest vs Arsenal": ("Arsenal Takım Golü 1.5 Üst & Arsenal Galibiyeti", 79),
    "Istanbul BB vs Gaziantep": ("Maç 2.5 Gol Üst / KG Var", 69),
    "Málaga vs Real Sociedad": ("Real Sociedad Çifte Şans (X2) & 3.5 Alt", 67),
    "Gladbach vs Hoffenheim": ("Maç 2.5 Gol Üst / KG Var", 65),
    "Kasimpasa vs Samsunspor": ("Kasimpasa Çifte Şans (1X) & 3.5 Alt", 64),
    "Le Havre AC vs Auxerre": ("Auxerre Çifte Şans (X2) & 3.5 Alt", 63),
    "D Dresden vs Magdeburg": ("Magdeburg Çifte Şans (X2) & 3.5 Alt", 63),
    "Juventus vs Lazio": ("Juventus Takım Golü 1.5 Üst", 62),
    "Kocaelispor vs Goztepe": ("KG Var / İlk Yarı 1.5 Alt", 62),
    "Lorient vs Monaco": ("KG Var / İlk Yarı 1.5 Alt", 54),
    "Paris FC vs Rennes": ("KG Var / İlk Yarı 1.5 Alt", 53),
    "Milan vs Atalanta": ("KG Var / İlk Yarı 1.5 Alt", 53),
    "Lyon vs Nice": ("KG Var / İlk Yarı 1.5 Alt", 52),
    "Fiorentina vs Como": ("KG Var / İlk Yarı 1.5 Alt", 52),
    "Angers vs Marseille": ("KG Var / İlk Yarı 1.5 Alt", 50),
    "Celta Vigo vs Alavés": ("KG Var / İlk Yarı 1.5 Alt", 50),
    "Udinese vs Lecce": ("KG Var / İlk Yarı 1.5 Alt", 49),
    "Bielefeld vs Osnabruck": ("KG Var / İlk Yarı 1.5 Alt", 48),
    "Karlsruher vs Darmstadt": ("KG Var / İlk Yarı 1.5 Alt", 48),
    "Leeds vs Man United": ("Maç Önü PAS (3.5 Alt / İY 1.5 Alt)", 25),
    "Osasuna vs Racing": ("Maç Önü PAS (3.5 Alt / İY 1.5 Alt)", 21),
    "Bournemouth vs Sunderland": ("Maç Önü PAS (3.5 Alt / İY 1.5 Alt)", 20),
}def sget(d, key, default=None):
    if not isinstance(d, dict): return default
    val = d.get(key, default)
    return default if val is None else val

def clean_form_and_momentum(raw_form, wins, draws, losses, is_unplayed=True):
    chars = [c for c in str(raw_form or "").upper() if c in ("W", "D", "L")]
    total_games = wins + draws + losses
    if chars and chars[0] == "D" and is_unplayed:
        if draws == 0 or chars[:5].count("D") > draws or len(chars) >= 5:
            chars = chars[1:]
    if len(chars) == 4 and total_games >= 5:
        rw = max(0, wins - chars.count("W"))
        rd = max(0, draws - chars.count("D"))
        rl = max(0, losses - chars.count("L"))
        if rw >= rd and rw >= rl and rw > 0: chars.append("W")
        elif rl >= rw and rl >= rd and rl > 0: chars.append("L")
        elif rd > 0: chars.append("D")
    clean_5 = chars[:5]
    if not clean_5:
        if total_games > 0:
            return "-----", int(round(((wins * 3 + draws) / (total_games * 3.0)) * 100))
        return "-----", 50
    pts_map = {"W": 3.0, "D": 1.0, "L": 0.0}
    w_slice = CHRONO_WEIGHTS[:len(clean_5)]
    w_sum = sum(w_slice)
    form_mom = (sum(pts_map[c] * (w / w_sum) for c, w in zip(clean_5, w_slice)) / 3.0) * 100.0
    if total_games > 0:
        season_mom = ((wins * 3 + draws) / (total_games * 3.0)) * 100.0
        final_mom = int(round((form_mom * 0.75) + (season_mom * 0.25)))
    else:
        final_mom = int(round(form_mom))
    return "".join(clean_5), max(0, min(100, final_mom))

def parse_american_odds(odds_str):
    m = re.search(r"([+-]\d+)", str(odds_str or ""))
    return float(m.group(1)) if m else None

def odds_to_implied_prob(odds_str):
    val = parse_american_odds(odds_str)
    if not val: return 50.0
    return (-val) / (-val + 100.0) * 100.0 if val < 0 else 100.0 / (val + 100.0) * 100.0

def verify_pre_prediction(tahmin_str, h_name, a_name, h_score, a_score, ht_goals):
    t = str(tahmin_str or "")
    tot = h_score + a_score
    btts = (h_score >= 1 and a_score >= 1)
    fav_is_h = t.startswith(h_name) or (f"/ {h_name}" in t)
    fav_g = h_score if fav_is_h else a_score
    fav_won = (h_score > a_score) if fav_is_h else (a_score > h_score)

    if "Takım Golü 2.5 Üst / Maç 3.5 Üst" in t: return (fav_g >= 3) or (tot >= 4)
    if "KG Var & 2.5 Üst /" in t: return (btts and tot >= 3) or (fav_g >= 2)
    if "Galibiyeti" in t and "1.5 Üst" in t: return fav_g >= 2 and fav_won
    if "Takım Golü 1.5 Üst & Maç 2.5 Üst" in t: return fav_g >= 2 and tot >= 3
    if "Takım Golü 1.5 Üst" in t: return fav_g >= 2
    if "Çifte Şans (1X) & Maç 1.5 Üst" in t: return h_score >= a_score and tot >= 2
    if "Çifte Şans (X2) & Maç 1.5 Üst" in t: return a_score >= h_score and tot >= 2
    if "Çifte Şans (1X) & 3.5 Alt" in t: return h_score >= a_score and tot <= 3
    if "Çifte Şans (X2) & 3.5 Alt" in t: return a_score >= h_score and tot <= 3
    if "Maç 2.5 Gol Üst / KG Var" in t or "KG Var & 2.5 Üst" in t: return tot >= 3 or btts
    if "Maç Önü PAS (3.5 Alt / İY 1.5 Alt)" in t: return tot <= 3 or ht_goals <= 1
    if "KG Var / İlk Yarı 1.5 Alt" in t: return btts or ht_goals <= 1
    return False
	def evaluate_pre_match(h_name, a_name, h_mom, a_mom, h_rec, a_rec, odds_str, tg_line, tier_weight):
    mom_diff, avg_mom = abs(h_mom - a_mom), (h_mom + a_mom) / 2.0
    imp_prob, raw_odds_val = odds_to_implied_prob(odds_str), parse_american_odds(odds_str)
    if raw_odds_val and raw_odds_val <= -150:
        fav_team = h_name if h_mom >= a_mom - 15 else a_name
    else:
        fav_team = h_name if h_mom >= a_mom else a_name
    fav_mom, dog_mom = max(h_mom, a_mom), min(h_mom, a_mom)
    fav_rec, dog_rec = (h_rec, a_rec) if h_mom >= a_mom else (a_rec, h_rec)
    fav_code = "1X" if fav_team == h_name else "X2"

    if fav_mom >= 72 and (mom_diff >= 24 or (raw_odds_val and raw_odds_val <= -400)) and tg_line >= 3.5:
        archetype = "MUTLAK_FAVORI"
        base = 74.0 + (mom_diff * 0.22) + ((imp_prob - 50.0) * 0.22) + ((tg_line - 2.5) * 3.5)
        if fav_mom >= 72 and (raw_odds_val and raw_odds_val <= -350):
            yorum = f"{fav_team} %{fav_mom} momentum ({fav_rec}) ve {tg_line} baremiyle mutlak favori (+{mom_diff} fark | Kademe: {tier_weight})."
            tahmin, pusu = f"{fav_team} Takım Golü 2.5 Üst / Maç 3.5 Üst", f"İlk 30 dk 0-0 geçilirse -> {fav_team} Korner Patlaması (6.5 Üst)"
        else:
            yorum = f"{fav_team} %{fav_mom} zirve momentumuyla ({fav_rec}) rakibinin (%{dog_mom}) +{mom_diff} puan önünde (Kademe: {tier_weight})."
            tahmin, pusu = f"{fav_team} Takım Golü 1.5 Üst", f"{fav_team} Geriye Düşerse veya İY 0-0 Kalırsa -> {fav_team} Korner Patlaması"
    elif h_mom >= 58 and a_mom >= 58 and tg_line >= 3.5:
        archetype = "CIFT_YONLU_MOMENTUM"
        base = 73.0 + (avg_mom * 0.20) + ((tg_line - 2.5) * 4.5) - (mom_diff * 0.08)
        yorum = f"Çift Yönlü Yüksek Momentum (%{h_mom} vs %{a_mom}). Açık oyun ve erken gol beklentisi (Kademe: {tier_weight})."
        tahmin, pusu = f"KG Var & 2.5 Üst / {fav_team} 1.5 Üst", "İlk 20 Dakika Erken Gol -> 3.5 Üst | FW->DF olursa alt/korner revizyonu"
    elif (dog_mom <= 36 and mom_diff >= 28) or mom_diff >= 40 or (mom_diff >= 28 and raw_odds_val and raw_odds_val <= -155):
        archetype = "RAKIP_COKUSU"
        weak_team = h_name if h_mom < a_mom else a_name
        strong_mkt = (raw_odds_val is not None and raw_odds_val <= -145) or (raw_odds_val is not None and raw_odds_val < 0 and dog_mom <= 17)
        if strong_mkt:
            base = 71.0 + (mom_diff * 0.24) + ((imp_prob - 50.0) * 0.20)
            yorum = f"Rakip Çöküş Asimetrisi: {weak_team} ({dog_rec}) %{dog_mom} momentumda. {fav_team} (+{mom_diff} fark | {odds_str}) net favori (Kademe: {tier_weight})."
            tahmin, pusu = f"{fav_team} Takım Golü 1.5 Üst & {fav_team} Galibiyeti", f"İlk yarı kilitlenirse -> {fav_team} Korner Patlaması (5.5 Üst)"
        elif tg_line >= 3.5 or dog_mom <= 15 or (odds_str == "Veri Yok" and fav_team == h_name and mom_diff >= 32):
            base = 66.0 + (mom_diff * 0.20)
            yorum = f"Savunma Çöküşü & Üstünlük: {weak_team} (%{dog_mom}) savunması kırılgan; {fav_team} (+{mom_diff} fark) hücumda üstün (Kademe: {tier_weight})."
            tahmin, pusu = f"{fav_team} Çifte Şans ({fav_code}) & Maç 1.5 Üst", f"İlk yarı gol gecikirse -> {fav_team} Korner Üst"
        else:
            base = 64.0 + (mom_diff * 0.20)
            yorum = f"Kontrollü Üstünlük: {fav_team} (%{fav_mom}) rakibinin (%{dog_mom}) +{mom_diff} puan önünde ancak barem ({tg_line}) kontrollü (Kademe: {tier_weight})."
            tahmin, pusu = f"{fav_team} Çifte Şans ({fav_code}) & 3.5 Alt", f"60. dakikada 0-0 ise -> {fav_team} Korner Üst & Kart Üst"
    elif raw_odds_val and raw_odds_val <= -170 and mom_diff < 28:
        archetype = "PIYASA_BASKISI"
        base = 63.0 + ((imp_prob - 50.0) * 0.32) + (mom_diff * 0.15)
        if h_mom <= 20 and tg_line <= 2.5:
            yorum = f"Piyasa ({odds_str}) {h_name} lehine ancak ev sahibi %{h_mom} momentumla ({h_rec}) form krizinde (Kademe: {tier_weight})."
            tahmin, pusu = f"{h_name} Çifte Şans (1X) & 3.5 Alt", f"{h_name} Golü Gecikirse -> {h_name} Korner Baskısı (5.5/6.5 Üst)"
        else:
            yorum = f"Piyasa ({odds_str}) oranı {h_name} lehine baskı fiyatlıyor ancak momentum dengeli (+{mom_diff} fark | Kademe: {tier_weight})."
            tahmin = f"{h_name} Takım Golü 1.5 Üst & Maç 2.5 Üst" if tg_line >= 3.5 else f"{h_name} Takım Golü 1.5 Üst"
            pusu = f"{h_name} Golü Gecikirse -> {h_name} Korner Baskısı (5.5/6.5 Üst)"
    elif tg_line >= 3.5:
        archetype = "CIFT_YONLU_MOMENTUM"
        base = 63.0 + (avg_mom * 0.20) + ((tg_line - 2.5) * 4.5)
        yorum = f"Piyasa {tg_line} gol baremiyle ({odds_str}) yüksek tempolu ve bol pozisyonlu geçiş oyunu fiyatlıyor (Kademe: {tier_weight})."
        tahmin, pusu = "Maç 2.5 Gol Üst / KG Var", "İlk 20 dk gol çıkarsa -> 3.5 Üst | İlk yarı 0-0 kalırsa -> Korner Üst"
    elif tg_line <= 1.5 or (h_mom < 42 and a_mom < 35 and tg_line <= 2.5):
        archetype = "KARA_DELIK"
        base = 66.0 if tg_line <= 1.5 else max(20.0, 42.0 - ((45.0 - avg_mom) * 0.65))
        yorum = f"Düşük Gol Baremi (T/G: {tg_line} | Mom: %{h_mom}-%{a_mom}). Kısır ve kontrollü taktik maç (Kademe: {tier_weight})."
        tahmin, pusu = "Maç Önü PAS (3.5 Alt / İY 1.5 Alt)", "75'+ Skor Yakınsa -> 80+ Kart Üst"
    else:
        archetype = "SIMETRIK_DENGE"
        base = 52.0 + (avg_mom * 0.16) + (mom_diff * 0.14)
        yorum = f"Simetrik güç ve momentum dengesi (%{h_mom} vs %{a_mom}). Taktik değişiklikler skoru belirler (Kademe: {tier_weight})."
        tahmin, pusu = "KG Var / İlk Yarı 1.5 Alt", "60. dakikaya kadar 1-0 giden senaryoda gerideki takımın kornerleri"

    final_conf = int(round(min(97.0, max(20.0, base * (0.62 + 0.38 * tier_weight) * ARCHETYPE_WEIGHTS.get(archetype, 1.0)))))
    is_ana_kasa = final_conf >= 83 and tier_weight >= 0.81 and archetype in ("MUTLAK_FAVORI", "CIFT_YONLU_MOMENTUM", "RAKIP_COKUSU")
    if is_ana_kasa: tahmin = f"{tahmin} (Ana Kasa)"
    return {"confidence": final_conf, "archetype": archetype, "yorum": yorum, "tahmin": tahmin, "pusu": pusu, "is_ana_kasa": is_ana_kasa}
	def evaluate_live_or_ft(minute, is_ft, h_name, a_name, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_foul, a_foul, tot_yc, h_poss, a_poss, tier_w, pre_conf, tunnel, first_goal_min, fw_notes):
    tot_goals, tot_sot, tot_cor, tot_fouls = h_score + a_score, h_sot + a_sot, h_cor + a_cor, h_foul + a_foul
    d_h_sh, d_a_sh = sget(tunnel, "d_h_sh", 0), sget(tunnel, "d_a_sh", 0)
    d_h_cor, d_a_cor = sget(tunnel, "d_h_cor", 0), sget(tunnel, "d_a_cor", 0)
    decisions, live_bonus, eff_w = [], 0.0, tier_w

    if not is_ft and minute <= 15:
        if a_cor >= 2 or (a_poss >= 64.0 and a_sh >= 1) or a_sot >= 2:
            decisions.append(f"⚡ {a_name} Erken Baskı (Şut:{a_sh}({a_sot})|Kor:{a_cor})"); live_bonus += 7.0
        elif h_cor >= 2 or (h_poss >= 64.0 and h_sh >= 1) or h_sot >= 2:
            decisions.append(f"⚡ {h_name} Erken Baskı (Şut:{h_sh}({h_sot})|Kor:{h_cor})"); live_bonus += 7.0
    if first_goal_min is not None and first_goal_min <= 22:
        if not is_ft: decisions.append(f"Erken Gol ({first_goal_min}') -> Yüksek Tempo / 2.5 Üst"); live_bonus += 8.0
        elif tot_goals >= 3: decisions.append(f"Erken Gol ({first_goal_min}') -> 2.5 Üst [OK]"); live_bonus += 8.0
    if h_score >= 2: decisions.append(f"{h_name} Takım Golü 1.5 Üst [OK]"); live_bonus += 6.0
    if a_score >= 2: decisions.append(f"{a_name} Takım Golü 1.5 Üst [OK]"); live_bonus += 6.0
    if not is_ft and tot_goals == 0 and minute >= 25 and (tot_sot >= 3 or (h_sh + a_sh) >= 8):
        decisions.append(f"🔥 0-0 Yüksek Şut Baskısı ({h_sh+a_sh} Şut/{tot_sot} İsb) -> Sıradaki Gol (0.5/1.5 Üst)"); live_bonus += 11.0; eff_w += 0.12
    if d_a_sh >= 6 and d_h_sh <= 1: decisions.append(f"🔒 Tünel Kilidi: {a_name} +{d_a_sh} Şut, +{d_a_cor} Korner!"); live_bonus += 12.0
    elif d_h_sh >= 6 and d_a_sh <= 1: decisions.append(f"🔒 Tünel Kilidi: {h_name} +{d_h_sh} Şut, +{d_h_cor} Korner!"); live_bonus += 12.0
    if a_cor >= 7 or d_a_cor >= 5 or (not is_ft and minute <= 45 and a_cor >= 4):
        decisions.append(f"📐 {a_name} Deplasman Korner Baskısı ({a_cor} Korner)"); live_bonus += 12.0
    elif h_cor >= 7 or d_h_cor >= 5 or (not is_ft and minute <= 45 and h_cor >= 4):
        decisions.append(f"📐 {h_name} Ev Sahibi Korner Baskısı ({h_cor} Korner)"); live_bonus += 12.0
    elif not is_ft and minute <= 45 and tot_cor >= 7:
        decisions.append(f"📐 İlk Yarı Korner Patlaması ({tot_cor} Korner)"); live_bonus += 10.0
    elif (minute >= 70 or is_ft) and tot_cor <= 4:
        decisions.append(f"Korner Kara Delik (Toplam {tot_cor} Korner)")
    if (minute <= 45 and tot_yc >= 4) or tot_yc >= 6:
        decisions.append(f"🟨 Yüksek Kart Tansiyonu ({tot_yc} Kart) -> Kart Üst"); live_bonus += 9.0
    elif tot_fouls >= 20 and tot_yc <= 1:
        decisions.append(f"Disiplin Gölge Sinyali ({tot_fouls} Faul / {tot_yc} Kart)")
    if fw_notes:
        decisions.append(f"🛡️ TAKTİK (FW->DF): {', '.join(fw_notes)}"); live_bonus += 6.0

    raw_live = (70.0 * tier_w) + live_bonus
    if not is_ft and minute < 45 and pre_conf >= 70:
        final_conf = int(round((pre_conf * ((45.0 - minute) / 45.0)) + (raw_live * (minute / 45.0)) + (live_bonus * 0.45)))
    else:
        final_conf = int(round(raw_live))
    if not decisions:
        decisions.append(f"Standart Dağılım (Etkin Ağırlık: {eff_w:.2f})")
    return max(25, min(96, final_conf)), " | ".join(decisions)

def fetch_json(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                res = json.loads(r.read().decode("utf-8", errors="ignore"))
                if isinstance(res, dict) and res: return res
        except Exception: continue
    return {}

def parse_stat(stats_list, keys, default=0.0):
    for s in (stats_list or []):
        if not isinstance(s, dict): continue
        if str(sget(s, "name", "")).lower() in keys:
            try: return float(str(sget(s, "displayValue", sget(s, "value", default))).replace("%", "").strip())
            except ValueError: return default
    return default

def parse_record_wdl(comp_dict):
    recs = sget(comp_dict, "records", [])
    if recs and isinstance(recs, list) and isinstance(recs[0], dict):
        summary = str(sget(recs[0], "summary", "0-0-0")).strip()
        p = summary.split("-")
        if len(p) == 3:
            try: return int(p[0]), int(p[1]), int(p[2]), summary
            except ValueError: pass
    return 0, 0, 0, "0-0-0"
	def detect_fw_to_df_subs(summary_data):
    notes, pos_map = [], {}
    for r in sget(summary_data, "rosters", []):
        for ath in sget(r, "roster", []):
            name = sget(sget(ath, "athlete", {}), "displayName", "")
            pos = sget(sget(ath, "position", {}), "abbreviation", "")
            if name and pos: pos_map[name] = str(pos).upper()
    for ev in sget(summary_data, "keyEvents", []):
        if "substitution" in str(sget(sget(ev, "type", {}), "text", "")).lower():
            pts = sget(ev, "participants", [])
            if len(pts) >= 2:
                p_in = sget(sget(pts[0], "athlete", {}), "displayName", "")
                p_out = sget(sget(pts[1], "athlete", {}), "displayName", "")
                if pos_map.get(p_out, "") in ("F", "FW", "ST", "CF") and pos_map.get(p_in, "") in ("D", "DF", "CB", "RB", "LB", "CDM"):
                    notes.append(f"{p_out}(FW)->{p_in}(DF) {sget(sget(ev, 'clock', {}), 'displayValue', '')}")
    return notes

def load_memory():
    if "dp_mem" in st.session_state: return st.session_state["dp_mem"]
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict):
                    st.session_state["dp_mem"] = d
                    return d
        except Exception: pass
    st.session_state["dp_mem"] = {}
    return st.session_state["dp_mem"]

def fetch_day_events(date_str):
    events = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        fut_map = {ex.submit(fetch_json, f"https://site.api.espn.com/apis/site/v2/sports/soccer/{s}/scoreboard?dates={date_str}"): (s, n, w) for s, (n, w) in LEAGUES.items()}
        for fut in as_completed(fut_map):
            s, n, w = fut_map[fut]
            for ev in sget(fut.result(), "events", []):
                if isinstance(ev, dict): events.append((s, n, w, ev, date_str))
    return events

def extract_match_details(comp, h_id, a_id):
    goals_list, yc_list, first_goal_min, ht_goals = [], [], None, 0
    det_h_yc = det_a_yc = 0
    for d in [x for x in sget(comp, "details", []) if isinstance(x, dict)]:
        clk = str(sget(sget(d, "clock", {}), "displayValue", ""))
        aths = [a for a in sget(d, "athletesInvolved", []) if isinstance(a, dict)]
        p_name = sget(aths[0], "displayName", "Oyuncu") if aths else "Oyuncu"
        ev_t_id = str(sget(sget(d, "team", {}), "id", ""))
        if sget(d, "scoringPlay"):
            goals_list.append(f"⚽ {p_name} ({clk})")
            gm = re.search(r"(\d+)", clk)
            if gm:
                g_min = int(gm.group(1))
                if first_goal_min is None: first_goal_min = g_min
                if g_min < 45 or clk.startswith("45'"): ht_goals += 1
        elif sget(d, "yellowCard"):
            yc_list.append(f"{p_name} ({clk})")
            if ev_t_id == h_id: det_h_yc += 1
            elif ev_t_id == a_id: det_a_yc += 1
    return goals_list, yc_list, first_goal_min, ht_goals, det_h_yc, det_a_yc

def ask_gemini_ai_analyst(api_key, report_text):
    if not api_key: return ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key.strip()}"
    prompt = (
        "Sen DELTA PULSE futbol analiz motorunun baş stratejistisin. Aşağıdaki güncel maç önü, canlı (Δ Tüneli) "
        "ve biten maç karnesini incele. En güvenilir 3 maç önü/canlı pusu hedefini, korner/gol baskısı olan maçları "
        "ve uzak durulması gereken tuzakları maddeler halinde net ve kısa olarak Türkçe özetle:\n\n" + report_text[:7500]
    )
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode("utf-8", errors="ignore"))
            return res["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ AI Bağlantı Uyarısı: API Anahtarını kontrol edin ({e})"
		def process_single_event(slug, lg_name, tier_w, ev, ev_day, date_str, memory):
    ev_id = str(sget(ev, "id", ""))
    comps = sget(ev, "competitions", [])
    if not comps or not isinstance(comps[0], dict): return None
    comp = comps[0]
    st_type = sget(sget(ev, "status", {}), "type", {})
    state = str(sget(st_type, "state", "pre")).lower()
    short_detail = str(sget(st_type, "shortDetail", ""))

    competitors = [c for c in sget(comp, "competitors", []) if isinstance(c, dict)]
    if len(competitors) < 2: return None
    home = next((c for c in competitors if sget(c, "homeAway") == "home"), competitors[0])
    away = next((c for c in competitors if sget(c, "homeAway") == "away"), competitors[1])
    h_team, a_team = sget(home, "team", {}), sget(away, "team", {})
    h_id, a_id = str(sget(h_team, "id", "H")), str(sget(a_team, "id", "A"))
    h_name = sget(h_team, "shortDisplayName") or sget(h_team, "displayName", "Ev")
    a_name = sget(a_team, "shortDisplayName") or sget(a_team, "displayName", "Deplasman")
    match_key = f"{h_name} vs {a_name}"

    kickoff_str = "00:00"
    try: kickoff_str = datetime.fromisoformat(str(sget(ev, "date", "")).replace("Z", "+00:00")).astimezone(TR_TZ).strftime("%H:%M")
    except Exception: pass
    day_tag = "DÜN " if ev_day < date_str else ("YARIN " if ev_day > date_str else "")

    h_w, h_d, h_l, h_rec = parse_record_wdl(home)
    a_w, a_d, a_l, a_rec = parse_record_wdl(away)
    h_form, h_mom = clean_form_and_momentum(sget(home, "form", ""), h_w, h_d, h_l, state in ("pre", "in"))
    a_form, a_mom = clean_form_and_momentum(sget(away, "form", ""), a_w, a_d, a_l, state in ("pre", "in"))

    odds_list = [o for o in sget(comp, "odds", []) if isinstance(o, dict)]
    odds_str = str(sget(odds_list[0], "details", "Veri Yok")) if odds_list else "Veri Yok"
    try: tg_line = float(sget(odds_list[0], "overUnder", 2.5)) if odds_list else 2.5
    except Exception: tg_line = 2.5

    pre_eval = evaluate_pre_match(h_name, a_name, h_mom, a_mom, h_rec, a_rec, odds_str, tg_line, tier_w)
    mem_entry = sget(memory, ev_id, {})
    if match_key in LOCKED_PRE_CACHE and state != "pre":
        stored_tahmin, stored_pre_conf = LOCKED_PRE_CACHE[match_key]
    else:
        stored_pre_conf = pre_eval["confidence"] if state == "pre" else int(sget(mem_entry, "pre_conf", pre_eval["confidence"]))
        stored_tahmin = pre_eval["tahmin"] if state == "pre" else str(sget(mem_entry, "tahmin", pre_eval["tahmin"]))

    if state == "pre":
        mem_data = {"match": match_key, "pre_conf": pre_eval["confidence"], "tahmin": pre_eval["tahmin"], "snapshots": sget(mem_entry, "snapshots", [])}
        meta_str = f"Mom: %{h_mom} ({h_rec}|{h_form}) vs %{a_mom} ({a_rec}|{a_form}) | Barem: {odds_str} | T/G: {tg_line}"
        lines = [f"🕒 [{day_tag}{kickoff_str} | {lg_name}] {match_key} ({meta_str})", f"   🎯 Tahmin: {pre_eval['tahmin']} | 📐 Pusu: {pre_eval['pusu']}"]
        item = {"confidence": pre_eval["confidence"], "state": "pre", "priority": 2, "kickoff": f"{day_tag}{kickoff_str}", "league": lg_name, "match_title": match_key, "meta": meta_str, "yorum": pre_eval["yorum"], "tahmin": pre_eval["tahmin"], "pusu": pre_eval["pusu"], "is_hit": None, "lines": lines}
        return {"ev_id": ev_id, "mem_data": mem_data, "item": item, "is_ana_kasa": pre_eval["is_ana_kasa"], "state": "pre", "is_hit": None, "is_ak_ft": False}

    is_ft = state == "post"
    h_score, a_score = int(sget(home, "score", 0) or 0), int(sget(away, "score", 0) or 0)
    disp_clock = str(sget(sget(ev, "status", {}), "displayClock", short_detail))
    mm = re.search(r"(\d+)", disp_clock)
    minute = 90 if is_ft else (int(mm.group(1)) if mm else 45)
    min_label = f"{day_tag}FT" if is_ft else f"{minute}'"

    hs, as_ = sget(home, "statistics", []), sget(away, "statistics", [])
    h_cor, a_cor = int(parse_stat(hs, ("woncorners", "corners", "cornerkicks"))), int(parse_stat(as_, ("woncorners", "corners", "cornerkicks")))
    h_sh, a_sh = int(parse_stat(hs, ("totalshots", "shots"))), int(parse_stat(as_, ("totalshots", "shots")))
    h_sot, a_sot = int(parse_stat(hs, ("shotsontarget", "ontargetscoringattempt"))), int(parse_stat(as_, ("shotsontarget", "ontargetscoringattempt")))
    h_foul, a_foul = int(parse_stat(hs, ("foulscommitted", "fouls"))), int(parse_stat(as_, ("foulscommitted", "fouls")))
    h_yc, a_yc = int(parse_stat(hs, ("yellowcards",))), int(parse_stat(as_, ("yellowcards",)))
    h_poss = parse_stat(hs, ("possessionpct", "possession"), 50.0)
    a_poss = parse_stat(as_, ("possessionpct", "possession"), round(100.0 - h_poss, 1))

    goals_list, yc_list, first_goal_min, ht_goals, det_h_yc, det_a_yc = extract_match_details(comp, h_id, a_id)
    if h_yc == 0 and a_yc == 0 and (det_h_yc + det_a_yc) > 0: h_yc, a_yc = det_h_yc, det_a_yc
    tot_yc = max(h_yc + a_yc, len(yc_list))

    sum_json = fetch_json(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={ev_id}", 4) if not is_ft else {}
    fw_notes = detect_fw_to_df_subs(sum_json) if sum_json else []

    snaps = [s for s in sget(mem_entry, "snapshots", []) if isinstance(s, dict)]
    if not snaps: snaps.append({"min": minute, "h_sh": h_sh, "a_sh": a_sh, "h_cor": h_cor, "a_cor": a_cor})
    prev_s = snaps[0]
    if minute > sget(snaps[-1], "min", 0):
        prev_s = snaps[-1]
        snaps.append({"min": minute, "h_sh": h_sh, "a_sh": a_sh, "h_cor": h_cor, "a_cor": a_cor})
        snaps = snaps[-3:]

    p_min = sget(prev_s, "min", minute)
    d_h_sh, d_a_sh = max(0, h_sh - sget(prev_s, "h_sh", h_sh)), max(0, a_sh - sget(prev_s, "a_sh", a_sh))
    d_h_cor, d_a_cor = max(0, h_cor - sget(prev_s, "h_cor", h_cor)), max(0, a_cor - sget(prev_s, "a_cor", a_cor))
    tunnel = {"d_h_sh": d_h_sh, "d_a_sh": d_a_sh, "d_h_cor": d_h_cor, "d_a_cor": d_a_cor}

    live_conf, dec_str = evaluate_live_or_ft(minute, is_ft, h_name, a_name, h_score, a_score, h_sh, a_sh, h_sot, a_sot, h_cor, a_cor, h_foul, a_foul, tot_yc, h_poss, a_poss, tier_w, stored_pre_conf, tunnel, first_goal_min, fw_notes)
    mem_data = {"match": match_key, "pre_conf": stored_pre_conf, "tahmin": stored_tahmin, "snapshots": snaps}

    is_hit = verify_pre_prediction(stored_tahmin, h_name, a_name, h_score, a_score, ht_goals) if is_ft else None
    is_ak_ft = ("(Ana Kasa)" in stored_tahmin) if is_ft else False
    hit_badge = f" | 🎯 MaçÖnü: {stored_tahmin} ➔ {'✅[TUTTU]' if is_hit else '❌[YATTI]'}" if is_ft else ""
    meta_str = f"Şut: {h_sh}({h_sot})-{a_sh}({a_sot}) | Korner: {h_cor}-{a_cor} | Kart: {tot_yc} | Faul: {h_foul}-{a_foul} | Top: %{h_poss:.0f}-%{a_poss:.0f}"
    lines = [f"{'🏁 FT' if is_ft else '🔴 CANLI'} [{min_label} | {lg_name}] {h_name} {h_score} - {a_score} {a_name} | {meta_str}", f"   🤖 Karar -> {dec_str}{hit_badge}"]
    item = {"confidence": live_conf, "state": state, "priority": (3 if not is_ft else 1), "kickoff": min_label, "league": lg_name, "match_title": f"{h_name} {h_score} - {a_score} {a_name}", "meta": meta_str, "yorum": " | ".join(goals_list) if goals_list else "Gol Yok", "tahmin": stored_tahmin, "pusu": dec_str, "is_hit": is_hit, "lines": lines}
    return {"ev_id": ev_id, "mem_data": mem_data, "item": item, "is_ana_kasa": False, "state": state, "is_hit": is_hit, "is_ak_ft": is_ak_ft}

def main():
    now_tr = datetime.now(TR_TZ)
    date_str, time_str = now_tr.strftime("%Y%m%d"), now_tr.strftime("%H:%M")
    yesterday_str = (now_tr - timedelta(days=1)).strftime("%Y%m%d")

    with st.sidebar:
        st.header("⚡ Delta Pulse Bulut")
        inc_yest = st.checkbox("📅 Dünkü (18 Ekim) Sonuçları Dahil Et", value=True)
        auto_ref = st.checkbox("🔄 60 Saniyede Bir Otomatik Yenile", value=False)
        default_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
        gem_key = st.text_input("🤖 Gemini API Anahtarı (Otomatik AI):", value=default_key, type="password")
        run_ai = st.button("🧠 Yapay Zekaya Canlı Analiz Yaptır", use_container_width=True)
        st.button("⚡ Verileri Şimdi Yenile", type="primary", use_container_width=True)

    memory = load_memory()
    raw_events = fetch_day_events(date_str)
    if inc_yest: raw_events.extend(fetch_day_events(yesterday_str))

    processed, ana_kasa = [], []
    live_cnt = ft_cnt = pre_cnt = ft_hit = ft_total = ak_hit = ak_total = 0
    for slug, lg_name, tier_w, ev, ev_day in raw_events:
        res = process_single_event(slug, lg_name, tier_w, ev, ev_day, date_str, memory)
        if not res: continue
        memory[res["ev_id"]] = res["mem_data"]
        processed.append(res["item"])
        if res["state"] == "pre":
            pre_cnt += 1
            if res["is_ana_kasa"]: ana_kasa.append(res["item"])
        elif res["state"] == "post":
            ft_cnt += 1; ft_total += 1
            if res["is_hit"]: ft_hit += 1
            if res["is_ak_ft"]:
                ak_total += 1
                if res["is_hit"]: ak_hit += 1
        else: live_cnt += 1

    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f: json.dump(memory, f, ensure_ascii=False)
    except Exception: pass

    processed.sort(key=lambda x: (x["priority"], x["confidence"]), reverse=True)
    ana_kasa.sort(key=lambda x: x["confidence"], reverse=True)
    ft_pct = int(round((ft_hit / ft_total) * 100)) if ft_total > 0 else 0
    ak_pct = int(round((ak_hit / ak_total) * 100)) if ak_total > 0 else 0

    st.title(f"⚡ DELTA PULSE v4.5 | Bulut Radar ({time_str})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Maç Önü Karnesi", f"{ft_hit}/{ft_total} (%{ft_pct})")
    c2.metric("💎 Ana Kasa Karnesi", f"{ak_hit}/{ak_total} (%{ak_pct})")
    c3.metric("🔴 Canlı Maçlar", str(live_cnt))
    c4.metric("🕒 Maç Önü Bülten", str(pre_cnt))

    rep_lines = [f"TARİH: {date_str} {time_str} | KARNE: {ft_hit}/{ft_total} (%{ft_pct}) | ANA KASA: {ak_hit}/{ak_total} (%{ak_pct})"]
    for i, it in enumerate(processed, 1): rep_lines.extend([f"#{i}. [%{it['confidence']}] {it['lines'][0]}", it["lines"][1]])
    full_rep_text = "\n".join(rep_lines)

    if run_ai and gem_key:
        with st.spinner("🤖 Yapay Zeka canlı bülteni analiz ediyor..."):
            st.info(ask_gemini_ai_analyst(gem_key, full_rep_text))

    if ana_kasa:
        st.subheader(f"💎 Günün 'Ana Kasa' Hedefleri ({len(ana_kasa)} Maç)")
        for ak in ana_kasa:
            st.markdown(f"<div class='dp-ak'><b>[%{ak['confidence']} GÜVEN | {ak['kickoff']}] {ak['match_title']}</b> ({ak['league']})<br>🎯 <b>Tahmin:</b> {ak['tahmin']}</div>", unsafe_allow_html=True)

    t_live, t_pre, t_ft, t_raw = st.tabs([f"🔴 Canlı ({live_cnt})", f"🕒 Maç Önü ({pre_cnt})", f"🏁 Biten & Karne ({ft_cnt})", "📋 Tek Tık Kopyala"])
    with t_live:
        for m in [x for x in processed if x["state"] == "in"]:
            st.markdown(f"<div class='dp-card dp-live'><b>[%{m['confidence']} GÜVEN | {m['kickoff']}] {m['match_title']}</b> ({m['league']})<br>📊 {m['meta']}<br>⏱️ {m['yorum']}<br>🤖 <b>Karar:</b> {m['pusu']}</div>", unsafe_allow_html=True)
    with t_pre:
        for m in [x for x in processed if x["state"] == "pre"]:
            st.markdown(f"<div class='dp-card dp-pre'><b>[%{m['confidence']} GÜVEN | {m['kickoff']}] {m['match_title']}</b> ({m['league']})<br>📊 {m['meta']}<br>🧠 {m['yorum']}<br>🎯 <b>Tahmin:</b> {m['tahmin']}<br>📐 <b>Pusu:</b> {m['pusu']}</div>", unsafe_allow_html=True)
    with t_ft:
        for m in [x for x in processed if x["state"] == "post"]:
            cls = "dp-ft-ok" if m["is_hit"] else "dp-ft-no"
            badge = "✅ [TUTTU]" if m["is_hit"] else "❌ [YATTI]"
            st.markdown(f"<div class='dp-card {cls}'><b>[%{m['confidence']} | {m['kickoff']}] {m['match_title']}</b> — <b>{badge}</b><br>🎯 <b>Maç Önü Tahmini:</b> {m['tahmin']}<br>📊 {m['meta']} | 🤖 {m['pusu']}</div>", unsafe_allow_html=True)
    with t_raw:
        st.code(full_rep_text, language="text")

    if auto_ref:
        time.sleep(60)
        st.rerun()

if __name__ == "__main__":
    main()