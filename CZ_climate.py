import streamlit as st
import pandas as pd
from plotmanager import PlotManager


@st.cache_data
def all_data():
    return pd.read_csv('Data.csv')

# Veškerá data v proměnné (využití cache pro zrychlení aplikace)
data = all_data()

# Nadpis a deklarace zdroje dat
title = 'PROHLÍŽEČ HISTORICKÝCH KLIMATOLOGICKÝCH DAT'
reference = 'https://www.chmi.cz/files/portal/docs/meteo/ok/open_data/Podminky_uziti_udaju.pdf'
st.markdown(f"<h3 style='text-align: center; color: red'>{title}</h3>", unsafe_allow_html=True)
st.write('**Zdroj dat: Český hydrometeorologický ústav (ČHMÚ)**')
st.write("**Podmínky při využití dat: [Pravidla ČHMÚ](%s)**" % reference)

# Oddělovací čára
st.markdown('---')

# Hlavní widgety - stanice, veličina, počáteční rok
col1, col2, col3 = st.columns(3)

with col1:
    station = st.selectbox('Výběr meteorologické stanice', sorted(list(set(data['Stanice']))))

with col2:
    quantity = st.selectbox('Měřená veličina', PlotManager.quantities.keys())

with col3:
    start_year = st.selectbox('Data od roku', (1980, 1975, 1970, 1965, 1961))

# Vedlejší widgety - filtr měsíčních dat, řazení, zobrazení průměru
col1, col2, col3 = st.columns(3)

with col1:
    filter = st.selectbox('Filtr', PlotManager.filters)

with col2:
    sort = st.radio('Řazení', ['chronologické', 'vzestupné', 'sestupné'])

with col3:
    average = st.radio('Staniční normál', ['1961 - 1990', '1981 - 2010'])

# Speciální widgety při chronologickém řazení - lineární trend a klouzavý průměr
if sort == 'chronologické':

    col1, col2 = st.columns(2)

    with col1:
        lintrend = st.checkbox('Lineární trend')

    with col2:
        roll_avg = st.checkbox('Klouzavý průměr')

# Oddělovací čára
st.markdown('---')

# Instance třídy PlotManager podle výběru stanice
PM = PlotManager(station, data)

# Tisk poznámky, pokud pro danou stanici existuje
if station in PM.station_remarks.keys():
    st.write('Poznámka: ', PM.station_remarks[station])

# Geneze výsledku (omluvná hláška nebo graf, obstarává metoda PlotManager.plot_req(...)
# Liší se případ, kdy je řazení chronologické, nebo sestupné/vzestupné
# U chronologického řazení mohou parametry lintrend a roll_avg nabývat hodnoty True
# Podle toho, co si vybere uživatel pomocí checboxů, které u nechronologických řazení nejsou k dispozici
if sort == 'chronologické':
    result = PM.plot_req(quantity, filter, sort, start_yr=start_year, avg=average, lintrend=lintrend, roll_avg=roll_avg)
else:
    result = PM.plot_req(quantity, filter, sort, start_yr=start_year, avg=average)

# Grafický výstup
# Výsledek typu string je nutné vypsat přes st.write, zato výsledek typu pyplot se musí vypsat přes st.pyplot
# Oboje je možné, protože metoda PlotManager.plot_req vrací buď "omluvný string", nebo graf
if isinstance(result, str):
    st.write(result)
else:
    st.pyplot(result)
