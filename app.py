import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. TOTALNO SKRIVANJE SVIH IKONA (FORK, GITHUB, KRUNICA) ---
st.set_page_config(page_title="Catering Management", layout="centered")

ultimate_hide_style = """
    <style>
    /* Sakrij gornju traku (Fork, GitHub, Menu) */
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    
    /* Sakrij donju traku (Made with Streamlit) i krunicu (Deploy) */
    footer {display: none !important; visibility: hidden !important;}
    [data-testid="stFooter"] {display: none !important;}
    .stAppDeployButton {display: none !important;}
    
    /* Sakrij sve ikonice u uglovima i toolbarove */
    [data-testid="stStatusWidget"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    button[title="View source on GitHub"] {display: none !important;}
    .st-emotion-cache-zq59db {display: none !important;}
    
    /* Smanji prazan prostor na vrhu */
    .block-container {padding-top: 1rem !important; padding-bottom: 0rem !important;}
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
    return p_jela

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
        
        with t_a1:
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                d_sel = st.selectbox("Izaberi dan za kuhinju:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                st.table(prikaz)
            else: st.info("Nema narudžbi.")

        with t_a2:
            st.subheader("Uređivanje Menija")
            odabir_m = st.radio("Koji meni mijenjaš?", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(odabir_m)
            
            with st.form(f"form_admin_{odabir_m}"):
                nova_lista = []
                # Specijalna polja (Sedmica, Rok, Kuvar)
                for spec in ["Sedmica", "Rok", "Kuvar"]:
                    val = df_m[df_m['Dan'] == spec]['Jelo'].values[0] if not df_m[df_m['Dan'] == spec].empty else ""
                    n_val = st.text_input(f"{spec}:", value=val)
                    nova_lista.append({"Dan": spec, "Jelo": n_val})
                
                st.divider()
                for dan in dani_std:
                    st.write(f"**{dan}**")
                    postojeca = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    j1 = st.text_input(f"Jelo 1 ({dan})", value=postojeca[0] if len(postojeca) > 0 else "", key=f"{dan}_1")
                    j2 = st.text_input(f"Jelo 2 ({dan})", value=postojeca[1] if len(postojeca) > 1 else "", key=f"{dan}_2")
                    j3 = st.text_input(f"Jelo 3 ({dan})", value=postojeca[2] if len(postojeca) > 2 else "", key=f"{dan}_3")
                    for j in [j1, j2, j3]:
                        if j.strip(): nova_lista.append({"Dan": dan, "Jelo": j.strip()})
                
                if st.form_submit_button("💾 SAČUVAJ IZMJENE"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=odabir_m, data=pd.DataFrame(nova_lista))
                    st.success("Meni uspješno ažuriran!"); time.sleep(1); st.rerun()

        with t_a3:
            st.subheader("⭐ Ocjene korisnika")
            df_o = ucitaj_sheet("Ocjene")
            st.dataframe(df_o, use_container_width=True, hide_index=True)

        with t_a4:
            st.subheader("🔄 Rotacija Sedmica")
            st.warning("Ovo prebacuje 'Narednu' u 'Trenutnu' i čuva narudžbe klijenata!")
            if st.button("🚀 IZVRŠI ROTACIJU"):
                df_next_menu = ucitaj_sheet("Meni_Naredni")
                df_sve = ucitaj_sheet("Sheet1")
                if not df_next_menu.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next_menu)
                if not df_sve.empty:
                    df_naredna = df_sve[df_sve['Dan'].str.startswith("Naredna")].copy()
                    df_naredna['Dan'] = df_naredna['Dan'].str.replace("Naredna", "Ova")
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=df_naredna)
                st.success("Sistem rotiran!"); time.sleep(1); st.rerun()

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_t, t_n, t_h, t_o = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija", "⭐ Ocijeni"])
        p_jela = izracunaj_prosjeke()

        def prikazi_formu(sheet_name, prefix, zakljucaj):
            df_m = ucitaj_sheet(sheet_name)
            df_sve = ucitaj_sheet("Sheet1")
            
            with st.form(f"f_{prefix}"):
                unose = []
                for dan in dani_std:
                    idx = dani_std.index(dan)
                    # Otključaj sve ako je nedjelja, inače prati index
                    onemoguci = False if danasnji_dan_index == 6 else (zakljucaj and danasnji_dan_index >= idx)
                    
                    st.markdown(f"#### 📅 {dan} {'🔒' if onemoguci else '🔓'}")
                    jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    for j in jela:
                        prosjek = p_jela.get(j, "")
                        st.write(f"**{j}** {f'(⭐ {prosjek})' if prosjek else ''}")
                        col1, col2, col3 = st.columns(3)
                        mask = (df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{prefix}-{dan}") & (df_sve['Jelo']==j)
                        v1 = df_sve[mask & (df_sve['Smjena']=="I")]['Kolicina'].sum()
                        v2 = df_sve[mask & (df_sve['Smjena']=="II")]['Kolicina'].sum()
                        v3 = df_sve[mask & (df_sve['Smjena']=="III")]['Kolicina'].sum()
                        
                        k1 = col1.number_input(f"I Smj", 0, 100, int(v1), key=f"{prefix}_{dan}_{j}_1", disabled=onemoguci)
                        k2 = col2.number_input(f"II Smj", 0, 100, int(v2), key=f"{prefix}_{dan}_{j}_2", disabled=onemoguci)
                        k3 = col3.number_input(f"III Smj", 0, 100, int(v3), key=f"{prefix}_{dan}_{j}_3", disabled=onemoguci)
                        
                        for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                            if k > 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(k), "Smjena": s})
                
                if st.form_submit_button("Sačuvaj narudžbu", use_container_width=True):
                    df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))]
                    novo = pd.concat([df_ostali, pd.DataFrame(unose)], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=novo)
                    st.success("Spremljeno!"); st.rerun()

        with t_t: prikazi_formu("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_formu("Meni_Naredni", "Naredna", False)
        
        with t_h:
            st.subheader("📜 Istorija tvojih narudžbi")
            df_h = ucitaj_sheet("Sheet1")
            if not df_h.empty:
                moje = df_h[df_h['Firma'] == st.session_state['user']]
                st.dataframe(moje, use_container_width=True, hide_index=True)
            else: st.write("Nema podataka.")

        with t_o:
            st.subheader("⭐ Ocijeni jelo")
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            sva_j = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist()
            with st.form("forma_ocjena"):
                od_j = st.selectbox("Izaberi jelo:", sva_j)
                ocj = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                kom = st.text_area("Komentar:")
                if st.form_submit_button("Pošalji"):
                    df_o_p = ucitaj_sheet("Ocjene")
                    nova_o = pd.DataFrame([{"Firma": st.session_state['user'], "Jelo": od_j, "Ocjena": ocj, "Komentar": kom}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o_p, nova_o], ignore_index=True))
                    st.success("Hvala!"); time.sleep(1); st.rerun()
