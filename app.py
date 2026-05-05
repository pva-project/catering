import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import re
import time

# --- 1. STILIZACIJA (Originalni klijent i admin stil) ---
st.set_page_config(page_title="Catering System", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important; background-color: #0E1117;}
    
    /* Box za Period (Plavi sa slike) */
    .period-box { background-color: #1A2C42; border: 1px solid #2D4A6E; border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #4A90E2; display: flex; align-items: center; gap: 10px; }
    
    /* Box za narudžbu (Sivi sa slike) */
    .order-card { background-color: #161922; border: 1px solid #333; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
    
    /* Admin stilovi */
    .kuhinja-box { background-color: #161922; border-radius: 15px; padding: 20px; border-left: 5px solid #E24A4A; margin-bottom: 20px; color: white; }
    .jelo-title { background-color: #1A1C23; color: #E24A4A; padding: 10px; border-radius: 5px; font-weight: bold; margin-top: 10px; }
    .chef-card { background: linear-gradient(145deg, #1A1C23, #11141C); border: 1px solid #333; border-radius: 20px; padding: 20px; text-align: center; border-bottom: 3px solid #FFD700; }
    .badge { background: #FFD700; color: black; padding: 2px 8px; border-radius: 50px; font-weight: bold; }
    
    /* Crveni gumb za štampu */
    .stDownloadButton button { background: #E24A4A !important; color: white !important; border-radius: 10px !important; font-weight: bold !important; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- 2. POMOĆNE FUNKCIJE ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

def ucitaj_sheet(name):
    try: return conn.read(spreadsheet=spreadsheet_url, worksheet=name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

def izvadi_sat(tekst):
    brojevi = re.findall(r'\d+', str(tekst))
    return int(brojevi[0]) if brojevi else 16

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
    # --- ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.markdown('## 👨‍🍳 Admin Panel')
        t1, t2, t3, t4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t1: # KUHINJA (Sa štampom)
            df_nar = ucitaj_sheet("Sheet1")
            dan_sel = st.selectbox("Izaberi dan:", dani_std)
            if not df_nar.empty:
                dan_data = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"]
                st.download_button("📥 PREUZMI LISTU ZA ŠTAMPU", data=dan_data.to_csv(), file_name=f"{dan_sel}.csv", use_container_width=True)
                for smj in ["I", "II", "III"]:
                    smj_d = dan_data[dan_data['Smjena'] == smj]
                    if not smj_d.empty:
                        h_box = f'<div class="kuhinja-box"><b>🕒 SMJENA {smj}</b>'
                        for jelo, j_d in smj_d.groupby("Jelo"):
                            h_box += f'<div class="jelo-title">{jelo}</div>'
                            for _, r in j_d.iterrows(): h_box += f'<div class="row-firma"><span>🏢 {r["Firma"]}</span><b>{int(r["Kolicina"])} kom</b></div>'
                        st.markdown(h_box + '</div>', unsafe_allow_html=True)
        
        with t3: # OCJENE (Titule i Tabela)
            df_o = ucitaj_sheet("Ocjene")
            if not df_o.empty:
                df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
                pk = df_o.groupby('Kuvar')['Numericka'].mean().to_dict()
                cols = st.columns(len(pk))
                for i, (ime, oc) in enumerate(pk.items()):
                    with cols[i]:
                        st.markdown(f'<div class="chef-card"><div class="chef-avatar-circle">👩‍🍳</div><b>{ime}</b><br><span style="font-size:1.5rem; color:#FFD700;">{oc:.1f} ⭐</span></div>', unsafe_allow_html=True)
                
                st.markdown("### 💬 Posljednji komentari")
                st.table(df_o[['Jelo', 'Ocjena', 'Komentar']].tail(5))

    # --- KLIJENT PANEL (Vraćen prema slici 4) ---
    else:
        f_user = st.session_state["user"]
        st.markdown(f"# {f_user}")
        
        meni_t = ucitaj_sheet("Meni_Trenutni")
        df_nar = ucitaj_sheet("Sheet1")
        
        if not meni_t.empty:
            period = meni_t[meni_t['Dan']=='Sedmica']['Jelo'].values[0]
            rok_tekst = meni_t[meni_t['Dan']=='Rok']['Jelo'].values[0]
            sat_limita = izvadi_sat(rok_tekst)
            sada = datetime.now() + timedelta(hours=2)
            
            # Plavi period box sa slike
            st.markdown(f'<div class="period-box">📅 Period: {period}</div>', unsafe_allow_html=True)
            
            izbor_dana = st.selectbox("Izaberi dan:", dani_std)
            jela_za_dan = meni_t[meni_t['Dan'] == izbor_dana]['Jelo'].tolist()
            
            # Logika zakljucavanja
            idx_dana = dani_std.index(izbor_dana)
            zakljucano = (idx_dana < sada.weekday()) or (idx_dana == sada.weekday() and sada.hour >= sat_limita)
            
            # Sivi box za unos (Slika 4)
            st.markdown('<div class="order-card">', unsafe_allow_html=True)
            if zakljucano:
                st.error(f"🔒 Narudžbe za {izbor_dana} su zatvorene (Rok: {rok_tekst}).")
            else:
                with st.form("narudzba_forma"):
                    jelo = st.selectbox("Izaberi jelo:", jela_za_dan)
                    smjena = st.radio("Smjena:", ["I", "II", "III"], horizontal=True)
                    kol = st.number_input("Količina:", min_value=1, value=1)
                    if st.form_submit_button("🚀 NARUČI"):
                        nova = pd.DataFrame([{"Firma": f_user, "Dan": f"Ova-{izbor_dana}", "Smjena": smjena, "Jelo": jelo, "Kolicina": kol, "Vrijeme": sada.strftime("%H:%M")}])
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_nar, nova]))
                        st.success("Dodano!")
                        time.sleep(0.5)
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            # ISTORIJA (Da klijent vidi sta je narucio)
            st.markdown("### 📋 Tvoja istorija za ovu sedmicu")
            moje = df_nar[df_nar['Firma'] == f_user]
            if not moje.empty:
                st.dataframe(moje[['Dan', 'Smjena', 'Jelo', 'Kolicina']], use_container_width=True, hide_index=True)
                
                # OCJENE (Ispod istorije)
                with st.expander("⭐ Ocjeni obrok"):
                    kuvar_ime = meni_t[meni_t['Dan']=='Kuvar']['Jelo'].values[0] if not meni_t.empty else "Nepoznato"
                    with st.form("ocjena_k"):
                        j_za_o = st.selectbox("Jelo:", moje['Jelo'].unique())
                        ocj = st.select_slider("Ocjena:", options=list(mapa_ocjena.keys()), value="Dobro")
                        kom = st.text_input("Komentar:")
                        if st.form_submit_button("Pošalji"):
                            n_ocj = pd.DataFrame([{"Jelo": j_za_o, "Ocjena": ocj, "Kuvar": kuvar_ime, "Komentar": kom, "Firma": f_user}])
                            conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([ucitaj_sheet("Ocjene"), n_ocj]))
                            st.success("Hvala!")
        
        if st.button("🚪 Odjavi se"):
            st.session_state["logged_in"] = False
            st.rerun()
