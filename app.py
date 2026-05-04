import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. STILIZACIJA (Ažurirano da odgovara slici) ---
st.set_page_config(page_title="Catering Management", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important;}
    
    /* Info kartice na vrhu klijenta */
    .info-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }
    .info-card { flex: 1; padding: 15px; border-radius: 10px; text-align: center; color: white; font-weight: bold; font-size: 0.9rem; }
    .blue-card { background-color: #1e3a5f; border: 1px solid #3b82f6; }
    .yellow-card { background-color: #3e3e10; border: 1px solid #ca8a04; }
    .green-card { background-color: #143e2a; border: 1px solid #16a34a; }
    
    /* ADMIN PANEL DIZAJN PREMA SLICI */
    .admin-card {
        background-color: #0E1117;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .smjena-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: white;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .sub-header {
        color: #888;
        font-size: 0.7rem;
        text-transform: uppercase;
        border-bottom: 1px solid #333;
        padding-bottom: 5px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
    }
    .jelo-header-box {
        background-color: #1E1E1E;
        color: #FF4B4B;
        padding: 8px 12px;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 15px;
    }
    .firma-red {
        display: flex;
        justify-content: space-between;
        padding: 8px 12px;
        border-bottom: 1px solid #222;
        font-size: 0.9rem;
    }
    .ukupno-label {
        text-align: right;
        color: #00FF00;
        font-weight: bold;
        font-size: 0.85rem;
        padding-top: 5px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. POVEZIVANJE ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

def ucitaj_sheet(sheet_name):
    try: return conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    pj = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    pk = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return pj, pk

# --- 3. LOGIN ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Korisničko ime")
        p = st.text_input("Lozinka", type="password")
        if st.button("Prijavi se", use_container_width=True):
            if u in users and users[u] == p:
                st.session_state["logged_in"], st.session_state["user"] = True, u
                st.rerun()
else:
    # --- 4. ADMIN PANEL (DIZAJN PREMA SLICI) ---
    if st.session_state["user"] == "admin":
        st.markdown("## 👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene", "🔄 Reset"])
        
        with t_a1:
            st.markdown("### 👨‍🍳 Nalozi po smjenama")
            df_nar = ucitaj_sheet("Sheet1")
            d_sel = st.selectbox("Izaberi dan:", dani_std)
            prikaz_df = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"] if not df_nar.empty else pd.DataFrame()
            
            if not prikaz_df.empty:
                for smj in ["I", "II", "III"]:
                    smj_data = prikaz_df[prikaz_df['Smjena'] == smj]
                    if not smj_data.empty:
                        # Otvaranje Smjena Kontejnera
                        st.markdown(f"""
                            <div class="admin-card">
                                <div class="smjena-title">🕒 SMJENA {smj}</div>
                                <div class="sub-header"><span>JELO / FIRMA</span><span>KOLIČINA</span></div>
                        """, unsafe_allow_html=True)
                        
                        for jelo, jelo_data in smj_data.groupby("Jelo"):
                            st.markdown(f'<div class="jelo-header-box">{jelo}</div>', unsafe_allow_html=True)
                            for _, r in jelo_data.iterrows():
                                st.markdown(f"""
                                    <div class="firma-red">
                                        <span>🏢 {r['Firma']}</span>
                                        <span style="font-weight: bold;">{int(r['Kolicina'])} kom</span>
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            ukupno_jela = int(jelo_data['Kolicina'].sum())
                            st.markdown(f'<div class="ukupno-label">UKUPNO {jelo}: {ukupno_jela}</div>', unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True) # Zatvaranje admin-card
            else:
                st.info("Nema narudžbi za izabrani dan.")

        # --- OSTALI ADMIN TABOVI (Nepromijenjeno) ---
        with t_a2:
            od_m = st.radio("Uredi:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"f_adm_{od_m}"):
                c1, c2, c3 = st.columns(3)
                v_s = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan'] == 'Sedmica'].empty else ""
                v_r = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan'] == 'Rok'].empty else ""
                v_k = df_m[df_m['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan'] == 'Kuvar'].empty else ""
                n_s = c1.text_input("📅 Period:", value=v_s)
                n_r = c2.text_input("⏰ Rok:", value=v_r)
                n_k = c3.text_input("👨‍🍳 Kuvar:", value=v_k)
                novi_p = [{"Dan": "Sedmica", "Jelo": n_s}, {"Dan": "Rok", "Jelo": n_r}, {"Dan": "Kuvar", "Jelo": n_k}]
                for dan in dani_std:
                    st.markdown(f"**{dan}**")
                    jela_p = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    for i in range(3):
                        v_j = jela_p[i] if i < len(jela_p) else ""
                        nj = st.text_input(f"{dan} - {i+1}", value=v_j, key=f"e_{od_m}_{dan}_{i}")
                        if nj.strip(): novi_p.append({"Dan": dan, "Jelo": nj.strip()})
                if st.form_submit_button("💾 SAČUVAJ"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi_p))
                    st.success("Meni sačuvan!"); time.sleep(1); st.rerun()

        with t_a3:
            df_o = ucitaj_sheet("Ocjene")
            if not df_o.empty:
                _, pk = izracunaj_prosjeke()
                cols = st.columns(len(pk)) if pk else st.columns(1)
                for i, (kuvar, ocj) in enumerate(pk.items()): cols[i].metric(f"👨‍🍳 {kuvar}", f"{ocj} ⭐")
                st.dataframe(df_o, use_container_width=True, hide_index=True)

        with t_a4:
            if st.button("🚀 ROTIRAJ SEDMICE"):
                df_next = ucitaj_sheet("Meni_Naredni")
                if not df_next.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                    df_all = ucitaj_sheet("Sheet1")
                    if not df_all.empty:
                        df_all['Dan'] = df_all['Dan'].str.replace("Naredna-", "Ova-")
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=df_all)
                    st.success("Uspješno!"); time.sleep(1); st.rerun()

    # --- 5. KLIJENT PANEL (Netaknuto - ispravno čita podatke) ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_t, t_n, t_h, t_o = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna", "📜 Istorija", "⭐ Ocijeni"])
        pj, _ = izracunaj_prosjeke()

        def prikazi_klijent(sh_name, prefix, lock):
            df_m = ucitaj_sheet(sh_name)
            df_sve = ucitaj_sheet("Sheet1")
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Sedmica'].empty else "/"
            r = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Rok'].empty else "/"
            k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty and not df_m[df_m['Dan']=='Kuvar'].empty else "/"
            st.markdown(f'<div class="info-container"><div class="info-card blue-card">📅 {s}</div><div class="info-card yellow-card">⏰ {r}</div><div class="info-card green-card">👨‍🍳 {k}</div></div>', unsafe_allow_html=True)

            with st.form(f"f_{prefix}"):
                unose = []
                for dan in dani_std:
                    idx = dani_std.index(dan)
                    onemoguci = False if danasnji_dan_index == 6 else (lock and danasnji_dan_index >= idx)
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan} {'🔒' if onemoguci else '🔓'}")
                        jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist() if not df_m.empty else []
                        for j in jela:
                            st.markdown(f"**{j}** {f'(⭐ {pj.get(j)})' if pj.get(j) else ''}")
                            c1, c2, c3 = st.columns(3)
                            def find_old(smj):
                                if df_sve.empty: return 0
                                m = df_sve[(df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{prefix}-{dan}") & (df_sve['Jelo']==j) & (df_sve['Smjena']==smj)]
                                return int(m['Kolicina'].iloc[0]) if not m.empty else 0
                            k1 = c1.number_input("I", 0, 100, find_old("I"), key=f"{prefix}{dan}{j}1", disabled=onemoguci)
                            k2 = c2.number_input("II", 0, 100, find_old("II"), key=f"{prefix}{dan}{j}2", disabled=onemoguci)
                            k3 = c3.number_input("III", 0, 100, find_old("III"), key=f"{prefix}{dan}{j}3", disabled=onemoguci)
                            for val, sn in zip([k1, k2, k3], ["I", "II", "III"]):
                                if val > 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": val, "Smjena": sn})
                if st.form_submit_button("SAČUVAJ"):
                    df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))] if not df_sve.empty else pd.DataFrame()
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_ostali, pd.DataFrame(unose)], ignore_index=True))
                    st.success("Sačuvano!"); time.sleep(1); st.rerun()

        with t_t: prikazi_klijent("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_klijent("Meni_Naredni", "Naredna", False)
        with t_h: st.dataframe(ucitaj_sheet("Sheet1")[lambda df: df['Firma']==st.session_state['user']] if not ucitaj_sheet("Sheet1").empty else pd.DataFrame(), use_container_width=True, hide_index=True)
        with t_o:
            # Ocjenjivanje (Netaknuto)
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            k_t = df_m_t[df_m_t['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m_t.empty and not df_m_t[df_m_t['Dan'] == 'Kuvar'].empty else "N/A"
            jela_o = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist() if not df_m_t.empty else []
            with st.form("f_ocj"):
                j_sel = st.selectbox("Jelo:", jela_o)
                oc = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                km = st.text_area("Komentar:")
                if st.form_submit_button("Pošalji"):
                    df_o = ucitaj_sheet("Ocjene")
                    novi = pd.DataFrame([{"Firma": st.session_state['user'], "Jelo": j_sel, "Ocjena": oc, "Komentar": km, "Kuvar": k_t}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o, novi], ignore_index=True))
                    st.success("Hvala!"); time.sleep(1); st.rerun()
