import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import smtplib
from email.mime.text import MIMEText

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Narudžbe", layout="centered")

# Povezivanje sa Google Sheets (koristi podatke iz Secrets-a)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. BAZA KORISNIKA I MENI ---
users = {
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

meni = {
    "Ponedjeljak": ["Grah sa mesom", "Piletina u curry sosu", "Falafel salata"],
    "Utorak": ["Musaka", "Bečka šnicla", "Rižoto sa povrćem"],
    "Srijeda": ["Sarma", "Piletina na žaru", "Pohovani sir"],
    "Četvrtak": ["Gulaš", "Pastrmka", "Pasta Napoli"],
    "Petak": ["Oslić sa krompirom", "Lignje", "Povrtni đuveč"]
}

# --- 3. FUNKCIJA ZA EMAIL ---
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

# --- 4. LOGIN SISTEM ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.sidebar.header("Prijava za Firme")
    u = st.sidebar.text_input("Korisničko ime")
    p = st.sidebar.text_input("Lozinka", type="password")
    if st.sidebar.button("Prijavi se"):
        if u in users and users[u] == p:
            st.session_state["logged_in"] = True
            st.session_state["user"] = u
            st.rerun()
        else:
            st.sidebar.error("Pogrešni podaci")
else:
    # --- 5. FORMA ZA NARUČIVANJE ---
    st.title(f"Dobrodošli, {st.session_state['user']}")
    
    with st.form("narudzba_forma"):
        nove_narudzbe = []
        for dan, jela in meni.items():
            st.subheader(f"📅 {dan}")
            for jelo in jela:
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{jelo}**")
                kol = c2.number_input("Količina", min_value=0, step=1, key=f"{dan}_{jelo}")
                if kol > 0:
                    nove_narudzbe.append({
                        "Firma": st.session_state['user'], 
                        "Dan": dan, 
                        "Jelo": jelo, 
                        "Kolicina": int(kol)
                    })
            st.divider()

        if st.form_submit_button("POŠALJI NARUDŽBU"):
            if nove_narudzbe:
                try:
                    # Čitanje postojećih podataka (Sheet1 mora postojati!)
                    try:
                        stari_podaci = conn.read(worksheet="Sheet1", ttl=0)
                    except:
                        stari_podaci = pd.DataFrame(columns=["Firma", "Dan", "Jelo", "Kolicina"])
                    
                    novi_df = pd.DataFrame(nove_narudzbe)
                    
                    # Spajanje
                    if not stari_podaci.empty:
                        updated_df = pd.concat([stari_podaci, novi_df], ignore_index=True)
                    else:
                        updated_df = novi_df
                    
                    # Slanje u tabelu
                    conn.update(worksheet="Sheet1", data=updated_df)
                    
                    # Slanje emaila
                    posalji_email(st.session_state['user'], nove_narudzbe)
                    
                    st.success("✅ Narudžba uspješno sačuvana!")
                    st.balloons()
                    st.table(novi_df)
                except Exception as e:
                    st.error("❌ Detaljna greška:")
                    st.exception(e)  # Ovo će ispisati kompletan 'Traceback' koji mi treba
            else:
                st.warning("Niste odabrali nijedno jelo.")

    if st.sidebar.button("Odjavi se"):
        st.session_state["logged_in"] = False
        st.rerun()
