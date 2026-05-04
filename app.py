import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. STILIZACIJA (Kopirano direktno sa tvojih slika) ---
st.set_page_config(page_title="Catering Admin", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important;}
    
    /* Glavni crni kontejner smjene */
    .kuhinja-box {
        background-color: #11141C;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 25px;
        color: white;
    }
    .smjena-header-text {
        font-size: 1.6rem;
        font-weight: bold;
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
    .jelo-title {
        background-color: #1A1C23;
        color: #E24A4A;
        padding: 10px 15px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 1.1rem;
        margin-top: 10px;
    }
    .row-firma {
        display: flex;
        justify-content: space-between;
        padding: 10px 15px;
        border-bottom: 1px solid #222;
        font-size: 1rem;
        color: #DDD;
    }
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

# --- 2. POVEZIVANJE ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

def ucitaj_sheet(name):
    try:
        return conn.read(spreadsheet=spreadsheet_url, worksheet=name, ttl=0).dropna(how='all')
    except:
        return pd.DataFrame()

# --- 3. LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

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
                st.error("Pogrešni podaci")
else:
    # --- 4. ADMIN PANEL (Fiksiran za renderovanje) ---
    if st.session_state["user"] == "admin":
        st.markdown("## 👨‍🍳 Admin Upravljanje")
        t1, t2, t3, t4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t1:
            st.markdown("### 👨‍🍳 Nalozi po smjenama")
            df_nar = ucitaj_sheet("Sheet1")
            dan_sel = st.selectbox("Izaberi dan:", dani_std)
            
            # Filtriranje podataka za odabrani dan (Ova-Ponedjeljak npr.)
            dan_prefix = f"Ova-{dan_sel}"
            if not df_nar.empty:
                dan_filtrirano = df_nar[df_nar['Dan'] == dan_prefix]
            else:
                dan_filtrirano = pd.DataFrame()

            for smj in ["I", "II", "III"]:
                smj_data = dan_filtrirano[dan_filtrirano['Smjena'] == smj]
                if not smj_data.empty:
                    # POCETAK IZGRADNJE HTML BLOKA
                    html_smjena = '<div class="kuhinja-box">'
                    html_smjena += f'<div class="smjena-header-text">🕒 SMJENA {smj}</div>'
                    html_smjena += '<div class="table-header"><span>JELO / FIRMA</span><span>KOLIČINA</span></div>'
                    
                    # Grupisanje po jelu
                    for jelo, j_data in smj_data.groupby("Jelo"):
                        html_smjena += f'<div class="jelo-title">{jelo}</div>'
                        
                        for _, r in j_data.iterrows():
                            # Svaki red firme
                            html_smjena += f'<div class="row-firma">'
                            html_smjena += f'<span>🏢 {r["Firma"]}</span>'
                            html_smjena += f'<span style="font-weight:bold;">{int(r["Kolicina"])} kom</span>'
                            html_smjena += '</div>'
                        
                        # Zeleno ukupno za to jelo
                        ukupno = int(j_data['Kolicina'].sum())
                        html_smjena += f'<div class="jelo-ukupno">UKUPNO {jelo}: {ukupno}</div>'
                    
                    html_smjena += '</div>' # KRAJ BOXA
                    
                    # JEDAN JEDINI ISPIS ZA CIJELU SMJENU
                    st.markdown(html_smjena, unsafe_allow_html=True)
                else:
                    st.info(f"Nema narudžbi za smjenu {smj}")

        # --- OSTALI ADMIN TABOVI (Sređeni) ---
        with t2:
            od_m = st.radio("Uredi:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"f_admin_{od_m}"):
                # Meta podaci na vrhu
                c1, c2, c3 = st.columns(3)
                v_s = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan'] == 'Sedmica'].empty else ""
                v_r = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan'] == 'Rok'].empty else ""
                v_k = df_m[df_m['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan'] == 'Kuvar'].empty else ""
                n_s = c1.text_input("Period:", v_s)
                n_r = c2.text_input("Rok:", v_r)
                n_k = c3.text_input("Kuvar:", v_k)
                
                novi_unosi = [{"Dan": "Sedmica", "Jelo": n_s}, {"Dan": "Rok", "Jelo": n_r}, {"Dan": "Kuvar", "Jelo": n_k}]
                
                for d in dani_std:
                    st.markdown(f"--- \n**{d}**")
                    postojeca = df_m[df_m['Dan'] == d]['Jelo'].tolist()
                    for i in range(3):
                        val = postojeca[i] if i < len(postojeca) else ""
                        un = st.text_input(f"{d} jelo {i+1}", val, key=f"inp_{od_m}_{d}_{i}")
                        if un: novi_unosi.append({"Dan": d, "Jelo": un})
                
                if st.form_submit_button("💾 SAČUVAJ"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi_unosi))
                    st.success("Sačuvano!"); time.sleep(1); st.rerun()

        with t3:
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

        with t4:
            if st.button("🚀 ROTIRAJ: PREBACI NAREDNU U TRENUTNU"):
                df_next = ucitaj_sheet("Meni_Naredni")
                if not df_next.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                    st.success("Rotacija završena!"); time.sleep(1); st.rerun()

    # --- 5. KLIJENT PANEL (Netaknuto) ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_o, t_n = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna"])
        
        def render_client(sheet_name, prefix, lock):
            df_m = ucitaj_sheet(sheet_name)
            df_sve = ucitaj_sheet("Sheet1")
            
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Sedmica'].empty else "/"
            r = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Rok'].empty else "/"
            k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Kuvar'].empty else "/"
            st.markdown(f'<div class="info-container"><div class="info-card blue-card">📅 {s}</div><div class="info-card yellow-card">⏰ {r}</div><div class="info-card green-card">👨‍🍳 {k}</div></div>', unsafe_allow_html=True)

            with st.form(f"form_{prefix}"):
                nove_narudžbe = []
                for d in dani_std:
                    idx = dani_std.index(d)
                    danas_idx = datetime.now().weekday()
                    is_locked = (lock and danas_idx >= idx and danas_idx != 6)
                    
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {d} {'🔒' if is_locked else ''}")
                        jela = df_m[df_m['Dan'] == d]['Jelo'].tolist() if not df_m.empty else []
                        for j in jela:
                            st.write(f"**{j}**")
                            c1, c2, c3 = st.columns(3)
                            
                            def find_val(sn):
                                if df_sve.empty: return 0
                                m = df_sve[(df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'] == f"{prefix}-{d}") & (df_sve['Jelo'] == j) & (df_sve['Smjena'] == sn)]
                                return int(m['Kolicina'].iloc[0]) if not m.empty else 0

                            k1 = c1.number_input("I", 0, 100, find_val("I"), key=f"{prefix}{d}{j}1", disabled=is_locked)
                            k2 = c2.number_input("II", 0, 100, find_val("II"), key=f"{prefix}{d}{j}2", disabled=is_locked)
                            k3 = c3.number_input("III", 0, 100, find_val("III"), key=f"{prefix}{d}{j}3", disabled=is_locked)
                            for val, sn in zip([k1, k2, k3], ["I", "II", "III"]):
                                if val > 0: nove_narudžbe.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{d}", "Jelo": j, "Kolicina": val, "Smjena": sn})
                
                if st.form_submit_button("SAČUVAJ"):
                    df_others = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))] if not df_sve.empty else pd.DataFrame()
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_others, pd.DataFrame(nove_narudžbe)]))
                    st.success("Spremljeno!"); time.sleep(1); st.rerun()

        with t_o: render_client("Meni_Trenutni", "Ova", True)
        with t_n: render_client("Meni_Naredni", "Naredna", False)
