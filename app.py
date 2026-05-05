import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import re
import time

# --- 1. STILIZACIJA ---
st.set_page_config(page_title="Catering System", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important;}
    
    .kuhinja-box {
        background-color: #11141C;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 25px;
        color: white;
    }
    .smjena-header-text {
        font-size: 1.6rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .table-header {
        display: flex;
        justify-content: space-between;
        color: #666;
        font-size: 0.75rem;
        font-weight: bold;
        border-bottom: 1px solid #333;
        padding-bottom: 8px;
        margin-bottom: 15px;
    }
    .jelo-title {
        background-color: #1A1C23;
        color: #E24A4A;
        padding: 10px 15px;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 10px;
    }
    .row-firma {
        display: flex;
        justify-content: space-between;
        padding: 8px 15px;
        border-bottom: 1px solid #222;
    }
    .jelo-ukupno {
        text-align: right;
        color: #00FF00;
        font-weight: bold;
        padding: 10px 15px;
    }
    
    .status-badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-left: 10px;
    }
    
    .info-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }
    .info-card { flex: 1; padding: 15px; border-radius: 10px; text-align: center; color: white; font-weight: bold; }
    .blue-card { background-color: #1e3a5f; border: 1px solid #3b82f6; }
    .yellow-card { background-color: #3e3e10; border: 1px solid #ca8a04; }
    .green-card { background-color: #143e2a; border: 1px solid #16a34a; }
    </style>
""", unsafe_allow_html=True)

# --- 2. POMOĆNE FUNKCIJE ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
# Definišemo firme (bez admina) za status traku
sve_firme = ["Lattonedil", "PVA Group", "Esintec", "ActivBH"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

def ucitaj_sheet(name):
    try: return conn.read(spreadsheet=spreadsheet_url, worksheet=name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    pj = df_o.groupby('Jelo')['Numericka'].mean().round(1).sort_values(ascending=False).to_dict()
    pk = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return pj, pk

def izvadi_sat_iz_roka(rok_tekst):
    try:
        brojevi = re.findall(r'\d+', str(rok_tekst))
        return int(brojevi[0]) if brojevi else 16
    except:
        return 16

# --- 3. LOGIN SISTEM ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava</h1>", unsafe_allow_html=True)
    u = st.text_input("Korisnik")
    p = st.text_input("Lozinka", type="password")
    if st.button("Prijavi se", use_container_width=True):
        if u in users and users[u] == p:
            st.session_state["logged_in"], st.session_state["user"] = True, u
            st.rerun()
else:
    # --- 4. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t1, t2, t3, t4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t1: # KUHINJA + STATUSI
            df_nar = ucitaj_sheet("Sheet1")
            df_meni_t = ucitaj_sheet("Meni_Trenutni")
            rok_tekst = df_meni_t[df_meni_t['Dan']=='Rok']['Jelo'].values[0] if not df_meni_t.empty else "16:00"
            sat_limita = izvadi_sat_iz_roka(rok_tekst)
            
            dan_sel = st.selectbox("Izaberi dan:", dani_std)
            
            # --- STATUSI FIRMI (VIZUELNI PREGLED) ---
            st.markdown("### 🕒 Statusi narudžbi za izabrani dan")
            cols = st.columns(len(sve_firme))
            sada = datetime.now() + timedelta(hours=2)
            danas_idx = sada.weekday()
            izabrani_idx = dani_std.index(dan_sel)
            trenutni_sat = sada.hour
            
            for i, f in enumerate(sve_firme):
                if not df_nar.empty:
                    unio = not df_nar[(df_nar['Firma'] == f) & (df_nar['Dan'] == f"Ova-{dan_sel}")].empty
                else:
                    unio = False
                
                # Logika za boju
                prošao_rok = (izabrani_idx == danas_idx + 1 and trenutni_sat >= sat_limita) or (izabrani_idx <= danas_idx)
                
                if unio:
                    status_text = "🟢 Naručeno"
                elif prošao_rok:
                    status_text = "🔴 Kasne"
                else:
                    status_text = "🟡 Na čekanju"
                
                cols[i].markdown(f"**{f}** \n{status_text}")
            
            st.divider()

            if not df_nar.empty:
                dan_data = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"]
                datum_str = (datetime.now() + timedelta(hours=2)).strftime('%d.%m.%Y')

                # HTML ZA ŠTAMPU (Nepromijenjeno)
                html_izvjestaj = f"<html><head><meta charset='utf-8'><style>body {{ font-family: Arial; padding: 20px; }} .header {{ background: #E24A4A; color: white; padding: 20px; text-align: center; border-radius: 10px; }} .card {{ border: 1px solid #ddd; margin-top: 20px; border-radius: 8px; overflow: hidden; }} .card-h {{ background: #1A1C23; color: white; padding: 12px; font-weight: bold; }} table {{ width: 100%; border-collapse: collapse; }} th {{ background: #f2f2f2; text-align: left; padding: 10px; }} td {{ padding: 10px; border-bottom: 1px solid #eee; }} .jelo-row {{ background: #fff5f5; font-weight: bold; color: #E24A4A; }} .total-row {{ background: #f9f9f9; text-align: right; padding: 10px; font-weight: bold; border-top: 2px solid #ddd; }}</style></head><body><div class='header'><h1>LISTA ZA KUHINJU</h1><p>{dan_sel}, {datum_str}</p></div>"
                for smj in ["I", "II", "III"]:
                    smj_d = dan_data[dan_data['Smjena'] == smj]
                    if not smj_d.empty:
                        html_izvjestaj += f'<div class="card"><div class="card-h">🕒 SMJENA {smj}</div><table><thead><tr><th>JELO / FIRMA</th><th style="text-align:right">KOL.</th></tr></thead><tbody>'
                        for jelo, j_d in smj_d.groupby("Jelo"):
                            html_izvjestaj += f'<tr class="jelo-row"><td>🍴 {jelo}</td><td style="text-align:right">{int(j_d["Kolicina"].sum())} UKUPNO</td></tr>'
                            for _, r in j_d.iterrows():
                                html_izvjestaj += f'<tr><td style="padding-left:20px;">🏢 {r["Firma"]}</td><td style="text-align:right">{int(r["Kolicina"])} kom</td></tr>'
                        html_izvjestaj += f'</tbody></table><div class="total-row">UKUPNO SMJENA {smj}: {int(smj_d["Kolicina"].sum())} obroka</div></div>'
                html_izvjestaj += "</body></html>"

                st.download_button("📥 PREUZMI LISTU ZA ŠTAMPU", data=html_izvjestaj, file_name=f"Kuhinja_{dan_sel}.html", mime="text/html", use_container_width=True)
                st.divider()

                for smj in ["I", "II", "III"]:
                    smj_d = dan_data[dan_data['Smjena'] == smj]
                    if not smj_d.empty:
                        html_box = f'<div class="kuhinja-box"><div class="smjena-header-text">🕒 SMJENA {smj}</div>'
                        html_box += '<div class="table-header"><span>JELO / FIRMA</span><span>KOLIČINA</span></div>'
                        for jelo, j_d in smj_d.groupby("Jelo"):
                            html_box += f'<div class="jelo-title">{jelo}</div>'
                            for _, r in j_d.iterrows():
                                html_box += f'<div class="row-firma"><span>🏢 {r["Firma"]}</span><span style="font-weight:bold;">{int(r["Kolicina"])} kom</span></div>'
                            html_box += f'<div class="jelo-ukupno">UKUPNO {jelo}: {int(j_d["Kolicina"].sum())}</div>'
                        html_box += '</div>'
                        st.markdown(html_box, unsafe_allow_html=True)

        with t2: # EDIT MENI
            od_m = st.radio("Uredi:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"f_{od_m}"):
                c1,c2,c3 = st.columns(3)
                v_s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty and len(df_m[df_m['Dan']=='Sedmica'])>0 else ""
                v_r = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty and len(df_m[df_m['Dan']=='Rok'])>0 else ""
                v_k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty and len(df_m[df_m['Dan']=='Kuvar'])>0 else ""
                n_s = c1.text_input("Period:", v_s); n_r = c2.text_input("Rok:", v_r); n_k = c3.text_input("Kuvar:", v_k)
                
                novi = [{"Dan":"Sedmica","Jelo":n_s},{"Dan":"Rok","Jelo":n_r},{"Dan":"Kuvar","Jelo":n_k}]
                for d in dani_std:
                    st.markdown(f"**{d}**")
                    p_jela = df_m[df_m['Dan']==d]['Jelo'].tolist() if not df_m.empty else []
                    col1, col2, col3 = st.columns(3)
                    p_cols = [col1, col2, col3]
                    for i in range(3):
                        stara = p_jela[i] if i < len(p_jela) else ""
                        un = p_cols[i].text_input(f"Jelo {i+1}", stara, key=f"e_{od_m}_{d}_{i}")
                        if un: novi.append({"Dan":d, "Jelo":un})
                if st.form_submit_button("SAČUVAJ"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi))
                    st.success("Sačuvano!"); time.sleep(1); st.rerun()

        with t3: # OCJENE + SEMAFOR (DASHBOARD)
            df_o = ucitaj_sheet("Ocjene")
            pj, pk = izracunaj_prosjeke()
            
            # Semafor / Dashboard
            st.subheader("📊 Semafor popularnosti jela")
            if pj:
                df_pj = pd.DataFrame(list(pj.items()), columns=['Jelo', 'Ocjena'])
                st.bar_chart(df_pj.set_index('Jelo'))
                
                col_best, col_worst = st.columns(2)
                best_jelo = df_pj.iloc[0]
                worst_jelo = df_pj.iloc[-1]
                col_best.success(f"🏆 HIT MJESECA: **{best_jelo['Jelo']}** ({best_jelo['Ocjena']} ⭐)")
                col_worst.error(f"⚠️ NAJLOŠIJE: **{worst_jelo['Jelo']}** ({worst_jelo['Ocjena']} ⭐)")
            
            st.divider()
            if pk:
                st.write("**👨‍🍳 Ocjene kuvara:**")
                cols = st.columns(len(pk))
                for i, (k, v) in enumerate(pk.items()): cols[i].metric(f"{k}", f"{v} ⭐")
            
            st.divider()
            st.dataframe(df_o, use_container_width=True, hide_index=True)

        with t4: # RESET
            if st.button("🚀 ROTIRAJ SEDMICE"):
                df_n = ucitaj_sheet("Meni_Naredni")
                if not df_n.empty:
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_n)
                    st.success("Rotirano!"); time.sleep(1); st.rerun()

    # --- 5. KLIJENT PANEL (Nepromijenjeno) ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_o, t_n, t_h, t_oc = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna", "📜 Istorija", "⭐ Ocijeni"])
        pj, _ = izracunaj_prosjeke()

        def render_c(sh, pref, lock):
            df_m = ucitaj_sheet(sh); df_sve = ucitaj_sheet("Sheet1")
            s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty else "/"
            rok_tekst = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty else "16:00"
            k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty else "/"
            
            sat_limita = izvadi_sat_iz_roka(rok_tekst)
            sada = datetime.now() + timedelta(hours=2) 
            danas_idx = sada.weekday()
            trenutni_sat = sada.hour
            
            if lock:
                if trenutni_sat < sat_limita:
                    rok_vrijeme = sada.replace(hour=sat_limita, minute=0, second=0, microsecond=0)
                    razlika = (rok_vrijeme - sada).seconds
                    pre_sati = razlika // 3600
                    pre_min = (razlika % 3600) // 60
                    st.info(f"⏳ **Narudžbe za SUTRA su otvorene još: {pre_sati}h {pre_min}min**")
                else:
                    st.error(f"🔒 **Rok ({rok_tekst}) za sutrašnju narudžbu je istekao!**")

            st.markdown(f'<div class="info-container"><div class="info-card blue-card">📅 {s}</div><div class="info-card yellow-card">⏰ ROK: {rok_tekst}</div><div class="info-card green-card">👨‍🍳 {k}</div></div>', unsafe_allow_html=True)
            
            with st.form(f"f_{pref}"):
                unose = []
                for d in dani_std:
                    idx = dani_std.index(d)
                    if not lock: dis = False
                    else:
                        is_proslost = danas_idx > idx
                        is_danas = danas_idx == idx
                        is_sutra = (danas_idx + 1 == idx)
                        if is_proslost or is_danas: dis = True
                        elif is_sutra: dis = (trenutni_sat >= sat_limita)
                        else: dis = False
                    
                    icon = "🔒" if dis else "📅"
                    with st.container(border=True):
                        st.markdown(f"#### {icon} {d}")
                        jela = df_m[df_m['Dan']==d]['Jelo'].tolist() if not df_m.empty else []
                        for j in jela:
                            st.write(f"**{j}** {f'(⭐ {pj.get(j)})' if pj.get(j) else ''}")
                            c1,c2,c3 = st.columns(3)
                            def g_v(sn):
                                if df_sve.empty: return 0
                                m = df_sve[(df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{pref}-{d}") & (df_sve['Jelo']==j) & (df_sve['Smjena']==sn)]
                                return int(m['Kolicina'].iloc[0]) if not m.empty else 0
                            k1=c1.number_input("I SMJENA",0,100,g_v("I"),key=f"{pref}{d}{j}1",disabled=dis)
                            k2=c2.number_input("II SMJENA",0,100,g_v("II"),key=f"{pref}{d}{j}2",disabled=dis)
                            k3=c3.number_input("III SMJENA",0,100,g_v("III"),key=f"{pref}{d}{j}3",disabled=dis)
                            for v, sn in zip([k1,k2,k3],["I","II","III"]):
                                if v > 0: unose.append({"Firma":st.session_state['user'], "Dan":f"{pref}-{d}", "Jelo":j, "Kolicina":v, "Smjena":sn})
                if st.form_submit_button("SAČUVAJ"):
                    df_ost = df_sve[~((df_sve['Firma']==st.session_state['user']) & (df_sve['Dan'].str.startswith(pref)))] if not df_sve.empty else pd.DataFrame()
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_ost, pd.DataFrame(unose)]))
                    st.success("Spremljeno!"); time.sleep(1); st.rerun()

        with t_o: render_c("Meni_Trenutni", "Ova", True)
        with t_n: render_c("Meni_Naredni", "Naredna", False)
        with t_h:
            df_sve = ucitaj_sheet("Sheet1")
            if not df_sve.empty:
                moje = df_sve[df_sve['Firma'] == st.session_state['user']]
                st.dataframe(moje, use_container_width=True, hide_index=True)
        with t_oc:
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            k_t = df_m_t[df_m_t['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m_t.empty else "N/A"
            jela = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist() if not df_m_t.empty else []
            with st.form("f_ocj"):
                j_sel = st.selectbox("Izaberi jelo:", jela)
                oc = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                kom = st.text_area("Komentar:")
                if st.form_submit_button("POŠALJI"):
                    df_o = ucitaj_sheet("Ocjene")
                    novi = pd.DataFrame([{"Firma":st.session_state['user'], "Jelo":j_sel, "Ocjena":oc, "Komentar":kom, "Kuvar":k_t}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o, novi]))
                    st.success("Hvala!"); time.sleep(1); st.rerun()
