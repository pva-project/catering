import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. STILIZACIJA (Sve po tvom dizajnu) ---
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

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. POMOĆNE FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        return conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

# --- 4. LOGIN ---
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
        st.title("👨‍🍳 Admin Kontrola")
        t1, t2 = st.tabs(["📊 Kuhinja (Zbir)", "📝 Izmjena Menija"])
        
        with t1:
            df_nar = ucitaj_sheet("Sheet1")
            dan_izbor = st.selectbox("Izaberi dan:", dani_std)
            prikaz = df_nar[df_nar['Dan'] == f"Ova-{dan_izbor}"] if not df_nar.empty else pd.DataFrame()
            
            if not prikaz.empty:
                for smj in ["I", "II", "III"]:
                    s_data = prikaz[prikaz['Smjena'] == smj]
                    if not s_data.empty:
                        st.markdown(f'<div class="smjena-header">🕒 SMJENA {smj}</div>', unsafe_allow_html=True)
                        for jelo, j_data in s_data.groupby("Jelo"):
                            st.markdown(f'<div class="jelo-red">{jelo}</div>', unsafe_allow_html=True)
                            for _, r in j_data.iterrows():
                                st.write(f"🏢 {r['Firma']}: {int(r['Kolicina'])} kom")
                            ukupno = int(j_data["Kolicina"].sum())
                            st.markdown(f'<div class="ukupno-zeleno">UKUPNO {jelo}: {ukupno}</div>', unsafe_allow_html=True)
            else: st.info("Nema narudžbi za ovaj dan.")

    # --- KLIJENTSKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_o, t_n = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica"])

        def klijent_prikaz(sh_nm, prefix):
            df_m = ucitaj_sheet(sh_nm)
            df_sve = ucitaj_sheet("Sheet1")
            
            # Kartice (Period, Rok, Kuvar)
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Sedmica'].empty else "/"
            r = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Rok'].empty else "/"
            k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Kuvar'].empty else "/"
            
            st.markdown(f"""<div class="info-container">
                <div class="info-card blue-card">📅 Period<br>{s}</div>
                <div class="info-card yellow-card">⏰ Rok<br>{r}</div>
                <div class="info-card green-card">👨‍🍳 Kuvar<br>{k}</div>
            </div>""", unsafe_allow_html=True)

            with st.form(f"form_{prefix}"):
                novi_unosi = []
                for d in dani_std:
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {d}")
                        jela = df_m[df_m['Dan'] == d]['Jelo'].tolist() if not df_m.empty else []
                        for j in jela:
                            st.markdown(f"**{j}**")
                            c1, c2, c3 = st.columns(3)
                            
                            # KLJUČNI DIO: Pronalaženje starih vrijednosti da ne budu 0
                            def get_old_val(smjena_ime):
                                if df_sve.empty: return 0
                                match = df_sve[
                                    (df_sve['Firma'] == st.session_state['user']) & 
                                    (df_sve['Dan'] == f"{prefix}-{d}") & 
                                    (df_sve['Jelo'] == j) & 
                                    (df_sve['Smjena'] == smjena_ime)
                                ]
                                return int(match['Kolicina'].iloc[0]) if not match.empty else 0

                            v1 = c1.number_input("I Smj", 0, 100, value=get_old_val("I"), key=f"k_{prefix}{d}{j}1")
                            v2 = c2.number_input("II Smj", 0, 100, value=get_old_val("II"), key=f"k_{prefix}{d}{j}2")
                            v3 = c3.number_input("III Smj", 0, 100, value=get_old_val("III"), key=f"k_{prefix}{d}{j}3")
                            
                            for val, sn in zip([v1, v2, v3], ["I", "II", "III"]):
                                if val > 0: novi_unosi.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{d}", "Jelo": j, "Kolicina": val, "Smjena": sn})
                
                if st.form_submit_button("💾 SAČUVAJ NARUDŽBU", use_container_width=True):
                    # Filter: zadrži sve OSIM trenutnog klijenta za ovu sedmicu
                    df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))] if not df_sve.empty else pd.DataFrame()
                    final = pd.concat([df_ostali, pd.DataFrame(novi_unosi)], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final)
                    st.success("Narudžba snimljena!"); time.sleep(1); st.rerun()

        with t_o: klijent_prikaz("Meni_Trenutni", "Ova")
        with t_n: klijent_prikaz("Meni_Naredni", "Naredna")
