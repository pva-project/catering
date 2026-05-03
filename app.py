import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. ČISTI PRIKAZ ZVJEZDICA (Bez HTML koda koji kvari ekran)
def tekstualne_zvijezde(ocjena):
    if pd.isna(ocjena) or ocjena == 0:
        return "☆☆☆☆☆ (0.0)"
    pune = int(round(ocjena))
    # Direktno ispisivanje simbola koji rade na svakom telefonu
    return "⭐" * pune + "☆" * (5 - pune) + f" ({ocjena})"

# 2. POVEZIVANJE S TABELOM
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

def ucitaj_list(ime_lista):
    return conn.read(spreadsheet=spreadsheet_url, worksheet=ime_lista, ttl=0).dropna(how='all')

# 3. STATISTIKA PO IMENU (Jelena, Dragana...)
def dohvati_rejtinge():
    df_o = ucitaj_list("Ocjene")
    vrijednosti = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
    
    if not df_o.empty and "Ocjena" in df_o.columns and "Kuvar" in df_o.columns:
        df_o['Bodovi'] = df_o['Ocjena'].map(vrijednosti)
        # Grupisanje tačno po imenima iz kolone F tvoje tabele
        return df_o.groupby('Kuvar')['Bodovi'].mean().round(1).to_dict()
    return {}

# --- ADMIN PANEL ---
st.title("👨‍🍳 Admin Upravljanje")

# Izvlačenje pravih imena iz Menija (kolona Jelo gdje je Dan 'Kuvar 1/2')
df_m = ucitaj_list("Meni_Trenutni")
k1_ime = df_m[df_m['Dan'].str.contains("Kuvar 1", na=False)]['Jelo'].values[0] if not df_m.empty else "N/A"
k2_ime = df_m[df_m['Dan'].str.contains("Kuvar 2", na=False)]['Jelo'].values[0] if not df_m.empty else "N/A"

rejtingzi = dohvati_rejtinge()

t1, t2, t3 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene"])

with t1:
    # INFO BOX: Prikazuje ime i zvjezdice bez grešaka u kodu
    st.info(f"👨‍🍳 Kuvari: {k1_ime} ({tekstualne_zvijezde(rejtingzi.get(k1_ime, 0.0))}) | {k2_ime} ({tekstualne_zvijezde(rejtingzi.get(k2_ime, 0.0))})")
    
    df_s1 = ucitaj_list("Sheet1")
    if not df_s1.empty:
        izbor_dana = st.selectbox("Dan:", ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak"])
        # Tabela narudžbi koja ti je radila
        prikaz = df_s1[df_s1['Dan'] == f"Ova-{izbor_dana}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
        st.table(prikaz)

with t3:
    st.subheader("⭐ Rang lista")
    c1, c2 = st.columns(2)
    # Metrike koje sada vuku ispravne prosjeke za Jelenu i Draganu
    c1.metric(k1_ime, f"{rejtingzi.get(k1_ime, 0.0)} ⭐")
    c2.metric(k2_ime, f"{rejtingzi.get(k2_ime, 0.0)} ⭐")
    
    st.divider()
    st.dataframe(ucitaj_list("Ocjene"), hide_index=True)
