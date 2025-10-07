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


    avg_selections = \
        ['Vybrané období',
         'Normál 1961 - 1990',
         'Normál 1981 - 2010',
         'Normál 1991 - 2020'
         ]


    station_remarks = \
        {'Plzeň - Bolevec': 'Počty charakteristických dní podle maximální teploty dostupné až od roku 1969',
         'Staňkov': 'Sluneční svit k dispozici až od roku 2002',
         'Děčín': 'Chybí data z období 1972 - 1992 a data z měření úhrnu slunečního svitu od roku 1979',
         'Vizovice': 'Sluneční svit k dispozici až od roku 2007'}


    @classmethod
    def _prepare_source_data(cls):
        col_dict = {value['column']:key for key, value in cls.quantities.items()}
        source_data = pd.read_csv('Data.csv').rename(columns=col_dict)
        cls.source_data = source_data


    @classmethod
    def _prepare_data_accessibility_tbl(cls):
        source_data = cls.source_data

        id_vars = ['Stanice', 'Rok']  # include station here
        quantity_cols = [col for col in source_data.columns if col not in id_vars]

        melted = source_data.melt(id_vars=id_vars, var_name='Veličina', value_name='value')
        melted = melted.dropna(subset=['value'])

        # group by both station and quantity
        cls.data_accessibility = (
            melted.groupby(['Stanice', 'Veličina'])
                .agg(rok_min=('Rok', 'min'), rok_max=('Rok', 'max'))
        )

    def __init__(self, selection):

        self.selection = selection
        self.required_data = self._prepare_required_data()
        self.main_plot_df = self._create_main_plot_dataframe()
        self.slc_period_stats = self.compute_stats(selection['start_yr'], selection['end_yr'], selection['lintrend'])


    def _prepare_required_data(self):
        '''Returns dataframe which is necessary as a data source for all plots and calculations
        Resulting dataframe is set as an instance attribute plot_data

        REFACTORING NOTE:
        Evaluate the relation of avg and start_yr and return dataframe from min(avg, start_yr)
        Because the solution for station normals - coming back to source data - is really ugly'''

        # Selekce v samostatne promenne pro snazsi referencovani
        slc = self.selection

        # Vyberu data pro danou stanici a velicinu, rok jako index
        req_data = (PlotManager.source_data
                         .query("Stanice == @slc['location']")
                         .set_index('Rok')
                         .loc[:,['Měsíc', slc['quantity']]]
                        )

        # Specificky postup, pokud jsou jako velicina vybrany charakteristicke dny a zaroven je vybran filtr na roky
        # Tato data nejsou pro uroven roku predagregovana, jinak je vsak postup stejny
        # Zkousim, zda mam ve vybranem obdobi dostupna data
        # Pokud nemam ve vybranem obdobi zadna data, vracim prazdnou dataframe a dalsi metody s tim pracuji
        # V opacnem pripade dodelam transformaci dat, rozdilnou pro dva vyse uvedene pripady
        # Nevracim vsak pouze data pro vybrane obdobi
        # Protoze muzeme chtit zobrazit klimaticky normal, ktery nemusi cely spadat do vybraneho obdobi
        if ('dny' in slc['quantity']) and (slc['filter'] == 'rok'):
            acc_test_data = req_data.loc[slc['start_yr']:slc['end_yr']].dropna()
            if acc_test_data.empty:
                return acc_test_data
            else:
                return req_data.loc[:,[slc['quantity']]].groupby('Rok').sum().dropna()
        else:
            acc_test_data = req_data.query("Měsíc == @slc['filter']").loc[slc['start_yr']:slc['end_yr']].dropna()
            if acc_test_data.empty:
                return acc_test_data.query("Měsíc == @slc['filter']").dropna()
            else:
                return req_data.query("Měsíc == @slc['filter']").loc[:,[slc['quantity']]].dropna()


    def _create_main_plot_dataframe(self):
        '''Pri chronologickem razeni dat se vrati self.required_data
        Pri ostatnich se vrati serazena dataframe se stringovym indexem'''

        plot_df_base = self.required_data.loc[self.selection['start_yr']:self.selection['end_yr']]

        if self.selection['sorting'] != 'chronologické':
            sort_type = {'vzestupné': True, 'sestupné': False}
            main_plot_df = plot_df_base.sort_values(by=self.selection['quantity'], ascending=sort_type[self.selection['sorting']])
            main_plot_df.index = main_plot_df.index.map(str)
        else:
            main_plot_df = plot_df_base

        return main_plot_df


    def compute_stats(self, start_year:int, end_year:int, regression=False):
        '''computes basic statistics from the required data
        for a time period from start_year to end_year
        if regression=True, computes also regression parameters, default False'''

        # Slovnik, do ktereho sbiram vysledky
        stats = dict()

        # Pokud je DataFrame s pozadovanymi daty pro dane obdobi prazdna, rovnou vracim prazdny slovnik
        if self.required_data.loc[start_year:end_year].empty:
            return stats

        # Pokud mame pozadovana data, pocitam a sbiram vysledky
        eval_data = self.required_data.loc[start_year:end_year].iloc[:,0]
        stats['mean'] = float(eval_data.mean())
        stats['min'] = float(eval_data.min())
        stats['max'] = float(eval_data.max())
        stats['stdev'] = float(eval_data.std())

        # Dale regrese
        if regression:
            x = eval_data.index
            y = eval_data
            a, b = np.polyfit(x, y, 1)
            yhat = a*x + b
            sstot = np.sum((y - stats['mean'])**2)
            ssres = np.sum((y - yhat)**2)
            r2 = 1 - ssres/sstot

            stats['reg_a'] = a
            stats['reg_b'] = b
            stats['r2'] = r2

        return stats


    def plot_req(self):
        '''Creates the plot according to the requirements from the user, which are defined by following parameters
        filter - month (leden, únor... prosinec) or year (rok)
        sorting - asc is ascending, desc is descending, default None (sorted by time)'''


        def basic_bar_plot(ax):
            '''Creates the basic bar chart without trend lines, but with all axes objects'''

            # x, y, barva sloupců, popisek osy y (proměnné, nezávislé na requestu)
            x = self.main_plot_df.index
            y = self.main_plot_df.iloc[:,0]
            barclr = PlotManager.quantities[self.selection['quantity']]['color']
            ylbl = PlotManager.quantities[self.selection['quantity']]['ylabel']

            # Popisky osy x - rozdílné podle toho, zda se data řadí (vzestupně/sestupně) nebo je řazení chronologické
            if self.selection['sorting'] == 'chronologické':
                xticks = range(min(x), max(x) + 1)
            else:
                xticks = x

            # Titulek grafu - liší se podle toho, zda zobrazujeme roky, nebo měsíce
            if filter == 'rok':
                chart_ttl = f"Stanice: {self.selection['location']}, roční data"
            else:
                chart_ttl = f"Stanice: {self.selection['location']}, data za měsíc {self.selection['filter']}"

            # Kompletní nastavení grafu
            ax.bar(x, y, edgecolor='black', linewidth=1, color=barclr, label=self.selection['quantity'])
            ax.set_ylabel(ylbl)
            ax.set_xlabel('Rok')
            ax.set_xticks(xticks)
            ax.set_xticklabels(xticks, rotation=75)
            ax.set_title(chart_ttl)
            ax.grid(linewidth=1, color='grey')


        def avgline(ax):
            '''Creates the average line plot'''

            x = self.main_plot_df.index

            if self.selection['avg'] == 'Vybrané období':
                yavg = self.slc_period_stats['mean']
                yr_min = self.selection['start_yr']
                yr_max = self.selection['end_yr']
            else:
                yr_min = int(self.selection['avg'][-12:-7])
                yr_max = int(self.selection['avg'][-4:])

                # Funkce pocita prumer a kresli prumer, jen pokud jsou k dispozici data za cele normalove obdobi
                if self.required_data.loc[yr_min:yr_max].shape[0] < 30:
                    return None
                else:
                    yavg = self.compute_stats(yr_min, yr_max)['mean']

            ax.plot(x,
                    np.array(len(x) * [yavg]),
                    label=f'Průměr {yr_min} - {yr_max}',
                    color='black',
                    linewidth=2,
                    linestyle='--')


        def regline(ax):
            '''Function for construction of linear regression line'''
            x = self.main_plot_df.index
            y = self.main_plot_df.iloc[:,0]

            a, b = self.slc_period_stats['reg_a'], self.slc_period_stats['reg_b']
            reg_x = np.linspace(x.min(), x.max(), 3)
            reg_y = a * reg_x + np.array(3 * [b])

            ax.plot(reg_x, reg_y, label='Lineární trend', linestyle='-.', color='black', linewidth=1.5)


        def rolling_average(ax, ravg_window):
            '''Function for plotting years rolling average
            ravg_window determines the width of averaging window'''
            x = self.main_plot_df.index
            y = self.main_plot_df.iloc[:, 0].rolling(ravg_window).mean()

            if ravg_window < 5:
                label_str = f'Klouzavý průměr ({ravg_window} roky)'
            else:
                label_str = f'Klouzavý průměr ({ravg_window} let)'

            ax.plot(x, y, label=label_str, color='black', linewidth=1.8)

        # ZDE ZAČÍNÁ TĚLO FUNKCE PLOT_REQ

        # Pripad, kdy je hlavni plot_dataframe prazdna
        # Rovnou vracim omluvny string prislusneho typu a metoda pro tvorbu grafu se nevola
        if self.main_plot_df.empty:
            return 'Data pro zobrazení grafu nejsou k dispozici'

        # Dále případy, kdy plot_dataframe není prázdná, ale daný jev se nevyskytuje (sníh v červenci atd.)
        # Opět se rovnou vrátí "omluvný string" příslušného typu a procedury pro tvorbu grafů se nevolají
        if max(self.main_plot_df.iloc[:,0]) == 0:
            if 'dny' in self.selection['quantity']:
                return f"{self.selection['quantity']} se na dané stanici a při zvoleném nastavení podmínek nevyskytují"
            else:   # Podle mě pouze případ, kdy chci max. výšku sněhu, tj. veličinu "Sníh"
                return f"{self.selection['quantity']} se na dané stanici a při zvoleném nastavení nevyskytl"

        # Pokud program nespadl do jedné ze 2 předchozích podmínek, jde se na grafy
        # Vždy se v tomto případě dělá základní graf, s klimatickým normálem
        fig, ax = plt.subplots(figsize=(12, 8))
        basic_bar_plot(ax)
        avgline(ax)

        # Pokud uzivatel vybere tez linearni trend nebo klouzavy prumer, pridaji se do grafu
        # Spravne by zde melo byt osetrene, aby se funkce volaly pouze pri urcitych vstupnich podminkach
        # Temi jsou chronologicke razeni dat a vyber obdobi o minimalni pripustne delce
        # Ale ve streamlit app nebude mozne v jinem pripade tyto veliciny vybrat
        if self.selection['lintrend']:
            regline(ax)

        # self.selection ma item roll_avg_window
        # Jeji hodnota je cele cislo, kdyz je klouzavy prumer vyzadovan, a pote udava sirku okna pro klouzavy prumer
        # Neni-li klouzavy prumer vyzadovan, je vyplnena hodnota None, coz umoznuje nasledujici vetveni
        if self.selection['roll_avg_window']:
            rolling_average(ax, self.selection['roll_avg_window'])

        # A nakonec legenda, aby se do ni propsaly vsechny labely
        ax.legend()

        return fig

# Az tady musim incializovat class variables, protoze uvnitr class nelze volat class methods
PlotManager._prepare_source_data()
PlotManager._prepare_data_accessibility_tbl()

if __name__ == '__main__':
    selection = \
        {'location': 'Cheb',
         'filter': 'rok',
         'quantity': 'Sluneční svit',
         'sorting': 'chronologické',
         'start_yr': 2010,
         'end_yr': 2020,
         'avg': 'Vybrané období',
         'lintrend': True,
         'roll_avg_window': 3
         }


    test_inst = PlotManager(selection)
    test_inst.plot_req()
    plt.show()