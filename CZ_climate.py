import streamlit as st
import pandas as pd
from plotmanager import PlotManager

# Inicializace promennych, do kterych se ukladaji nepovinne vybery uzivatele
roll_avg_window = None
lintrend = False


@st.cache_data
def data_accessibility():
    '''Metadata pro handling nabidky v jednotlivych widgets'''
    return PlotManager.data_accessibility


# Veškerá data a udaje o jejich dostupnosti v proměnných (využití cache pro zrychlení aplikace)
data_accessibility = data_accessibility()


def average_selection(station, filter, quantity):
    '''Sestavuje nabidku prumeru, ktere lze zobrazit v grafu v zavislosti na dostupnosti dat pro jejich vypocet'''
    accessible_selection = ['Vybrané období']
    cols = [col for col in data_accessibility.columns if col.startswith('Normál')]
    normals = data_accessibility.loc[[(station, filter, quantity)], cols].dropna(how='all', axis=1).columns
    accessible_selection.extend(normals)
    return accessible_selection

# Nadpis a deklarace zdroje dat
title = 'PROHLÍŽEČ HISTORICKÝCH KLIMATOLOGICKÝCH DAT'
reference = 'https://www.chmi.cz/files/portal/docs/meteo/ok/open_data/Podminky_uziti_udaju.pdf'
st.markdown(f"<h3 style='text-align: center; color: red'>{title}</h3>", unsafe_allow_html=True)
st.write('**Zdroj dat: Český hydrometeorologický ústav (ČHMÚ)**')
st.write("**Podmínky při využití dat: [Pravidla ČHMÚ](%s)**" % reference)

# Oddělovací čára
st.markdown('---')

# Hlavní widgety - stanice, veličina, filtr (vybraný měsíc nebo data za celý rok)
col1, col2, col3 = st.columns(3)

with col1:
    station_set = sorted(list(set(data_accessibility.index.get_level_values('Stanice'))))
    station = st.selectbox('Výběr meteorologické stanice', station_set)

with col2:
    quantity = st.selectbox('Měřená veličina', PlotManager.quantities.keys())

with col3:
    filter = st.selectbox('Filtr', PlotManager.filters)


# Vedlejší widgety - filtr měsíčních dat, řazení, zobrazení průměru

with col1:
    year_min = int(data_accessibility.loc[(station, filter, quantity), 'min_year'])
    year_max = int(data_accessibility.loc[(station, filter, quantity), 'max_year'])
    start_yr, end_yr = st.slider('Obdobi', year_min, year_max, (year_min, year_max))

with col2:
    sorting = st.radio('Řazení', ['chronologické', 'vzestupné', 'sestupné'])

with col3:
    average = st.radio('Zobrazený průměr', average_selection(station, filter, quantity))

# Specialni widgety pri chronologickém razeni - linearni trend a klouzavy prumer
# Nove sloupce pomhaji udrzet format, col6 je placeholder
# Widgety pouze tehdy, kdy maji pro vybrany casovy interval smysl, col6 je placeholder

col4, col5, col6 = st.columns(3)

with col4:
    bar_labels = st.checkbox('Popisky dat')

if sorting == 'chronologické':

    with col5:
        if end_yr - start_yr > 1:
            lintrend = st.checkbox('Lineární trend')

    with col6:
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
         'roll_avg_window': roll_avg_window,
         'bar_labels': bar_labels
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

    col7, col8 = st.columns(2)

    with col7:
        st.write('Základní statistika')
        st.table(PM.table_req('stat'))

    if lintrend:
        with col8:
            st.write('Regresní parametry')
            st.table(PM.table_req('reg'))


