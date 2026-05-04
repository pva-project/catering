import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I PUN STIL ---
st.set_page_config(page_title="Catering Management", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    .block-container {padding-top: 1rem !important;}
    
    /* Info kartice na vrhu */
    .info-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }
    .info-card { flex: 1; padding: 15px; border-radius: 10px; text-align: center; color: white; font-weight: bold; font-size: 0.9rem; }
    .blue-card { background-color: #1e3a5f; border: 1px solid #3b82f6; }
    .yellow-card { background-color: #3e3e10; border: 1px solid #ca8a04; }
    .green-card { background-color: #143e2a; border: 1px solid #16a34a; }
    
    /* Admin stilovi */
    .smjena-header { background-color: #333; padding: 10px; border-radius: 5px; color: white; font-weight: bold; margin-top: 20px; }
    .jelo-red { background-color: #1E1E1E; padding: 8px; border-radius: 5px; margin-top: 10px; font-weight: bold; color: #FF4B4B; }
    .ukupno-zeleno { text-align: right; padding: 5px; font-weight: bold; color: #00FF00; font-size: 1.1rem; border-top: 1px dashed #444; }
    </style>
""", unsafe_allow_html=True)

# --- 2. POVEZIVANJE I PODACI ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    pj = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    pk = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return pj, pk

# --- 4. PRIJAVA ---
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
            else: st.error("Pogrešni podaci")
else:
    # --- 5. ADMIN PANEL (Vraćen sav sadržaj) ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja (Zbir)", "📝 Izmjena Menija", "⭐ Ocjene & Kuvari", "🔄 Reset/Rotacija"])
        
        with t_a1: # KUHINJA SA ZELENIM ZBIROM
            df_nar = ucitaj_sheet("Sheet1")
            d_sel = st.selectbox("Izaberi dan:", dani_std)
            prikaz_df = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"] if not df_nar.empty else pd.DataFrame()
            if not prikaz_df.empty:
                for smj in ["I", "II", "III"]:
                    smj_data = prikaz_df[prikaz_df['Smjena'] == smj]
                    if not smj_data.empty:
                        st.markdown(f'<div class="smjena-header">🕒 SMJENA {smj}</div>', unsafe_allow_html=True)
                        for jelo, jelo_data in smj_data.groupby("Jelo"):
                            st.markdown(f'<div class="jelo-red">{jelo}</div>', unsafe_allow_html=True)
                            for _, r in jelo_data.iterrows():
                                st.write(f"🏢 {r['Firma']}: {int(r['Kolicina'])} kom")
                            ukupno = int(jelo_data['Kolicina'].sum())
                            st.markdown(f'<div class="ukupno-zeleno">UKUPNO {jelo}: {ukupno}</div>', unsafe_allow_html=True)
            else: st.info("Nema narudžbi.")

        with t_a2: # UREĐIVANJE MENIJA
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
                    jela_postojeća = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    for i in range(3):
                        v_j = jela_postojeća[i] if i < len(jela_postojeća) else ""
                        nj = st.text_input(f"{dan} - {i+1}", value=v_j, key=f"e_{od_m}_{dan}_{i}")
                        if nj.strip(): novi_p.append({"Dan": dan, "Jelo": nj.strip()})
                if st.form_submit_button("💾 SAČUVAJ"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi_p))
                    st.success("Meni sačuvan!"); time.sleep(1); st.rerun()

        with t_a3: # OCJENE I KUVARI (Nema više crnog)
            st.subheader("⭐ Statistika")
            df_o = ucitaj_sheet("Ocjene")
            if not df_o.empty:
                _, pk = izracunaj_prosjeke()
                if pk:
                    cols = st.columns(len(pk))
                    for i, (kuvar, ocj) in enumerate(pk.items()):
                        cols[i].metric(f"👨‍🍳 {kuvar}", f"{ocj} ⭐")
                st.divider()
                st.dataframe(df_o, use_container_width=True, hide_index=True)
            else: st.info("Nema ocjena.")

        with t_a4: # ROTACIJA
            if st.button("🚀 ROTIRAJ (Prebaci Narednu u Trenutnu)"):
                df_next = ucitaj_sheet("Meni_Naredni")
                if not df_next.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                    # Opciono: prebacivanje narudžbi u Sheet1 sa "Naredna-" na "Ova-"
                    df_all = ucitaj_sheet("Sheet1")
                    if not df_all.empty:
                        df_all['Dan'] = df_all['Dan'].str.replace("Naredna-", "Ova-")
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=df_all)
                    st.success("Rotirano!"); time.sleep(1); st.rerun()

    # --- 6. KLIJENTSKI PANEL (Sve vraćeno i popravljeno) ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_t, t_n, t_h, t_o = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija", "⭐ Ocijeni"])
        pj, _ = izracunaj_prosjeke()

        def prikazi_klijent(sh_name, prefix, lock):
            df_m = ucitaj_sheet(sh_name)
            df_sve = ucitaj_sheet("Sheet1")
            
            # Kartice
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
                            st.markdown(f"**{j}** {f'(⭐ {pj.get(j, bytes)})' if pj.get(j) else ''}")
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
                
                if st.form_submit_button("💾 SAČUVAJ NARUDŽBU", use_container_width=True):
                    df_ostali = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))] if not df_sve.empty else pd.DataFrame()
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_ostali, pd.DataFrame(unose)], ignore_index=True))
                    st.success("Spremljeno!"); time.sleep(1); st.rerun()

        with t_t: prikazi_klijent("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_klijent("Meni_Naredni", "Naredna", False)
        with t_h:
            st.dataframe(ucitaj_sheet("Sheet1")[lambda df: df['Firma']==st.session_state['user']] if not ucitaj_sheet("Sheet1").empty else pd.DataFrame(), use_container_width=True, hide_index=True)
        with t_o:
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            k_t = df_m_t[df_m_t['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m_t.empty and not df_m_t[df_m_t['Dan'] == 'Kuvar'].empty else "N/A"
            jela_za_ocjenu = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist() if not df_m_t.empty else []
            with st.form("f_ocj"):
                j_o = st.selectbox("Izaberi jelo:", jela_za_ocjenu)
                oc = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                km = st.text_area("Komentar:")
                if st.form_submit_button("Pošalji ocjenu"):
                    df_o = ucitaj_sheet("Ocjene")
                    novi_r = pd.DataFrame([{"Firma": st.session_state['user'], "Jelo": j_o, "Ocjena": oc, "Komentar": km, "Kuvar": k_t}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o, novi_r], ignore_index=True))
                    st.success("Hvala!"); time.sleep(1); st.rerun()
