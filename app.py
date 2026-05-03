import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I STIL ---
st.set_page_config(page_title="Catering Admin", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"], header, footer {display: none !important;}
    .stAppDeployButton, [data-testid="stStatusWidget"], div[data-testid="stToolbar"] {display: none !important;}
    .block-container {padding-top: 1rem !important;}
    
    /* Stil za zvjezdice */
    .star-ratings {
        color: #ccc;
        position: relative;
        display: inline-block;
        font-size: 20px;
    }
    .star-ratings-fill {
        color: #ffca08;
        padding: 0;
        position: absolute;
        z-index: 1;
        display: block;
        top: 0;
        left: 0;
        overflow: hidden;
        white-space: nowrap;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNKCIJA ZA CRTANJE ZVJEZDICA ---
def prikazi_zvjezdice(ocjena):
    # Procenat popunjenosti (npr. 4.5 od 5 je 90%)
    procenat = (ocjena / 5) * 100
    html_kod = f"""
    <div style="display: inline-block; vertical-align: middle;">
        <span style="font-weight: bold; font-size: 1.1rem; margin-right: 8px;">{ocjena}</span>
        <div class="star-ratings">
            <div class="star-ratings-fill" style="width: {procenat}%;">
                <span>★★★★★</span>
            </div>
            <div><span>★★★★★</span></div>
        </div>
    </div>
    """
    return html_kod

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
    ukupni_prosjek_kuvara = df_o['Numericka'].mean().round(1)
    return prosjeci_jela, ukupni_prosjek_kuvara

# --- 3. LOGIN & ADMIN PANEL ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 Prijava")
    u = st.text_input("Korisnik")
    p = st.text_input("Lozinka", type="password")
    if st.button("Prijava"):
        if u == "admin" and p == "admin123":
            st.session_state["logged_in"], st.session_state["user"] = True, "admin"
            st.rerun()
else:
    t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene", "🔄 Reset"])
    
    with t_a1:
        df_m_t = ucitaj_sheet("Meni_Trenutni")
        prosjeci_jela, ocjena_kuvara = analiziraj_ocjene()
        
        kuvar = df_m_t[df_m_t['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar'].empty else "N/A"
        
        # PRIKAZ KUVARA SA ZVJEZDICAMA
        with st.container(border=True):
            st.markdown(f"**👨‍🍳 Glavni kuvar: {kuvar}**")
            st.markdown(prikazi_zvjezdice(ocjena_kuvara), unsafe_allow_html=True)

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
                                rang = prosjeci_jela.get(jelo, 0.0)
                                # PRIKAZ JELA SA ZVJEZDICAMA
                                st.markdown(f"""
                                    <div style="background-color:#1E1E1E; padding:10px; border-radius:5px; margin-top:10px;">
                                        <div style="font-weight:bold; color:#FF4B4B; font-size:1.1rem; margin-bottom:5px;">{jelo}</div>
                                        {prikazi_zvjezdice(rang)}
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                for _, row in jelo_data.iterrows():
                                    st.markdown(f'<div style="display:flex; justify-content:space-between; padding:5px 10px;"><div>🏢 {row["Firma"]}</div><div style="font-weight:bold;">{int(row["Kolicina"])} kom</div></div>', unsafe_allow_html=True)
                                
                                st.markdown(f'<div style="text-align:right; font-weight:bold; color:#00FF00; padding:5px;">UKUPNO: {int(jelo_data["Kolicina"].sum())}</div>', unsafe_allow_html=True)
    
    # --- OSTATAK KODA (TAB 2, 3, 4) OSTAJE ISTI KAO PRETHODNO ---
    with t_a2:
        st.subheader("Uređivanje Menija")
        # ... (kod za editovanje menija)
    with t_a3:
        st.subheader("⭐ Detaljne ocjene")
        st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)
    with t_a4:
        if st.button("🚀 ROTIRAJ SEDMICU"):
            # ... (kod za rotaciju)
            st.success("Meni rotiran!")
