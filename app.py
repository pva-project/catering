import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. TOTALNO SKRIVANJE SVIH IKONA (FORK, GITHUB, KRUNICA) ---
st.set_page_config(page_title="Catering Management", layout="centered")

ultimate_hide_style = """
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    [data-testid="stFooter"] {display: none !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    button[title="View source on GitHub"] {display: none !important;}
    .block-container {padding-top: 1rem !important; padding-bottom: 0rem !important;}
    
    /* Stil za kartice u kuhinji */
    .kuhinja-card {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 10px;
    }
    </style>
"""
st.markdown(ultimate_hide_style, unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()

# --- FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame()

# --- LOGIN ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Korisničko ime")
        p = st.text_input("Lozinka", type="password")
        if st.button("Prijavi se", use_container_width=True):
            if u == "admin" and p == "admin123": # Primjer, dodaj ostale
                st.session_state["logged_in"], st.session_state["user"] = True, u
                st.rerun()
            else: st.error("Pogrešni podaci")
else:
    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene", "🔄 Reset"])
        
        with t_a1:
            st.subheader("Pregled narudžbi po firmama")
            df_nar = ucitaj_sheet("Sheet1")
            
            if not df_nar.empty:
                d_sel = st.selectbox("Izaberi dan:", dani_std)
                # Filtriramo narudžbe za odabrani dan
                prikaz_df = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"]
                
                if not prikaz_df.empty:
                    # Grupišemo po firmi da krupno vidimo ko je šta naručio
                    for firma, data in prikaz_df.groupby("Firma"):
                        with st.container(border=True):
                            st.markdown(f"### 🏢 {firma}")
                            for _, row in data.iterrows():
                                col1, col2 = st.columns([2, 1])
                                col1.markdown(f"**{row['Jelo']}** (Smjena: {row['Smjena']})")
                                col2.markdown(f"## 🔢 {int(row['Kolicina'])}")
                else:
                    st.info(f"Nema narudžbi za {d_sel}.")
            else:
                st.info("Baza podataka je prazna.")

        # --- OSTATAK ADMIN KODA (IZMJENA, OCJENE, RESET) ---
        with t_a2:
            st.info("Ovdje ide tvoj kod za izmjenu menija (vidi prethodne poruke)")
            # ... (ovdje ubaci svoj kod za Meni_Trenutni / Meni_Naredni)
            
        with t_a4:
            if st.button("🚀 ROTIRAJ SEDMICU"):
                # ... (ovdje ubaci kod za rotaciju koji smo ranije napravili)
                st.success("Rotirano!")

    # --- KORISNIČKI PANEL OSTALJE ISTI KAO PRIJE ---
    else:
        st.write(f"Dobrodošli, {st.session_state['user']}")
        # ... (ovdje ide tvoj kod za korisnike)
