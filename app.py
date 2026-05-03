import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I STIL ---
st.set_page_config(page_title="Catering Management", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"], header, footer {display: none !important;}
    .block-container {padding-top: 1rem !important;}
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame()

def tekstualne_zvijezde(ocjena):
    pune = int(round(ocjena)) if not pd.isna(ocjena) else 0
    return "⭐" * pune + "☆" * (5 - pune) + f" ({ocjena if not pd.isna(ocjena) else 0.0})"

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    p_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    p_kuvari = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return p_jela, p_kuvari

# --- 3. LOGIN SISTEM (VRAĆEN NA ORIGINALNI) ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava za Catering</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Korisničko ime")
        p = st.text_input("Lozinka", type="password")
        if st.button("Prijavi se", use_container_width=True):
            if u in users and users[u] == p:
                st.session_state["logged_in"] = True
                st.session_state["user"] = u
                st.rerun()
            else:
                st.error("Pogrešni podaci")
else:
    # --- 4. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        df_m_t = ucitaj_sheet("Meni_Trenutni")
        p_jela, p_kuvari = izracunaj_prosjeke()

        # Povlačenje imena kuvara iz Menija
        k1_ime = df_m_t[df_m_t['Dan'].str.contains('Kuvar 1', na=False)]['Jelo'].values[0] if not df_m_t[df_m_t['Dan'].str.contains('Kuvar 1', na=False)].empty else "N/A"
        k2_ime = df_m_t[df_m_t['Dan'].str.contains('Kuvar 2', na=False)]['Jelo'].values[0] if not df_m_t[df_m_t['Dan'].str.contains('Kuvar 2', na=False)].empty else "N/A"

        st.title("👨‍🍳 Admin Panel")
        t_kuh, t_meni, t_ocj, t_res = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])

        with t_kuh: #
            c1, c2 = st.columns(2)
            c1.metric(f"Kuvar 1: {k1_ime}", tekstualne_zvijezde(p_kuvari.get(k1_ime, 0.0)))
            c2.metric(f"Kuvar 2: {k2_ime}", tekstualne_zvijezde(p_kuvari.get(k2_ime, 0.0)))
            
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                d_sel = st.selectbox("Izaberi dan:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"]
                for smjena in ["I", "II", "III"]:
                    sm_data = prikaz[prikaz['Smjena'] == smjena]
                    if not sm_data.empty:
                        with st.container(border=True):
                            st.subheader(f"Smjena {smjena}")
                            for jelo, j_data in sm_data.groupby("Jelo"):
                                st.write(f"🍱 **{jelo}** | {tekstualne_zvijezde(p_jela.get(jelo, 0.0))}")
                                st.write(f"Ukupno: **{int(j_data['Kolicina'].sum())} kom**")
                                st.divider()

        with t_ocj: #
            st.subheader("⭐ Rang lista")
            col1, col2 = st.columns(2)
            col1.info(f"Prosjek {k1_ime}: {p_kuvari.get(k1_ime, 0.0)} ⭐")
            col2.info(f"Prosjek {k2_ime}: {p_kuvari.get(k2_ime, 0.0)} ⭐")
            st.divider()
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

    # --- 5. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 Zdravo, {st.session_state['user']}")
        # Ovdje nastavi tvoj originalni kod za naručivanje...
        if st.button("Odjavi se"):
            st.session_state["logged_in"] = False
            st.rerun()
