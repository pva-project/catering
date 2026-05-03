import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. FUNKCIJA ZA ZVJEZDICE (Bez HTML-a, direktan prikaz)
def prikazi_zvijezde(ocjena):
    if pd.isna(ocjena) or ocjena == 0:
        return "☆☆☆☆☆ (0.0)"
    pune = int(round(ocjena))
    return "⭐" * pune + "☆" * (5 - pune) + f" ({ocjena})"

# 2. KONFIGURACIJA POVEZIVANJA
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

def ucitaj_podatke(sheet):
    return conn.read(spreadsheet=spreadsheet_url, worksheet=sheet, ttl=0).dropna(how='all')

# 3. ANALIZA OCJENA (Povezivanje imena iz baze)
def izracunaj_statistiku():
    df_o = ucitaj_podatke("Ocjene")
    mapa = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
    
    if not df_o.empty and "Ocjena" in df_o.columns:
        df_o['Br'] = df_o['Ocjena'].map(mapa)
        # Prosjek po imenu kuvara (Jelena, Dragana...)
        prosjeci_kuvara = df_o.groupby('Kuvar')['Br'].mean().round(1).to_dict()
        prosjeci_jela = df_o.groupby('Jelo')['Br'].mean().round(1).to_dict()
        return prosjeci_kuvara, prosjeci_jela
    return {}, {}

# --- ADMIN PANEL ---
st.title("👨‍🍳 Admin Upravljanje")

# Dohvatanje trenutnih imena kuvara iz Menija
df_meni = ucitaj_podatke("Meni_Trenutni")
k1_ime = df_meni[df_meni['Dan'].str.contains("Kuvar 1", na=False)]['Jelo'].values[0] if not df_meni.empty else "N/A"
k2_ime = df_meni[df_meni['Dan'].str.contains("Kuvar 2", na=False)]['Jelo'].values[0] if not df_meni.empty else "N/A"

p_kuvari, p_jela = izracunaj_statistiku()

t1, t2, t3 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene"])

with t1:
    # Ispravljen prikaz: Ime kuvara + zvjezdice bez HTML koda
    st.info(f"👨‍🍳 Glavni kuvari: {k1_ime} ({prikazi_zvijezde(p_kuvari.get(k1_ime, 0.0))}) & {k2_ime} ({prikazi_zvijezde(p_kuvari.get(k2_ime, 0.0))})")
    
    # Tabela narudžbi
    df_narudzbe = ucitaj_podatke("Sheet1")
    if not df_narudzbe.empty:
        dan = st.selectbox("Izaberi dan:", ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak"])
        prikaz = df_narudzbe[df_narudzbe['Dan'] == f"Ova-{dan}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
        st.table(prikaz)

with t3:
    st.subheader("⭐ Rang lista kuvara")
    # Prikaz rejtinga za konkretna imena
    c1, c2 = st.columns(2)
    with c1:
        st.metric(f"Kuvar: {k1_ime}", f"{p_kuvari.get(k1_ime, 0.0)} ⭐")
    with c2:
        st.metric(f"Kuvar: {k2_ime}", f"{p_kuvari.get(k2_ime, 0.0)} ⭐")
    
    st.divider()
    st.write("Svi komentari:")
    st.dataframe(ucitaj_podatke("Ocjene"), hide_index=True)
