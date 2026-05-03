import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- KONFIGURACIJA ---
st.set_page_config(page_title="Catering Admin", layout="centered")

# CSS za čist prikaz bez HTML koda
st.markdown("""
    <style>
    [data-testid="stHeader"], header, footer {display: none !important;}
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

def tekstualne_zvijezde(ocjena):
    pune = int(round(ocjena))
    return "⭐" * pune + "☆" * (5 - pune) + f" ({ocjena})"

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

def ucitaj_sheet(sheet_name):
    try:
        return conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

# --- KLJUČNA FUNKCIJA ZA PROSJEK ---
def analiziraj_kuvare_iz_tabele():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns or "Kuvar" not in df_o.columns:
        return {}
    
    # Pretvaramo tekstualne ocjene (Odlično -> 4)
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    # Grupišemo po imenu kuvara (Jelena, Dragana...)
    return df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict()

# --- ADMIN PANEL ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if st.session_state["logged_in"] or st.sidebar.checkbox("Admin Mode (Test)"):
    # 1. Povuci imena trenutnih kuvara iz Menija
    df_m = ucitaj_sheet("Meni_Trenutni")
    k1_ime = df_m[df_m['Dan'].str.contains('Kuvar 1', na=False)]['Jelo'].values[0] if not df_m[df_m['Dan'].str.contains('Kuvar 1', na=False)].empty else "Nije unijet"
    k2_ime = df_m[df_m['Dan'].str.contains('Kuvar 2', na=False)]['Jelo'].values[0] if not df_m[df_m['Dan'].str.contains('Kuvar 2', na=False)].empty else "Nije unijet"

    # 2. Izračunaj prosjeke na osnovu imena
    prosjeci = analiziraj_kuvare_iz_tabele()

    st.title("👨‍🍳 Admin Upravljanje")
    t1, t2 = st.tabs(["📊 Kuhinja", "⭐ Ocjene"])

    with t2:
        st.subheader("⭐ Rang lista na osnovu baze")
        c1, c2 = st.columns(2)
        
        # Prikaz za Kuvara 1 (npr. Jelena)
        p1 = prosjeci.get(k1_ime, 0.0)
        c1.metric(f"Kuvar 1: {k1_ime}", tekstualne_zvijezde(p1))
        
        # Prikaz za Kuvara 2 (npr. Dragana)
        p2 = prosjeci.get(k2_ime, 0.0)
        c2.metric(f"Kuvar 2: {k2_ime}", tekstualne_zvijezde(p2))

        st.divider()
        st.write("Podaci iz šita 'Ocjene':")
        st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)
