import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I STIL ---
st.set_page_config(page_title="Catering App", layout="centered")

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
    .ukupno-zeleno { text-align: right; padding: 5px; font-weight: bold; color: #00FF00; font-size: 1.1rem; border-top: 1px dashed #444; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    pj = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    pk = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return pj, pk

# --- 4. LOGIN ---
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
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel")
        t1, t2, t3, t4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t1: # KUHINJA SA ZBIROM (Zeleno)
            st.subheader("📊 Zbir narudžbi")
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                dan_izbor = st.selectbox("Dan:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{dan_izbor}"]
                if not prikaz.empty:
                    for smj in ["I", "II", "III"]:
                        s_data = prikaz[prikaz['Smjena'] == smj]
                        if not s_data.empty:
                            st.markdown(f'<div class="smjena-header">🕒 SMJENA {smj}</div>', unsafe_allow_html=True)
                            for jelo, j_data in s_data.groupby("Jelo"):
                                st.markdown(f'<div class="jelo-red">{jelo}</div>', unsafe_allow_html=True)
                                for _, r in j_data.iterrows():
                                    st.markdown(f'<div style="display:flex; justify-content:space-between; padding:2px 10px;"><div>🏢 {r["Firma"]}</div><div>{int(r["Kolicina"])} kom</div></div>', unsafe_allow_html=True)
                                ukupno = int(j_data['Kolicina'].sum())
                                st.markdown(f'<div class="ukupno-zeleno">UKUPNO: {ukupno} kom</div>', unsafe_allow_html=True)
                else: st.info("Nema narudžbi.")

        with t3: # OCJENE (Sada popravljeno)
            st.subheader("⭐ Sve ocjene i recenzije")
            df_o = ucitaj_sheet("Ocjene")
            if not df_o.empty:
                # Metrike za kuvare
                _, pk = izracunaj_prosjeke()
                if pk:
                    cols = st.columns(len(pk))
                    for i, (kuvar, ocj) in enumerate(pk.items()):
                        cols[i].metric(f"👨‍🍳 {kuvar}", f"{ocj} ⭐")
                st.divider()
                # Tabela sa svim ocjenama
                st.dataframe(df_o, use_container_width=True, hide_index=True)
            else:
                st.info("Tabela ocjena je trenutno prazna.")

        # --- Ostatak Admin funkcija (Meni i Reset) ---
        with t2:
            od_m = st.radio("Uredi:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"f_m_{od_m}"):
                if not df_m.empty:
                    v_s = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Sedmica'].empty else ""
                    n_s = st.text_input("Period:", value=v_s)
                    novi = [{"Dan": "Sedmica", "Jelo": n_s}]
                    for d in dani_std:
                        st.markdown(f"**{d}**")
                        postojeća = df_m[df_m['Dan'] == d]['Jelo'].tolist()
                        for i in range(3):
                            v = postojeća[i] if i < len(postojeća) else ""
                            nj = st.text_input(f"{d} - {i+1}", value=v, key=f"{od_m}{d}{i}")
                            if nj: novi.append({"Dan": d, "Jelo": nj})
                    if st.form_submit_button("Sačuvaj"):
                        conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi))
                        st.success("Sačuvano!"); st.rerun()

        with t4:
            if st.button("🚀 ROTIRAJ SEDMICE"):
                df_n = ucitaj_sheet("Meni_Naredni")
                if not df_n.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_n)
                    st.success("Meni rotiran!"); st.rerun()

    else: # KORISNIČKI PANEL
        st.title(f"🍴 {st.session_state['user']}")
        t_o, t_n, t_ocj = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna", "⭐ Ocijeni"])
        pj, _ = izracunaj_prosjeke()

        def prikazi_klijent(sh, prfx):
            df_m = ucitaj_sheet(sh)
            df_sve = ucitaj_sheet("Sheet1")
            # Info kartice
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Sedmica'].empty else "N/A"
            st.markdown(f'<div class="info-container"><div class="info-card blue-card">📅 Period: {s}</div></div>', unsafe_allow_html=True)
            
            with st.form(f"f_{prfx}"):
                unosi = []
                for d in dani_std:
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {d}")
                        jela = df_m[df_m['Dan'] == d]['Jelo'].tolist() if not df_m.empty else []
                        for j in jela:
                            st.markdown(f"**{j}** {f'(⭐ {pj.get(j, bytes)})' if pj.get(j) else ''}")
                            c1, c2, c3 = st.columns(3)
                            k1 = c1.number_input("I", 0, 100, key=f"{prfx}{d}{j}1")
                            k2 = c2.number_input("II", 0, 100, key=f"{prfx}{d}{j}2")
                            k3 = c3.number_input("III", 0, 100, key=f"{prfx}{d}{j}3")
                            for v, s_n in zip([k1, k2, k3], ["I", "II", "III"]):
                                if v > 0: unosi.append({"Firma": st.session_state['user'], "Dan": f"{prfx}-{d}", "Jelo": j, "Kolicina": v, "Smjena": s_n})
                if st.form_submit_button("SAČUVAJ"):
                    df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prfx)))] if not df_sve.empty else pd.DataFrame()
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_ostali, pd.DataFrame(unosi)]))
                    st.success("Spremljeno!"); st.rerun()

        with t_o: prikazi_klijent("Meni_Trenutni", "Ova")
        with t_n: prikazi_klijent("Meni_Naredni", "Naredna")
        with t_ocj:
            with st.form("f_ocj"):
                j_o = st.text_input("Jelo koje ocjenjujete:")
                oc = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"])
                km = st.text_area("Komentar:")
                if st.form_submit_button("Pošalji"):
                    df_o = ucitaj_sheet("Ocjene")
                    novi_red = pd.DataFrame([{"Firma": st.session_state['user'], "Jelo": j_o, "Ocjena": oc, "Komentar": km}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o, novi_red]))
                    st.success("Hvala!"); st.rerun()
