import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Management", layout="centered")
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
    except: return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    prosjeci_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    prosjeci_kuvara = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict()
    return prosjeci_jela, prosjeci_kuvara

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
    st.sidebar.write(f"Korisnik: **{st.session_state['user']}**")
    if st.sidebar.button("Odjavi se", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene & Kuvari", "🔄 Reset"])
        
        with t_a2:
            st.subheader("Uredi jela, rokove i kuvare")
            odabir_m = st.radio("Meni:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(odabir_m)
            v_sed = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if 'Sedmica' in df_m['Dan'].values else ""
            v_rok = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if 'Rok' in df_m['Dan'].values else ""
            v_kuvar = df_m[df_m['Dan'] == 'Kuvar']['Jelo'].values[0] if 'Kuvar' in df_m['Dan'].values else ""

            with st.form(f"form_admin_{odabir_m}"):
                c1, c2, c3 = st.columns(3)
                n_sed = c1.text_input("📅 Period:", value=v_sed)
                n_rok = c2.text_input("⏰ Rok:", value=v_rok)
                n_kuvar = c3.text_input("👨‍🍳 Glavni kuvar:", value=v_kuvar)
                
                nova_lista = [{"Dan": "Sedmica", "Jelo": n_sed}, {"Dan": "Rok", "Jelo": n_rok}, {"Dan": "Kuvar", "Jelo": n_kuvar}]
                for dan in dani_std:
                    st.write(f"**{dan}**")
                    postojeca = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    j1 = st.text_input(f"Jelo 1", value=postojeca[0] if len(postojeca) > 0 else "", key=f"{dan}_1")
                    j2 = st.text_input(f"Jelo 2", value=postojeca[1] if len(postojeca) > 1 else "", key=f"{dan}_2")
                    j3 = st.text_input(f"Jelo 3", value=postojeca[2] if len(postojeca) > 2 else "", key=f"{dan}_3")
                    for j in [j1, j2, j3]:
                        if j.strip(): nova_lista.append({"Dan": dan, "Jelo": j.strip()})
                if st.form_submit_button("💾 SAČUVAJ SVE"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=odabir_m, data=pd.DataFrame(nova_lista))
                    st.success("Sačuvano!"); time.sleep(1); st.rerun()

        with t_a3:
            st.subheader("⭐ Rang lista kuvara")
            _, p_kuvari = izracunaj_prosjeke()
            if p_kuvari:
                for k, v in p_kuvari.items():
                    st.write(f"👨‍🍳 **{k}**: {v} ⭐")
            
            st.divider()
            st.subheader("Sve ocjene")
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

        # (Kuhinja i Reset tabovi ostaju isti kao prije...)
        with t_a1:
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                d_sel = st.selectbox("Dan za kuhanje:", dani_std)
                st.table(df_nar[df_nar['Dan'] == f"Ova-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index())
        with t_a4:
            if st.button("🚀 ROTACIJA SEDMICA"):
                df_next = ucitaj_sheet("Meni_Naredni")
                conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.DataFrame(columns=["Firma","Dan","Jelo","Kolicina","Smjena"]))
                st.success("Rotirano!"); time.sleep(1); st.rerun()

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_t, t_n, t_h, t_o = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija", "⭐ Ocijeni"])
        
        p_jela, _ = izracunaj_prosjeke()

        def prikazi_formu(sheet_name, prefix, zakljucaj):
            df_m = ucitaj_sheet(sheet_name)
            if df_m.empty: return
            inf_sed = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if 'Sedmica' in df_m['Dan'].values else "N/A"
            inf_rok = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if 'Rok' in df_m['Dan'].values else "N/A"
            inf_kuvar = df_m[df_m['Dan'] == 'Kuvar']['Jelo'].values[0] if 'Kuvar' in df_m['Dan'].values else "N/A"
            
            c1, c2, c3 = st.columns(3)
            c1.info(f"📅 **Period:**\n{inf_sed}")
            c2.warning(f"⏰ **Rok:**\n{inf_rok}")
            c3.success(f"👨‍🍳 **Kuvar:**\n{inf_kuvar}")

            df_sve = ucitaj_sheet("Sheet1")
            with st.form(f"f_{prefix}"):
                unose = []
                for dan in dani_std:
                    idx = dani_std.index(dan)
                    onemoguci = (zakljucaj and danasnji_dan_index <= 5 and danasnji_dan_index >= idx)
                    status = " 🔒" if onemoguci else " 🔓"
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}{status}")
                        jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                        for j in jela:
                            prosjek = p_jela.get(j, None)
                            oznaka = f" (⭐ {prosjek})" if prosjek else " (🆕)"
                            st.write(f"**{j}{oznaka}**")
                            col1, col2, col3 = st.columns(3)
                            def get_v(d, jl, s):
                                if not df_sve.empty:
                                    v = df_sve[(df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{prefix}-{d}") & (df_sve['Jelo']==jl) & (df_sve['Smjena']==s)]['Kolicina'].tolist()
                                    return int(v[0]) if v else 0
                                return 0
                            k1 = col1.number_input("I Smjena", 0, 100, get_v(dan, j, "I"), key=f"{prefix}_{dan}_{j}_1", disabled=onemoguci)
                            k2 = col2.number_input("II Smjena", 0, 100, get_v(dan, j, "II"), key=f"{prefix}_{dan}_{j}_2", disabled=onemoguci)
                            k3 = col3.number_input("III Smjena", 0, 100, get_v(dan, j, "III"), key=f"{prefix}_{dan}_{j}_3", disabled=onemoguci)
                            for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                                if k >= 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(k), "Smjena": s})
                
                if st.form_submit_button("🚀 SAČUVAJ", use_container_width=True):
                    mask = ~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].astype(str).str.startswith(prefix)))
                    final = pd.concat([df_sve[mask] if not df_sve.empty else df_sve, pd.DataFrame([n for n in unose if n['Kolicina']>0])], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final)
                    st.success("Narudžba sačuvana!"); st.balloons(); time.sleep(1); st.rerun()

        with t_t: prikazi_formu("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_formu("Meni_Naredni", "Naredna", False)
        with t_h: st.dataframe(ucitaj_sheet("Sheet1")[lambda df: df['Firma'] == st.session_state['user']], use_container_width=True, hide_index=True)
        
        with t_o:
            st.subheader("⭐ Ocijeni obrok i kuvara")
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            kuvar_trenutni = df_m_t[df_m_t['Dan'] == 'Kuvar']['Jelo'].values[0] if 'Kuvar' in df_m_t['Dan'].values else "Nepoznato"
            sva_jela = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist()
            
            st.write(f"Ove sedmice kuha za vas: **{kuvar_trenutni}**")
            with st.form("forma_ocjena", clear_on_submit=True):
                od_jelo = st.selectbox("Jelo:", sva_jela)
                ocj = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                kom = st.text_area("Komentar:")
                if st.form_submit_button("📩 Pošalji ocjenu"):
                    df_o_p = ucitaj_sheet("Ocjene")
                    nova_o = pd.DataFrame([{"Firma": st.session_state['user'], "Jelo": od_jelo, "Ocjena": ocj, "Komentar": kom, "Kuvar": kuvar_trenutni}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o_p, nova_o], ignore_index=True))
                    st.success("Hvala na ocjeni!"); time.sleep(1); st.rerun()
