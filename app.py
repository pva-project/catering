import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I SKRIVANJE SVIH IKONA ---
st.set_page_config(page_title="Catering Management", layout="centered")

ultimate_hide_style = """
    <style>
    /* Sakrij gornji meni, krunicu i GitHub ikonice */
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    [data-testid="stFooter"] {display: none !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    
    /* Smanjenje margina za mobilne ekrane */
    .block-container {padding-top: 1rem !important; padding-bottom: 0rem !important;}
    
    /* Stil za kartice u Kuhinji */
    .kuhinja-firma-container {
        border: 1px solid #444;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #0E1117;
    }
    </style>
"""
st.markdown(ultimate_hide_style, unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday() # 0=Pon, 6=Ned
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
        return df.dropna(how='all')
    except: return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    return df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()

# --- 4. LOGIN SISTEM ---
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
            st.subheader("👨‍🍳 Današnji nalozi")
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                d_sel = st.selectbox("Izaberi dan:", dani_std)
                prikaz_df = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"]
                if not prikaz_df.empty:
                    for firma, data in prikaz_df.groupby("Firma"):
                        with st.container(border=True):
                            st.markdown(f"#### 🏢 {firma}")
                            st.markdown('<div style="display: flex; justify-content: space-between; border-bottom: 1px solid #444; color: #888; font-size: 0.8rem;"><div>JELO / SMJENA</div><div>KOLIČINA</div></div>', unsafe_allow_html=True)
                            for _, row in data.iterrows():
                                st.markdown(f"""
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                                        <div>
                                            <div style="font-weight: bold; font-size: 1.1rem;">{row['Jelo']}</div>
                                            <div style="font-size: 0.85rem; color: #FFAA00;">Smjena: {row['Smjena']}</div>
                                        </div>
                                        <div style="background-color: #FF4B4B; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 1.2rem;">
                                            {int(row['Kolicina'])}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                else: st.info(f"Nema narudžbi za {d_sel}.")
            else: st.info("Baza narudžbi je prazna.")

        with t_a2:
            st.subheader("Uređivanje Menija")
            od_m = st.radio("Meni:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"form_{od_m}"):
                novi_podaci = []
                # Meta podaci
                for meta in ["Sedmica", "Rok", "Kuvar"]:
                    v = df_m[df_m['Dan'] == meta]['Jelo'].values[0] if not df_m[df_m['Dan'] == meta].empty else ""
                    nv = st.text_input(f"{meta}:", value=v)
                    novi_podaci.append({"Dan": meta, "Jelo": nv})
                st.divider()
                # Dani
                for dan in dani_std:
                    st.write(f"**{dan}**")
                    jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    for i in range(3):
                        postojece = jela[i] if i < len(jela) else ""
                        n_j = st.text_input(f"{dan} - Jelo {i+1}", value=postojece, key=f"{dan}_{i}_{od_m}")
                        if n_j.strip(): novi_podaci.append({"Dan": dan, "Jelo": n_j.strip()})
                if st.form_submit_button("💾 SAČUVAJ"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi_podaci))
                    st.success("Meni sačuvan!"); time.sleep(1); st.rerun()

        with t_a4:
            st.subheader("🔄 Rotacija Sedmica")
            if st.button("🚀 IZVRŠI ROTACIJU (Prebaci Narednu u Trenutnu)"):
                df_next = ucitaj_sheet("Meni_Naredni")
                df_sve = ucitaj_sheet("Sheet1")
                if not df_next.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                if not df_sve.empty:
                    # Filter narudžbi: briši stare "Ova", a "Naredna" postaju "Ova"
                    df_naredna = df_sve[df_sve['Dan'].str.startswith("Naredna")].copy()
                    df_naredna['Dan'] = df_naredna['Dan'].str.replace("Naredna", "Ova")
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=df_naredna)
                st.success("Sistem rotiran!"); time.sleep(1); st.rerun()

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_t, t_n, t_h, t_o = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija", "⭐ Ocijeni"])
        prosjeci = izracunaj_prosjeke()

        def prikazi_klijent_formu(sh_name, prefix, zakljucaj):
            df_m = ucitaj_sheet(sh_name)
            df_sve = ucitaj_sheet("Sheet1")
            with st.form(f"f_{prefix}"):
                unosi = []
                for dan in dani_std:
                    idx = dani_std.index(dan)
                    # Zaključavanje: ako je nedjelja (6), sve je otključano za 'Ova'
                    onemoguci = False if danasnji_dan_index == 6 else (zakljucaj and danasnji_dan_index >= idx)
                    st.markdown(f"#### 📅 {dan} {'🔒' if onemoguci else '🔓'}")
                    jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    for j in jela:
                        p = prosjeci.get(j, "")
                        st.write(f"**{j}** {f'(⭐ {p})' if p else ''}")
                        col1, col2, col3 = st.columns(3)
                        mask = (df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{prefix}-{dan}") & (df_sve['Jelo']==j)
                        v1 = df_sve[mask & (df_sve['Smjena']=="I")]['Kolicina'].sum()
                        v2 = df_sve[mask & (df_sve['Smjena']=="II")]['Kolicina'].sum()
                        v3 = df_sve[mask & (df_sve['Smjena']=="III")]['Kolicina'].sum()
                        k1 = col1.number_input("I Smj", 0, 100, int(v1), key=f"{prefix}_{dan}_{j}_1", disabled=onemoguci)
                        k2 = col2.number_input("II Smj", 0, 100, int(v2), key=f"{prefix}_{dan}_{j}_2", disabled=onemoguci)
                        k3 = col3.number_input("III Smj", 0, 100, int(v3), key=f"{prefix}_{dan}_{j}_3", disabled=onemoguci)
                        for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                            if k > 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(k), "Smjena": s})
                if st.form_submit_button("Sačuvaj narudžbu", use_container_width=True):
                    df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))]
                    final = pd.concat([df_ostali, pd.DataFrame(unose)], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final)
                    st.success("Spremljeno!"); st.rerun()

        with t_t: prikazi_klijent_formu("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_klijent_formu("Meni_Naredni", "Naredna", False)
        with t_h:
            st.subheader("📜 Tvoje narudžbe")
            df_hist = ucitaj_sheet("Sheet1")
            if not df_hist.empty:
                st.dataframe(df_hist[df_hist['Firma'] == st.session_state['user']], use_container_width=True, hide_index=True)
        with t_o:
            st.subheader("⭐ Ocijeni jelo")
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            sva_jela = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist()
            with st.form("f_ocjena"):
                j_sel = st.selectbox("Jelo:", sva_jela)
                ocj = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                kom = st.text_area("Komentar:")
                if st.form_submit_button("Pošalji"):
                    df_o_p = ucitaj_sheet("Ocjene")
                    nova = pd.DataFrame([{"Firma": st.session_state['user'], "Jelo": j_sel, "Ocjena": ocj, "Komentar": kom}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o_p, nova], ignore_index=True))
                    st.success("Hvala!"); time.sleep(1); st.rerun()
