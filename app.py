import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import re
import time

# --- 1. STILIZACIJA (Premium Dashboard UI) ---
st.set_page_config(page_title="Catering System Pro", layout="centered")

st.markdown("""
    <style>
    /* Globalno sklanjanje suvišnih elemenata */
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important; background-color: #0E1117;}

    /* Naslov */
    .admin-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: white;
        margin-bottom: 20px;
        text-align: center;
    }

    /* KARTICE STATUSA (Kuhinja) */
    .status-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
    .status-card {
        background: #1A1C23;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
    }
    .status-f-name { font-size: 0.75rem; color: #999; text-transform: uppercase; margin-bottom: 5px; }
    .dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .dot-green { background-color: #00FF41; box-shadow: 0 0 8px #00FF41; }
    .dot-red { background-color: #FF3131; box-shadow: 0 0 8px #FF3131; }
    .dot-yellow { background-color: #FFD700; box-shadow: 0 0 8px #FFD700; }
    .st-green { color: #00FF41; font-weight: bold; font-size: 0.8rem; }
    .st-red { color: #FF3131; font-weight: bold; font-size: 0.8rem; }
    .st-yellow { color: #FFD700; font-weight: bold; font-size: 0.8rem; }

    /* ANALITIKA (Ocjene) */
    .highlight-card {
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 15px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .hit-bg { background: linear-gradient(90deg, rgba(0,255,65,0.1) 0%, rgba(0,0,0,0) 100%); border-left: 5px solid #00FF41; }
    .lose-bg { background: linear-gradient(90deg, rgba(255,49,49,0.1) 0%, rgba(0,0,0,0) 100%); border-left: 5px solid #FF3131; }

    /* CHEF GRID */
    .chef-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 12px;
        margin: 15px 0;
    }
    .chef-card-v2 {
        background: #1A1C23;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        position: relative;
        border: 1px solid #333;
    }
    .crown { position: absolute; top: -8px; right: -5px; font-size: 1.2rem; transform: rotate(15deg); }
    .chef-val { font-size: 1.6rem; font-weight: 800; color: #FFD700; display: block; }
    .chef-name-v2 { font-size: 0.7rem; color: #777; text-transform: uppercase; }

    /* RESET KARTICA */
    .reset-card {
        background: rgba(226, 74, 74, 0.05);
        border: 1px dashed #E24A4A;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Kuhinja Box i Dugme */
    .kuhinja-box { background: #161922; border-radius: 15px; padding: 20px; border-left: 5px solid #E24A4A; margin-bottom: 20px; }
    .stDownloadButton button {
        background: linear-gradient(135deg, #E24A4A 0%, #8B0000 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        width: 100%;
        font-weight: bold !important;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. POMOĆNE FUNKCIJE ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
sve_firme = ["Lattonedil", "PVA Group", "Esintec", "ActivBH"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

def ucitaj_sheet(name):
    try: return conn.read(spreadsheet=spreadsheet_url, worksheet=name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    pj = df_o.groupby('Jelo')['Numericka'].mean().round(1).sort_values(ascending=False).to_dict()
    pk = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return pj, pk

def izvadi_sat_iz_roka(rok_tekst):
    try:
        brojevi = re.findall(r'\d+', str(rok_tekst))
        return int(brojevi[0]) if brojevi else 16
    except: return 16

# --- 3. LOGIN ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava</h1>", unsafe_allow_html=True)
    u = st.text_input("Korisnik")
    p = st.text_input("Lozinka", type="password")
    if st.button("Prijavi se", use_container_width=True):
        if u in users and users[u] == p:
            st.session_state["logged_in"], st.session_state["user"] = True, u
            st.rerun()
else:
    # --- 4. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.markdown('<div class="admin-title">👨‍🍳 Admin Upravljanje</div>', unsafe_allow_html=True)
        t1, t2, t3, t4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t1: # KUHINJA
            df_nar = ucitaj_sheet("Sheet1")
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            rok_tekst = df_m_t[df_m_t['Dan']=='Rok']['Jelo'].values[0] if not df_m_t.empty else "16:00"
            sat_limita = izvadi_sat_iz_roka(rok_tekst)
            dan_sel = st.selectbox("Izaberi dan:", dani_std)
            
            st.markdown("### 🕒 Statusi narudžbi")
            status_html = '<div class="status-container">'
            sada = datetime.now() + timedelta(hours=2)
            danas_idx = sada.weekday()
            iz_idx = dani_std.index(dan_sel)
            for f in sve_firme:
                unio = not df_nar[(df_nar['Firma'] == f) & (df_nar['Dan'] == f"Ova-{dan_sel}")].empty if not df_nar.empty else False
                kasni = (iz_idx == danas_idx + 1 and sada.hour >= sat_limita) or (iz_idx <= danas_idx)
                if unio: cls, dot, txt = "st-green", "dot-green", "NARUČENO"
                elif kasni: cls, dot, txt = "st-red", "dot-red", "KASNE"
                else: cls, dot, txt = "st-yellow", "dot-yellow", "ČEKANJE"
                status_html += f'<div class="status-card"><div class="status-f-name">{f}</div><div class="{cls}"><span class="dot {dot}"></span>{txt}</div></div>'
            st.markdown(status_html + '</div>', unsafe_allow_html=True)
            
            if not df_nar.empty:
                dan_data = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"]
                st.download_button("📥 PREUZMI LISTU ZA ŠTAMPU", data="HTML_KOD_GENERATOR", file_name=f"Kuhinja_{dan_sel}.html", use_container_width=True)
                for smj in ["I", "II", "III"]:
                    smj_d = dan_data[dan_data['Smjena'] == smj]
                    if not smj_d.empty:
                        html = f'<div class="kuhinja-box"><div style="font-size:1.2rem; font-weight:bold; margin-bottom:10px;">🕒 SMJENA {smj}</div>'
                        for jelo, j_d in smj_d.groupby("Jelo"):
                            html += f'<div style="color:#E24A4A; font-weight:bold; margin-top:10px; border-bottom:1px solid #333;">🍴 {jelo}</div>'
                            for _, r in j_d.iterrows():
                                html += f'<div style="display:flex; justify-content:space-between; font-size:0.9rem; padding:5px 0;"><span>{r["Firma"]}</span><span>{int(r["Kolicina"])} kom</span></div>'
                            html += f'<div style="text-align:right; color:#00FF41; font-weight:bold; padding-top:5px;">UKUPNO: {int(j_d["Kolicina"].sum())}</div>'
                        st.markdown(html + '</div>', unsafe_allow_html=True)

        with t2: # MENI
            od_m = st.radio("Uredi:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"f_{od_m}"):
                c1,c2,c3 = st.columns(3)
                n_s = c1.text_input("Period:", df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty else "")
                n_r = c2.text_input("Rok:", df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty else "")
                n_k = c3.text_input("Kuvar:", df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty else "")
                novi = [{"Dan":"Sedmica","Jelo":n_s},{"Dan":"Rok","Jelo":n_r},{"Dan":"Kuvar","Jelo":n_k}]
                for d in dani_std:
                    st.markdown(f"**{d}**")
                    p_jela = df_m[df_m['Dan']==d]['Jelo'].tolist() if not df_m.empty else []
                    col1, col2, col3 = st.columns(3)
                    for i, c in enumerate([col1, col2, col3]):
                        stara = p_jela[i] if i < len(p_jela) else ""
                        un = c.text_input(f"{d} {i+1}", stara, key=f"{od_m}{d}{i}")
                        if un: novi.append({"Dan":d, "Jelo":un})
                if st.form_submit_button("SAČUVAJ"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi))
                    st.success("Sačuvano!"); time.sleep(1); st.rerun()

        with t3: # OCJENE (Premium Dashboard)
            pj, pk = izracunaj_prosjeke()
            st.markdown("### 📈 Analitika Kuhinje")
            if pj:
                df_pj = pd.DataFrame(list(pj.items()), columns=['Jelo', 'Ocjena'])
                st.markdown(f"""
                    <div class="highlight-card hit-bg">
                        <span style="font-size: 2rem;">🏆</span>
                        <div><small style="color: #00FF41; font-weight: bold; text-transform: uppercase;">Hit Mjeseca</small>
                        <div style="font-size: 1.1rem; font-weight: bold;">{df_pj.iloc[0]['Jelo']} ({df_pj.iloc[0]['Ocjena']} ⭐)</div></div>
                    </div>
                    <div class="highlight-card lose-bg">
                        <span style="font-size: 2rem;">⚠️</span>
                        <div><small style="color: #FF3131; font-weight: bold; text-transform: uppercase;">Izbaciti sa menija</small>
                        <div style="font-size: 1.1rem; font-weight: bold;">{df_pj.iloc[-1]['Jelo']} ({df_pj.iloc[-1]['Ocjena']} ⭐)</div></div>
                    </div>
                """, unsafe_allow_html=True)
                st.bar_chart(df_pj.set_index('Jelo'))
            st.divider()
            if pk:
                st.markdown("### 👨‍🍳 Rang Lista Kuvara")
                ch_html = '<div class="chef-grid">'
                max_r = max(pk.values())
                for ime, oc in pk.items():
                    kruna = '<div class="crown">👑</div>' if oc == max_r else ""
                    ch_html += f'<div class="chef-card-v2">{kruna}<span class="chef-name-v2">{ime}</span><span class="chef-val">{oc}</span><span style="color:#FFD700; font-size:0.7rem;">★★★★★</span></div>'
                st.markdown(ch_html + '</div>', unsafe_allow_html=True)

        with t4: # RESET (Danger Zone)
            st.markdown("""<div class="reset-card"><span style="font-size: 3rem;">🚀</span><h2 style="color: white; margin: 10px 0;">Rotacija Sedmica</h2>
            <span style="color:#E24A4A; font-weight:bold;">UPOZORENJE: Ovo resetuje sve narudžbe i postavlja novi meni!</span></div>""", unsafe_allow_html=True)
            if st.button("POTVRDI I ROTIRAJ", use_container_width=True, type="primary"):
                df_n = ucitaj_sheet("Meni_Naredni")
                if not df_n.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_n)
                    st.balloons(); st.success("Sistem ažuriran!"); time.sleep(1); st.rerun()

    # --- 5. KLIJENT PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_o, t_n, t_h, t_oc = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna", "📜 Istorija", "⭐ Ocijeni"])
        pj, _ = izracunaj_prosjeke()
        def render_c(sh, pref, lock):
            df_m = ucitaj_sheet(sh); df_sve = ucitaj_sheet("Sheet1")
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty else "/"
            r_t = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty else "16:00"
            k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty else "/"
            sat_l = izvadi_sat_iz_roka(r_t); sada = datetime.now() + timedelta(hours=2)
            if lock:
                if sada.hour < sat_l: st.info(f"⏳ **ROK: Još {sat_l - sada.hour}h do zatvaranja**")
                else: st.error(f"🔒 **Rok ({r_t}) je istekao!**")
            st.markdown(f'<div class="info-container"><div class="info-card blue-card">📅 {s}</div><div class="info-card yellow-card">⏰ ROK: {r_t}</div><div class="info-card green-card">👨‍🍳 {k}</div></div>', unsafe_allow_html=True)
            with st.form(f"f_{pref}"):
                unose = []
                for d in dani_std:
                    idx = dani_std.index(d); dis = (sada.weekday() >= idx or (sada.weekday()+1 == idx and sada.hour >= sat_l)) if lock else False
                    with st.container(border=True):
                        st.markdown(f"#### {'🔒' if dis else '📅'} {d}")
                        for j in (df_m[df_m['Dan']==d]['Jelo'].tolist() if not df_m.empty else []):
                            st.write(f"**{j}** {f'(⭐ {pj.get(j)})' if pj.get(j) else ''}")
                            c1,c2,c3 = st.columns(3)
                            def g_v(sn):
                                m = df_sve[(df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{pref}-{d}") & (df_sve['Jelo']==j) & (df_sve['Smjena']==sn)] if not df_sve.empty else pd.DataFrame()
                                return int(m['Kolicina'].iloc[0]) if not m.empty else 0
                            k1=c1.number_input("I",0,100,g_v("I"),key=f"{pref}{d}{j}1",disabled=dis)
                            k2=c2.number_input("II",0,100,g_v("II"),key=f"{pref}{d}{j}2",disabled=dis)
                            k3=c3.number_input("III",0,100,g_v("III"),key=f"{pref}{d}{j}3",disabled=dis)
                            for v, sn in zip([k1,k2,k3],["I","II","III"]):
                                if v > 0: unose.append({"Firma":st.session_state['user'], "Dan":f"{pref}-{d}", "Jelo":j, "Kolicina":v, "Smjena":sn})
                if st.form_submit_button("SAČUVAJ"):
                    df_ost = df_sve[~((df_sve['Firma']==st.session_state['user']) & (df_sve['Dan'].str.startswith(pref)))] if not df_sve.empty else pd.DataFrame()
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_ost, pd.DataFrame(unose)]))
                    st.success("Spremljeno!"); time.sleep(1); st.rerun()

        with t_o: render_c("Meni_Trenutni", "Ova", True)
        with t_n: render_c("Meni_Naredni", "Naredna", False)
        with t_h: st.dataframe(ucitaj_sheet("Sheet1")[lambda x: x['Firma'] == st.session_state['user']] if not ucitaj_sheet("Sheet1").empty else pd.DataFrame(), use_container_width=True, hide_index=True)
        with t_oc:
            with st.form("f_ocj"):
                jela = ucitaj_sheet("Meni_Trenutni")[lambda x: x['Dan'].isin(dani_std)]['Jelo'].unique().tolist()
                j_sel = st.selectbox("Jelo:", jela); oc = st.select_slider("Ocjena:", ["Loše","Može bolje","Dobro","Odlično","Savršeno"], "Odlično")
                kom = st.text_area("Komentar:")
                if st.form_submit_button("POŠALJI"):
                    df_o = ucitaj_sheet("Ocjene"); novi = pd.DataFrame([{"Firma":st.session_state['user'], "Jelo":j_sel, "Ocjena":oc, "Komentar":kom, "Kuvar": ucitaj_sheet("Meni_Trenutni")[lambda x: x['Dan']=='Kuvar']['Jelo'].values[0]}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o, novi])); st.success("Hvala!"); time.sleep(1); st.rerun()
