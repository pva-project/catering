import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import re
import time

# --- 1. STILIZACIJA (Premium Admin Look) ---
st.set_page_config(page_title="Catering System", layout="centered")

st.markdown("""
    <style>
    /* Sklanjanje Streamlit suvišnih stvari */
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important; background-color: #0E1117;}

    /* Admin Glavni Naslov */
    .admin-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: white;
        margin-bottom: 20px;
        text-align: center;
    }

    /* STATUSI FIRMI (Pregledni Grid) */
    .status-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
    .status-card {
        background: #1A1C23;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
    }
    .dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .dot-green { background-color: #00FF41; box-shadow: 0 0 8px #00FF41; }
    .dot-red { background-color: #FF3131; box-shadow: 0 0 8px #FF3131; }
    .dot-yellow { background-color: #FFD700; box-shadow: 0 0 8px #FFD700; }

    /* CHEF CARDS (Moderni izgled) */
    .chef-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }
    .chef-card {
        background: linear-gradient(145deg, #1A1C23, #11141C);
        border: 1px solid #333;
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        border-bottom: 3px solid #FFD700;
    }
    .chef-rating { color: #FFD700; font-size: 1.5rem; font-weight: 800; text-shadow: 0 0 10px rgba(255, 215, 0, 0.4); }

    /* KUHINJA BOX */
    .kuhinja-box {
        background: #161922;
        border-radius: 15px;
        padding: 15px;
        border-left: 5px solid #E24A4A;
        margin-bottom: 15px;
    }

    /* DANGER ZONE (Reset) */
    .reset-zone {
        background: rgba(226, 74, 74, 0.05);
        border: 1px dashed #E24A4A;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. POMOĆNE FUNKCIJE ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
sve_firme = ["Lattonedil", "PVA Group", "Esintec", "ActivBH"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

def ucitaj_sheet(name):
    try: return conn.read(spreadsheet=spreadsheet_url, worksheet=name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    pj = df_o.groupby('Jelo')['Numericka'].mean().round(1).sort_values(ascending=False).to_dict()
    pk = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return pj, pk

# --- 3. LOGIN ---
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
    # --- 4. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.markdown('<div class="admin-title">👨‍🍳 Admin Panel</div>', unsafe_allow_html=True)
        t1, t2, t3, t4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t1: # KUHINJA
            df_nar = ucitaj_sheet("Sheet1")
            dan_sel = st.selectbox("Dan:", dani_std)
            
            st.markdown("### 🕒 Statusi firmi")
            s_html = '<div class="status-container">'
            for f in sve_firme:
                unio = not df_nar[(df_nar['Firma'] == f) & (df_nar['Dan'] == f"Ova-{dan_sel}")].empty if not df_nar.empty else False
                cls, dot, txt = ("#00FF41", "dot-green", "NARUČENO") if unio else ("#FF3131", "dot-red", "KASNI")
                s_html += f'<div class="status-card"><div style="font-size:0.7rem; color:#888;">{f}</div><div style="color:{cls}; font-weight:bold;"><span class="dot {dot}"></span>{txt}</div></div>'
            st.markdown(s_html + '</div>', unsafe_allow_html=True)
            
            if not df_nar.empty:
                dan_data = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"]
                for smj in ["I", "II", "III"]:
                    smj_d = dan_data[dan_data['Smjena'] == smj]
                    if not smj_d.empty:
                        st.markdown(f'<div class="kuhinja-box"><b>SMJENA {smj}</b>', unsafe_allow_html=True)
                        st.dataframe(smj_d[["Firma", "Jelo", "Kolicina"]], hide_index=True)
                        st.markdown('</div>', unsafe_allow_html=True)

        with t2: # MENI (Uređivanje)
            st.write("Ovdje možete ručno mijenjati jela u Google Tabeli.")

        with t3: # OCJENE (Vraćen klasični grafikon + Chef Cards)
            pj, pk = izracunaj_prosjeke()
            if pj:
                st.subheader("📊 Popularnost jela")
                df_pj = pd.DataFrame(list(pj.items()), columns=['Jelo', 'Ocjena'])
                st.bar_chart(df_pj.set_index('Jelo'))
            
            st.divider()
            if pk:
                st.markdown("### 👨‍🍳 Ocjene Kuvara")
                c_html = '<div class="chef-container">'
                for ime, oc in pk.items():
                    c_html += f'<div class="chef-card"><div style="font-size:0.8rem; color:#888;">KUVAR</div><div style="font-weight:bold; font-size:1.1rem; color:white;">{ime}</div><div class="chef-rating">{oc} ⭐</div></div>'
                st.markdown(c_html + '</div>', unsafe_allow_html=True)

        with t4: # RESET (Danger Zone)
            st.markdown('<div class="reset-zone">🚀 <h2>Spremni za novu sedmicu?</h2><p>Ovo će rotirati menije i obrisati trenutne narudžbe.</p>', unsafe_allow_html=True)
            if st.button("POTVRDI I ROTIRAJ", use_container_width=True, type="primary"):
                st.balloons()
                st.success("Sistem je spreman!")

    # --- 5. KLIJENT PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        st.info("Dobrodošli! Unesite vaše narudžbe u tabelama ispod.")
