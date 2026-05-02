import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Management", layout="centered")
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# --- 4. LOGIN ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

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
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t_a1:
            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                d_sel = st.selectbox("Dan za kuhanje:", dani_std)
                st.table(df_nar[df_nar['Dan'] == f"Ova-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index())
        
        with t_a2:
            st.info("Meni mijenjajte direktno u Google Sheets listovima 'Meni_Trenutni' i 'Meni_Naredni'.")

        with t_a3:
            st.subheader("⭐ Povratne informacije klijenata")
            df_ocjene = ucitaj_sheet("Ocjene")
            if not df_ocjene.empty:
                st.dataframe(df_ocjene, use_container_width=True, hide_index=True)
            else: st.info("Još nema ocjena.")

        with t_a4:
            if st.button("🚀 ROTACIJA SEDMICA"):
                df_next = ucitaj_sheet("Meni_Naredni")
                conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.DataFrame(columns=["Firma","Dan","Jelo","Kolicina","Smjena"]))
                st.success("Sistem rotiran!")
                time.sleep(1)
                st.rerun()

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_t, t_n, t_h, t_o = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija", "⭐ Ocijeni obrok"])
        
        # --- TAB: OCA I NAREDNA (NARUČIVANJE) ---
        def prikazi_formu(sheet_name, prefix, zakljucaj):
            df_m = ucitaj_sheet(sheet_name)
            if df_m.empty: return
            inf_sed = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values if 'Sedmica' in df_m['Dan'].values else "N/A"
            inf_rok = df_m[df_m['Dan'] == 'Rok']['Jelo'].values if 'Rok' in df_m['Dan'].values else "N/A"
            c1, c2 = st.columns(2); c1.info(f"📅 {inf_sed}"); c2.warning(f"⏰ {inf_rok}")
            
            df_sve = ucitaj_sheet("Sheet1")
            with st.form(f"f_{prefix}"):
                unose = []
                for dan in dani_std:
                    onemoguci = False; status = " 🔓"
                    if zakljucaj and danasnji_dan_index <= 5:
                        if danasnji_dan_index >= dani_std.index(dan): onemoguci, status = True, " 🔒"
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}{status}")
                        jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                        for j in jela:
                            st.write(f"**{j}**")
                            col1, col2, col3 = st.columns(3)
                            def get_v(d, jl, s):
                                if not df_sve.empty:
                                    v = df_sve[(df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{prefix}-{d}") & (df_sve['Jelo']==jl) & (df_sve['Smjena']==s)]['Kolicina'].tolist()
                                    return int(v) if v else 0
                                return 0
                            k1 = col1.number_input("I Smjena", 0, 100, get_v(dan, j, "I"), key=f"{prefix}_{dan}_{j}_1", disabled=onemoguci)
                            k2 = col2.number_input("II Smjena", 0, 100, get_v(dan, j, "II"), key=f"{prefix}_{dan}_{j}_2", disabled=onemoguci)
                            k3 = col3.number_input("III Smjena", 0, 100, get_v(dan, j, "III"), key=f"{prefix}_{dan}_{j}_3", disabled=onemoguci)
                            for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                                if k >= 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(k), "Smjena": s})
                if st.form_submit_button("🚀 SAČUVAJ NARUDŽBU", use_container_width=True):
                    df_sve_clean = df_sve if not df_sve.empty else pd.DataFrame(columns=["Firma", "Dan", "Jelo", "Kolicina", "Smjena"])
                    mask = ~((df_sve_clean['Firma'] == st.session_state['user']) & (df_sve_clean['Dan'].astype(str).str.startswith(prefix)))
                    final = pd.concat([df_sve_clean[mask], pd.DataFrame([n for n in unose if n['Kolicina']>0])], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final)
                    st.success("✅ Sačuvano!"); st.balloons(); time.sleep(1); st.rerun()

        with t_t: prikazi_formu("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_formu("Meni_Naredni", "Naredna", False)
        with t_h: 
            df_h = ucitaj_sheet("Sheet1")
            if not df_h.empty: st.dataframe(df_h[df_h['Firma'] == st.session_state['user']], use_container_width=True, hide_index=True)
            else: st.info("Nema narudžbi.")

        # --- NOVI TAB: OCJENJIVANJE ---
        with t_o:
            st.subheader("⭐ Ocijenite kvalitet obroka")
            st.write("Vaše mišljenje nam pomaže da budemo bolji!")
            
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            sva_jela_ove_sedmice = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist()
            
            with st.form("forma_ocjena", clear_on_submit=True):
                odabrano_jelo = st.selectbox("Izaberite jelo koje ste probali:", sva_jela_ove_sedmice)
                ocjena = st.select_slider("Vaša ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                komentar = st.text_area("Dodatni komentar (opcionalno):")
                
                if st.form_submit_button("📩 Pošalji ocjenu"):
                    df_postojace_ocjene = ucitaj_sheet("Ocjene")
                    nova_ocjena = pd.DataFrame([{
                        "Firma": st.session_state['user'],
                        "Jelo": odabrano_jelo,
                        "Ocjena": ocjena,
                        "Komentar": komentar
                    }])
                    final_ocjene = pd.concat([df_postojace_ocjene, nova_ocjena], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=final_ocjene)
                    st.success("Hvala vam na ocjeni! ⭐")
                    time.sleep(1)
                    st.rerun()

