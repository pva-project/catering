import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I "ULTIMATE" STILIZACIJA (Vizuelno ko u tvom kodu) ---
st.set_page_config(page_title="Catering Management", layout="centered")

st.markdown("""
    <style>
    /* Skrivanje svega nepotrebnog */
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    .block-container {padding-top: 1rem !important; padding-bottom: 0rem !important;}
    
    /* Info kartice na vrhu (Period, Rok, Kuvar) */
    .info-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 20px;
    }
    .info-card {
        flex: 1;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .blue-card { background-color: #1e3a5f; border: 1px solid #3b82f6; }
    .yellow-card { background-color: #3e3e10; border: 1px solid #ca8a04; }
    .green-card { background-color: #143e2a; border: 1px solid #16a34a; }
    
    /* Stilovi za jela i naslove */
    .dish-title { font-weight: bold; color: #ffffff; font-size: 1.1rem; margin-top: 10px; }
    .smjena-label { color: #888; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame(columns=["Dan", "Jelo"])

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    pj = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    pk = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return pj, pk

# --- 4. LOGIN ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava za Catering</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Korisničko ime")
        p = st.text_input("Lozinka", type="password")
        if st.button("Prijavi se", use_container_width=True):
            if u in users and users[u] == p:
                st.session_state["logged_in"], st.session_state["user"] = True, u
                st.rerun()
            else: st.error("Pogrešni podaci")
else:
    # --- 5. ADMIN PANEL (Tehnički tvoj kod, vizuelno sl3/sl2) ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene & Kuvari", "🔄 Reset"])
        
        with t_a1:
            st.subheader("👨‍🍳 Nalozi po smjenama")
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
                                    st.markdown(f'<div style="background-color:#1E1E1E; padding:8px; border-radius:5px; margin-top:10px; font-weight:bold; color:#FF4B4B;">{jelo}</div>', unsafe_allow_html=True)
                                    for _, row in jelo_data.iterrows():
                                        st.markdown(f'<div style="display:flex; justify-content:space-between; padding:5px 10px; border-bottom:1px solid #333;"><div>🏢 {row["Firma"]}</div><div>{int(row["Kolicina"])} kom</div></div>', unsafe_allow_html=True)
                else: st.info(f"Nema narudžbi za {d_sel}")

        with t_a2:
            st.subheader("📝 Uređivanje Menija")
            od_m = st.radio("Meni:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"f_adm_{od_m}"):
                c1, c2, c3 = st.columns(3)
                v_s = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Sedmica'].empty else ""
                v_r = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Rok'].empty else ""
                v_k = df_m[df_m['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Kuvar'].empty else ""
                n_s = c1.text_input("📅 Period:", value=v_s)
                n_r = c2.text_input("⏰ Rok:", value=v_r)
                n_k = c3.text_input("👨‍🍳 Kuvar:", value=v_k)
                novi_p = [{"Dan": "Sedmica", "Jelo": n_s}, {"Dan": "Rok", "Jelo": n_r}, {"Dan": "Kuvar", "Jelo": n_k}]
                for dan in dani_std:
                    st.markdown(f"**{dan}**")
                    jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    for i in range(3):
                        pj = jela[i] if i < len(jela) else ""
                        nj = st.text_input(f"{dan} - {i+1}", value=pj, key=f"e_{od_m}_{dan}_{i}")
                        if nj.strip(): novi_p.append({"Dan": dan, "Jelo": nj.strip()})
                if st.form_submit_button("💾 SAČUVAJ"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi_p))
                    st.success("Meni sačuvan!"); time.sleep(1); st.rerun()

        with t_a3:
            st.subheader("⭐ Rang lista kuvara")
            _, pk = izracunaj_prosjeke()
            for kuvar, ocjena in pk.items():
                st.markdown(f"👨‍🍳 **{kuvar}**: {ocjena} ⭐")
            st.divider()
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

        with t_a4:
            st.subheader("🔄 Rotacija")
            if st.button("🚀 ROTIRAJ (Naredna -> Ova)"):
                df_next = ucitaj_sheet("Meni_Naredni")
                df_sve = ucitaj_sheet("Sheet1")
                if not df_next.empty: conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                if not df_sve.empty:
                    df_nar = df_sve[df_sve['Dan'].str.startswith("Naredna")].copy()
                    df_nar['Dan'] = df_nar['Dan'].str.replace("Naredna", "Ova")
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=df_nar)
                st.success("Rotirano!"); time.sleep(1); st.rerun()

    # --- 6. KORISNIČKI PANEL (Tehnički tvoj kod, vizuelno sl1) ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_t, t_n, t_h, t_o = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija", "⭐ Ocijeni"])
        pj, _ = izracunaj_prosjeke()

        def prikazi_klijent(sh_name, prefix, lock):
            df_m = ucitaj_sheet(sh_name)
            df_sve = ucitaj_sheet("Sheet1")
            
            # Obojene kartice na vrhu
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m[df_m['Dan']=='Sedmica'].empty else "N/A"
            r = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m[df_m['Dan']=='Rok'].empty else "N/A"
            k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m[df_m['Dan']=='Kuvar'].empty else "N/A"
            st.markdown(f"""<div class="info-container">
                <div class="info-card blue-card">📅 Period<br>{s}</div>
                <div class="info-card yellow-card">⏰ Rok<br>{r}</div>
                <div class="info-card green-card">👨‍🍳 Kuvar<br>{k}</div>
            </div>""", unsafe_allow_html=True)

            with st.form(f"f_{prefix}"):
                unose = []
                for dan in dani_std:
                    idx = dani_std.index(dan)
                    onemoguci = False if danasnji_dan_index == 6 else (lock and danasnji_dan_index >= idx)
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan} {'🔒' if onemoguci else '🔓'}")
                        jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                        for j in jela:
                            p = pj.get(j, "")
                            st.markdown(f'<div class="dish-title">{j} {f"(⭐ {p})" if p else ""}</div>', unsafe_allow_html=True)
                            c1, c2, c3 = st.columns(3)
                            mask = (df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{prefix}-{dan}") & (df_sve['Jelo']==j) if not df_sve.empty else None
                            def get_v(smj):
                                if mask is not None:
                                    res = df_sve[mask & (df_sve['Smjena']==smj)]['Kolicina'].sum()
                                    return int(res)
                                return 0
                            k1 = c1.number_input("I Smj", 0, 100, get_v("I"), key=f"{prefix}_{dan}_{j}_1", disabled=onemoguci)
                            k2 = c2.number_input("II Smj", 0, 100, get_v("II"), key=f"{prefix}_{dan}_{j}_2", disabled=onemoguci)
                            k3 = c3.number_input("III Smj", 0, 100, get_v("III"), key=f"{prefix}_{dan}_{j}_3", disabled=onemoguci)
                            for val, s_nm in zip([k1, k2, k3], ["I", "II", "III"]):
                                if val >= 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(val), "Smjena": s_nm})
                if st.form_submit_button("🚀 SAČUVAJ NARUDŽBU", use_container_width=True):
                    df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))] if not df_sve.empty else pd.DataFrame()
                    final = pd.concat([df_ostali, pd.DataFrame([u for u in unose if u['Kolicina'] > 0])], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final)
                    st.success("Spremljeno!"); st.rerun()

        with t_t: prikazi_klijent("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_klijent("Meni_Naredni", "Naredna", False)
        with t_h:
            st.subheader("📜 Istorija")
            st.dataframe(ucitaj_sheet("Sheet1")[lambda df: df['Firma']==st.session_state['user']], use_container_width=True, hide_index=True)
        with t_o:
            st.subheader("⭐ Ocijeni jelo")
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            k_t = df_m_t[df_m_t['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar'].empty else "N/A"
            sva_j = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist()
            with st.form("f_ocj"):
                j_o = st.selectbox("Jelo:", sva_j)
                oc = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                km = st.text_area("Komentar:")
                if st.form_submit_button("Pošalji"):
                    df_o = ucitaj_sheet("Ocjene")
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o, pd.DataFrame([{"Firma":st.session_state['user'], "Jelo":j_o, "Ocjena":oc, "Komentar":km, "Kuvar":k_t}])], ignore_index=True))
                    st.success("Hvala!"); st.rerun()
