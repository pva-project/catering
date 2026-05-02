import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Management", layout="centered")

# ✅ MINIMALNI CSS (NE LOMI LOGIN)
st.markdown("""
<style>
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. KORISNICI ---
users = {
    "admin": "admin123",
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# --- 3. FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        df = df.dropna(how='all')
        if "Dan" not in df.columns or "Jelo" not in df.columns:
            return pd.DataFrame(columns=["Dan", "Jelo"])
        return df
    except: 
        return pd.DataFrame(columns=["Dan", "Jelo"])

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: 
        return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    p_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    p_kuvari = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return p_jela, p_kuvari

# --- 4. LOGIN ---
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
    st.sidebar.write(f"Korisnik: **{st.session_state['user']}**")
    if st.sidebar.button("Odjavi se", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene & Kuvari", "🔄 Reset"])
        
        # ✅ KUHINJA (SIGURNA)
        with t_a1:
            st.subheader("📺 Kuhinja")

            df_nar = ucitaj_sheet("Sheet1")

            if not df_nar.empty and "Dan" in df_nar.columns:
                d_sel = st.selectbox("Dan za kuhanje:", dani_std)

                df_dan = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"]

                if not df_dan.empty:
                    for jelo in df_dan['Jelo'].unique():
                        df_j = df_dan[df_dan['Jelo'] == jelo]

                        i = df_j[df_j['Smjena'] == "I"]['Kolicina'].sum()
                        ii = df_j[df_j['Smjena'] == "II"]['Kolicina'].sum()
                        iii = df_j[df_j['Smjena'] == "III"]['Kolicina'].sum()

                        ukupno = i + ii + iii

                        st.markdown(f"""
                        <div style="background:#1e1e1e;padding:15px;border-radius:10px;margin-bottom:10px">
                        <b>{jelo}</b><br>
                        I: {i} | II: {ii} | III: {iii}<br>
                        <b>UKUPNO: {ukupno}</b>
                        </div>
                        """, unsafe_allow_html=True)

                else:
                    st.info("Nema narudžbi za ovaj dan.")
            else:
                st.info("Nema podataka.")

        # --- OSTALO OSTAVLJENO ISTO ---
        with t_a2:
            st.subheader("Izmijeni jela, rokove i kuvare")
            odabir_m = st.radio("Koji meni mijenjaš?", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(odabir_m)
            
            v_sed = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Sedmica'].empty else ""
            v_rok = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Rok'].empty else ""
            v_kuv = df_m[df_m['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Kuvar'].empty else ""

            with st.form(f"form_admin_{odabir_m}"):
                c1, c2, c3 = st.columns(3)
                n_sed = c1.text_input("📅 Period:", value=v_sed)
                n_rok = c2.text_input("⏰ Rok:", value=v_rok)
                n_kuv = c3.text_input("👨‍🍳 Glavni kuvar:", value=v_kuv)
                
                nova_lista = [{"Dan": "Sedmica", "Jelo": n_sed}, {"Dan": "Rok", "Jelo": n_rok}, {"Dan": "Kuvar", "Jelo": n_kuv}]
                for dan in dani_std:
                    st.write(f"**{dan}**")
                    postojeca = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    j1 = st.text_input(f"Jelo 1", value=postojeca[0] if len(postojeca) > 0 else "", key=f"{dan}_1")
                    j2 = st.text_input(f"Jelo 2", value=postojeca[1] if len(postojeca) > 1 else "", key=f"{dan}_2")
                    j3 = st.text_input(f"Jelo 3", value=postojeca[2] if len(postojeca) > 2 else "", key=f"{dan}_3")
                    for j in [j1, j2, j3]:
                        if j.strip(): 
                            nova_lista.append({"Dan": dan, "Jelo": j.strip()})
                
                if st.form_submit_button("💾 SAČUVAJ SVE"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=odabir_m, data=pd.DataFrame(nova_lista))
                    st.success("Sačuvano!")
                    time.sleep(1)
                    st.rerun()