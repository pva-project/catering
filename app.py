import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. STILIZACIJA (Dizajn prema tvojim slikama) ---
st.set_page_config(page_title="Catering Management", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important;}
    
    /* Glavni kontejner smjene (Admin) */
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

# --- 2. POVEZIVANJE I OSNOVNE POSTAVKE ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

def ucitaj_sheet(name):
    try:
        return conn.read(spreadsheet=spreadsheet_url, worksheet=name, ttl=0).dropna(how='all')
    except:
        return pd.DataFrame()

# --- 3. PRIJAVA ---
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
    # --- 4. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.markdown("## 👨‍🍳 Admin Upravljanje")
        t1, t2, t3, t4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene", "🔄 Reset"])
        
        with t1:
            st.markdown("### 👨‍🍳 Nalozi po smjenama")
            df_nar = ucitaj_sheet("Sheet1")
            dan_sel = st.selectbox("Izaberi dan:", dani_std)
            dan_filtrirano = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"] if not df_nar.empty else pd.DataFrame()

            for smj in ["I", "II", "III"]:
                smj_data = dan_filtrirano[dan_filtrirano['Smjena'] == smj]
                if not smj_data.empty:
                    # Kreiramo kompletan HTML string da izbjegnemo greške u renderovanju
                    html_box = f"""
                    <div class="kuhinja-box">
                        <div class="smjena-header-text">🕒 SMJENA {smj}</div>
                        <div class="table-header">
                            <span>JELO / FIRMA</span>
                            <span>KOLIČINA</span>
                        </div>
                    """
                    for jelo, j_data in smj_data.groupby("Jelo"):
                        html_box += f'<div class="jelo-title">{jelo}</div>'
                        for _, r in j_data.iterrows():
                            html_box += f"""
                            <div class="row-firma">
                                <span>🏢 {r['Firma']}</span>
                                <span style="font-weight:bold;">{int(r['Kolicina'])} kom</span>
                            </div>
                            """
                        ukupno = int(j_data['Kolicina'].sum())
                        html_box += f'<div class="jelo-ukupno">UKUPNO {jelo}: {ukupno}</div>'
                    
                    html_box += "</div>"
                    st.markdown(html_box, unsafe_allow_html=True)
                else:
                    st.info(f"Nema narudžbi za smjenu {smj}")

        with t2: # Izmjena menija
            od_m = st.radio("Uredi:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"adm_edit_{od_m}"):
                c1, c2, c3 = st.columns(3)
                v_s = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan'] == 'Sedmica'].empty else ""
                v_r = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan'] == 'Rok'].empty else ""
                v_k = df_m[df_m['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan'] == 'Kuvar'].empty else ""
                n_s = c1.text_input("Period:", v_s)
                n_r = c2.text_input("Rok:", v_r)
                n_k = c3.text_input("Kuvar:", v_k)
                novi_data = [{"Dan": "Sedmica", "Jelo": n_s}, {"Dan": "Rok", "Jelo": n_r}, {"Dan": "Kuvar", "Jelo": n_k}]
                for d in dani_std:
                    st.write(f"**{d}**")
                    jela_postoje = df_m[df_m['Dan'] == d]['Jelo'].tolist()
                    for i in range(3):
                        stara = jela_postoje[i] if i < len(jela_postoje) else ""
                        unos = st.text_input(f"{d} - {i+1}", stara, key=f"edit_{od_m}_{d}_{i}")
                        if unos: novi_data.append({"Dan": d, "Jelo": unos})
                if st.form_submit_button("SAČUVAJ IZMJENE"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi_data))
                    st.success("Meni ažuriran!"); time.sleep(1); st.rerun()

        with t3: # Ocjene
            df_o = ucitaj_sheet("Ocjene")
            if not df_o.empty:
                st.dataframe(df_o, use_container_width=True, hide_index=True)
            else: st.info("Nema ocjena.")

        with t4: # Reset / Rotacija
            if st.button("🚀 ROTIRAJ SEDMICE (Prebaci Narednu u Trenutnu)"):
                df_next = ucitaj_sheet("Meni_Naredni")
                if not df_next.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                    st.success("Rotirano!"); time.sleep(1); st.rerun()

    # --- 5. KLIJENT PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_o, t_n = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna"])
        
        def prikazi_klijent(sh_nm, prefix, lock_past):
            df_m = ucitaj_sheet(sh_nm)
            df_sve = ucitaj_sheet("Sheet1")
            
            # Kartice
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Sedmica'].empty else "/"
            r = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Rok'].empty else "/"
            k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Kuvar'].empty else "/"
            st.markdown(f'<div class="info-container"><div class="info-card blue-card">📅 {s}</div><div class="info-card yellow-card">⏰ {r}</div><div class="info-card green-card">👨‍🍳 {k}</div></div>', unsafe_allow_html=True)

            with st.form(f"form_client_{prefix}"):
                unose = []
                for d in dani_std:
                    idx = dani_std.index(d)
                    onemoguci = (lock_past and danasnji_dan_index >= idx and danasnji_dan_index != 6)
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {d} {'🔒' if onemoguci else ''}")
                        jela = df_m[df_m['Dan'] == d]['Jelo'].tolist() if not df_m.empty else []
                        for j in jela:
                            st.markdown(f"**{j}**")
                            c1, c2, c3 = st.columns(3)
                            
                            def get_old(smj_n):
                                if df_sve.empty: return 0
                                match = df_sve[(df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'] == f"{prefix}-{d}") & (df_sve['Jelo'] == j) & (df_sve['Smjena'] == smj_n)]
                                return int(match['Kolicina'].iloc[0]) if not match.empty else 0

                            k1 = c1.number_input("I", 0, 100, get_old("I"), key=f"{prefix}{d}{j}1", disabled=onemoguci)
                            k2 = c2.number_input("II", 0, 100, get_old("II"), key=f"{prefix}{d}{j}2", disabled=onemoguci)
                            k3 = c3.number_input("III", 0, 100, get_old("III"), key=f"{prefix}{d}{j}3", disabled=onemoguci)
                            for v, sn in zip([k1, k2, k3], ["I", "II", "III"]):
                                if v > 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{d}", "Jelo": j, "Kolicina": v, "Smjena": sn})
                
                if st.form_submit_button("💾 SAČUVAJ NARUDŽBU", use_container_width=True):
                    # Zadrži sve druge, obriši samo moje za ovu sedmicu
                    df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))] if not df_sve.empty else pd.DataFrame()
                    finalni_df = pd.concat([df_ostali, pd.DataFrame(unose)], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=finalni_df)
                    st.success("Uspješno sačuvano!"); time.sleep(1); st.rerun()

        with t_o: prikazi_klijent("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_klijent("Meni_Naredni", "Naredna", False)
