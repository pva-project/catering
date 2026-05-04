import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. STILIZACIJA ---
st.set_page_config(page_title="Catering Management", layout="centered")
st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important;}
    .info-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }
    .info-card { flex: 1; padding: 15px; border-radius: 10px; text-align: center; color: white; font-weight: bold; font-size: 0.9rem; }
    .blue-card { background-color: #1e3a5f; border: 1px solid #3b82f6; }
    .yellow-card { background-color: #3e3e10; border: 1px solid #ca8a04; }
    .green-card { background-color: #143e2a; border: 1px solid #16a34a; }
    .smjena-header { background-color: #333; padding: 10px; border-radius: 5px; color: white; font-weight: bold; margin-top: 20px; }
    .jelo-red { background-color: #1E1E1E; padding: 8px; border-radius: 5px; margin-top: 10px; font-weight: bold; color: #FF4B4B; }
    .ukupno-zeleno { text-align: right; padding: 5px; font-weight: bold; color: #00FF00; font-size: 1.1rem; border-top: 1px dashed #444; }
    </style>
""", unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. POMOĆNE FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        return conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    return df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict(), df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict()

# --- 4. PRIJAVA ---
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
    # --- ADMIN ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel")
        t1, t2, t3 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene"])
        with t1:
            df_nar = ucitaj_sheet("Sheet1")
            dan_izbor = st.selectbox("Dan:", dani_std)
            prikaz = df_nar[df_nar['Dan'] == f"Ova-{dan_izbor}"] if not df_nar.empty else pd.DataFrame()
            for smj in ["I", "II", "III"]:
                s_data = prikaz[prikaz['Smjena'] == smj]
                if not s_data.empty:
                    st.markdown(f'<div class="smjena-header">🕒 SMJENA {smj}</div>', unsafe_allow_html=True)
                    for jelo, j_data in s_data.groupby("Jelo"):
                        st.markdown(f'<div class="jelo-red">{jelo}</div>', unsafe_allow_html=True)
                        for _, r in j_data.iterrows():
                            st.write(f"🏢 {r['Firma']}: {int(r['Kolicina'])} kom")
                        st.markdown(f'<div class="ukupno-zeleno">UKUPNO: {int(j_data["Kolicina"].sum())}</div>', unsafe_allow_html=True)

    # --- KLIJENT ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_o, t_n, t_ocj = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna", "⭐ Ocijeni"])
        pj, _ = izracunaj_prosjeke()

        def klijent_prikaz(sh_nm, prefix):
            df_m = ucitaj_sheet(sh_nm)
            df_sve = ucitaj_sheet("Sheet1")
            
            # Header kartice
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Sedmica'].empty else "N/A"
            r = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Rok'].empty else "N/A"
            k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Kuvar'].empty else "N/A"
            
            st.markdown(f"""<div class="info-container">
                <div class="info-card blue-card">📅 Period<br>{s}</div>
                <div class="info-card yellow-card">⏰ Rok<br>{r}</div>
                <div class="info-card green-card">👨‍🍳 Kuvar<br>{k}</div>
            </div>""", unsafe_allow_html=True)

            with st.form(f"f_{prefix}"):
                novi_unosi = []
                for d in dani_std:
                    with st.container(border=True):
                        st.markdown(f"### 📅 {d}")
                        jela = df_m[df_m['Dan'] == d]['Jelo'].tolist() if not df_m.empty else []
                        for j in jela:
                            st.markdown(f"**{j}** {f'(⭐ {pj.get(j, bytes)})' if pj.get(j) else ''}")
                            c1, c2, c3 = st.columns(3)
                            
                            # POPRAVLJENO: Traženje starih vrijednosti
                            def get_old(smjena_ime):
                                if df_sve.empty: return 0
                                cond = (df_sve['Firma'] == st.session_state['user']) & \
                                       (df_sve['Dan'] == f"{prefix}-{d}") & \
                                       (df_sve['Jelo'] == j) & \
                                       (df_sve['Smjena'] == smjena_ime)
                                rez = df_sve[cond]['Kolicina'].values
                                return int(rez[0]) if len(rez) > 0 else 0

                            k1 = c1.number_input("I Smj", 0, 100, value=get_old("I"), key=f"{prefix}{d}{j}1")
                            k2 = c2.number_input("II Smj", 0, 100, value=get_old("II"), key=f"{prefix}{d}{j}2")
                            k3 = c3.number_input("III Smj", 0, 100, value=get_old("III"), key=f"{prefix}{d}{j}3")
                            
                            for v, sn in zip([k1, k2, k3], ["I", "II", "III"]):
                                if v > 0: novi_unosi.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{d}", "Jelo": j, "Kolicina": v, "Smjena": sn})
                
                if st.form_submit_button("💾 SAČUVAJ NARUDŽBU", use_container_width=True):
                    # Brišemo stare narudžbe za tu firmu i tu sedmicu i pišemo nove
                    if not df_sve.empty:
                        df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))]
                    else:
                        df_ostali = pd.DataFrame()
                    finalni_df = pd.concat([df_ostali, pd.DataFrame(novi_unosi)], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=finalni_df)
                    st.success("Narudžba sačuvana!"); time.sleep(1); st.rerun()

        with t_o: klijent_prikaz("Meni_Trenutni", "Ova")
        with t_n: klijent_prikaz("Meni_Naredni", "Naredna")
