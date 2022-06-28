import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


class PlotManager:
    '''Manages the plotting of climatological data.
    If there are no data for plot, it returns only the message regarding the data inavailability'''

    quantities = \
        {'Srážky': {'column': 'Precipitations_sum', 'color': 'blue', 'ylabel': 'Suma srážek (mm)'},
         'Teplota - průměr': {'column': 'Temperatures_avg', 'color': 'green', 'ylabel': 'Průměrná teplota (°C)'},
         'Teplota - minimum': {'column': 'Temperatures_min_min', 'color': 'purple', 'ylabel': 'Minimální teplota (°C)'},
         'Teplota - maximum': {'column': 'Temperatures_max_max', 'color': 'red', 'ylabel': 'Maximální teplota (°C)'},
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


    def plot_req(self, quantity: str, filter: str, sorting='chronologické', start_yr=1980, avg='1961 - 1990',
                 lintrend = False, roll_avg = False):
        '''Creates the plot according to the requirements from the user, which are defined by following parameters
        filter - month (leden, únor... prosinec) or year (rok)
        sorting - asc is ascending, desc is descending, default None (sorted by time)'''


        def create_plot_dataframe():
            '''Creates DataFrame which is necessary as a data source for all plots'''

            # Sloupec, který si pak vezmu z gigantické DataFrame self.data (odpovídá vybrané meteo veličině)
            column = PlotManager.quantities[quantity]['column']

            # Agregace výchozí tabulky self.data. Záleží, jestli chci charakteristické dny, nebo jinou veličinu
            # U charakteristických dní totiž nejsou v řádku "rok" hodnoty, což je třeba řešit agregací
            if ('dny' in quantity) and (filter == 'rok'):
                plot_df = self.data[[column]].loc[start_yr:].groupby('Rok').sum().dropna()
            else:
                plot_df = self.data.loc[start_yr:].query("Měsíc == @filter")[[column]].dropna()

            # Už v tuto chvíli je možné, že plot_df je prázdná, nejsou-li data dostupná (př. Děčín, sluneční svit)
            # V tom případě prázdnou DataFrame rovnou vracím, a zbytek funkce se nevykoná
            # Graf se z ní stejně dělat nebude (což pak musím v proceduře pro graf rovněž zaimplementovat)
            if plot_df.empty:
                return plot_df

            # Tady je výchozí DataFrame tříděna, je-li parametr sorting asc nebo desc
            # Dále v takovém případě měním roky na string, má-li být tabulka řazená (protože graf pak musí mít takové x)
            if sorting == 'vzestupné':
                plot_df = plot_df.sort_values(by=column, ascending=True)
                plot_df.index = plot_df.index.map(str)
            elif sorting == 'sestupné':
                plot_df = plot_df.sort_values(by=column, ascending=False)
                plot_df.index = plot_df.index.map(str)

            return plot_df


        def basic_bar_plot(ax, df):
            '''Creates the basic bar chart without trend lines, but with all axes objects'''

            # x, y, barva sloupců, popisek osy y (proměnné, nezávislé na requestu)
            x = df.index
            y = df.iloc[:,0]
            barclr = PlotManager.quantities[quantity]['color']
            ylbl = PlotManager.quantities[quantity]['ylabel']

            # Popisky osy x - rozdílné podle toho, zda se data řadí (vzestupně/sestupně) nebo je řazení chronologické
            if sorting == 'chronologické':
                xticks = range(min(x), max(x) + 1)
            else:
                xticks = x

            # Titulek grafu - liší se podle toho, zda zobrazujeme roky, nebo měsíce
            if filter == 'rok':
                chart_ttl = f'Stanice: {self.location}, roční data'
            else:
                chart_ttl = f'Stanice: {self.location}, data za měsíc {filter}'

            # Kompletní nastavení grafu
            ax.bar(x, y, edgecolor='black', linewidth=1, color=barclr, label=quantity)
            ax.set_ylabel(ylbl)
            ax.set_xlabel('Rok')
            ax.set_xticks(xticks)
            ax.set_xticklabels(xticks, rotation=75)
            ax.set_title(chart_ttl)
            ax.grid(linewidth=1, color='grey')


        def climatic_normal(ax, df):
            '''Creates the plot of climatic normal'''
            # Je třeba sáhnout zpět k self.data, protože DataFrame pro graf je oseknutá od start_yr

            column = PlotManager.quantities[quantity]['column']  # Sloupec, který budu hledat v self.data
            start_year, end_year = int(avg[:4]), int(avg[-4:])  # Startovní a konečný rok
            x = df.index    # x, které se bude lišit podle toho, jaká je výchozí dataframe (soulad s hlavním grafem)

            if ('dny' in quantity) and (filter == 'rok'):  # Výpočet průměru pro danou charakteristiku (fuj)
                result_avg = np.mean(self.data[[column]].loc[start_year:end_year + 1].groupby('Rok').sum()[column])
            else:
                result_avg = np.mean(self.data.loc[start_year:end_year + 1].query("Měsíc == @filter")[column])

            ax.plot(x, np.array(len(x) * [result_avg]), label=f'Průměr {avg}', color='black', linewidth=2,
                    linestyle='--')


        def regline(ax, df):
            '''Function for construction of linear regression line'''
            x = df.index
            y = df.iloc[:,0]

            a, b = np.polyfit(x, y, 1)
            reg_x = np.linspace(x.min(), x.max(), 3)
            reg_y = a * reg_x + np.array(3 * [b])

            ax.plot(reg_x, reg_y, label='Lineární trend', linestyle='-.', color='black', linewidth=1.5)


        def rolling_average(ax, df):
            '''Function for plotting 5 years rolling average'''
            x = df.index
            y = df.iloc[:, 0].rolling(5).mean()
            ax.plot(x, y, label='Klouzavý průměr (5 let)', color='black', linewidth=1.8)

        # ZDE ZAČÍNÁ TĚLO FUNKCE PLOT_REQ

        # Výchozí plot_dataframe pro všechny grafy
        plot_dataframe = create_plot_dataframe()

        # Případ, kdy je plot_dataframe prázdná
        # Rovnou vracím "omluvný string" příslušného typu a procedury pro tvorbu grafů se nevolají
        if plot_dataframe.empty:
            return 'Data pro zobrazení grafu nejsou k dispozici'

        # Dále případy, kdy plot_dataframe není prázdná, ale daný jev se nevyskytuje (sníh v červenci atd.)
        # Opět se rovnou vrátí "omluvný string" příslušného typu a procedury pro tvorbu grafů se nevolají
        if max(plot_dataframe.iloc[:,0]) == 0:
            if 'dny' in quantity:
                return f'{quantity} se na dané stanici a při zvoleném nastavení podmínek nevyskytují'
            else:   # Podle mě pouze případ, kdy chci max. výšku sněhu, tj. veličinu "Sníh"
                return f'{quantity} se na dané stanici a při zvoleném nastavení nevyskytl'

        # Pokud program nespadl do jedné ze 2 předchozích podmínek, jde se na grafy
        # Vždy se v tomto případě dělá základní graf, s klimatickým normálem
        fig, ax = plt.subplots(figsize=(12, 8))
        basic_bar_plot(ax, plot_dataframe)
        climatic_normal(ax, plot_dataframe)

        # A pokud je řazení chronologické, tak se přidají ještě klouzavý průměr a lineární trend
        # Později předělám, plot_reg bude mít ještě 2 parametry - jestli vykreslovat, nebo nevykreslovat tyto řady
        # A ve streamlitu se pak volba klouzavého a lineárního trendu bude objevovat, když bude chronologické řazení
        if lintrend:
            regline(ax, plot_dataframe)

        if roll_avg:
            rolling_average(ax, plot_dataframe)

        # A nakonec legenda, aby se do ní propsaly všechny labely
        ax.legend()

        return fig

if __name__ == '__main__':
    data = pd.read_csv('Data.csv')
    test_inst = PlotManager('Teplice', data)
    plot = test_inst.plot_req('Srážky', 'rok', 'chronologické', 1980)
    plt.show()