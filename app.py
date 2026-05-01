import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import smtplib
from email.mime.text import MIMEText

# 1. Konfiguracija i povezivanje
st.set_page_config(page_title="Catering Narudžbe", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Baza korisnika
users = {
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# 3. Sedmični meni
meni = {
    "Ponedjeljak": ["Grah sa mesom", "Piletina u curry sosu", "Falafel salata"],
    "Utorak": ["Musaka", "Bečka šnicla", "Rižoto sa povrćem"],
    "Srijeda": ["Sarma", "Piletina na žaru", "Pohovani sir"],
    "Četvrtak": ["Gulaš", "Pastrmka", "Pasta Napoli"],
    "Petak": ["Oslić sa krompirom", "Lignje", "Povrtni đuveč"]
}

# --- FUNKCIJA ZA EMAIL ---
def posalji_email(firma, podaci):
    sender = st.secrets["connections"]["gsheets"]["email_user"] # Gmail u Secrets
    pwd = st.secrets["connections"]["gsheets"]["email_password"] # App Password u Secrets
    
    detalji = "\n".join([f"{n['Dan']} - {n['Jelo']}: {n['Kolicina']} kom" for n in podaci])
    msg = MIMEText(f"Nova narudžba od: {firma}\n\n{detalji}")
    msg['Subject'] = f"Nova Narudžba - {firma}"
    msg['From'] = sender
    msg['To'] = sender # Šalješ samom sebi

    try:
        with smtplib.SMTP_SSL("://gmail.com", 465) as server:
            server.login(sender, pwd)
            server.sendmail(sender, sender, msg.as_string())
    except:
        pass # Ignoriši grešku ako mail ne prođe

# --- LOGIN SISTEM ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.sidebar.header("Prijava")
    user_input = st.sidebar.text_input("Korisničko ime")
    pw_input = st.sidebar.text_input("Lozinka", type="password")
    if st.sidebar.button("Prijavi se"):
        if user_input in users and users[user_input] == pw_input:
            st.session_state["logged_in"] = True
            st.session_state["user"] = user_input
            st.rerun()
        else:
            st.sidebar.error("Pogrešni podaci")
else:
    # --- FORMA ZA NARUČIVANJE ---
    st.title(f"Dobrodošli, {st.session_state['user']}")
    
    with st.form("narudzba_forma"):
        nove_narudzbe = []
        
        for dan, jela in meni.items():
            st.subheader(f"📅 {dan}")
            for jelo in jela:
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**{jelo}**")
                with c2:
                    kol = st.number_input("Količina", min_value=0, step=1, key=f"{dan}_{jelo}")
                
                if kol > 0:
                    nove_narudzbe.append({
                        "Firma": st.session_state['user'], 
                        "Dan": dan, 
                        "Jelo": jelo, 
                        "Kolicina": kol
                    })
            st.divider()

        if st.form_submit_button("POŠALJI NARUDŽBU"):
            if nove_narudzbe:
                # 1. Spasi u Google Sheets
                stari_podaci = conn.read(worksheet="Sheet1")
                updated_df = pd.concat([stari_podaci, pd.DataFrame(nove_narudzbe)], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                # 2. Pošalji Email (ako si podesio Secrets)
                if "email_password" in st.secrets["connections"]["gsheets"]:
                    posalji_email(st.session_state['user'], nove_narudzbe)
                
                st.success("Narudžba je uspješno poslana!")
                st.balloons()
                st.table(pd.DataFrame(nove_narudzbe))
            else:
                st.error("Niste unijeli količine.")

    if st.sidebar.button("Odjavi se"):
        st.session_state["logged_in"] = False
        st.rerun()
