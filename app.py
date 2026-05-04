import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. STILIZACIJA (Precizno prema Snimak 1.png) ---
st.set_page_config(page_title="Catering Management", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important;}
    
    /* Glavni kontejner smjene sa slike */
    .kuhinja-box {
        background-color: #11141C;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 25px;
    }
    .smjena-header-text {
        font-size: 1.6rem;
        font-weight: bold;
        color: white;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    .table-header {
        display: flex;
        justify-content: space-between;
        color: #666;
        font-size: 0.75rem;
        font-weight: bold;
        border-bottom: 1px solid #333;
        padding-bottom: 8px;
        margin-bottom: 15px;
    }
    /* Jelo naslov */
    .jelo-title {
        background-color: #1A1C23;
        color: #E24A4A;
        padding: 10px 15px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 1.1rem;
        margin-top: 10px;
    }
    /* Redovi sa firmama */
    .row-firma {
        display: flex;
        justify-content: space-between;
        padding: 10px 15px;
        border-bottom: 1px solid #222;
        font-size: 1rem;
        color: #DDD;
    }
    /* Ukupno zeleno */
    .jelo-ukupno {
        text-align: right;
        color: #00FF00;
        font-weight: bold;
        font-size: 0.9rem;
        padding: 10px 15px;
        margin-bottom: 5px;
    }
    
    /* Klijent info kartice */
    .info-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }
    .info-card { flex: 1; padding: 15px; border-radius: 10px; text-align: center; color: white; font-weight: bold; font-size: 0.9rem; }
    .blue-card { background-color: #1e3a5f; border: 1px solid #3b82f6; }
    .yellow-card { background-color: #3e3e10; border: 1px solid #ca8a04; }
    .green-card { background-color: #143e2a; border: 1px solid #16a34a; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA POVEZIVANJA ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

def ucitaj_sheet(name):
    try: return conn.read(spreadsheet=spreadsheet_url, worksheet=name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

# --- 3. LOGIN ---
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
else:
    # --- 4. ADMIN PANEL (TAČAN IZGLED SA SLIKE) ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t1, t2, t3, t4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t1:
            st.markdown("### 👨‍🍳 Nalozi po smjenama")
            df_nar = ucitaj_sheet("Sheet1")
            dan_sel = st.selectbox("Izaberi dan:", dani_std)
            dan_filtrirano = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"] if not df_nar.empty else pd.DataFrame()

            for smj in ["I", "II", "III"]:
                smj_data = dan_filtrirano[dan_filtrirano['Smjena'] == smj]
                if not smj_data.empty:
                    # POCETAK BOXA SMJENE
                    html_smjena = f"""
                    <div class="kuhinja-box">
                        <div class="smjena-header-text">🕒 SMJENA {smj}</div>
                        <div class="table-header">
                            <span>JELO / FIRMA</span>
                            <span>KOLIČINA</span>
                        </div>
                    """
                    for jelo, j_data in smj_data.groupby("Jelo"):
                        html_smjena += f'<div class="jelo-title">{jelo}</div>'
                        for _, r in j_data.iterrows():
                            html_smjena += f"""
                            <div class="row-firma">
                                <span>🏢 {r['Firma']}</span>
                                <span style="font-weight:bold;">{int(r['Kolicina'])} kom</span>
                            </div>
                            """
                        ukupno = int(j_data['Kolicina'].sum())
                        html_smjena += f'<div class="jelo-ukupno">UKUPNO {jelo}: {ukupno}</div>'
                    
                    html_smjena += "</div>" # KRAJ BOXA
                    st.markdown(html_smjena, unsafe_allow_html=True)

    # --- 5. KLIJENT PANEL (Netaknuto, popravljeno čitanje) ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_o, t_n = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna"])
        
        def prikazi_klijent(sh_nm, prefix):
            df_m = ucitaj_sheet(sh_nm)
            df_sve = ucitaj_sheet("Sheet1")
            
            # Kartice
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Sedmica'].empty else "/"
            r = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Rok'].empty else "/"
            k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Kuvar'].empty else "/"
            st.markdown(f'<div class="info-container"><div class="info-card blue-card">📅 {s}</div><div class="info-card yellow-card">⏰ {r}</div><div class="info-card green-card">👨‍🍳 {k}</div></div>', unsafe_allow_html=True)

            with st.form(f"form_{prefix}"):
                unose = []
                for d in dani_std:
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {d}")
                        jela = df_m[df_m['Dan'] == d]['Jelo'].tolist() if not df_m.empty else []
                        for j in jela:
                            st.markdown(f"**{j}**")
                            c1, c2, c3 = st.columns(3)
                            
                            def get_old(smj_n):
                                if df_sve.empty: return 0
                                match = df_sve[(df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'] == f"{prefix}-{d}") & (df_sve['Jelo'] == j) & (df_sve['Smjena'] == smj_n)]
                                return int(match['Kolicina'].iloc[0]) if not match.empty else 0

                            k1 = c1.number_input("I", 0, 100, get_old("I"), key=f"{prefix}{d}{j}1")
                            k2 = c2.number_input("II", 0, 100, get_old("II"), key=f"{prefix}{d}{j}2")
                            k3 = c3.number_input("III", 0, 100, get_old("III"), key=f"{prefix}{d}{j}3")
                            for v, sn in zip([k1, k2, k3], ["I", "II", "III"]):
                                if v > 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{d}", "Jelo": j, "Kolicina": v, "Smjena": sn})
                
                if st.form_submit_button("SAČUVAJ"):
                    df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))] if not df_sve.empty else pd.DataFrame()
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_ostali, pd.DataFrame(unose)]))
                    st.success("Sačuvano!"); time.sleep(1); st.rerun()

        with t_o: prikazi_klijent("Meni_Trenutni", "Ova")
        with t_n: prikazi_klijent("Meni_Naredni", "Naredna")
