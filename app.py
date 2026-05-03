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
    
    .star-ratings { color: #ccc; position: relative; display: inline-block; font-size: 20px; }
    .star-ratings-fill { color: #ffca08; padding: 0; position: absolute; z-index: 1; display: block; top: 0; left: 0; overflow: hidden; white-space: nowrap; }
    </style>
""", unsafe_allow_html=True)

# Funkcija za vizuelni prikaz zvjezdica
def prikazi_zvjezdice(ocjena):
    procenat = (ocjena / 5) * 100
    return f"""
    <div style="display: inline-block; vertical-align: middle;">
        <span style="font-weight: bold; font-size: 1.1rem; margin-right: 8px;">{ocjena}</span>
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

# Logika za prosjek kuvara na osnovu ocjena jela
def izracunaj_prosjek_kuvara():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return 0.0
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    return round(df_o['Numericka'].mean(), 1)

# --- 2. LOGIN SISTEM ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Korisnik")
        p = st.text_input("Lozinka", type="password")
        if st.button("Prijavi se", use_container_width=True):
            if u == "admin" and p == "admin123":
                st.session_state["logged_in"] = True
                st.session_state["user"] = "admin"
                st.rerun()
else:
    # --- 3. ADMIN PANEL ---
    df_m_t = ucitaj_sheet("Meni_Trenutni")
    
    # Povlačenje imena oba kuvara iz tabele
    kuvar1 = df_m_t[df_m_t['Dan'] == 'Kuvar 1']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 1'].empty else "N/A"
    kuvar2 = df_m_t[df_m_t['Dan'] == 'Kuvar 2']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 2'].empty else "N/A"
    
    prosjek_sedmice = izracunaj_prosjek_kuvara()
    
    t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])

    with t_a1: # TAB KUHINJA
        with st.container(border=True):
            st.markdown(f"**👨‍🍳 Trenutni tim: {kuvar1} & {kuvar2}**")
            st.markdown(prikazi_zvjezdice(prosjek_sedmice), unsafe_allow_html=True)

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
                            # Tekstualna ocjena jela
                            st.markdown(f"<div style='background:#1E1E1E; padding:8px; border-radius:5px;'><b>{jelo}</b></div>", unsafe_allow_html=True)
                            for _, row in j_data.iterrows():
                                st.write(f"🏢 {row['Firma']}: {int(row['Kolicina'])} kom")
                            st.success(f"UKUPNO: {int(j_data['Kolicina'].sum())}")

    with t_a3: # TAB OCJENE
        st.subheader("⭐ Rang lista kuvara")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Kuvar 1: {kuvar1}")
            st.markdown(prikazi_zvjezdice(prosjek_sedmice), unsafe_allow_html=True)
        with col2:
            st.info(f"Kuvar 2: {kuvar2}")
            st.markdown(prikazi_zvjezdice(prosjek_sedmice), unsafe_allow_html=True)
        
        st.divider()
        st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)
