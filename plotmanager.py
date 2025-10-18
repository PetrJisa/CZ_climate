import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


class PlotManager:
    '''Obstarava veskery data handling s cilem dosazeni zadanych vystupu'''

    quantities = \
        {'Srážky': {'color': 'blue', 'ylabel': 'Suma srážek (mm)'},
         'Teplota - průměr': {'color': 'green', 'ylabel': 'Průměrná teplota (°C)'},
         'Teplota - minimum': {'color': 'purple', 'ylabel': 'Minimální teplota (°C)'},
         'Teplota - maximum': {'color': 'red', 'ylabel': 'Maximální teplota (°C)'},
         'Sluneční svit': {'color': 'yellow', 'ylabel': 'Úhrn slunečního svitu (hod)'},
         'Sníh': {'color': 'lightblue', 'ylabel': 'Maximum sněhové pokrývky (cm)'},
         'Vítr': {'color': 'brown', 'ylabel': 'Průměrná rychlost větru (m/s)'},
         'Arktické dny': {'color': 'purple', 'ylabel': 'Počet arktických dnů (Tmax < -10 °C)'},
         'Ledové dny': {'color': 'darkblue', 'ylabel': 'Počet ledových dnů (Tmax < 0 °C)'},
         'Letní dny': {'color': 'brown', 'ylabel': 'Počet letních dnů (Tmax >= 25 °C)'},
         'Tropické dny': {'color': 'red', 'ylabel': 'Počet tropických dnů (Tmax >= 30 °C)'},
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
         'Vizovice': 'Sluneční svit k dispozici až od roku 2007'}


    source_data = pd.read_csv('Data.csv')


    @classmethod
    def _prepare_data_accessibility_tbl(cls):

        def climatic_normal(df, eval_col, start_year, end_year):
            '''Vypocet klimatickeho normalu za obdobi, ohranicene start_year a end_year
            Pokud jsou k dispozici data za vsechny roky, funkce vrati klimaticky normal
            V opacnem pripade vrati hodnotu NaN
            Promenna eval_col je nazev sloupce v dataframe, ze ktereho pocitam klimaticky normal'''

            # df je obecne jakakoli dataframe, vcetne dataframe slice objektu dataframe.groupby()
            sub = df[(df['Rok'] >= start_year) & (df['Rok'] <= end_year)]

            # overeni, zda nechybi data pro vypocet klimatickeho normalu
            expected_years = end_year - start_year + 1
            actual_years = sub['Rok'].nunique()

            # Chybi data --> vratim nan, jinak vracim normal (nutne specifikovat, z jakeho sloupce)
            if actual_years < expected_years:
                return float('nan')
            else:
                return sub[eval_col].mean() # dirty solution - spoleham se, ze v cilove dataframe bude sloupec value

        def applied_functions(df, eval_col):
            '''Sestavuje pandas.Serie s nadefinovanymi funkcemi
            Tato je pak predana metode dataframe.apply()
            Promenna eval_col je sloupec v dataframe, ze ktereho pocitam normal'''

            return pd.Series({
                'min_year': df['Rok'].min(),
                'max_year': df['Rok'].max(),
                'Normál 1961 - 1990': climatic_normal(df, eval_col, 1961, 1990),
                'Normál 1981 - 2010': climatic_normal(df, eval_col, 1981, 2010),
                'Normál 1991 - 2020': climatic_normal(df, eval_col, 1991, 2020)
                })

        source_data = cls.source_data

        # Vsechny sloupce, ktere nechceme pivotovat
        id_vars = ['Stanice', 'Měsíc', 'Rok']

        # Pivotace - nazvy velicin do sloupce 'Veličina', hodnoty do sloupce 'value', dropna() podle 'value'
        melted = source_data.melt(id_vars=id_vars, var_name='Veličina', value_name='value')
        melted = melted.dropna(subset=['value'])

        # Agregace melted tabulky s vypoctem, ktery ridi pd.Serie applied_functions
        cls.data_accessibility = (melted
                                  .groupby(['Stanice', 'Měsíc', 'Veličina'])
                                  .apply(lambda x: applied_functions(x, 'value'), include_groups=False)
                                  )


    def __init__(self, selection):

        self.selection = selection
        self.required_data = self._prepare_required_data()
        self.missing_count = self._count_missing_years()
        self.main_plot_df = self._create_main_plot_dataframe()
        self.slc_period_stats = self.compute_stats(selection['lintrend'])


    def _prepare_required_data(self):
        '''Returns dataframe which is necessary as a data source for all plots and calculations
        Resulting dataframe is set as an instance attribute plot_data

        REFACTORING NOTE:
        Evaluate the relation of avg and start_yr and return dataframe from min(avg, start_yr)
        Because the solution for station normals - coming back to source data - is really ugly'''

        # Selekce v samostatne promenne pro snazsi referencovani
        slc = self.selection

        # Vyberu data pro danou stanici a velicinu, rok jako index
        return (PlotManager.source_data
                        .query("Stanice == @slc['location'] & Měsíc == @slc['filter']")
                        .set_index('Rok')
                        .loc[slc['start_yr']:slc['end_yr'],[slc['quantity']]]
                        .dropna()
                )


    def _count_missing_years(self):
        '''Pocita, pro kolik roku pri danem vyberu chybi data'''
        expected = self.selection['end_yr'] - self.selection['start_yr']
        real = self.required_data.shape[0]
        return expected - real


    def _create_main_plot_dataframe(self):
        '''Pri chronologickem razeni dat se vrati self.required_data
        Pri ostatnich se vrati serazena dataframe se stringovym indexem'''

        plot_df_base = self.required_data

        if self.selection['sorting'] != 'chronologické':
            sort_type = {'vzestupné': True, 'sestupné': False}
            main_plot_df = plot_df_base.sort_values(by=self.selection['quantity'], ascending=sort_type[self.selection['sorting']])
            main_plot_df.index = main_plot_df.index.map(str)
        else:
            main_plot_df = plot_df_base

        return main_plot_df


    def compute_stats(self, regression=False):
        '''computes basic statistics from the required data
        if regression=True, computes also regression parameters, default False'''

        # Slovnik, do ktereho sbiram vysledky
        stats = dict()

        # Pokud je DataFrame s pozadovanymi daty pro dane obdobi prazdna, rovnou vracim prazdny slovnik
        if self.required_data.empty:
            return stats

        # Pokud mame pozadovana data, pocitam a sbiram vysledky
        eval_data = self.required_data.iloc[:,0]
        stats['Průměr'] = float(eval_data.mean())
        stats['Minimum'] = float(eval_data.min())
        stats['Maximum'] = float(eval_data.max())
        stats['Směrodatná odchylka'] = float(eval_data.std())
        stats['Dolní tercil'] = float(np.quantile(eval_data, 1/3))
        stats['Horní tercil'] = float(np.quantile(eval_data, 2/3))

        # Dale regrese
        if regression:
            x = eval_data.index
            y = eval_data
            a, b = np.polyfit(x, y, 1)
            yhat = a*x + b
            sstot = np.sum((y - stats['Průměr'])**2)
            ssres = np.sum((y - yhat)**2)
            r2 = 1 - ssres/sstot

            stats['a']= float(a)
            stats['b'] = float(b)
            stats['R2'] = float(r2)

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
            if self.selection['filter'] == 'rok':
                chart_ttl = f"Stanice: {self.selection['location']}, roční data"
            else:
                chart_ttl = f"Stanice: {self.selection['location']}, data za měsíc {self.selection['filter']}"

            # Nastaveni grafu - default
            bar_plot = ax.bar(x, y, edgecolor='black', linewidth=1, color=barclr, label=self.selection['quantity'])
            ax.set_ylabel(ylbl)
            ax.set_xlabel('Rok')
            ax.set_xticks(xticks)
            ax.set_xticklabels(xticks, rotation=75)
            ax.set_title(chart_ttl)
            ax.grid(linewidth=0.5, color='grey')

            # Pridani popisku dat - custom (0 digits pro charakteristicke dny, jinak 1 digit)
            if self.selection['bar_labels']:
                if 'dny' in self.selection['quantity']:
                    fmt = '%.0f'
                else:
                    fmt = '%.1f'

                ax.bar_label(bar_plot, padding=2, color='black', zorder=2, fmt=fmt)


        def avgline(ax):
            '''Creates the average line plot'''

            slc = self.selection

            x = self.main_plot_df.index

            if self.selection['avg'] == 'Vybrané období':
                yavg = self.slc_period_stats['Průměr']
                label = f"Průměr {slc['start_yr']} - {slc['end_yr']}"
            else:
                yavg = (PlotManager
                    .data_accessibility
                    .loc[(slc['location'], slc['filter'], slc['quantity']), slc['avg']]
                )
                label = slc['avg']

            ax.plot(x,
                    np.array(len(x) * [yavg]),
                    label=label,
                    color='black',
                    linewidth=2,
                    linestyle='--')


        def regline(ax):
            '''Function for construction of linear regression line'''
            x = self.main_plot_df.index
            y = self.main_plot_df.iloc[:,0]

            a, b = self.slc_period_stats['a'], self.slc_period_stats['b']
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


    def table_req(self, kind='stat'):
        '''Pripravuje data, ktera se zobrazuji v tabulkach
        Parametr kind muze nabyvat 2 hodnot - "stat" a "reg"
        "stat" - pripravi se data pro zobrazeni zakladni statistiky za vybrane odobi
        "reg" - pripravi se data pro zobrazeni regresnich parametru'''

        if kind == "stat":
            keys = ['Průměr', 'Minimum', 'Maximum', 'Směrodatná odchylka']
            dict_ = {k:f'{v:.1f}' for k,v in self.slc_period_stats.items() if k in keys}
            norm_lbound = self.slc_period_stats['Dolní tercil']
            norm_ubound = self.slc_period_stats['Horní tercil']
            dict_['Interval normálních hodnot'] = f'{norm_lbound:.1f} - {norm_ubound:.1f}'
        elif kind == "reg":
            keys = ['a', 'b']
            dict_ = {k:f'{v:.3f}' for k, v in self.slc_period_stats.items() if k in keys}
            dict_['R2'] = f"{self.slc_period_stats['R2']:.2f}"

        df_out = pd.DataFrame.from_dict(dict_, orient='index', columns=['Hodnota'])
        df_out.index.name = 'Parametr'

        return df_out


# Az tady musim incializovat class variable data_accessibility, protoze uvnitr class nelze volat class methods
PlotManager._prepare_data_accessibility_tbl()

if __name__ == '__main__':
    selection = \
        {'location': 'Cheb',
         'filter': 'rok',
         'quantity': 'Sníh',
         'sorting': 'chronologické',
         'start_yr': 1961,
         'end_yr': 2020,
         'avg': 'Normál 1961 - 1990',
         'lintrend': True,
         'roll_avg_window': None,
         'bar_labels':True
         }


    test_inst = PlotManager(selection)
    test_inst.plot_req()
    plt.show()