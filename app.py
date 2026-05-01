import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Narudžbe", layout="centered")

# CSS ZA FORSIRANJE KOLONA NA MOBITELU
st.markdown("""
    <style>
    /* Smanjuje razmak između kolona na mobilnim uređajima */
    [data-testid="column"] {
        min-width: 0px !important;
        flex-basis: 0 !important;
        flex-grow: 1 !important;
    }
    /* Centriranje teksta i smanjenje paddinga */
    .stNumberInput div div input {
        text-align: center;
        padding: 0px !important;
    }
    .jelo-text {
        font-size: 14px;
        font-weight: bold;
        padding-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_standard = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota", "Nedjelja"]
danasnji_dan_index = datetime.now().weekday()

# --- 2. KORISNICI ---
users = {
    "admin": "tvoja_admin_sifra_123",
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# --- 3. DINAMIČKI MENI ---
try:
    df_raw = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni", ttl=0)
    df_raw['Dan'] = df_raw['Dan'].str.strip().replace(['Ponedeljak', 'Ponedjeljak '], 'Ponedjeljak')
    
    sedmica_info = df_raw[df_raw['Dan'] == 'Sedmica']['Jelo'].values
    rok_info = df_raw[df_raw['Dan'] == 'Rok']['Jelo'].values
    sed_tekst = sedmica_info[0] if len(sedmica_info) > 0 else "Nije uneseno"
    rok_tekst = rok_info[0] if len(rok_info) > 0 else "Nije uneseno"

    pravi_dani = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
    df_jela = df_raw[df_raw['Dan'].isin(pravi_dani)]
    meni = {dan: df_jela[df_jela['Dan'] == dan]['Jelo'].tolist() for dan in pravi_dani if not df_jela[df_jela['Dan'] == dan].empty}
except Exception as e:
    st.error(f"Greška pri učitavanju menija: {e}")
    st.stop()

# --- 4. LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.sidebar.header("🔐 Prijava")
    u = st.sidebar.text_input("Korisničko ime")
    p = st.sidebar.text_input("Lozinka", type="password")
    if st.sidebar.button("Prijavi se", use_container_width=True):
        if u in users and users[u] == p:
            st.session_state["logged_in"] = True
            st.session_state["user"] = u
            st.rerun()
        else:
            st.sidebar.error("Pogrešni podaci")
else:
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel")
        df_n = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
        if not df_n.empty:
            dan_sel = st.selectbox("Izaberi dan:", list(meni.keys()))
            zbirno = df_n[df_n['Dan'] == dan_sel].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
            st.table(zbirno)
    else:
        st.title(f"🍴 {st.session_state['user']}")
        
        c_i1, c_i2 = st.columns(2)
        c_i1.info(f"📅 **Sedmica:** {sed_tekst}")
        c_i2.warning(f"⏰ **Rok:** {rok_tekst}")
        
        t1, t2 = st.tabs(["🛒 Narudžba", "📜 Istorija"])
        
        try:
            df_sve = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
            moja_narudzba = df_sve[df_sve['Firma'] == st.session_state['user']]
        except:
            moja_narudzba = pd.DataFrame()

        with t1:
            with st.form("narudzba_mobilna"):
                sve_n = []
                for dan, jela in meni.items():
                    onemoguci = False
                    status = ""
                    idx_dan = dani_standard.index(dan)
                    
                    if danasnji_dan_index <= 5: 
                        if danasnji_dan_index >= idx_dan:
                            onemoguci, status = True, " 🔒 (Zatvoreno)"
                    else:
                        onemoguci, status = False, " 🔓 (Nova sedmica)"

                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}{status}")
                        # FIKSNE KOLONE ZA MOBITEL
                        h1, h2, h3, h4 = st.columns([1.5, 1, 1, 1])
                        h2.caption("I smj.")
                        h3.caption("II smj.")
                        h4.caption("III smj.")
                        
                        for jelo in jela:
                            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
                            c1.markdown(f"<div class='jelo-text'>{jelo}</div>", unsafe_allow_html=True)
                            
                            def get_stara_kol(d, j, s):
                                if not moja_narudzba.empty:
                                    val = moja_narudzba[(moja_narudzba['Dan'] == d) & (moja_narudzba['Jelo'] == j) & (moja_narudzba['Smjena'] == s)]['Kolicina'].values
                                    return int(val) if len(val) > 0 else 0
                                return 0

                            k1 = c2.number_input("", 0, 100, step=1, value=get_stara_kol(dan, jelo, "I"), key=f"{dan}_{jelo}_S1", label_visibility="collapsed", disabled=onemoguci)
                            k2 = c3.number_input("", 0, 100, step=1, value=get_stara_kol(dan, jelo, "II"), key=f"{dan}_{jelo}_S2", label_visibility="collapsed", disabled=onemoguci)
                            k3 = c4.number_input("", 0, 100, step=1, value=get_stara_kol(dan, jelo, "III"), key=f"{dan}_{jelo}_S3", label_visibility="collapsed", disabled=onemoguci)
                            
                            for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                                sve_n.append({"Firma": st.session_state['user'], "Dan": dan, "Jelo": jelo, "Kolicina": int(k), "Smjena": s})
                
                if st.form_submit_button("🚀 SAČUVAJ IZMJENE", use_container_width=True):
                    try:
                        dani_za_upis = [d for d in meni.keys() if dani_standard.index(d) > danasnji_dan_index] if danasnji_dan_index <= 5 else list(meni.keys())
                        mask_ostavi = ~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].isin(dani_za_upis)))
                        df_zadrzano = df_sve[mask_ostavi]
                        novi_podaci = [n for n in sve_n if n['Kolicina'] > 0 and n['Dan'] in dani_za_upis]
                        df_final = pd.concat([df_zadrzano, pd.DataFrame(novi_podaci)], ignore_index=True)
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=df_final)
                        st.success("✅ Sačuvano!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Greška: {e}")

        with t2:
            st.dataframe(moja_narudzba, use_container_width=True, hide_index=True)

    if st.sidebar.button("Odjavi se", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
