import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Sistem", layout="centered")

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]

# --- 2. KORISNICI (Originalni podaci) ---
users = {
    "admin": "admin123",
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# --- 3. DINAMIČKI MENI ---
try:
    df_meni_raw = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni", ttl=0)
    df_meni_raw['Dan'] = df_meni_raw['Dan'].astype(str).str.strip()
except:
    st.error("Greška: List 'Meni' mora imati kolone 'Dan', 'Jelo', 'Tip'.")
    st.stop()

# --- 4. LOGIN SISTEM (CENTRALNI) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava za Catering</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Korisničko ime")
        p = st.text_input("Lozinka", type="password")
        if st.button("Prijavi se", use_container_width=True):
            if u in users and users[u] == p:
                st.session_state["logged_in"] = True
                st.session_state["user"] = u
                st.rerun()
            else:
                st.error("Pogrešni podaci")
else:
    # Sidebar za odjavu
    st.sidebar.write(f"Ulogovani ste: **{st.session_state['user']}**")
    if st.sidebar.button("Odjavi se", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel")
        t_adm1, t_adm2, t_adm3 = st.tabs(["📊 Kuhinja", "📝 Meni Editor", "⚙️ Reset"])
        
        with t_adm1:
            df_n = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
            if not df_n.empty:
                d_sel = st.selectbox("Izaberi dan za kuhanje:", dani_std)
                # Prikaz narudžbi za TRENUTNU sedmicu
                prikaz = df_n[df_n['Dan'] == f"Trenutna-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                st.table(prikaz)
            else: st.info("Nema narudžbi.")

        with t_adm2:
            edited = st.data_editor(df_meni_raw, use_container_width=True, hide_index=True)
            if st.button("💾 SAČUVAJ IZMJENE MENIJA"):
                conn.update(spreadsheet=spreadsheet_url, worksheet="Meni", data=edited)
                st.success("Meni ažuriran!")

        with t_adm3:
            if st.button("🗑️ RESETUJ SVE NARUDŽBE (Sheet1)"):
                conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.DataFrame(columns=["Firma","Dan","Jelo","Kolicina","Smjena"]))
                st.success("Tabela ispražnjena!")

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        
        tab_t, tab_n, tab_h = st.tabs(["🍱 Trenutna Sedmica", "🚀 Naredna Sedmica", "📜 Istorija"])
        
        try:
            df_sve = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
            moja_n = df_sve[df_sve['Firma'] == st.session_state['user']]
        except: df_sve, moja_n = pd.DataFrame(), pd.DataFrame()

        def prikazi_formu_sedmice(tip_sedmice, prefix):
            df_v = df_meni_raw[df_meni_raw['Tip'] == tip_sedmice]
            with st.form(f"forma_{prefix}"):
                unose = []
                for dan in dani_std:
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}")
                        jela_dan = df_v[df_v['Dan'] == dan]['Jelo'].tolist()
                        for jelo in jela_dan:
                            st.markdown(f"**{jelo}**")
                            c1, c2, c3 = st.columns(3)
                            
                            def get_v(d, j, s):
                                if not moja_n.empty:
                                    f = moja_n[(moja_n['Dan']==f"{prefix}-{d}") & (moja_n['Jelo']==j) & (moja_n['Smjena']==s)]
                                    return int(f['Kolicina'].iloc[0]) if not f.empty else 0
                                return 0

                            k1 = c1.number_input("I Smjena", 0, 100, step=1, value=get_v(dan, jelo, "I"), key=f"{prefix}_{dan}_{jelo}_1")
                            k2 = c2.number_input("II Smjena", 0, 100, step=1, value=get_v(dan, jelo, "II"), key=f"{prefix}_{dan}_{jelo}_2")
                            k3 = c3.number_input("III Smjena", 0, 100, step=1, value=get_v(dan, jelo, "III"), key=f"{prefix}_{dan}_{jelo}_3")
                            
                            for k, smj in zip([k1, k2, k3], ["I", "II", "III"]):
                                unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": jelo, "Kolicina": int(k), "Smjena": smj})
                
                if st.form_submit_button(f"🚀 SAČUVAJ {tip_sedmice.upper()}", use_container_width=True):
                    dani_za_prefix = [f"{prefix}-{d}" for d in dani_std]
                    mask = ~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].isin(dani_za_prefix)))
                    novi_podaci = [n for n in unose if n['Kolicina'] > 0]
                    final_df = pd.concat([df_sve[mask] if not df_sve.empty else df_sve, pd.DataFrame(novi_podaci)], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final_df)
                    st.success("Narudžba sačuvana!")
                    st.rerun()

        with tab_t: prikazi_formu_sedmice("Trenutna", "Trenutna")
        with tab_n: prikazi_formu_sedmice("Naredna", "Naredna")
        with tab_h: st.dataframe(moja_n, use_container_width=True, hide_index=True)
