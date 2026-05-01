import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Narudžbe", layout="centered")

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

# Mapiranje dana za provjeru (Python dani su na engleskom)
dani_mapa = {
    0: "Ponedjeljak",
    1: "Utorak",
    2: "Srijeda",
    3: "Četvrtak",
    4: "Petak",
    5: "Subota",
    6: "Nedjelja"
}
danasnji_dan_index = datetime.now().weekday()
danas_je = dani_mapa[danasnji_dan_index]

# --- 2. KORISNICI ---
users = {
    "admin": "tvoja_admin_sifra_123",
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# --- 3. MENI, DATUM I ROK ---
try:
    df_raw = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni", ttl=0)
    sedmica_info = df_raw[df_raw['Dan'] == 'Sedmica']['Jelo'].values
    rok_info = df_raw[df_raw['Dan'] == 'Rok']['Jelo'].values
    sed_tekst = sedmica_info[0] if len(sedmica_info) > 0 else "Nije uneseno"
    rok_tekst = rok_info[0] if len(rok_info) > 0 else "Nije uneseno"

    pravi_dani = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak"]
    meni = df_raw[df_raw['Dan'].isin(pravi_dani)].groupby('Dan', sort=False)['Jelo'].apply(list).to_dict()
except:
    st.stop()

# --- 4. LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.sidebar.header("🔐 Prijava")
    u = st.sidebar.text_input("Korisničko ime")
    p = st.sidebar.text_input("Lozinka", type="password")
    if st.sidebar.button("Prijavi se"):
        if u in users and users[u] == p:
            st.session_state["logged_in"] = True
            st.session_state["user"] = u
            st.rerun()
else:
    if st.session_state["user"] == "admin":
        # --- ADMIN PANEL ---
        st.title("👨‍🍳 Admin Panel")
        df_n = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
        if not df_n.empty:
            zbirno = df_n.groupby(['Dan', 'Jelo'])['Kolicina'].sum().reset_index()
            dan_sel = st.selectbox("Izaberi dan:", list(meni.keys()))
            st.table(zbirno[zbirno['Dan'] == dan_sel])
            st.metric("Ukupno obroka", zbirno[zbirno['Dan'] == dan_sel]['Kolicina'].sum())
    else:
        # --- KORISNIČKI PANEL ---
        st.title(f"🍴 Dobrodošli, {st.session_state['user']}")
        
        c1, c2 = st.columns(2)
        c1.info(f"📅 **Sedmica:** {sed_tekst}")
        c2.warning(f"⏰ **Rok:** {rok_tekst}")
        
        t1, t2 = st.tabs(["🛒 Narudžba / Izmjena", "📜 Istorija"])
        
        with t1:
            with st.form("forma_izmjena", clear_on_submit=True):
                nove_n = []
                for dan, jela in meni.items():
                    # PROVJERA: Da li je ovaj dan već prošao ili je danas?
                    # Ako je danas Srijeda, onemogući Ponedjeljak, Utorak i Srijedu
                    onemoguci = False
                    status_tekst = ""
                    
                    # Logika: onemogući ako je dan već prošao u sedmici ili je danas
                    index_dana_u_meniju = list(dani_mapa.values()).index(dan)
                    if danasnji_dan_index >= index_dana_u_meniju:
                        onemoguci = True
                        status_tekst = " 🔒 (Zatvoreno)"

                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}{status_tekst}")
                        for jelo in jela:
                            col1, col2 = st.columns([3, 1])
                            col1.markdown(f"<div style='padding-top:8px;'><b>{jelo}</b></div>", unsafe_allow_html=True)
                            
                            # Onemogućavamo polje ako je dan danas ili je prošao
                            kol = col2.number_input("Kol.", 0, 100, step=1, key=f"{dan}_{jelo}", 
                                                   label_visibility="collapsed", disabled=onemoguci)
                            
                            if kol >= 0:
                                nove_n.append({"Firma": st.session_state['user'], "Dan": dan, "Jelo": jelo, "Kolicina": int(kol)})
                
                if st.form_submit_button("🚀 SAČUVAJ IZMJENE"):
                    try:
                        df_trenutno = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
                        
                        # Brišemo stare zapise samo za dane koje korisnik MOŽE mijenjati (budući dani)
                        dani_koji_se_mijenjaju = [n['Dan'] for n in nove_n if list(dani_mapa.values()).index(n['Dan']) > danasnji_dan_index]
                        
                        mask = ~((df_trenutno['Firma'] == st.session_state['user']) & (df_trenutno['Dan'].isin(dani_koji_se_mijenjaju)))
                        df_bez_starih = df_trenutno[mask]
                        
                        nove_df = pd.DataFrame([n for n in nove_n if n['Kolicina'] > 0 and n['Dan'] in dani_koji_se_mijenjaju])
                        finalni_df = pd.concat([df_bez_starih, nove_df], ignore_index=True)
                        
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=finalni_df)
                        st.success("✅ Izmjene su sačuvane za buduće dane!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Greška: {e}")

        with t2:
            try:
                hist = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
                st.dataframe(hist[hist['Firma'] == st.session_state['user']], use_container_width=True, hide_index=True)
            except:
                st.info("Još nema narudžbi.")

    if st.sidebar.button("Odjavi se"):
        st.session_state["logged_in"] = False
        st.rerun()
