import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. FUNKCIJA ZA ZVJEZDICE (Vraćena na tekstualni format koji radi na mobilnom)
def prikazi_zvijezde(ocjena):
    # Ako je ocjena N/A ili 0, prikaži prazne zvijezde
    if pd.isna(ocjena) or ocjena == 0:
        return "☆☆☆☆☆ (0.0)"
    pune = int(round(ocjena))
    return "⭐" * pune + "☆" * (5 - pune) + f" ({ocjena})"

# 2. KONFIGURACIJA POVEZIVANJA
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

def ucitaj_podatke(sheet):
    # Dodato clear_cache=True da uvijek vuče najnovije ocjene iz Google Sheets-a
    return conn.read(spreadsheet=spreadsheet_url, worksheet=sheet, ttl=0).dropna(how='all')

# 3. ANALIZA OCJENA (Fokus na kolonu 'Kuvar' iz tvoje slike)
def izracunaj_statistiku():
    df_o = ucitaj_podatke("Ocjene")
    mapa = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
    
    if not df_o.empty and "Ocjena" in df_o.columns and "Kuvar" in df_o.columns:
        # Pretvaramo tekstualne ocjene (Odlično -> 4)
        df_o['Br'] = df_o['Ocjena'].map(mapa)
        # Prosjek po imenu kuvara (Jelena, Dragana...)
        prosjeci_kuvara = df_o.groupby('Kuvar')['Br'].mean().round(1).to_dict()
        return prosjeci_kuvara
    return {}

# --- ADMIN PANEL ---
st.title("👨‍🍳 Admin Upravljanje")

# Dohvatanje imena (Jelena/Dragana) iz lista Meni_Trenutni
df_meni = ucitaj_podatke("Meni_Trenutni")

# Popravljena pretraga za Kuvar 1 i Kuvar 2
k1_red = df_meni[df_meni['Dan'].str.contains("Kuvar 1", na=False)]
k1_ime = k1_red['Jelo'].values[0] if not k1_red.empty else "N/A"

k2_red = df_meni[df_meni['Dan'].str.contains("Kuvar 2", na=False)]
k2_ime = k2_red['Jelo'].values[0] if not k2_red.empty else "N/A"

p_kuvari = izracunaj_statistiku()

t1, t2, t3 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene"])

with t1:
    # Čist prikaz bez HTML koda koji je pravio problem
    st.info(f"👨‍🍳 Glavni kuvari: {k1_ime} ({prikazi_zvijezde(p_kuvari.get(k1_ime, 0.0))}) & {k2_ime} ({prikazi_zvijezde(p_kuvari.get(k2_ime, 0.0))})")
    
    df_narudzbe = ucitaj_podatke("Sheet1")
    if not df_narudzbe.empty:
        dan = st.selectbox("Izaberi dan:", ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak"])
        # Prikaz tabele narudžbi
        prikaz = df_narudzbe[df_narudzbe['Dan'] == f"Ova-{dan}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
        st.table(prikaz)

with t3:
    st.subheader("⭐ Rang lista")
    c1, c2 = st.columns(2)
    # Prikaz metrika za konkretna imena iz tvoje baze
    with c1:
        st.metric(f"Kuvar: {k1_ime}", f"{p_kuvari.get(k1_ime, 0.0)} ⭐")
    with c2:
        st.metric(f"Kuvar: {k2_ime}", f"{p_kuvari.get(k2_ime, 0.0)} ⭐")
    
    st.divider()
    st.dataframe(ucitaj_podatke("Ocjene"), hide_index=True)
