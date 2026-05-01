import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Narudžbe", layout="centered")

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

# Mapiranje dana (0=Pon, ..., 5=Sub, 6=Ned)
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

# --- 2. KORISNICI ---
users = {
    "admin": "tvoja_admin_sifra_123",
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# --- 3. DINAMIČKI MENI, DATUM I ROK ---
try:
    df_raw = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni", ttl=0)
    
    # Izvlačenje info redova
    sedmica_info = df_raw[df_raw['Dan'] == 'Sedmica']['Jelo'].values
    rok_info = df_raw[df_raw['Dan'] == 'Rok']['Jelo'].values
    sed_tekst = sedmica_info[0] if len(sedmica_info) > 0 else "Nije uneseno"
    rok_tekst = rok_info[0] if len(rok_info) > 0 else "Nije uneseno"

    # Radni dani uključujući subotu
    pravi_dani = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
    df_jela = df_raw[df_raw['Dan'].isin(pravi_dani)]
    meni = df_jela.groupby('Dan', sort=False)['Jelo'].apply(list).to_dict()
except Exception as e:
    st.error(f"Greška pri učitavanju tabele Meni: {e}")
    st.stop()

# --- 4. LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.sidebar.header("🔐 Prijava za Firme")
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
        st.title("👨‍🍳 Admin Panel - Pregled Kuhinje")
        df_n = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
        
        if not df_n.empty:
            zbirno = df_n.groupby(['Dan', 'Jelo'])['Kolicina'].sum().reset_index()
            izbor_dana = st.selectbox("Izaberi dan za pregled:", list(meni.keys()))
            plan = zbirno[zbirno['Dan'] == izbor_dana]
            
            st.subheader(f"Plan kuhanja za {izbor_dana}")
            st.table(plan)
            st.metric("Ukupno obroka", plan['Kolicina'].sum())
        else:
            st.info("Nema narudžbi u sistemu.")

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 Dobrodošli, {st.session_state['user']}")
        
        # Info traka
        c_i1, c_i2 = st.columns(2)
        c_i1.info(f"📅 **Sedmica:** {sed_tekst}")
        c_i2.warning(f"⏰ **Rok:** {rok_tekst}")
        
        t1, t2 = st.tabs(["🛒 Narudžba / Izmjena", "📜 Istorija"])
        
        with t1:
            with st.form("narudzba_izmjena", clear_on_submit=True):
                sve_n = []
                for dan, jela in meni.items():
                    onemoguci = False
                    status_tekst = ""
                    idx_dana = list(dani_mapa.values()).index(dan)
                    
                    # Logika zaključavanja (Subota je radna, Nedjelja otključava sve)
                    if danasnji_dan_index <= 5: 
                        if danasnji_dan_index >= idx_dana:
                            onemoguci = True
                            status_tekst = " 🔒 (Zatvoreno)"
                    else:
                        status_tekst = " 🔓 (Nova sedmica)"

                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}{status_tekst}")
                        for jelo in jela:
                            c1, c2 = st.columns([3, 1])
                            c1.markdown(f"<div style='padding-top:8px;'><b>{jelo}</b></div>", unsafe_allow_html=True)
                            kol = c2.number_input("Kol.", 0, 100, step=1, key=f"{dan}_{jelo}", 
                                                   label_visibility="collapsed", disabled=onemoguci)
                            sve_n.append({"Firma": st.session_state['user'], "Dan": dan, "Jelo": jelo, "Kolicina": int(kol)})
                
                if st.form_submit_button("🚀 SAČUVAJ NARUDŽBU / IZMJENE", use_container_width=True):
                    try:
                        df_tr = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
                        
                        # Određivanje dozvoljenih dana za upis
                        if danasnji_dan_index <= 5:
                            dani_za_upis = [d for d in meni.keys() if list(dani_mapa.values()).index(d) > danasnji_dan_index]
                        else:
                            dani_za_upis = list(meni.keys())
                        
                        # Brisanje starih i dodavanje novih
                        mask = ~((df_tr['Firma'] == st.session_state['user']) & (df_tr['Dan'].isin(dani_za_upis)))
                        novi_podaci = [n for n in sve_n if n['Kolicina'] > 0 and n['Dan'] in dani_za_upis]
                        df_final = pd.concat([df_tr[mask], pd.DataFrame(novi_podaci)], ignore_index=True)
                        
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=df_final)
                        st.success("✅ Vaša narudžba je uspješno zabilježena!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Greška: {e}")

        with t2:
            try:
                hist = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
                st.dataframe(hist[hist['Firma'] == st.session_state['user']], use_container_width=True, hide_index=True)
            except:
                st.info("Nema prethodnih narudžbi.")

    if st.sidebar.button("Odjavi se", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
