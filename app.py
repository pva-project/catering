import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import smtplib
from email.mime.text import MIMEText

# --- 1. KONFIGURACIJA STRANICE ---
st.set_page_config(page_title="Catering Narudžbe", layout="centered")

# CSS za dodatno uljepšavanje (opcionalno, ali pomaže ravnini)
st.markdown("""
    <style>
    .stNumberInput { width: 120px !important; }
    .day-container { background-color: #f9f9f9; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. KORISNICI ---
users = {
    "admin": "tvoja_admin_sifra_123",
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# --- 3. DINAMIČKI MENI IZ GOOGLE TABELE ---
try:
    df_meni = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni", ttl=0)
    meni = df_meni.groupby('Dan', sort=False)['Jelo'].apply(list).to_dict()
except Exception as e:
    st.error(f"Greška pri učitavanju menija: {e}")
    st.stop()

# --- 4. FUNKCIJA ZA EMAIL ---
def posalji_email(firma, podaci):
    try:
        sender = st.secrets["connections"]["gsheets"].get("email_user")
        pwd = st.secrets["connections"]["gsheets"].get("email_password")
        if sender and pwd:
            detalji = "\n".join([f"{n['Dan']} - {n['Jelo']}: {n['Kolicina']} kom" for n in podaci])
            msg = MIMEText(f"Nova narudžba od: {firma}\n\n{detalji}")
            msg['Subject'] = f"Nova Narudžba - {firma}"
            msg['From'] = sender
            msg['To'] = sender
            with smtplib.SMTP_SSL("://gmail.com", 465) as server:
                server.login(sender, pwd)
                server.sendmail(sender, sender, msg.as_string())
    except:
        pass

# --- 5. LOGIN ---
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
    # --- 6. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel - Pregled Kuhinje")
        df_narudzbe = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
        
        if not df_narudzbe.empty:
            zbirno = df_narudzbe.groupby(['Dan', 'Jelo'])['Kolicina'].sum().reset_index()
            izbor_dana = st.selectbox("Izaberi dan za pregled:", list(meni.keys()))
            danasnji_plan = zbirno[zbirno['Dan'] == izbor_dana]
            
            st.subheader(f"Plan kuhanja za {izbor_dana}")
            st.table(danasnji_plan)
            st.metric("Ukupno obroka", danasnji_plan['Kolicina'].sum())
        else:
            st.info("Još uvijek nema narudžbi u sistemu.")

    # --- 7. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 Dobrodošli, {st.session_state['user']}")
        
        t1, t2 = st.tabs(["🛒 Nova Narudžba", "📜 Istorija Narudžbi"])
        
        with t1:
            st.markdown("### 📝 Odaberite meni za iduću sedmicu")
            with st.form("narudzba_forma", clear_on_submit=True):
                sve_narudzbe = []
                
                for dan, jela in meni.items():
                    # Svaki dan je u svom okviru
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}")
                        
                        for jelo in jela:
                            # 3/4 širine za jelo, 1/4 za broj (ravnina!)
                            col_naziv, col_input = st.columns([3, 1])
                            
                            with col_naziv:
                                st.markdown(f"<div style='padding-top: 8px;'><b>{jelo}</b></div>", unsafe_allow_html=True)
                            
                            with col_input:
                                kol = st.number_input("Količina", 0, 100, step=1, key=f"{dan}_{jelo}", label_visibility="collapsed")
                            
                            if kol > 0:
                                sve_narudzbe.append({
                                    "Firma": st.session_state['user'], 
                                    "Dan": dan, 
                                    "Jelo": jelo, 
                                    "Kolicina": int(kol)
                                })
                
                st.markdown("<br>", unsafe_allow_html=True)
                # Centrirano i veliko dugme
                _, col_dugme, _ = st.columns([1, 2, 1])
                with col_dugme:
                    posalji = st.form_submit_button("🚀 POŠALJI NARUDŽBU", use_container_width=True)
                
                if posalji:
                    if sve_narudzbe:
                        try:
                            stari = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
                            # Čišćenje praznih redova prije spajanja
                            stari = stari.dropna(how='all')
                            novo_df = pd.DataFrame(sve_narudzbe)
                            updated_df = pd.concat([stari, novo_df], ignore_index=True)
                            
                            conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=updated_df)
                            posalji_email(st.session_state['user'], sve_narudzbe)
                            
                            st.success("✅ Narudžba je uspješno sačuvana!")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Greška pri slanju: {e}")
                    else:
                        st.warning("⚠️ Molimo unesite količinu za barem jedno jelo.")

        with t2:
            st.subheader("Vaša istorija narudžbi")
            try:
                df_history = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
                istorija = df_history[df_history['Firma'] == st.session_state['user']]
                if not istorija.empty:
                    st.dataframe(istorija, use_container_width=True, hide_index=True)
                else:
                    st.info("Nema prethodnih narudžbi.")
            except:
                st.error("Nije moguće učitati istoriju.")

    if st.sidebar.button("Odjavi se", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
