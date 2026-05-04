import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Management", layout="centered")

# CSS za vizuelni identitet sa slika (boje kartica i sakrivanje Streamlit elemenata)
st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    .stAppDeployButton {display: none !important;}
    .info-card {
        padding: 15px; border-radius: 10px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px;
    }
    .blue-card { background-color: #1e3a5f; border: 1px solid #3b82f6; }
    .yellow-card { background-color: #3e3e10; border: 1px solid #ca8a04; }
    .green-card { background-color: #143e2a; border: 1px solid #16a34a; }
    </style>
""", unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. FUNKCIJE SA ZAŠTITOM OD PRAZNIH TABELA ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Dan", "Jelo"])
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=["Dan", "Jelo"])

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    p_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    p_kuvari = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return p_jela, p_kuvari

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
    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene & Kuvari", "🔄 Reset"])
        
        with t_a1:
            st.subheader("👨‍🍳 Nalozi za kuhinju")
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty and "Dan" in df_nar.columns:
                d_sel = st.selectbox("Prikaži narudžbe za dan:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                if not prikaz.empty: st.table(prikaz)
                else: st.info(f"Nema narudžbi za {d_sel}")
            else: st.info("Tabela narudžbi (Sheet1) je trenutno prazna.")

        with t_a2: # Izgled kao sl3.png
            st.subheader("Izmijeni jela, rokove i kuvare")
            od_m = st.radio("Koji meni mijenjaš?", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            
            # Sigurno izvlačenje meta podataka
            v_sed = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Sedmica'].empty else ""
            v_rok = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Rok'].empty else ""
            v_kuv = df_m[df_m['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Kuvar'].empty else ""

            with st.form(f"admin_form_{od_m}"):
                c1, c2, c3 = st.columns(3)
                n_sed = c1.text_input("📅 Period:", value=v_sed)
                n_rok = c2.text_input("⏰ Rok:", value=v_rok)
                n_kuv = c3.text_input("👨‍🍳 Glavni kuvar:", value=v_kuv)
                
                nova_data = [{"Dan": "Sedmica", "Jelo": n_sed}, {"Dan": "Rok", "Jelo": n_rok}, {"Dan": "Kuvar", "Jelo": n_kuv}]
                for dan in dani_std:
                    st.write(f"**{dan}**")
                    postojeca = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    for i in range(3):
                        val = postojeca[i] if i < len(postojeca) else ""
                        nj = st.text_input(f"{dan} - Jelo {i+1}", value=val, key=f"edt_{od_m}_{dan}_{i}")
                        if nj: nova_data.append({"Dan": dan, "Jelo": nj})
                
                if st.form_submit_button("💾 SAČUVAJ"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(nova_data))
                    st.success("Meni sačuvan!"); time.sleep(1); st.rerun()

        with t_a3: # Izgled kao sl2.png
            st.subheader("⭐ Rang lista kuvara")
            _, pk = izracunaj_prosjeke()
            for k, v in pk.items(): st.markdown(f"👨‍🍳 **{k}**: {v} ⭐")
            st.divider()
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

        with t_a4:
            if st.button("🚀 ROTIRAJ SEDMICE (Naredna -> Ova)"):
                df_next = ucitaj_sheet("Meni_Naredni")
                if not df_next.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                    st.success("Rotacija završena!"); time.sleep(1); st.rerun()

    # --- 6. KORISNIČKI PANEL (Izgled kao sl1.png) ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        tabs = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija", "⭐ Ocijeni"])
        pj, _ = izracunaj_prosjeke()

        def render_klijent(sh_name, prefix, lock):
            df_m = ucitaj_sheet(sh_name)
            if df_m.empty: 
                st.warning("Meni nije postavljen.")
                return

            # Kartice sa vrha sl1.png
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m[df_m['Dan']=='Sedmica'].empty else "N/A"
            r = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m[df_m['Dan']=='Rok'].empty else "N/A"
            k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m[df_m['Dan']=='Kuvar'].empty else "N/A"
            
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="info-card blue-card">📅 Period: {s}</div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="info-card yellow-card">⏰ Rok: {r}</div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="info-card green-card">👨‍🍳 Kuvar: {k}</div>', unsafe_allow_html=True)

            df_sve = ucitaj_sheet("Sheet1")
            with st.form(f"form_{prefix}"):
                unose = []
                for dan in dani_std:
                    idx = dani_std.index(dan)
                    onemoguci = (lock and danasnji_dan_index >= idx)
                    status = "🔒" if onemoguci else "🔓"
                    
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan} {status}")
                        jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                        for j in jela:
                            pr = pj.get(j, None)
                            st.write(f"**{j}** {'(⭐ '+str(pr)+')' if pr else '(🆕)'}")
                            col1, col2, col3 = st.columns(3)
                            
                            # Vraćanje starih vrijednosti ako postoje
                            mask = (df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{prefix}-{dan}") & (df_sve['Jelo']==j) if not df_sve.empty else False
                            def get_k(smj):
                                if not df_sve.empty:
                                    v = df_sve[mask & (df_sve['Smjena']==smj)]['Kolicina'].tolist()
                                    return int(v[0]) if v else 0
                                return 0

                            k1 = col1.number_input("I Smj", 0, 100, get_k("I"), key=f"n_{prefix}_{dan}_{j}_1", disabled=onemoguci)
                            k2 = col2.number_input("II Smj", 0, 100, get_k("II"), key=f"n_{prefix}_{dan}_{j}_2", disabled=onemoguci)
                            k3 = col3.number_input("III Smj", 0, 100, get_k("III"), key=f"n_{prefix}_{dan}_{j}_3", disabled=onemoguci)
                            for val, s_name in zip([k1, k2, k3], ["I", "II", "III"]):
                                if val > 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(val), "Smjena": s_name})
                
                if st.form_submit_button("🚀 SAČUVAJ"):
                    # Brišemo stare narudžbe za taj prefix i firmu, pa dodajemo nove
                    if not df_sve.empty:
                        df_sve = df_sve[~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))]
                    final = pd.concat([df_sve, pd.DataFrame(unose)], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final)
                    st.success("Sačuvano!"); st.rerun()

        with tabs[0]: render_klijent("Meni_Trenutni", "Ova", True)
        with tabs[1]: render_klijent("Meni_Naredni", "Naredna", False)
        with tabs[3]: # Ocjenjivanje
            st.subheader("⭐ Ocijeni obrok")
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            kuv_t = df_m_t[df_m_t['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar'].empty else "N/A"
            sva_j = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist()
            with st.form("f_o"):
                j_o = st.selectbox("Izaberi jelo:", sva_j)
                oc = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                km = st.text_area("Komentar:")
                if st.form_submit_button("Pošalji"):
                    df_o = ucitaj_sheet("Ocjene")
                    nova = pd.DataFrame([{"Firma": st.session_state['user'], "Jelo": j_o, "Ocjena": oc, "Komentar": km, "Kuvar": kuv_t}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o, nova], ignore_index=True))
                    st.success("Hvala!"); st.rerun()
