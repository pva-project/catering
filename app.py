import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I DIZAJN ---
st.set_page_config(page_title="Catering Management", layout="centered")

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

def analiziraj_ocjene(ime_kuvara1, ime_kuvara2):
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns:
        return {}, 0.0, 0.0
    
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    prosjeci_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    
    # Računanje prosjeka za svakog kuvara na osnovu kolone 'Kuvar' u tabeli Ocjene
    # Ako te kolone nema, prosjek će biti 0.0 dok se ne unesu prve ocjene sa imenom
    k1_skor = 0.0
    k2_skor = 0.0
    
    if 'Kuvar' in df_o.columns:
        k1_skor = df_o[df_o['Kuvar'] == ime_kuvara1]['Numericka'].mean()
        k2_skor = df_o[df_o['Kuvar'] == ime_kuvara2]['Numericka'].mean()
    
    return prosjeci_jela, round(k1_skor if pd.notnull(k1_skor) else 0.0, 1), round(k2_skor if pd.notnull(k2_skor) else 0.0, 1)

# --- 3. LOGIN SISTEM ---
users = {
    "admin": "admin123", 
    "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", 
    "Esintec": "esintec321", "ActivBH": "activbh321"
}

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
    # --- 4. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene", "🔄 Reset"])
        
        df_m_t = ucitaj_sheet("Meni_Trenutni")
        # Dobavljanje imena kuvara iz baze
        k1_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 1']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 1'].empty else "N/A"
        k2_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 2']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 2'].empty else "N/A"
        
        pros_jela, skor_k1, skor_k2 = analiziraj_ocjene(k1_ime, k2_ime)

        with t_a1:
            # Prikaz kuvara sa zvjezdicama na vrhu kuhinje
            with st.container(border=True):
                col_k1, col_k2 = st.columns(2)
                with col_k1:
                    st.markdown(f"**Glavni kuvar 1: {k1_ime}**")
                    st.markdown(prikazi_zvjezdice(skor_k1), unsafe_allow_html=True)
                with col_k2:
                    st.markdown(f"**Glavni kuvar 2: {k2_ime}**")
                    st.markdown(prikazi_zvjezdice(skor_k2), unsafe_allow_html=True)

            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                d_sel = st.selectbox("Izaberi dan:", dani_std)
                prikaz_df = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"]
                if not prikaz_df.empty:
                    for smjena in ["I", "II", "III"]:
                        sm_data = prikaz_df[prikaz_df['Smjena'] == smjena]
                        if not sm_data.empty:
                            with st.container(border=True):
                                st.markdown(f"### 🕒 SMJENA {smjena}")
                                for jelo, jelo_data in sm_data.groupby("Jelo"):
                                    # Rang jela (kao tekst kako si tražio)
                                    rang = pros_jela.get(jelo, "0.0")
                                    st.markdown(f"""
                                        <div style="background-color:#1E1E1E; padding:10px; border-radius:5px; margin-top:10px;">
                                            <span style="font-weight:bold; color:#FF4B4B; font-size:1.1rem;">{jelo}</span>
                                            <span style="color:#FFAA00; font-size:0.9rem; margin-left:10px;">⭐ {rang}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    for _, row in jelo_data.iterrows():
                                        st.markdown(f'<div style="display:flex; justify-content:space-between; padding:5px 10px; border-bottom:1px solid #333;"><div>🏢 {row["Firma"]}</div><div style="font-weight:bold;">{int(row["Kolicina"])} kom</div></div>', unsafe_allow_html=True)
                                    st.markdown(f'<div style="text-align:right; font-weight:bold; color:#00FF00; padding:5px;">UKUPNO {jelo}: {int(jelo_data["Kolicina"].sum())}</div>', unsafe_allow_html=True)

        with t_a3:
            st.subheader("⭐ Statistika Kuvara")
            with st.container(border=True):
                c_r1, c_r2 = st.columns(2)
                with c_r1:
                    st.info(f"Rejting: {k1_ime}")
                    st.markdown(prikazi_zvjezdice(skor_k1), unsafe_allow_html=True)
                with c_r2:
                    st.info(f"Rejting: {k2_ime}")
                    st.markdown(prikazi_zvjezdice(skor_k2), unsafe_allow_html=True)
            st.divider()
            st.write("### Detaljne ocjene i komentari")
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

        # Tabovi za izmjenu i reset (standardni kod)
        with t_a2:
            st.subheader("Uređivanje Menija")
            od_m = st.radio("Meni:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"f_{od_m}"):
                novi = []
                for meta in ["Sedmica", "Rok", "Kuvar 1", "Kuvar 2"]:
                    v = df_m[df_m['Dan'] == meta]['Jelo'].values[0] if not df_m[df_m['Dan'] == meta].empty else ""
                    nv = st.text_input(f"{meta}:", value=v)
                    novi.append({"Dan": meta, "Jelo": nv})
                st.divider()
                for d in dani_std:
                    st.write(f"**{d}**")
                    jela = df_m[df_m['Dan'] == d]['Jelo'].tolist()
                    for i in range(3):
                        p_v = jela[i] if i < len(jela) else ""
                        n_j = st.text_input(f"{d} - {i+1}", value=p_v, key=f"{d}_{i}_{od_m}")
                        if n_j.strip(): novi.append({"Dan": d, "Jelo": n_j.strip()})
                if st.form_submit_button("💾 Sačuvaj"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi))
                    st.success("Sačuvano!"); time.sleep(1); st.rerun()

        with t_a4:
            if st.button("🚀 ROTIRAJ SEDMICU"):
                df_next = ucitaj_sheet("Meni_Naredni")
                if not df_next.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                    st.success("Meni rotiran!"); time.sleep(1); st.rerun()
    else:
        # KLIJENTSKI DIO (Ovaj dio već imaš funkcionalan)
        st.title(f"🍴 Dobrodošli, {st.session_state['user']}")
        # ... (kod za klijente)
