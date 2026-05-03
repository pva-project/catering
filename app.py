import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Admin", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"], header, footer {display: none !important;}
    .stAppDeployButton, [data-testid="stStatusWidget"], div[data-testid="stToolbar"] {display: none !important;}
    .block-container {padding-top: 1rem !important;}
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

def analiziraj_ocjene():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns:
        return {}, 0.0
    
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    prosjeci_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    ukupni_prosjek_kuvara = df_o['Numericka'].mean().round(2)
    
    return prosjeci_jela, ukupni_prosjek_kuvara

# --- 3. LOGIN SISTEM (Skraćeno za admina) ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    # ... (ovdje ide tvoj standardni login kod koji već imaš)
    # Radi testiranja, postavi session_state na True ručno ako treba
    st.title("🔐 Prijava")
    u = st.text_input("Korisnik")
    p = st.text_input("Lozinka", type="password")
    if st.button("Prijava"):
        if u == "admin" and p == "admin123":
            st.session_state["logged_in"], st.session_state["user"] = True, "admin"
            st.rerun()
else:
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene", "🔄 Reset"])
        
        # --- TAB 1: KUHINJA (SA PROSJEKOM KUVARA) ---
        with t_a1:
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            prosjeci_jela, ocjena_kuvara = analiziraj_ocjene()
            
            # Prikaz kuvara i njegove ukupne ocjene
            kuvar = df_m_t[df_m_t['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar'].empty else "N/A"
            st.info(f"👨‍🍳 Glavni kuvar: **{kuvar}** | ⭐ Prosječna ocjena: **{ocjena_kuvara}**")
            
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                d_sel = st.selectbox("Izaberi dan:", dani_std)
                prikaz_df = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"]
                
                if not prikaz_df.empty:
                    for smjena in ["I", "II", "III"]:
                        smjena_data = prikaz_df[prikaz_df['Smjena'] == smjena]
                        if not smjena_data.empty:
                            with st.container(border=True):
                                st.markdown(f"### 🕒 SMJENA {smjena}")
                                for jelo, jelo_data in smjena_data.groupby("Jelo"):
                                    # Rang jela
                                    rang = prosjeci_jela.get(jelo, "Nema ocjena")
                                    st.markdown(f"""
                                        <div style="background-color:#1E1E1E; padding:8px; border-radius:5px; margin-top:10px;">
                                            <span style="font-weight:bold; color:#FF4B4B; font-size:1.1rem;">{jelo}</span>
                                            <span style="color:#FFAA00; font-size:0.9rem; margin-left:10px;">⭐ Rang: {rang}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    
                                    for _, row in jelo_data.iterrows():
                                        st.markdown(f'<div style="display:flex; justify-content:space-between; padding:5px 10px; border-bottom:1px solid #333;"><div>🏢 {row["Firma"]}</div><div style="font-weight:bold;">{int(row["Kolicina"])} kom</div></div>', unsafe_allow_html=True)
                                    
                                    st.markdown(f'<div style="text-align:right; padding:5px; font-weight:bold; color:#00FF00;">UKUPNO: {int(jelo_data["Kolicina"].sum())}</div>', unsafe_allow_html=True)
                else: st.warning("Nema narudžbi.")

        # --- TAB 2: IZMJENA (Vrati i unos za kuvara) ---
        with t_a2:
            st.subheader("Uređivanje Menija")
            od_m = st.radio("Meni:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"f_{od_m}"):
                novi = []
                for meta in ["Sedmica", "Rok", "Kuvar"]:
                    v = df_m[df_m['Dan'] == meta]['Jelo'].values[0] if not df_m[df_m['Dan'] == meta].empty else ""
                    nv = st.text_input(f"{meta}:", value=v)
                    novi.append({"Dan": meta, "Jelo": nv})
                st.divider()
                for d in dani_std:
                    st.write(f"**{d}**")
                    jela = df_m[df_m['Dan'] == d]['Jelo'].tolist()
                    for i in range(3):
                        p = jela[i] if i < len(jela) else ""
                        n_j = st.text_input(f"{d} - {i+1}", value=p, key=f"{d}_{i}_{od_m}")
                        if n_j.strip(): novi.append({"Dan": d, "Jelo": n_j.strip()})
                if st.form_submit_button("💾 Sačuvaj"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi))
                    st.success("Sačuvano!"); time.sleep(1); st.rerun()

        # --- TAB 3: OCJENE (Tabela sa svim detaljima) ---
        with t_a3:
            st.subheader("⭐ Sve ocjene klijenata")
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

        # --- TAB 4: RESET ---
        with t_a4:
            if st.button("🚀 ROTIRAJ SEDMICU"):
                # Kod za prebacivanje Naredne u Trenutnu
                df_next = ucitaj_sheet("Meni_Naredni")
                if not df_next.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                    st.success("Meni rotiran!")
                    time.sleep(1); st.rerun()
