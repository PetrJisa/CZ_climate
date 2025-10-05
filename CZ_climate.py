import streamlit as st
import pandas as pd
from plotmanager import PlotManager

# Inicializace promennych, do kterych se ukladaji nepovinne vybery uzivatele
roll_avg_window = None
lintrend = False


@st.cache_data
def data_accessibility():
    return PlotManager.data_accessibility

# Veškerá data a udaje o jejich dostupnosti v proměnných (využití cache pro zrychlení aplikace)
data_accessibility = data_accessibility()

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
    station_set = sorted(list(set(data_accessibility.index.get_level_values('Stanice'))))
    station = st.selectbox('Výběr meteorologické stanice', station_set)

with col2:
    quantity = st.selectbox('Měřená veličina', PlotManager.quantities.keys())

with col3:
    year_min = data_accessibility.loc[(station, quantity), 'rok_min']
    year_max = data_accessibility.loc[(station, quantity), 'rok_max']
    start_yr, end_yr = st.slider('Obdobi', year_min, year_max, (year_min, year_max))

# Vedlejší widgety - filtr měsíčních dat, řazení, zobrazení průměru

with col1:
    filter = st.selectbox('Filtr', PlotManager.filters)

with col2:
    sorting = st.radio('Řazení', ['chronologické', 'vzestupné', 'sestupné'])

with col3:
    average = st.radio('Zobrazený průměr', PlotManager.avg_selections)

# Specialni widgety pri chronologickém razeni - linearni trend a klouzavy prumer
# Nove sloupce pomhaji udrzet format, col6 je placeholder
# Widgety pouze tehdy, kdy maji pro vybrany casovy interval smysl, col6 je placeholder

if sorting == 'chronologické':

    col4, col5, col6 = st.columns(3)

    with col4:
        if end_yr - start_yr > 1:
            lintrend = st.checkbox('Lineární trend')

    with col5:
        if end_yr - start_yr > 4:
            roll_avg_required = st.checkbox('Klouzavý průměr')

            if roll_avg_required:
                max_window_width = end_yr - start_yr - 1
                roll_avg_window = st.slider('Šířka okna', 3, max_window_width, min(max_window_width, 10))

# Oddělovací čára
st.markdown('---')

# Slovnik s uzivatelskym vyberem
user_selection = \
        {'location': station,
         'filter': filter,
         'quantity': quantity,
         'sorting': sorting,
         'start_yr': start_yr,
         'end_yr': end_yr,
         'avg': average,
         'lintrend': lintrend,
         'roll_avg_window': roll_avg_window
         }

# Instance třídy PlotManager podle výběru stanice
PM = PlotManager(user_selection)

# Tisk poznámky, pokud pro danou stanici existuje
if station in PM.station_remarks.keys():
    st.write('Poznámka: ', PM.station_remarks[station])

# Geneze hlavniho vysledku - graf nebo hlaska, ze data nejsou k dispozici
# Pokud metoda plot_req() vrati omluvny string, ze data nejsou k dispozici, vytiskne se
# Jinak se importuje vykresleny graf pro vybranou uzivatelskou selekci
main_result = PM.plot_req()

if isinstance(main_result, str):
    st.write(main_result)
else:
    st.pyplot(main_result)
