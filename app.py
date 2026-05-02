import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Sistem", layout="centered")

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_standard = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota", "Nedjelja"]
danasnji_dan_index = datetime.now().weekday()

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. DINAMIČKI MENI ---
try:
    df_raw = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni", ttl=0)
    df_raw['Dan'] = df_raw['Dan'].astype(str).str.strip()
    
    # POPRAVKA: Čitanje teksta bez ArrowStringArray zagrada
    sed_info = df_raw[df_raw['Dan'] == 'Sedmica']['Jelo'].values
    rok_info = df_raw[df_raw['Dan'] == 'Rok']['Jelo'].values
    
    sed_tekst = sed_info[0] if len(sed_info) > 0 else "Nije uneseno"
    rok_tekst = rok_info[0] if len(rok_info) > 0 else "Nije uneseno"
    
    pravi_dani = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
    df_jela_samo = df_raw[df_raw['Dan'].isin(pravi_dani)]
    meni = {dan: df_jela_samo[df_jela_samo['Dan'] == dan]['Jelo'].tolist() for dan in pravi_dani if not df_jela_samo[df_jela_samo['Dan'] == dan].empty}
except:
    st.error("Greška pri učitavanju menija.")
    st.stop()

# --- 4. LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

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
        adm_t1, adm_t2, adm_t3 = st.tabs(["📊 Kuhinja", "📝 Meni", "📂 Arhiva"])
        
        with adm_t1:
            with st.expander("⚠️ Kraj sedmice (Arhiviraj)"):
                st.warning("Ovo će prebaciti narudžbe u Arhivu i isprazniti trenutnu tabelu.")
                if st.button("📁 ARHIVIRAJ I RESETUJ"):
                    df_trenutno = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
                    if not df_trenutno.empty:
                        df_arhiva = conn.read(spreadsheet=spreadsheet_url, worksheet="Arhiva", ttl=0)
                        df_trenutno['Datum_Arhive'] = datetime.now().strftime("%d.%m.%Y")
                        novo_arhiva = pd.concat([df_arhiva, df_trenutno], ignore_index=True)
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Arhiva", data=novo_arhiva)
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.DataFrame(columns=["Firma", "Dan", "Jelo", "Kolicina", "Smjena"]))
                        st.success("Narudžbe prebačene u Arhivu!")
                        st.rerun()
                    else: st.info("Tabela je već prazna.")
            
            df_n = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
            if not df_n.empty:
                dan_sel = st.selectbox("Izaberi dan:", pravi_dani)
                zbir = df_n[df_n['Dan'] == dan_sel].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                st.table(zbir)
            else: st.info("Nema narudžbi.")

        with adm_t2:
            edited_meni = st.data_editor(df_raw, use_container_width=True, hide_index=True)
            if st.button("💾 SAČUVAJ NOVI MENI"):
                conn.update(spreadsheet=spreadsheet_url, worksheet="Meni", data=edited_meni)
                st.success("Meni ažuriran!")
                st.rerun()

        with adm_t3:
            st.subheader("📂 Kompletna Arhiva")
            df_a = conn.read(spreadsheet=spreadsheet_url, worksheet="Arhiva", ttl=0)
            st.dataframe(df_a, use_container_width=True, hide_index=True)

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        c1, c2 = st.columns(2)
        c1.info(f"📅 **Sedmica:** {sed_tekst}")
        c2.warning(f"⏰ **Rok:** {rok_tekst}")
        
        t1, t2 = st.tabs(["🛒 Narudžba", "📜 Moja Istorija"])
        
        try:
            df_sve = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
            moja_n = df_sve[df_sve['Firma'] == st.session_state['user']]
        except: df_sve, moja_n = pd.DataFrame(), pd.DataFrame()

        with t1:
            with st.form("forma_final"):
                sve_n = []
                for dan, jela in meni.items():
                    idx = dani_standard.index(dan)
                    onemoguci = (danasnji_dan_index <= 5 and danasnji_dan_index >= idx)
                    status = " 🔒" if onemoguci else " 🔓"
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}{status}")
                        for jelo in jela:
                            st.write(f"**{jelo}**")
                            c1, c2, c3 = st.columns(3)
                            def get_v(d, j, s):
                                if not moja_n.empty:
                                    v = moja_n[(moja_n['Dan']==d) & (moja_n['Jelo']==j) & (moja_n['Smjena']==s)]['Kolicina'].tolist()
                                    return int(v[0]) if v else 0
                                return 0
                            k1 = c1.number_input("I Smjena", 0, 100, get_v(dan, jelo, "I"), key=f"{dan}_{jelo}_1", disabled=onemoguci)
                            k2 = c2.number_input("II Smjena", 0, 100, get_v(dan, jelo, "II"), key=f"{dan}_{jelo}_2", disabled=onemoguci)
                            k3 = c3.number_input("III Smjena", 0, 100, get_v(dan, jelo, "III"), key=f"{dan}_{jelo}_3", disabled=onemoguci)
                            for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                                sve_n.append({"Firma": st.session_state['user'], "Dan": dan, "Jelo": jelo, "Kolicina": int(k), "Smjena": s})
                
                if st.form_submit_button("🚀 SAČUVAJ", use_container_width=True):
                    dani_upis = [d for d in meni.keys() if dani_standard.index(d) > danasnji_dan_index] if danasnji_dan_index <= 5 else list(meni.keys())
                    mask = ~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].isin(dani_upis)))
                    df_final = pd.concat([df_sve[mask], pd.DataFrame([n for n in sve_n if n['Kolicina'] > 0 and n['Dan'] in dani_upis])], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=df_final)
                    st.success("Sačuvano!")
                    st.rerun()
        with t2: st.dataframe(moja_n, use_container_width=True, hide_index=True)
