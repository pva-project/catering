import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Management", layout="centered")
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. FUNKCIJE ZA ČITANJE/PISANJE ---
def ucitaj_meni(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df
    except:
        return pd.DataFrame(columns=["Dan", "Jelo"])

# --- 4. LOGIN ---
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
    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t1, t2, t3 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "🔄 Kraj Sedmice"])
        
        with t2:
            st.subheader("Izmijeni jela direktno")
            odabir_m = st.radio("Koji meni mijenjaš?", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_meni(odabir_m)
            
            with st.form(f"form_izmjena_{odabir_m}"):
                nova_lista = []
                for dan in dani_std:
                    st.write(f"**{dan}**")
                    # Uzimamo postojeće jelo iz tabele ili prazno
                    postojeca_jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    j1 = st.text_input(f"Jelo 1", value=postojeca_jela[0] if len(postojeca_jela) > 0 else "", key=f"{dan}_1")
                    j2 = st.text_input(f"Jelo 2", value=postojeca_jela[1] if len(postojeca_jela) > 1 else "", key=f"{dan}_2")
                    j3 = st.text_input(f"Jelo 3", value=postojeca_jela[2] if len(postojeca_jela) > 2 else "", key=f"{dan}_3")
                    
                    for j in [j1, j2, j3]:
                        if j.strip() != "": nova_lista.append({"Dan": dan, "Jelo": j})
                
                if st.form_submit_button("💾 SAČUVAJ IZMJENE"):
                    novi_df = pd.DataFrame(nova_lista)
                    conn.update(spreadsheet=spreadsheet_url, worksheet=odabir_m, data=novi_df)
                    st.success(f"Uspješno sačuvano u {odabir_m}!")
                    st.rerun()

        with t1:
            df_nar = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
            if not df_nar.empty:
                d_sel = st.selectbox("Dan za kuhanje:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                st.table(prikaz)
            else: st.info("Nema narudžbi.")

        with t3:
            if st.button("🚀 IZVRŠI ROTACIJU (Naredna -> Trenutna)"):
                df_next = ucitaj_meni("Meni_Naredni")
                conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.DataFrame(columns=["Firma","Dan","Jelo","Kolicina","Smjena"]))
                st.success("Sedmice su rotirane, narudžbe resetovane!")
                st.rerun()

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.sidebar.button("Odjavi se", on_click=lambda: st.session_state.update({"logged_in": False}))
        st.title(f"🍴 {st.session_state['user']}")
        t_t, t_n, t_h = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija"])
        
        df_t = ucitaj_meni("Meni_Trenutni")
        df_n = ucitaj_meni("Meni_Naredni")
        
        try:
            df_sve = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
            moja_n = df_sve[df_sve['Firma'] == st.session_state['user']]
        except: df_sve, moja_n = pd.DataFrame(), pd.DataFrame()

        def prikazi_formu(df_meni, prefix, zakljucaj):
            with st.form(f"f_{prefix}"):
                unose = []
                for dan in dani_std:
                    onemoguci = False
                    status = " 🔓"
                    if zakljucaj and danasnji_dan_index <= 5:
                        if danasnji_dan_index >= dani_std.index(dan): onemoguci, status = True, " 🔒"

                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}{status}")
                        jela = df_meni[df_meni['Dan'] == dan]['Jelo'].tolist()
                        for j in jela:
                            st.write(f"**{j}**")
                            c1, c2, c3 = st.columns(3)
                            def get_v(d, jl, s):
                                if not moja_n.empty:
                                    v = moja_n[(moja_n['Dan']==f"{prefix}-{d}") & (moja_n['Jelo']==jl) & (moja_n['Smjena']==s)]['Kolicina'].tolist()
                                    return int(v) if v else 0
                                return 0
                            k1 = c1.number_input("I Smjena", 0, 100, get_v(dan, j, "I"), key=f"{prefix}_{dan}_{j}_1", disabled=onemoguci)
                            k2 = c2.number_input("II Smjena", 0, 100, get_v(dan, j, "II"), key=f"{prefix}_{dan}_{j}_2", disabled=onemoguci)
                            k3 = c3.number_input("III Smjena", 0, 100, get_v(dan, j, "III"), key=f"{prefix}_{dan}_{j}_3", disabled=onemoguci)
                            for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                                unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(k), "Smjena": s})
                
                if st.form_submit_button("🚀 SAČUVAJ"):
                    pref_dani = [f"{prefix}-{d}" for d in dani_std]
                    mask = ~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].isin(pref_dani)))
                    final = pd.concat([df_sve[mask] if not df_sve.empty else df_sve, pd.DataFrame([n for n in unose if n['Kolicina']>0])], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final)
                    st.success("Sačuvano!")
                    st.rerun()

        with t_t: prikazi_formu(df_t, "Ova", True)
        with t_n: prikazi_formu(df_n, "Naredna", False)
        with t_h: st.dataframe(moja_n, use_container_width=True, hide_index=True)
