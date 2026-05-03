import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Admin", layout="centered")

# CSS za sakrivanje nepotrebnih elemenata i bolji UI
st.markdown("""
    <style>
    [data-testid="stHeader"], header, footer {display: none !important;}
    .block-container {padding-top: 1rem !important;}
    .stMetric { background-color: #1e1e1e; padding: 10px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# Funkcija za prikaz zvjezdica koja NEĆE izbacivati HTML grešku
def graficki_rejting(ocjena):
    pune_zvijezde = int(ocjena)
    prazne_zvijezde = 5 - pune_zvijezde
    return f"⭐" * pune_zvijezde + "☆" * prazne_zvijezde + f" ({ocjena})"

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame(columns=["Dan", "Jelo"])

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    p_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    p_kuvari = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return p_jela, p_kuvari

# --- 2. LOGIN (Skraćeno radi preglednosti) ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava</h1>", unsafe_allow_html=True)
    u = st.text_input("Korisnik")
    p = st.text_input("Lozinka", type="password")
    if st.button("Ulaz"):
        if u == "admin" and p == "admin123":
            st.session_state["logged_in"] = True
            st.rerun()
else:
    # --- 3. ADMIN PANEL ---
    df_m_t = ucitaj_sheet("Meni_Trenutni")
    p_jela, p_kuvari = izracunaj_prosjeke()

    # FIX ZA IMENA KUVARA: Tražimo tačno 'Kuvar 1' i 'Kuvar 2' u koloni Dan
    k1_ime = df_m_t[df_m_t['Dan'].str.strip() == 'Kuvar 1']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'].str.strip() == 'Kuvar 1'].empty else "Nije unijet"
    k2_ime = df_m_t[df_m_t['Dan'].str.strip() == 'Kuvar 2']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'].str.strip() == 'Kuvar 2'].empty else "Nije unijet"

    st.title("👨‍🍳 Admin Upravljanje")
    t_kuhinja, t_meni, t_ocjene, t_reset = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])

    with t_kuhinja: #
        st.subheader("Trenutni tim i narudžbe")
        c1, c2 = st.columns(2)
        c1.metric(f"Kuvar 1: {k1_ime}", graficki_rejting(p_kuvari.get(k1_ime, 0.0)))
        c2.metric(f"Kuvar 2: {k2_ime}", graficki_rejting(p_kuvari.get(k2_ime, 0.0)))

        df_nar = ucitaj_sheet("Sheet1")
        if not df_nar.empty:
            dan_sel = st.selectbox("Izaberi dan:", dani_std)
            prikaz = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"]
            for smjena in ["I", "II", "III"]:
                sm_data = prikaz[prikaz['Smjena'] == smjena]
                if not sm_data.empty:
                    with st.expander(f"🕒 SMJENA {smjena}", expanded=True):
                        for jelo, j_data in sm_data.groupby("Jelo"):
                            prosjek = p_jela.get(jelo, 0.0)
                            st.markdown(f"**{jelo}** | {graficki_rejting(prosjek)}")
                            for _, r in j_data.iterrows():
                                st.write(f"· {r['Firma']}: {int(r['Kolicina'])} kom")
                            st.info(f"Ukupno: {int(j_data['Kolicina'].sum())}")

    with t_ocjene: #
        st.subheader("⭐ Rang lista")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"### {k1_ime}")
            st.header(f"{p_kuvari.get(k1_ime, 0.0)} ⭐")
        with col2:
            st.write(f"### {k2_ime}")
            st.header(f"{p_kuvari.get(k2_ime, 0.0)} ⭐")
        
        st.divider()
        st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

    # ... (Ostatak koda za Meni i Reset ostaje isti kao tvoj originalni)
