import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ... (zadrži konfiguraciju i stilove iz prethodnog koda)

def analiziraj_podatke_kuvara(k1_ime, k2_ime):
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns:
        return {}, 0.0, 0.0
    
    # Pretvaranje tekstualnih ocjena u brojeve
    mapa = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa)
    
    # Prosjek po jelima
    prosjeci_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    
    # KLJUČNA ISPRAVKA: Računanje prosjeka za kuvara na osnovu kolone 'Kuvar' u tabeli 'Ocjene'
    # Provjeravamo da li kolona 'Kuvar' postoji u tabeli
    k1_skor = 0.0
    k2_skor = 0.0
    
    if 'Kuvar' in df_o.columns:
        # Filtriramo ocjene prema tačnom imenu kuvara koje je upisano u Meni_Trenutni
        k1_skor = df_o[df_o['Kuvar'] == k1_ime]['Numericka'].mean()
        k2_skor = df_o[df_o['Kuvar'] == k2_ime]['Numericka'].mean()
    
    return prosjeci_jela, round(pd.Series(k1_skor).fillna(0).iloc[0], 1), round(pd.Series(k2_skor).fillna(0).iloc[0], 1)

# --- UNUTAR ADMIN PANELA ---
df_m_t = ucitaj_sheet("Meni_Trenutni")

# Povlačenje imena kuvara iz tabele 'Meni_Trenutni' (provjeri da li su u koloni 'Dan' nazivi 'Kuvar 1' i 'Kuvar 2')
k1_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 1']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 1'].empty else "Nije unesen"
k2_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 2']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 2'].empty else "Nije unesen"

# Analiza sa povučenim imenima
prosjeci_jela, skor_k1, skor_k2 = analiziraj_podatke_kuvara(k1_ime, k2_ime)

# --- PRIKAZ U TABU OCJENE ---
with t_a3:
    st.subheader("⭐ Rang lista kuvara")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Kuvar 1: {k1_ime}**")
        st.markdown(renderuj_zvezdice(skor_k1), unsafe_allow_html=True)
    with col2:
        st.markdown(f"**Kuvar 2: {k2_ime}**")
        st.markdown(renderuj_zvezdice(skor_k2), unsafe_allow_html=True)
