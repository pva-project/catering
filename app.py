import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import re
import time

# --- 1. OSNOVNA STILIZACIJA ---
st.set_page_config(page_title="Catering System", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important; background-color: #0E1117;}
    
    .period-box { background-color: #1A2C42; padding: 15px; border-radius: 8px; color: white; margin-bottom: 20px; border-left: 5px solid #4A90E2; }
    .stDownloadButton button { background: #E24A4A !important; color: white !important; width: 100%; border-radius: 10px; }
    .kuhinja-box { background-color: #161922; border-radius: 15px; padding: 20px; border-left: 5px solid #E24A4A; margin-bottom: 20px; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. POVEZIVANJE ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

def ucitaj_sheet(name):
    try: return conn.read(spreadsheet=spreadsheet_url, worksheet=name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

def izvadi_sat(tekst):
    brojevi = re.findall(r'\d+', str(tekst))
    return int(brojevi[0]) if brojevi else 16

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
    # --- ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.markdown('## 👨‍🍳 Admin Panel')
        t1, t2, t3 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene"])
        
        with t1:
            df_nar = ucitaj_sheet("Sheet1")
            dan_sel = st.selectbox("Izaberi dan:", dani_std)
            if not df_nar.empty:
                dan_data = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"]
                st.download_button("📥 ŠTAMPAJ LISTU (CSV)", data=dan_data.to_csv(), file_name=f"{dan_sel}.csv")
                for smj in ["I", "II", "III"]:
                    smj_d = dan_data[dan_data['Smjena'] == smj]
                    if not smj_d.empty:
                        h_box = f'<div class="kuhinja-box"><b>🕒 SMJENA {smj}</b>'
                        for jelo, j_d in smj_d.groupby("Jelo"):
                            h_box += f'<div style="color:#E24A4A; font-weight:bold; margin-top:10px;">{jelo}</div>'
                            for _, r in j_d.iterrows():
                                h_box += f'<div style="display:flex; justify-content:space-between;"><span>{r["Firma"]}</span><b>{int(r["Kolicina"])}</b></div>'
                        st.markdown(h_box + '</div>', unsafe_allow_html=True)

    # --- KLIJENT PANEL (ORIGINALNA LOGIKA) ---
    else:
        f_user = st.session_state["user"]
        st.markdown(f"# {f_user}")
        
        meni_t = ucitaj_sheet("Meni_Trenutni")
        df_nar = ucitaj_sheet("Sheet1")
        
        if not meni_t.empty:
            period = meni_t[meni_t['Dan']=='Sedmica']['Jelo'].values[0]
            rok_tekst = meni_t[meni_t['Dan']=='Rok']['Jelo'].values[0]
            sat_limita = izvadi_sat(rok_tekst)
            sada = datetime.now() + timedelta(hours=2)
            
            st.markdown(f'<div class="period-box">📅 {period} | 🕒 Rok: {rok_tekst}h</div>', unsafe_allow_html=True)
            
            izbor_dana = st.selectbox("Dan:", dani_std)
            jela_za_dan = meni_t[meni_t['Dan'] == izbor_dana]['Jelo'].tolist()
            
            idx_dana = dani_std.index(izbor_dana)
            zakljucano = (idx_dana < sada.weekday()) or (idx_dana == sada.weekday() and sada.hour >= sat_limita)
            
            if zakljucano:
                st.error(f"🔒 Zatvoreno za {izbor_dana}.")
            else:
                with st.form("narudzba", clear_on_submit=True):
                    jelo = st.selectbox("Jelo:", jela_za_dan)
                    smjena = st.radio("Smjena:", ["I", "II", "III"], horizontal=True)
                    kol = st.number_input("Količina:", min_value=1, value=1)
                    if st.form_submit_button("🚀 NARUČI"):
                        nova = pd.DataFrame([{"Firma": f_user, "Dan": f"Ova-{izbor_dana}", "Smjena": smjena, "Jelo": jelo, "Kolicina": kol, "Vrijeme": sada.strftime("%H:%M")}])
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_nar, nova]))
                        st.success("Dodano!")
                        time.sleep(1)
                        st.rerun()

            st.markdown("### 📋 Tvoje narudžbe:")
            moje = df_nar[df_nar['Firma'] == f_user]
            st.dataframe(moje[['Dan', 'Smjena', 'Jelo', 'Kolicina']], use_container_width=True, hide_index=True)

            with st.expander("⭐ Ocjeni ručak"):
                with st.form("ocjena"):
                    j_ocj = st.selectbox("Šta ocjenjuješ?", jela_za_dan)
                    ocj_v = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Dobro")
                    kom_v = st.text_input("Komentar:")
                    if st.form_submit_button("Sačuvaj"):
                        n_ocj = pd.DataFrame([{"Jelo": j_ocj, "Ocjena": ocj_v, "Komentar": kom_v, "Firma": f_user}])
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([ucitaj_sheet("Ocjene"), n_ocj]))
                        st.success("Hvala!")
        
        if st.button("Odjavi se"):
            st.session_state["logged_in"] = False
            st.rerun()
