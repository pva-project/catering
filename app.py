import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I STIL ---
st.set_page_config(page_title="Catering Admin", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"], header, footer {display: none !important;}
    .stAppDeployButton, [data-testid="stStatusWidget"], div[data-testid="stToolbar"] {display: none !important;}
    .block-container {padding-top: 1rem !important;}
    
    /* Stil za grafičke zvjezdice */
    .star-ratings { color: #ccc; position: relative; display: inline-block; font-size: 24px; }
    .star-ratings-fill { color: #ffca08; padding: 0; position: absolute; z-index: 1; display: block; top: 0; left: 0; overflow: hidden; white-space: nowrap; }
    </style>
""", unsafe_allow_html=True)

# Funkcija koja generiše HTML za zvjezdice
def renderuj_zvezdice(ocjena):
    procenat = (ocjena / 5) * 100
    return f"""
    <div style="display: inline-block; vertical-align: middle; margin-bottom: 10px;">
        <span style="font-weight: bold; font-size: 1.2rem; margin-right: 10px;">{ocjena}</span>
        <div class="star-ratings">
            <div class="star-ratings-fill" style="width: {procenat}%;"><span>★★★★★</span></div>
            <div><span>★★★★★</span></div>
        </div>
    </div>
    """

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame()

def analiziraj_podatke(k1_ime, k2_ime):
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns:
        return {}, 0.0, 0.0
    
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    prosjeci_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    
    k1_skor = df_o[df_o['Kuvar'] == k1_ime]['Numericka'].mean() if 'Kuvar' in df_o.columns else 0.0
    k2_skor = df_o[df_o['Kuvar'] == k2_ime]['Numericka'].mean() if 'Kuvar' in df_o.columns else 0.0
    
    return prosjeci_jela, round(pd.Series(k1_skor).fillna(0).iloc[0], 1), round(pd.Series(k2_skor).fillna(0).iloc[0], 1)

# --- LOGIN SISTEM ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Korisnik")
        p = st.text_input("Lozinka", type="password")
        if st.button("Prijavi se", use_container_width=True):
            if u in users and users[u] == p:
                st.session_state["logged_in"], st.session_state["user"] = True, u
                st.rerun()
            else: st.error("Pogrešni podaci")
else:
    # --- DOBAVLJANJE PODATAKA ---
    df_m_t = ucitaj_sheet("Meni_Trenutni")
    k1_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 1']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 1'].empty else "Kuvar 1"
    k2_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 2']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 2'].empty else "Kuvar 2"
    
    prosjeci_jela, skor_k1, skor_k2 = analiziraj_podatke(k1_ime, k2_ime)

    if st.session_state["user"] == "admin":
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])

        with t_a1: # KUHINJA
            st.markdown("### 👨‍🍳 Trenutni tim")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{k1_ime}**")
                st.markdown(renderuj_zvezdice(skor_k1), unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{k2_ime}**")
                st.markdown(renderuj_zvezdice(skor_k2), unsafe_allow_html=True)

            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                dan_sel = st.selectbox("Izaberi dan:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"]
                for smjena in ["I", "II", "III"]:
                    sm_data = prikaz[prikaz['Smjena'] == smjena]
                    if not sm_data.empty:
                        with st.container(border=True):
                            st.subheader(f"🕒 SMJENA {smjena}")
                            for jelo, j_data in sm_data.groupby("Jelo"):
                                r = prosjeci_jela.get(jelo, "0.0")
                                st.markdown(f"""
                                    <div style='background:#1E1E1E; padding:10px; border-radius:5px; margin-top:10px;'>
                                        <b style='color:#FF4B4B;'>{jelo}</b> <span style='color:#FFAA00; margin-left:15px;'>⭐ {r}</span>
                                    </div>
                                """, unsafe_allow_html=True)
                                for _, row in j_data.iterrows():
                                    st.write(f"🏢 {row['Firma']}: {int(row['Kolicina'])} kom")
                                st.markdown(f"<p style='text-align:right; color:#00FF00; font-weight:bold;'>UKUPNO: {int(j_data['Kolicina'].sum())}</p>", unsafe_allow_html=True)

        with t_a3: # OCJENE
            st.subheader("⭐ Rang lista kuvara")
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                st.info(f"Kuvar 1: {k1_ime}")
                st.markdown(renderuj_zvezdice(skor_k1), unsafe_allow_html=True)
            with c_r2:
                st.info(f"Kuvar 2: {k2_ime}")
                st.markdown(renderuj_zvezdice(skor_k2), unsafe_allow_html=True)
            
            st.divider()
            st.write("### Svi komentari")
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

        # ... (Ostali tabovi Meni i Reset ostaju isti)
