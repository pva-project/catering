import streamlit as st
import pandas as pd

# 1. Baza korisnika (Lozinke za 10 firmi)
# U realnom sistemu ovo bi bilo u bazi, ovdje je radi jednostavnosti u rječniku
users = {
    "firma1": "lozinka123",
    "firma2": "sigurnost2024",
    "firma3": "catering03",
    # ... dodajte ostalih 7 firmi
}

# 2. Sedmični meni
meni = {
    "Ponedjeljak": ["Grah sa mesom", "Piletina u curry sosu", "Falafel salata"],
    "Utorak": ["Musaka", "Bečka šnicla", "Rižoto sa povrćem"],
    "Srijeda": ["Sarma", "Piletina na žaru", "Pohovani sir"],
    "Četvrtak": ["Gulaš", "Pastrmka", "Pasta Napoli"],
    "Petak": ["Oslić sa krompirom", "Lignje", "Povrtni đuveč"]
}

# Funkcija za Login
def login():
    st.sidebar.title("Prijava za Firme")
    username = st.sidebar.text_input("Korisničko ime")
    password = st.sidebar.text_input("Lozinka", type="password")
    
    if st.sidebar.button("Prijavi se"):
        if username in users and users[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.rerun()
        else:
            st.sidebar.error("Pogrešno korisničko ime ili lozinka")

# Glavni dio aplikacije
if "logged_in" not in st.session_state:
    login()
    st.warning("Molimo prijavite se sa strane da biste vidjeli meni.")
else:
    st.title(f"Dobrodošli, {st.session_state['user'].upper()}")
    st.info("Odaberite jela i količine za sljedeću sedmicu:")

    narudzbenica = []

    with st.form("narudzba_forma"):
        for dan, jela in meni.items():
            st.subheader(f"📅 {dan}")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                izbor = st.selectbox(f"Odaberi jelo za {dan}:", jela, key=f"jelo_{dan}")
            with col2:
                kol = st.number_input(f"Količina:", min_value=0, step=1, key=f"kol_{dan}")
            
            if kol > 0:
                narudzbenica.append({"Firma": st.session_state['user'], "Dan": dan, "Jelo": izbor, "Količina": kol})

        submit = st.form_submit_button("POŠALJI NARUDŽBU")

    if submit:
        if narudzbenica:
            df = pd.DataFrame(narudzbenica)
            # Ovdje možete dodati kod da se DF spasi u Google Sheets ili bazu
            st.success("Vaša narudžba je uspješno poslana!")
            st.table(df)
        else:
            st.error("Niste unijeli količine!")

    if st.sidebar.button("Odjavi se"):
        del st.session_state["logged_in"]
        st.rerun()
