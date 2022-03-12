import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


class PlotManager:
    '''Manages the plotting of climatological data.
    If there are no data for plot, it returns only the message regarding the data inavailability'''

    quantities = \
        {'Srážky': {'column': 'Precipitations_sum', 'color': 'blue', 'ylabel': 'Suma srážek (mm)'},
         'Teplota': {'column': 'Temperatures_avg', 'color': 'green', 'ylabel': 'Průměrná teplota (°C)'},
         'Sluneční svit': {'column': 'Sunshine_sum', 'color': 'yellow', 'ylabel': 'Úhrn slunečního svitu (hod)'},
         'Sníh': {'column': 'Snow_height_max', 'color': 'lightblue', 'ylabel': 'Maximum sněhové pokrývky (cm)'},
         'Vítr': {'column': 'Wind_avg', 'color': 'brown', 'ylabel': 'Průměrná rychlost větru (m/s)'},
         'Arktické dny': {'column': 'Arctic_days', 'color': 'purple', 'ylabel': 'Počet arktických dnů (Tmax < -10 °C)'},
         'Ledové dny': {'column': 'Ice_days', 'color': 'darkblue', 'ylabel': 'Počet ledových dnů (Tmax < 0 °C)'},
         'Letní dny': {'column': 'Summer_days', 'color': 'brown', 'ylabel': 'Počet letních dnů (Tmax >= 25 °C)'},
         'Tropické dny': {'column': 'Tropical_days', 'color': 'red', 'ylabel': 'Počet tropických dnů (Tmax >= 30 °C)'},
         }

    filters = \
        ['rok',
         'leden',
         'únor',
         'březen',
         'duben',
         'květen',
         'červen',
         'červenec',
         'srpen',
         'září',
         'říjen',
         'listopad',
         'prosinec']


    station_remarks = \
        {'Plzeň - Bolevec': 'Počty charakteristických dní podle maximální teploty dostupné až od roku 1969',
         'Staňkov': 'Sluneční svit k dispozici až od roku 2002',
         'Děčín': 'Chybí data z období 1972 - 1992 a data z měření úhrnu slunečního svitu od roku 1979',
         'Vizovice': 'Sluneční svit k dispozici až od roku 2008'}


    def __init__(self, location, data):

        self.location = location
        self.data = data.query("Stanice == @location").set_index('Rok')


    def plot_req(self, quantity: str, filter: str, sorting='chronologické', start_yr=1980, avg='1961 - 1990'):
        '''Creates the plot according to the requirements from the user, which are defined by following parameters
        filter - month (leden, únor... prosinec) or year (rok)
        sorting - asc is ascending, desc is descending, default None (sorted by time)'''
        # RCparams
        plt.rcParams.update({'font.size': 13, 'text.color': 'black', 'axes.labelcolor': 'black'})

        # Sloupec, který si bereme z DataFrame
        column = PlotManager.quantities[quantity]['column']

        # Tady tvořím výchozí DataFrame, přičemž záleží, jestli chci charakteristické dny, nebo jinou veličinu
        # U charakteristických dní totiž nejsou v řádku "rok" hodnoty, což je třeba řešit agregací
        if ('dny' in quantity) and (filter == 'rok'):
            plot_df = self.data[[column]].loc[start_yr:].groupby('Rok').sum()
        else:
            plot_df = self.data.loc[start_yr:].query("Měsíc == @filter")[[column]]

        # Tady vyhodíme řádky, ve kterých je hodnota NaN
        plot_df = plot_df.dropna()

        # Tady je výchozí DataFrame tříděna, je-li parametr sorting asc nebo desc
        # Je-li parametr sorting defaultní (None), přidávám sloupec s 5-letým klouzavým průměrem
        if sorting == 'chronologické':
            plot_df['Rolling_5y'] = plot_df[column].rolling(5).mean()
        elif sorting == 'vzestupné':
            plot_df = plot_df.sort_values(by=column, ascending=True)
        elif sorting == 'sestupné':
            plot_df = plot_df.sort_values(by=column, ascending=False)


        # Základní objektová notace pro graf
        fig, ax = plt.subplots(figsize=(12, 8))

        # Proměnné, které se nemění v závislosti na requestu, vyjma výběru lokality
        y = plot_df[column]
        barclr = PlotManager.quantities[quantity]['color']
        ylbl = PlotManager.quantities[quantity]['ylabel']

        # Parametry, které budou různé podle parametru sorting
        # Co se týká pole x, musí se při sortovaných výstupech převést na stringové
        # Pokud se nechá jako integer, osa x je numerická a vše se vynáší na pozici podle indexu
        # Tím pádem se sabotuje sorting a ze seřazené dataframe je opět zdánlivě neseřazený graf
        # Vytváří se totiž propojení mezi y (typ series) a x (typ index) a graf se uspořádává podle uspořádané osy x
        # Je to analogie s klasickým bodovým grafem (tam též jdou hodnoty v libovolném pořadí, ale přímku to nenarušuje)

        # Dále je zde ošetření případu, kdy pro dané období nejsou data
        # V tom případě je rovnou funkce vrací chybový string, namísto pokračování a finálního tisku prázdného grafu
        if sorting == 'chronologické':
            x = plot_df.index
            try:
                xticks = range(np.min(x), np.max(x)+1)
            except TypeError:
                return 'Data nejsou k dispozici'
        else:
            x = np.array([str(year) for year in plot_df.index])
            if len(x) > 0:
                xticks = x
            else:
                return 'Data nejsou k dispozici'

        # Titulek grafu - liší se podle toho, zda zobrazujeme roky, nebo měsíce
        if filter == 'rok':
            chart_ttl = f'Stanice: {self.location}, roční data'
        else:
            chart_ttl = f'Stanice: {self.location}, data za měsíc {filter}'


        ax.bar(x, y, edgecolor='black', linewidth=1, color=barclr, label=quantity)
        ax.set_ylabel(ylbl)
        ax.set_xlabel('Rok')
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticks, rotation=75)
        ax.set_title(chart_ttl)
        ax.grid(linewidth=1, color='grey')

        if sorting == 'chronologické':   # Klouzavý průměr v případě zobrazování nesortovaných dat
            ax.plot(x, plot_df['Rolling_5y'], label='Klouzavý průměr (5 let)', color='black', linewidth=1.8)

        # Klimatický normál, je-li vybrána jiná volba, než 'nezobrazovat'

        start_year, end_year = int(avg[:4]), int(avg[-4:]) # Startovní a konečný rok

        if ('dny' in quantity) and (filter == 'rok'):   # Výpočet průměru pro danou charakteristiku (fuj)
            result_avg = np.mean(self.data[[column]].loc[start_year:end_year + 1].groupby('Rok').sum()[column])
        else:
            result_avg = np.mean(self.data.loc[start_year:end_year + 1].query("Měsíc == @filter")[column])

        ax.plot(x, np.array(len(x)*[result_avg]), label = f'Průměr {avg}', color='black', linewidth=2, linestyle='--')

        ax.legend() # Až nakonec, aby se do ní propsal případně i klimatický normál a případně klouzavý průměr

        return fig

if __name__ == '__main__':
    data = pd.read_csv('Data.csv')
    test_inst = PlotManager('Děčín', data)
    df = test_inst.data

    sunshine_df = df[df['Měsíc'] == 'rok'][['Měsíc', 'Sunshine_sum']].dropna()
    precipitations_df = df[df['Měsíc'] == 'rok'][['Měsíc', 'Precipitations_sum']].dropna()

    sunshine_df['5Y_AVG'] = sunshine_df['Sunshine_sum'].rolling(5).mean()
    precipitations_df['5Y_AVG'] = precipitations_df['Precipitations_sum'].rolling(5).mean()

    print(sunshine_df)
    print(precipitations_df)
    print(sunshine_df.index)
    print(precipitations_df.index)
