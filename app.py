import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Management", layout="centered")

# Skrivanje Streamlit elemenata
st.markdown("""
    <style>
    [data-testid="stHeader"], header, footer {display: none !important;}
    .stAppDeployButton, [data-testid="stStatusWidget"], div[data-testid="stToolbar"] {display: none !important;}
    .block-container {padding-top: 1rem !important;}
    .star-ratings { color: #ccc; position: relative; display: inline-block; font-size: 20px; }
    .star-ratings-fill { color: #ffca08; padding: 0; position: absolute; z-index: 1; display: block; top: 0; left: 0; overflow: hidden; white-space: nowrap; }
    </style>
""", unsafe_allow_html=True)

# --- 2. POMOĆNE FUNKCIJE ---
def prikazi_zvjezdice(ocjena):
    procenat = (ocjena / 5) * 100
    return f"""
    <div style="display: inline-block; vertical-align: middle;">
        <span style="font-weight: bold; font-size: 1.1rem; margin-right: 8px;">{ocjena}</span>
        <div class="star-ratings">
            <div class="star-ratings-fill" style="width: {procenat}%;"><span>★★★★★</span></div>
            <div><span>★★★★★</span></div>
        </div>
    </div>
    """

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame()

def analiziraj_ocjene(k1_ime, k2_ime):
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns:
        return {}, 0.0, 0.0
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    prosjeci_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    
    # Računanje prosjeka po kuvarima
    k1_skor = 0.0
    k2_skor = 0.0
    if 'Kuvar' in df_o.columns:
        k1_skor = df_o[df_o['Kuvar'] == k1_ime]['Numericka'].mean()
        k2_skor = df_o[df_o['Kuvar'] == k2_ime]['Numericka'].mean()
    
    return prosjeci_jela, round(k1_skor if pd.notnull(k1_skor) else 0.0, 1), round(k2_skor if pd.notnull(k2_skor) else 0.0, 1)

# --- 3. LOGIN ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

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
    # --- 4. ADMIN I KLIJENT LOGIKA ---
    df_m_t = ucitaj_sheet("Meni_Trenutni")
    k1_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 1']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 1'].empty else "Kuvar 1"
    k2_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 2']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 2'].empty else "Kuvar 2"
    pros_jela, skor_k1, skor_k2 = analiziraj_ocjene(k1_ime, k2_ime)

    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t_a1:
            with st.container(border=True):
                c1, c2 = st.columns(2)
                c1.markdown(f"**{k1_ime}**\n{prikazi_zvjezdice(skor_k1)}", unsafe_allow_html=True)
                c2.markdown(f"**{k2_ime}**\n{prikazi_zvjezdice(skor_k2)}", unsafe_allow_html=True)
            
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                dan_sel = st.selectbox("Dan:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"]
                for smjena in ["I", "II", "III"]:
                    sm_data = prikaz[prikaz['Smjena'] == smjena]
                    if not sm_data.empty:
                        with st.container(border=True):
                            st.subheader(f"Smjena {smjena}")
                            for jelo, j_data in sm_data.groupby("Jelo"):
                                r = pros_jela.get(jelo, "0.0")
                                st.markdown(f"<div style='background:#1E1E1E;padding:8px;border-radius:5px;'><b>{jelo}</b> <span style='color:orange;'>⭐ {r}</span></div>", unsafe_allow_html=True)
                                for _, row in j_data.iterrows():
                                    st.write(f"🏢 {row['Firma']}: {int(row['Kolicina'])} kom")
                                st.success(f"Ukupno: {int(j_data['Kolicina'].sum())}")

        with t_a3:
            st.markdown(f"### Rejting timova\n{k1_ime}: {skor_k1} | {k2_ime}: {skor_k2}")
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)
            
        # ... (Ostali tabovi t_a2 i t_a4 ostaju isti kao prije)

    else:
        st.title(f"🍴 {st.session_state['user']}")
        t1, t2, t3 = st.tabs(["🍱 Narudžba", "📜 Istorija", "⭐ Ocijeni"])
        
        with t3:
            st.subheader("Ocijeni današnji obrok")
            sva_jela = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist()
            with st.form("f_ocena"):
                j_izbor = st.selectbox("Jelo:", sva_jela)
                k_izbor = st.radio("Koji kuvar je spremao?", [k1_ime, k2_ime], horizontal=True)
                ocj = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                kom = st.text_area("Komentar:")
                if st.form_submit_button("Pošalji"):
                    df_o_p = ucitaj_sheet("Ocjene")
                    nova = pd.DataFrame([{"Firma": st.session_state['user'], "Jelo": j_izbor, "Kuvar": k_izbor, "Ocjena": ocj, "Komentar": kom}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.DataFrame(pd.concat([df_o_p, nova])))
                    st.success("Hvala!"); time.sleep(1); st.rerun()
