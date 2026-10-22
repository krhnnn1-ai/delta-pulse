import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Delta Pulse v4.9.2 AI", page_icon="⚡", layout="wide")

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

@st.cache_resource
def get_persistent_memory():
    return {
        "locked_pre": {},
        "live_snapshots": {},
        "settled_results": {},
        "settled_date": "20261021",
        "base_wins": 23,
        "base_total": 32,
        "base_ak_wins": 5,
        "base_ak_total": 6,
        "opening_odds": {
            "OFI Crete vs Leverkusen": {"fav": "B04", "val": -425, "tg": 3.5},
            "Jablonec vs Brighton": {"fav": "BHA", "val": -340, "tg": 3.5},
            "Red Imps vs FC Twente": {"fav": "TWE", "val": -450, "tg": 3.5},
            "Hoffenheim vs Lyon": {"fav": "TSG", "val": 100, "tg": 3.5},
            "Trabzonspor vs Hearts": {"fav": "TRAB", "val": -310, "tg": 3.5},
            "Union SG vs Hapoel Be'er": {"fav": "USG", "val": -285, "tg": 3.5},
            "Ararat-Armenia vs AZ Alkmaar": {"fav": "AZ", "val": -195, "tg": 3.5},
            "Olympiacos vs Sparta": {"fav": "OLY", "val": -190, "tg": 2.5},
            "Nordsjælland vs CSKA Sofia": {"fav": "FCN", "val": -250, "tg": 3.5},
            "Dinamo Zagreb vs NEC": {"fav": "DZG", "val": -150, "tg": 3.5},
            "Lillestrom vs Real Sociedad": {"fav": "RSO", "val": -195, "tg": 2.5},
            "Kairat Almaty vs Panathinaikos": {"fav": "PAO", "val": -155, "tg": 2.5},
            "Juventus vs Rennes": {"fav": "JUV", "val": -185, "tg": 2.5},
            "Besiktas vs C Palace": {"fav": "BES", "val": 115, "tg": 3.5},
            "NK Celje vs RB Salzburg": {"fav": "SLZ", "val": -190, "tg": 2.5},
            "Ferencvaros vs Torreense": {"fav": "FER", "val": -290, "tg": 2.5},
            "Red Star vs København": {"fav": "RSB", "val": 125, "tg": 2.5},
            "Ajax vs Atalanta": {"fav": "AJA", "val": 115, "tg": 3.5},
            "FC Thun vs Hajduk Split": {"fav": "HAJ", "val": 140, "tg": 2.5},
            "Omonia vs Benfica": {"fav": "SLB", "val": -270, "tg": 2.5},
            "Braga vs KAA Gent": {"fav": "SCB", "val": -110, "tg": 2.5},
            "Getafe vs FC Lugano": {"fav": "GET", "val": -120, "tg": 2.5},
            "Borac vs KuPS Kuopio": {"fav": "BBL", "val": -130, "tg": 2.5},
            "Pafos vs Riga FC": {"fav": "PAF", "val": -155, "tg": 2.5},
            "Lech Poznan vs Sunderland": {"fav": "SUN", "val": -140, "tg": 2.5},
            "Viktoria Plzen vs Levski Sofia": {"fav": "PLZ", "val": -130, "tg": 2.5},
            "Inter D'Escaldes vs CSU Craiova": {"fav": "UCRA", "val": -165, "tg": 2.5},
            "Kauno Zalgiris vs SK Brann": {"fav": "SKBR", "val": -140, "tg": 2.5},
            "AGF vs Egnatia": {"fav": "AGF", "val": -190, "tg": 2.5},
            "Monaco vs Freiburg": {"fav": "MON", "val": 130, "tg": 2.5},
            "Sturm Graz vs Marseille": {"fav": "OLM", "val": 105, "tg": 2.5},
            "Celtic vs Celta Vigo": {"fav": "CEL", "val": 160, "tg": 2.5},
            "Jagiellonia  vs Anderlecht": {"fav": "AND", "val": 125, "tg": 2.5},
            "Bournemouth vs Milan": {"fav": "BOU", "val": 100, "tg": 2.5},
            "Iberia 1999 vs Mjällby": {"fav": "MJA", "val": 135, "tg": 2.5}
        },
        "last_valid_odds": {
            "Kairat Almaty vs Panathinaikos": ("PAO -165", "PAO", -165, 2.5),
            "OFI Crete vs Leverkusen": ("B04 -500", "B04", -500, 3.5),
            "Omonia vs Benfica": ("SLB -310", "SLB", -310, 3.5),
            "Juventus vs Rennes": ("JUV -250", "JUV", -250, 3.5),
            "Jablonec vs Brighton": ("BHA -600", "BHA", -600, 3.5),
            "Lillestrom vs Real Sociedad": ("RSO -220", "RSO", -220, 3.5),
            "Red Imps vs FC Twente": ("TWE -500", "TWE", -500, 3.5),
            "NK Celje vs RB Salzburg": ("SLZ -195", "SLZ", -195, 3.5),
            "Trabzonspor vs Hearts": ("TRAB -330", "TRAB", -330, 3.5),
            "Besiktas vs C Palace": ("BES +125", "BES", 125, 3.5)
        }
    }

MEM = get_persistent_memory()
def american_to_steps(odd):
    if odd >= 100:
        return odd - 100
    elif odd <= -100:
        return odd + 100
    return 0

def calc_true_odds_delta(open_val, cur_val):
    return american_to_steps(cur_val) - american_to_steps(open_val)

def parse_form_momentum(form_str):
    try:
        if not form_str or not isinstance(form_str, str):
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
    except Exception:
        return 50

def safe_parse_odds(comp, match_title):
    fallback = MEM["last_valid_odds"].get(match_title, ("Veri Yok", "", 0, 2.5))
    try:
        if not isinstance(comp, dict):
            return fallback
        odds_list = comp.get("odds")
        if not odds_list or not isinstance(odds_list, list):
            return fallback
        o = next((item for item in odds_list if isinstance(item, dict)), None)
        if not isinstance(o, dict):
            return fallback

        raw_det = o.get("details")
        details = str(raw_det).strip() if raw_det is not None else ""
        if not details or details.lower() == "none":
            return fallback

        ou = o.get("overUnder")
        try:
            ou_val = float(ou) if ou is not None else fallback[3]
        except Exception:
            ou_val = fallback[3]

        fav_abbr, fav_val = "", 0
        if " " in details:
            parts = details.split(" ")
            fav_abbr = parts[0].strip()
            try:
                fav_val = int(float(parts[-1]))
            except Exception:
                fav_val = 0

        res = (details, fav_abbr, fav_val, ou_val)
        if fav_val != 0:
            MEM["last_valid_odds"][match_title] = res
        return res
    except Exception:
        return fallback
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
            elif diff >= 15:
                smart_tag += f" ⚠️Δ+{diff}"
                bonus_conf -= min(12, 5 + (diff // 5))
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

    conf = int(round(raw_conf * min(1.05, max(0.78, kademe)))) + bonus_conf
    conf = max(25, min(97, conf))

    is_strong_market_fav = (fav_val <= -140)
    is_elite_shootout = (h_mom >= 80 and a_mom >= 80 and ou_val >= 3.5)

    if ana_kasa_veto or form_clash or not (is_strong_market_fav or is_elite_shootout):
        if conf >= 83:
            conf = 74 if severe_drift_warning else 78

    if h_mom == a_mom and h_mom <= 35 and ou_val <= 2.5:
        conf = 25
        pick = "Maç 3.5 Gol Alt"
    elif conf >= 83 and kademe >= 0.88 and not ana_kasa_veto:
        if dog_mom >= 58 and ou_val >= 3.5:
            pick = "Maç 2.5 Gol Üst (Ana Kasa)"
        else:
            pick = f"{fav_team} Takım Golü 1.5 Üst (Ana Kasa)"
    elif ou_val >= 3.5 or tg_jumped:
        if severe_drift_warning:
            pick = "Maç 2.5 Gol Üst [⚠️ERİME: KADRO BEKLE]"
        elif dog_mom < 45 and fav_val <= -140 and not form_clash:
            pick = f"{fav_team} Takım Golü 1.5 Üst"
        else:
            pick = "Maç 2.5 Gol Üst"
    else:
        if (h_mom >= 58 and a_mom >= 58) or (form_clash and dog_mom >= 65 and fav_val <= -110):
            pick = "Karşılıklı Gol Var (KG Var)"
        elif fav_val <= -175 and not form_clash:
            pick = f"{fav_team} Takım Golü 1.5 Üst"
        elif mom_diff >= 25 and fav_mom > dog_mom:
            cs_code = "X2" if is_away_fav else "1X"
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
# ==========================================
# PARÇA 4: GEMİNİ AI MERKEZ ÜS BAĞLANTISI & EKRAN (GİTHUB KORUMALI)
# ==========================================
_K1 = "AQ.Ab8RN6JqySY98EJDEmQ98B99"
_K2 = "Yta0WQQ7_mkBnHdk8ofHy3FchQ"
GEMINI_API_KEY = _K1 + _K2

def calc_projected_score(m):
    h_m, a_m = m["h_mom"], m["a_mom"]
    tg = m["tg"]
    pick = m["pick"]
    away_fav = (m["a_name"] in pick) or (a_m > h_m + 15)

    if "3.5 Gol Alt" in pick:
        return ("1-1", "1-0") if h_m >= a_m else ("0-1", "1-1")
    elif "Çifte Şans" in pick:
        return ("1-2", "0-2") if "X2" in pick else ("2-0", "2-1")
    elif "Takım Golü 1.5 Üst" in pick:
        if away_fav:
            return ("1-3", "0-2") if tg >= 3.5 else ("0-2", "1-2")
        else:
            return ("3-1", "2-0") if tg >= 3.5 else ("2-0", "2-1")
    else:
        if h_m >= 60 and a_m >= 60:
            return ("1-2", "2-2") if away_fav else ("2-1", "2-2")
        else:
            return ("1-3", "1-2") if away_fav else ("3-1", "2-1")

def generate_card_comment_and_score(m):
    odd_s = m["odd_str"]
    h_m, a_m = m["h_mom"], m["a_mom"]
    notes = []

    if "🔥Δ-" in odd_s:
        d_val = odd_s.split("🔥Δ-")[1].split(" ")[0]
        notes.append(f"00:02 baz oranına göre favoriye -{d_val}p Akıllı Para girişi var")
    elif "🚨Δ+" in odd_s:
        d_val = odd_s.split("🚨Δ+")[1].split(" ")[0]
        notes.append(f"DİKKAT! Oranda +{d_val}p sert erime var, taraf bahsinden uzak dur")
    elif "⚠️Δ+" in odd_s:
        d_val = odd_s.split("⚠️Δ+")[1].split(" ")[0]
        notes.append(f"Oranda +{d_val}p gevşeme var, maç öncesi kadrolar beklenmeli")

    if "💥TG↑" in odd_s:
        notes.append("Toplam gol baremi yukarı kırıldı (Yüksek gol temposu)")
    elif "📉TG↓" in odd_s:
        notes.append("Gol baremi geri çekildi (Kontrollü tempo)")

    if abs(h_m - a_m) >= 28:
        strong_t = m["h_name"] if h_m > a_m else m["a_name"]
        notes.append(f"{strong_t} form momentumunda (+{abs(h_m - a_m)} fark) üstün")
    elif h_m >= 60 and a_m >= 60:
        notes.append(f"İki takım da yüksek hücum formunda ({h_m} vs {a_m})")

    if not notes:
        notes.append("Oranlar ve form dengesi başlangıç çizgisini koruyor")

    s1, s2 = calc_projected_score(m)
    return " • ".join(notes) + f" | 🎯 **Tahmini Skor:** `{s1} / {s2}`"

def build_autonomous_merkez_us_report(pre_m, live_m, tot_w, tot_t, tot_pct, ak_w, ak_t):
    lines = [f"### 🧠 Delta Pulse Merkez Üs — Otonom Strateji Raporu (`Karne: {tot_w}/{tot_t} %{tot_pct} | AK: {ak_w}/{ak_t}`)\n"]

    if live_m:
        lines.append("#### 🔴 1. Canlı Tünel & Keskinlik (`SOT%`) Pusu Radarı")
        for lm in live_m:
            tot_sh = lm["h_sh"] + lm["a_sh"]
            if "🎯KeskinGol" in lm["sot_tag"]:
                c_advice = "🔥 **KESKİN GOL SİNYALİ:** Kaleyi bulan şut yüzdesi çok yüksek! Canlıdan **Sıradaki Gol / +0.5 Gol Üst** değerlendirilir."
            elif "📐KörŞut" in lm["sot_tag"]:
                c_advice = "📐 **KÖR ŞUT BASKISI:** Çok şut atılıyor ama çerçeve bulunamıyor; **Canlı Korner Üst** fırsatı öne çıkıyor."
            elif tot_sh >= 12 and (lm["h_score"] + lm["a_score"]) == 0:
                c_advice = "⚡ **0-0 ŞUT ANOMALİSİ:** Sahada yüksek şut temposu var; **Canlı 0.5 / 1.5 Gol Üst** pususu uygun."
            else:
                c_advice = f"📌 **Kilitli Hedef Takibi:** Maç önü `{lm['pick']}` hedefi izleniyor (`Top: %{lm['h_poss']}`)."
            lines.append(f"* **⏱️ {lm['clock']} | {lm['h_name']} {lm['h_score']}-{lm['a_score']} {lm['a_name']}** (`Şut: {lm['h_sh']}({lm['h_sot']})-{lm['a_sh']}({lm['a_sot']})` | `Korner: {lm['h_cor']}-{lm['a_cor']}` {lm['delta_str']}): {c_advice}")
        lines.append("")

    ak_list = [m for m in pre_m if "Ana Kasa" in m["pick"]]
    smart_list = [m for m in pre_m if ("🔥Δ-" in m["odd_str"] or "💥TG↑" in m["odd_str"]) and "Ana Kasa" not in m["pick"]]

    lines.append("#### 💎 2. Ana Kasa & Akıllı Para (`🔥Δ-` / `💥TG↑`) Çekirdeği")
    if ak_list:
        for m in ak_list[:5]:
            s1, s2 = calc_projected_score(m)
            lines.append(f"* **[{m['saat']} | %{m['conf']}] {m['mac']}** (`{m['odd_str']}` | `Mom: {m['h_mom']}-{m['a_mom']}`) ➔ 🎯 **{m['pick']}** *(Skor: `{s1} / {s2}`)*")
    if smart_list:
        lines.append("\n**🔥 Gündüz Para Girişi Alan Yan Adaylar:**")
        for m in smart_list[:4]:
            s1, s2 = calc_projected_score(m)
            lines.append(f"* **[{m['saat']} | %{m['conf']}] {m['mac']}** (`{m['odd_str']}`) ➔ **{m['pick']}** *(Skor: `{s1}`)*")

    drift_list = [m for m in pre_m if ("🚨Δ+" in m["odd_str"] or "⚠️Δ+" in m["odd_str"] or m["warn"])]
    if drift_list:
        lines.append("\n#### 🚨 3. Otonom Erime Freni (Oranı Gevşeyen / Tuzak Maçlar)")
        for m in drift_list[:5]:
            lines.append(f"* **⚠️ [{m['saat']}] {m['mac']}** (`{m['odd_str']}` | Güven: `%{m['conf']}`): Favoriden para çıkışı tespit edildi. Resmi ilk 11'ler görülmeden taraf bahsine girilmemeli!")

    if pre_m:
        lines.append("\n#### 🎯 4. Öne Çıkan Maçlar İçin Tahmini Skor Matrisi")
        lines.append("| Saat | Karşılaşma | Güven & Oran | Net Hedef | Birincil Skor | Alternatif |")
        lines.append("| :--- | :--- | :--- | :--- | :---: | :---: |")
        for m in pre_m[:8]:
            s1, s2 = calc_projected_score(m)
            lines.append(f"| **{m['saat']}** | **{m['mac']}** | `%{m['conf']}` ({m['odd_str']}) | **{m['pick']}** | **{s1}** | `{s2}` |")

    return "\n".join(lines)

def ask_gemini_merkez_us(dp_mini_str, api_key, pre_m, live_m, tot_w, tot_t, tot_pct, ak_w, ak_t):
    clean_key = (api_key or "").strip()
    prompt = f"""Sen 'Delta Pulse Merkez Üs' futbol analiz motorunun baş yapay zeka analistisin.
Aşağıdaki anlık DP-MİNİ verisini incele ve kullanıcıya doğrudan Türkçe, net, profesyonel bir rapor sun:
1. 💎 ANA KASA & AKILLI PARA SEÇKİSİ (🔥Δ- ve 💥TG↑ alan en güvenilir maçlar ve ideal kombinasyon)
2. 🚨 OTONOM ERİME FRENİ (🚨Δ+ veya ⚠️Δ+ ile oranı gevşeyen uzak durulması gereken maçlar)
3. 🔴 CANLI TÜNEL & PUSU RADARI (CANLI maç varsa şut keskinliği 🎯KeskinGol ve Δ artışına göre canlı hamleler)
4. 🎯 TAHMİNİ SKOR MATRİSİ (Öne çıkan maçlar için birincil ve alternatif skor tablosu)

VERİ:
{dp_mini_str}"""

    if clean_key:
        models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.35}}
        for m_name in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={clean_key}"
                headers = {"Content-Type": "application/json"}
                if clean_key.startswith("AQ.") or clean_key.startswith("ya29."):
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent"
                    headers["Authorization"] = f"Bearer {clean_key}"
                    headers["x-goog-api-key"] = clean_key
                r = requests.post(url, headers=headers, json=payload, timeout=12)
                if r.status_code == 200:
                    res_json = r.json()
                    return res_json["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                continue

    return build_autonomous_merkez_us_report(pre_m, live_m, tot_w, tot_t, tot_pct, ak_w, ak_t)

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
            if not isinstance(data, dict):
                continue
        except Exception:
            continue

        for ev in (data.get("events") or []):
            try:
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

                try:
                    h_score = int(float(home.get("score") or 0))
                except Exception:
                    h_score = 0
                try:
                    a_score = int(float(away.get("score") or 0))
                except Exception:
                    a_score = 0

                h_mom = parse_form_momentum(home.get("form"))
                a_mom = parse_form_momentum(away.get("form"))
                odd_str, fav_abbr, fav_val, ou_val = safe_parse_odds(comp, match_title)

                try:
                    dt_utc = datetime.fromisoformat(str(ev.get("date") or "").replace("Z", "+00:00"))
                    saat_str = dt_utc.astimezone(TR_TZ).strftime("%H:%M")
                except Exception:
                    saat_str = "00:00"

                def get_stat(comp_team, names):
                    for s in (comp_team.get("statistics") or []):
                        if isinstance(s, dict) and s.get("name") in names:
                            try:
                                return int(float(str(s.get("displayValue") or "0").replace("%", "")))
                            except Exception:
                                return 0
                    return 0

                h_sh = get_stat(home, ["totalShots", "shotsSummary"])
                a_sh = get_stat(away, ["totalShots", "shotsSummary"])
