import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import re
import time

# --- 1. STILIZACIJA (Moderni Dashboard + Chef Cards) ---
st.set_page_config(page_title="Catering System", layout="centered")

st.markdown("""
    <style>
    /* Sakrivanje Streamlit elemenata */
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important; background-color: #0E1117;}

    /* Glavni Naslov */
    .admin-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: white;
        margin-bottom: 20px;
        text-align: center;
    }

    /* Container za statuse firmi (Grid layout) */
    .status-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin: 15px 0;
    }

    .status-card {
        background: #1A1C23;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
    }

    .status-f-name { font-size: 0.8rem; color: #999; margin-bottom: 5px; font-weight: 600; text-transform: uppercase; }
    
    .dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .dot-green { background-color: #00FF41; box-shadow: 0 0 8px #00FF41; }
    .dot-red { background-color: #FF3131; box-shadow: 0 0 8px #FF3131; }
    .dot-yellow { background-color: #FFD700; box-shadow: 0 0 8px #FFD700; }

    .status-text { font-size: 0.8rem; font-weight: bold; }
    .st-green { color: #00FF41; }
    .st-red { color: #FF3131; }
    .st-yellow { color: #FFD700; }

    /* --- CHEF CARDS DIZAJN --- */
    .chef-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }

    .chef-card {
        background: linear-gradient(145deg, #1A1C23, #11141C);
        border: 1px solid #333;
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border-bottom: 3px solid #FFD700;
    }

    .chef-avatar {
        background: #2D323E;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px;
        font-size: 1.5rem;
        border: 2px solid #333;
    }

    .chef-name { color: white; font-size: 1rem; font-weight: bold; margin-bottom: 5px; }
    .chef-rating { color: #FFD700; font-size: 1.3rem; font-weight: 800; text-shadow: 0 0 10px rgba(255, 215, 0, 0.4); }

    /* Dugme za print */
    .stDownloadButton button {
        background: linear-gradient(135deg, #E24A4A 0%, #8B0000 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 12px !important;
        width: 100%;
        text-transform: uppercase;
        margin-top: 10px;
    }

    .kuhinja-box {
        background-color: #161922;
        border-radius: 15px;
        padding: 20px;
        border-left: 5px solid #E24A4A;
        margin-bottom: 20px;
        color: white;
    }
    .smjena-header-text { font-size: 1.4rem; font-weight: bold; margin-bottom: 10px; }
    .jelo-title { background-color: #1A1C23; color: #E24A4A; padding: 10px; border-radius: 5px; font-weight: bold; margin-top: 10px; }
    .row-firma { display: flex; justify-content: space-between; padding: 8px 10px; border-bottom: 1px solid #222; font-size: 0.9rem; }
    .jelo-ukupno { text-align: right; color: #00FF00; font-weight: bold; padding: 10px; }

    .info-container { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px; }
    .info-card { flex: 1; padding: 10px; border-radius: 8px; text-align: center; color: white; font-weight: bold; font-size: 0.8rem; }
    .blue-card { background-color: #1e3a5f; border: 1px solid #3b82f6; }
    .yellow-card { background-color: #3e3e10; border: 1px solid #ca8a04; }
    .green-card { background-color: #143e2a; border: 1px solid #16a34a; }
    </style>
""", unsafe_allow_html=True)

# --- 2. POMOĆNE FUNKCIJE ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
sve_firme = ["Lattonedil", "PVA Group", "Esintec", "ActivBH"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321", "Veletrgovina Kancelarija": "nina321}

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
        st.markdown('<div class="admin-title">👨‍🍳 Admin Upravljanje</div>', unsafe_allow_html=True)
        t1, t2, t3, t4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t1:
            df_nar = ucitaj_sheet("Sheet1")
            df_meni_t = ucitaj_sheet("Meni_Trenutni")
            rok_tekst = df_meni_t[df_meni_t['Dan']=='Rok']['Jelo'].values[0] if not df_meni_t.empty else "16:00"
            sat_limita = izvadi_sat_iz_roka(rok_tekst)
            dan_sel = st.selectbox("Izaberi dan:", dani_std)
            
            st.markdown("### 🕒 Statusi narudžbi")
            status_html = '<div class="status-container">'
            sada = datetime.now() + timedelta(hours=2)
            danas_idx = sada.weekday()
            izabrani_idx = dani_std.index(dan_sel)
            trenutni_sat = sada.hour

            for f in sve_firme:
                unio = not df_nar[(df_nar['Firma'] == f) & (df_nar['Dan'] == f"Ova-{dan_sel}")].empty if not df_nar.empty else False
                prošao_rok = (izabrani_idx == danas_idx + 1 and trenutni_sat >= sat_limita) or (izabrani_idx <= danas_idx)
                if unio: cls, dot, txt = "st-green", "dot-green", "NARUČENO"
                elif prošao_rok: cls, dot, txt = "st-red", "dot-red", "KASNE"
                else: cls, dot, txt = "st-yellow", "dot-yellow", "ČEKANJE"
                status_html += f'<div class="status-card"><div class="status-f-name">{f}</div><div class="status-text {cls}"><span class="dot {dot}"></span>{txt}</div></div>'
            status_html += '</div>'
            st.markdown(status_html, unsafe_allow_html=True)
            st.divider()

            if not df_nar.empty:
                dan_data = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"]
                datum_str = (datetime.now() + timedelta(hours=2)).strftime('%d.%m.%Y')
                html_izvjestaj = f"<html><head><meta charset='utf-8'><style>body {{ font-family: Arial; padding: 20px; }} .header {{ background: #E24A4A; color: white; padding: 15px; text-align: center; border-radius: 10px; }} .card {{ border: 1px solid #ddd; margin-top: 15px; border-radius: 8px; overflow: hidden; }} .card-h {{ background: #1A1C23; color: white; padding: 10px; font-weight: bold; }} table {{ width: 100%; border-collapse: collapse; }} td {{ padding: 10px; border-bottom: 1px solid #eee; }} .jelo-row {{ background: #fff5f5; font-weight: bold; color: #E24A4A; }} .total-row {{ background: #f9f9f9; text-align: right; padding: 10px; font-weight: bold; }}</style></head><body><div class='header'><h1>LISTA ZA KUHINJU</h1><p>{dan_sel}, {datum_str}</p></div>"
                for smj in ["I", "II", "III"]:
                    smj_d = dan_data[dan_data['Smjena'] == smj]
                    if not smj_d.empty:
                        html_izvjestaj += f'<div class="card"><div class="card-h">🕒 SMJENA {smj}</div><table><tbody>'
                        for jelo, j_d in smj_d.groupby("Jelo"):
                            html_izvjestaj += f'<tr class="jelo-row"><td>🍴 {jelo}</td><td style="text-align:right">{int(j_d["Kolicina"].sum())} UK.</td></tr>'
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

        with t3: # OCJENE + DASHBOARD + CHEF CARDS
            pj, pk = izracunaj_prosjeke()
            st.subheader("📊 Popularnost jela")
            if pj:
                df_pj = pd.DataFrame(list(pj.items()), columns=['Jelo', 'Ocjena'])
                st.bar_chart(df_pj.set_index('Jelo'))
                cb, cw = st.columns(2)
                cb.success(f"🏆 HIT: **{df_pj.iloc[0]['Jelo']}**")
                cw.error(f"⚠️ LOŠE: **{df_pj.iloc[-1]['Jelo']}**")
            st.divider()
            
            # --- CHEF CARDS SEKCIJA ---
            if pk:
                st.markdown("### 👨‍🍳 Naši Kuvari")
                chef_html = '<div class="chef-container">'
                for ime, ocjena in pk.items():
                    chef_html += f'<div class="chef-card"><div class="chef-avatar">👨‍🍳</div><div class="chef-name">{ime}</div><div class="chef-rating">{ocjena} <span style="font-size:0.9rem;">⭐</span></div></div>'
                chef_html += '</div>'
                st.markdown(chef_html, unsafe_allow_html=True)
            
            st.divider()
            df_o = ucitaj_sheet("Ocjene")
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
                    st.info(f"⏳ **ROK: Još {(razlika // 3600)}h {(razlika % 3600) // 60}min**")
                else: st.error(f"🔒 **Rok ({rok_tekst}) je istekao!**")
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
                        dis = True if (is_proslost or is_danas or (is_sutra and trenutni_sat >= sat_limita)) else False
                    with st.container(border=True):
                        st.markdown(f"#### {'🔒' if dis else '📅'} {d}")
                        jela = df_m[df_m['Dan']==d]['Jelo'].tolist() if not df_m.empty else []
                        for j in jela:
                            st.write(f"**{j}** {f'(⭐ {pj.get(j)})' if pj.get(j) else ''}")
                            c1,c2,c3 = st.columns(3)
                            def g_v(sn):
                                if df_sve.empty: return 0
                                m = df_sve[(df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{pref}-{d}") & (df_sve['Jelo']==j) & (df_sve['Smjena']==sn)]
                                return int(m['Kolicina'].iloc[0]) if not m.empty else 0
                            k1=c1.number_input("I",0,100,g_v("I"),key=f"{pref}{d}{j}1",disabled=dis)
                            k2=c2.number_input("II",0,100,g_v("II"),key=f"{pref}{d}{j}2",disabled=dis)
                            k3=c3.number_input("III",0,100,g_v("III"),key=f"{pref}{d}{j}3",disabled=dis)
                            for v, sn in zip([k1,k2,k3],["I","II","III"]):
                                if v > 0: unose.append({"Firma":st.session_state['user'], "Dan":f"{pref}-{d}", "Jelo":j, "Kolicina":v, "Smjena":sn})
                if st.form_submit_button("SAČUVAJ"):
                    df_ost = df_sve[~((df_sve['Firma']==st.session_state['user']) & (df_sve['Dan'].str.startswith(pref)))] if not df_sve.empty else pd.DataFrame()
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_ost, pd.DataFrame(unose)]))
                    st.success("Spremljeno!"); time.sleep(1); st.rerun()

        with t_o: render_c("Meni_Trenutni", "Ova", True)
        with t_n: render_c("Meni_Naredni", "Naredna", False)
        with t_h: st.dataframe(ucitaj_sheet("Sheet1")[lambda x: x['Firma'] == st.session_state['user']] if not ucitaj_sheet("Sheet1").empty else pd.DataFrame(), use_container_width=True, hide_index=True)
        with t_oc:
            with st.form("f_ocj"):
                jela = ucitaj_sheet("Meni_Trenutni")[lambda x: x['Dan'].isin(dani_std)]['Jelo'].unique().tolist()
                j_sel = st.selectbox("Jelo:", jela); oc = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                kom = st.text_area("Komentar:")
                if st.form_submit_button("POŠALJI"):
                    df_o = ucitaj_sheet("Ocjene")
                    novi = pd.DataFrame([{"Firma":st.session_state['user'], "Jelo":j_sel, "Ocjena":oc, "Komentar":kom, "Kuvar": ucitaj_sheet("Meni_Trenutni")[lambda x: x['Dan']=='Kuvar']['Jelo'].values[0]}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o, novi]))
                    st.success("Hvala!"); time.sleep(1); st.rerun()
