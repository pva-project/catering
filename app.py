import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Sistem", layout="wide")
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]

# --- 2. LOGIN ---
users = {"admin": "admin123", "Lattonedil": "lat1", "PVA Group": "pva1", "Esintec": "esi1", "ActivBH": "act1"}

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava</h1>", unsafe_allow_html=True)
    u = st.text_input("Korisnik")
    p = st.text_input("Lozinka", type="password")
    if st.button("Prijavi se", use_container_width=True):
        if u in users and users[u] == p:
            st.session_state["logged_in"], st.session_state["user"] = True, u
            st.rerun()
        else: st.error("Pogrešni podaci")
else:
    # --- 3. ČITANJE MENIJA ---
    try:
        df_meni_raw = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni", ttl=0)
    except:
        st.error("Greška: Provjerite da li list 'Meni' ima kolone 'Dan', 'Jelo', 'Tip'.")
        st.stop()

    # --- 4. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel")
        t1, t2, t3 = st.tabs(["📊 Kuhinja", "📝 Meni Editor", "🔄 Rotacija Sedmica"])
        
        with t1:
            df_n = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
            if not df_n.empty:
                d_sel = st.selectbox("Izaberi dan za kuhanje:", dani_std)
                # Admin vidi narudžbe za "Trenutnu" jer to kuha
                zbir = df_n[df_n['Dan'] == f"Trenutna-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                st.table(zbir)
            else: st.info("Nema narudžbi.")

        with t2:
            st.subheader("Uredi jela za obje sedmice")
            edited = st.data_editor(df_meni_raw, use_container_width=True, hide_index=True)
            if st.button("💾 SAČUVAJ IZMJENE"):
                conn.update(spreadsheet=spreadsheet_url, worksheet="Meni", data=edited)
                st.success("Tabela menija ažurirana!")

        with t3:
            st.subheader("Kraj sedmice i rotacija")
            st.warning("Ovo dugme će narudžbe iz 'Naredne' sedmice prebaciti u 'Trenutnu' i isprazniti sistem za nove narudžbe.")
            if st.button("🔄 ROTIRAJ SEDMICE I RESETUJ"):
                # 1. Arhiviranje ili Reset Sheet1
                conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.DataFrame(columns=["Firma","Dan","Jelo","Kolicina","Smjena"]))
                # 2. Rotacija jela u Meni tabeli: Naredna postaje Trenutna
                df_meni_raw.loc[df_meni_raw['Tip'] == 'Trenutna', 'Jelo'] = "---" # Brišemo staru trenutnu
                # Ovdje bi išla logika zamjene, ali najlakše je da ti rucno u Editoru samo promjenis nazive sedmica
                st.success("Sistem resetovan. Sada u 'Meni Editoru' kopirajte jela iz Naredne u Trenutnu.")

    # --- 5. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        
        tab_trenutna, tab_naredna, tab_hist = st.tabs(["🍱 Trenutna Sedmica", "🚀 Naredna Sedmica", "📜 Istorija"])
        
        try:
            df_sve = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
            moja_n = df_sve[df_sve['Firma'] == st.session_state['user']]
        except: df_sve, moja_n = pd.DataFrame(), pd.DataFrame()

        def prikazi_meni(tip_sedmice, prefix):
            df_vidljiva = df_meni_raw[df_meni_raw['Tip'] == tip_sedmice]
            with st.form(f"forma_{prefix}"):
                unose = []
                for dan in dani_std:
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}")
                        jela_dan = df_vidljiva[df_vidljiva['Dan'] == dan]['Jelo'].tolist()
                        for jelo in jela_dan:
                            st.write(f"**{jelo}**")
                            c1, c2, c3 = st.columns(3)
                            
                            def get_v(d, j, s):
                                if not moja_n.empty:
                                    f = moja_n[(moja_n['Dan']==f"{prefix}-{d}") & (moja_n['Jelo']==j) & (moja_n['Smjena']==s)]
                                    return int(f['Kolicina'].iloc[0]) if not f.empty else 0
                                return 0

                            k1 = c1.number_input("I Smjena", 0, 100, get_v(dan, jelo, "I"), key=f"{prefix}_{dan}_{jelo}_1")
                            k2 = c2.number_input("II Smjena", 0, 100, get_v(dan, jelo, "II"), key=f"{prefix}_{dan}_{jelo}_2")
                            k3 = c3.number_input("III Smjena", 0, 100, get_v(dan, jelo, "III"), key=f"{prefix}_{dan}_{jelo}_3")
                            
                            for k, smj in zip([k1, k2, k3], ["I", "II", "III"]):
                                unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": jelo, "Kolicina": int(k), "Smjena": smj})
                
                if st.form_submit_button(f"🚀 SAČUVAJ {tip_sedmice.upper()}"):
                    # Brišemo stare unose firme samo za ovaj tip sedmice
                    dani_za_prefix = [f"{prefix}-{d}" for d in dani_std]
                    mask = ~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].isin(dani_za_prefix)))
                    novi_podaci = [n for n in unose if n['Kolicina'] > 0]
                    final_df = pd.concat([df_sve[mask] if not df_sve.empty else df_sve, pd.DataFrame(novi_podaci)], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final_df)
                    st.success("Sačuvano!")
                    st.rerun()

        with tab_trenutna: prikazi_meni("Trenutna", "Trenutna")
        with tab_naredna: prikazi_meni("Naredna", "Naredna")
        with tab_hist: st.dataframe(moja_n, use_container_width=True, hide_index=True)

    if st.sidebar.button("Odjavi se"):
        st.session_state["logged_in"] = False
        st.rerun()
