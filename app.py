import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I UKLANJANJE SVIH STREAMLIT IKONA ---
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
    .block-container {padding-top: 1rem !important; padding-bottom: 0rem !important;}
    img[src*="streamlit_logo"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    </style>
"""
st.markdown(ultimate_hide_style, unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: 
        return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    p_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    p_kuvari = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return p_jela, p_kuvari

# --- 4. LOGIN ---
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
        
        with t_a4:
            st.subheader("🔄 Rotacija Sedmica")
            if datetime.now().weekday() == 6:
                st.warning("🔔 Danas je nedjelja. Vrijeme za prebacivanje narudžbi!")
            
            if st.button("🚀 IZVRŠI ROTACIJU (Prebaci Narednu u Trenutnu)", use_container_width=True):
                # 1. Rotacija Menija
                df_next_menu = ucitaj_sheet("Meni_Naredni")
                if not df_next_menu.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next_menu)
                
                # 2. Rotacija Narudžbi (Sheet1)
                df_sve = ucitaj_sheet("Sheet1")
                if not df_sve.empty:
                    # Uzmi samo one koje su bile "Naredna" i pretvori ih u "Ova"
                    df_naredna = df_sve[df_sve['Dan'].str.startswith("Naredna")].copy()
                    df_naredna['Dan'] = df_naredna['Dan'].str.replace("Naredna", "Ova")
                    
                    # Sačuvaj te narudžbe kao nove "Trenutne", a Sheet1 isprazni od starih
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=df_naredna)
                    st.success("Gotovo! Narudžbe iz 'Naredne' su sada u 'Ovoj' sedmici.")
                    time.sleep(2)
                    st.rerun()

        with t_a1:
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                d_sel = st.selectbox("Izaberi dan:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                st.table(prikaz)

        with t_a2:
            odabir_m = st.radio("Meni:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(odabir_m)
            with st.form(f"f_admin_{odabir_m}"):
                # Ovdje ide tvoj standardni kod za editovanje menija (kao u prethodnim verzijama)
                st.write("Uredi jela u tabeli ispod pa klikni Sačuvaj")
                # ... (skraćeno zbog preglednosti, ali ostaje isto)
                st.form_submit_button("Sačuvaj")

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_t, t_n = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica"])

        def prikazi_formu(sheet_name, prefix, zakljucaj):
            df_m = ucitaj_sheet(sheet_name)
            df_sve = ucitaj_sheet("Sheet1")
            with st.form(f"f_{prefix}"):
                unose = []
                for dan in dani_std:
                    idx = dani_std.index(dan)
                    onemoguci = (zakljucaj and danasnji_dan_index >= idx)
                    st.markdown(f"### {dan}")
                    jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    for j in jela:
                        col1, col2, col3 = st.columns(3)
                        # Dohvaćanje postojećih vrijednosti
                        mask = (df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{prefix}-{dan}") & (df_sve['Jelo']==j)
                        v1 = df_sve[mask & (df_sve['Smjena']=="I")]['Kolicina'].sum()
                        v2 = df_sve[mask & (df_sve['Smjena']=="II")]['Kolicina'].sum()
                        v3 = df_sve[mask & (df_sve['Smjena']=="III")]['Kolicina'].sum()
                        
                        k1 = col1.number_input(f"{j} (I)", 0, 100, int(v1), key=f"{prefix}_{dan}_{j}_1", disabled=onemoguci)
                        k2 = col2.number_input(f"II", 0, 100, int(v2), key=f"{prefix}_{dan}_{j}_2", disabled=onemoguci)
                        k3 = col3.number_input(f"III", 0, 100, int(v3), key=f"{prefix}_{dan}_{j}_3", disabled=onemoguci)
                        
                        for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                            if k > 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(k), "Smjena": s})
                
                if st.form_submit_button("Sačuvaj narudžbu"):
                    # Logika za čuvanje: Brišemo samo stare narudžbe tog korisnika za taj prefix (Ova/Naredna)
                    df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))]
                    novo = pd.concat([df_ostali, pd.DataFrame(unose)], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=novo)
                    st.success("Spremljeno!"); st.rerun()

        with t_t: prikazi_formu("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_formu("Meni_Naredni", "Naredna", False)
