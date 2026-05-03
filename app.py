import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA (Tvoja originalna) ---
st.set_page_config(page_title="Catering Management", layout="centered")
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. KORISNICI (Tvoji originalni) ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: 
        return pd.DataFrame(columns=["Dan", "Jelo"])

# Popravljena funkcija za zvjezdice (bez HTML koda koji puca)
def tekstualne_zvijezde(ocjena):
    pune = int(round(ocjena)) if not pd.isna(ocjena) else 0
    return "⭐" * pune + "☆" * (5 - pune) + f" ({ocjena if not pd.isna(ocjena) else 0.0})"

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    p_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    # Računanje po imenu kuvara iz kolone 'Kuvar'
    p_kuvari = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return p_jela, p_kuvari

# --- 4. LOGIN (Tvoj originalni koji radi) ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava za Catering</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Korisničko ime")
        p = st.text_input("Lozinka", type="password")
        if st.button("Prijavi se", use_container_width=True):
            if u in users and users[u] == p:
                st.session_state["logged_in"], st.session_state["user"] = True, u
                st.rerun()
            else: st.error("Pogrešni podaci")
else:
    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene", "🔄 Reset"])
        
        df_m_t = ucitaj_sheet("Meni_Trenutni")
        p_jela, p_kuvari = izracunaj_prosjeke()

        # POVLAČENJE IMENA (Jelena/Dragana)
        k1_ime = df_m_t[df_m_t['Dan'].str.contains('Kuvar 1', na=False)]['Jelo'].values[0] if not df_m_t[df_m_t['Dan'].str.contains('Kuvar 1', na=False)].empty else "N/A"
        k2_ime = df_m_t[df_m_t['Dan'].str.contains('Kuvar 2', na=False)]['Jelo'].values[0] if not df_m_t[df_m_t['Dan'].str.contains('Kuvar 2', na=False)].empty else "N/A"

        with t_a1: # TAB KUHINJA
            st.subheader("Glavni kuvari ove sedmice:")
            c1, c2 = st.columns(2)
            c1.metric(f"👨‍🍳 {k1_ime}", tekstualne_zvijezde(p_kuvari.get(k1_ime, 0.0)))
            c2.metric(f"👨‍🍳 {k2_ime}", tekstualne_zvijezde(p_kuvari.get(k2_ime, 0.0)))
            st.divider()
            
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                d_sel = st.selectbox("Dan:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                st.table(prikaz)

        with t_a3: # TAB OCJENE
            st.subheader("⭐ Rang lista")
            col1, col2 = st.columns(2)
            col1.info(f"{k1_ime}: {p_kuvari.get(k1_ime, 0.0)} ⭐")
            col2.info(f"{k2_ime}: {p_kuvari.get(k2_ime, 0.0)} ⭐")
            st.divider()
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

        # ... (Ostatak koda za t_a2 i t_a4 ostaje identičan tvom originalnom)
