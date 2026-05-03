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
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame()

def analiziraj_sve_ocjene():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, 0.0, {}
    
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    prosjeci_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    ukupni_prosjek = df_o['Numericka'].mean().round(1)
    
    # Ako u tabeli Ocjene imate kolonu 'Kuvar', možemo grupisati po njima
    prosjeci_kuvara = {}
    if 'Kuvar' in df_o.columns:
        prosjeci_kuvara = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict()
        
    return prosjeci_jela, ukupni_prosjek, prosjeci_kuvara

# --- ADMIN PANEL ---
if "logged_in" in st.session_state and st.session_state["user"] == "admin":
    t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene", "🔄 Reset"])
    
    prosjeci_jela, ukupni_skor, prosjeci_po_kuvarima = analiziraj_sve_ocjene()
    df_m_t = ucitaj_sheet("Meni_Trenutni")
    
    # Izvlačenje imena oba kuvara iz podešavanja menija
    kuvar1 = df_m_t[df_m_t['Dan'] == 'Kuvar 1']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 1'].empty else "N/A"
    kuvar2 = df_m_t[df_m_t['Dan'] == 'Kuvar 2']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 2'].empty else "N/A"

    # --- TAB 1: KUHINJA ---
    with t_a1:
        st.markdown("### 👨‍🍳 Trenutni tim")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Kuvar 1: {kuvar1}**")
            st.markdown(prikazi_zvjezdice(prosjeci_po_kuvarima.get(kuvar1, 0.0)), unsafe_allow_html=True)
        with c2:
            st.write(f"**Kuvar 2: {kuvar2}**")
            st.markdown(prikazi_zvjezdice(prosjeci_po_kuvarima.get(kuvar2, 0.0)), unsafe_allow_html=True)
        # ... ostatak koda za smjene ...

    # --- TAB 3: OCJENE (RANG OBA KUVARA) ---
    with t_a3:
        st.subheader("⭐ Rang lista kuvara")
        with st.container(border=True):
            col_k1, col_k2 = st.columns(2)
            with col_k1:
                st.info(f"**{kuvar1}**")
                st.markdown(prikazi_zvjezdice(prosjeci_po_kuvarima.get(kuvar1, 0.0)), unsafe_allow_html=True)
            with col_k2:
                st.info(f"**{kuvar2}**")
                st.markdown(prikazi_zvjezdice(prosjeci_po_kuvarima.get(kuvar2, 0.0)), unsafe_allow_html=True)
        
        st.divider()
        st.write("### Detaljni komentari i ocjene")
        st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

    # --- TAB 2: IZMJENA (Dodaj polje za drugog kuvara) ---
    with t_a2:
        with st.form("f_izmjena"):
            # Ovdje dodajemo inpute za oba kuvara da bi ih admin mogao upisati
            n_k1 = st.text_input("Glavni kuvar 1:", value=kuvar1)
            n_k2 = st.text_input("Glavni kuvar 2:", value=kuvar2)
            # ... ostatak forme za jela ...
            if st.form_submit_button("Sačuvaj"):
                # Logika za čuvanje oba kuvara u Meni_Trenutni
                pass
