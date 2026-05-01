import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Narudžbe", layout="centered")

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_mapa = {0: "Ponedjeljak", 1: "Utorak", 2: "Srijeda", 3: "Četvrtak", 4: "Petak", 5: "Subota", 6: "Nedjelja"}
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
    sedmica_info = df_raw[df_raw['Dan'] == 'Sedmica']['Jelo'].values
    rok_info = df_raw[df_raw['Dan'] == 'Rok']['Jelo'].values
    sed_tekst = sedmica_info[0] if len(sedmica_info) > 0 else "Nije uneseno"
    rok_tekst = rok_info[0] if len(rok_info) > 0 else "Nije uneseno"

    pravi_dani = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
    df_jela = df_raw[df_raw['Dan'].isin(pravi_dani)]
    meni = df_jela.groupby('Dan', sort=False)['Jelo'].apply(list).to_dict()
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
    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel")
        df_n = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
        if not df_n.empty:
            dan_sel = st.selectbox("Izaberi dan:", list(meni.keys()))
            zbirno = df_n[df_n['Dan'] == dan_sel].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
            st.table(zbirno)
    
    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        c_i1, c_i2 = st.columns(2)
        c_i1.info(f"📅 **Sedmica:** {sed_tekst}")
        c_i2.warning(f"⏰ **Rok:** {rok_tekst}")
        
        t1, t2 = st.tabs(["🛒 Narudžba", "📜 Istorija"])
        
        with t1:
            with st.form("narudzba_smjene", clear_on_submit=True):
                sve_n = []
                for dan, jela in meni.items():
                    onemoguci = False
                    status = ""
                    idx_dan = list(dani_mapa.values()).index(dan)
                    
                    # NOVA LOGIKA: Radnim danima (Pon-Pet) zaključaj prošle dane. 
                    # Subotom i Nedjeljom (5 i 6) otključaj SVE za novu sedmicu.
                    if danasnji_dan_index <= 4: 
                        if danasnji_dan_index >= idx_dan:
                            onemoguci, status = True, " 🔒 (Zatvoreno)"
                    else:
                        onemoguci, status = False, " 🔓 (Nova sedmica)"

                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}{status}")
                        h1, h2, h3, h4 = st.columns([2.5, 1, 1, 1])
                        h2.caption("I smjena")
                        h3.caption("II smjena")
                        h4.caption("III smjena")
                        
                        for jelo in jela:
                            c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
                            c1.markdown(f"<div style='padding-top:5px;'>{jelo}</div>", unsafe_allow_html=True)
                            k1 = c2.number_input("I", 0, 100, step=1, key=f"{dan}_{jelo}_S1", label_visibility="collapsed", disabled=onemoguci)
                            k2 = c3.number_input("II", 0, 100, step=1, key=f"{dan}_{jelo}_S2", label_visibility="collapsed", disabled=onemoguci)
                            k3 = c4.number_input("III", 0, 100, step=1, key=f"{dan}_{jelo}_S3", label_visibility="collapsed", disabled=onemoguci)
                            
                            for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                                sve_n.append({"Firma": st.session_state['user'], "Dan": dan, "Jelo": jelo, "Kolicina": int(k), "Smjena": s})
                
                if st.form_submit_button("🚀 SAČUVAJ NARUDŽBU", use_container_width=True):
                    try:
                        df_tr = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
                        
                        # Definisanje dana koji se smiju mijenjati
                        if danasnji_dan_index <= 4:
                            dani_upis = [d for d in meni.keys() if list(dani_mapa.values()).index(d) > danasnji_dan_index]
                        else:
                            dani_upis = list(meni.keys())
                        
                        mask = ~((df_tr['Firma'] == st.session_state['user']) & (df_tr['Dan'].isin(dani_upis)))
                        novi = [n for n in sve_n if n['Kolicina'] > 0 and n['Dan'] in dani_upis]
                        df_f = pd.concat([df_tr[mask], pd.DataFrame(novi)], ignore_index=True)
                        
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=df_f)
                        st.success("✅ Narudžba sačuvana!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Greška: {e}")

        with t2:
            hist = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
            st.dataframe(hist[hist['Firma'] == st.session_state['user']], use_container_width=True, hide_index=True)

    if st.sidebar.button("Odjavi se", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
