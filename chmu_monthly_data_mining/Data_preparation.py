import pandas as pd
import csv
import os
import numpy as np

def get_float(general_number: str):
    '''Kills the numbers which are represented as a string containing number with decimal ,.
    Also overtypes the int numbers to float numbers (calculated average is never really int!)'''
    if isinstance(general_number, int):
        return float(general_number)
    elif isinstance(general_number, float):
        return general_number
    else:
        return float(general_number.partition(',')[0] + '.' + general_number.partition(',')[2])


def correct_daily_data(general_number:str):
    '''Corrects the string formatted numbers of format ",x" and "-,x" in daily data'''
    # V některých souborech se vyskytují rovnou float hodnoty, proto ošetřují následující podmínkou
    if isinstance(general_number, float):
        return general_number

    # A tohle už je pro ten klasický ošklivý string
    if general_number[0] == ',':
        return "0" + general_number
    elif general_number[0] == '-':
        return general_number[0] + "0" + general_number[1:]
    else:
        return general_number

def file_to_df(filepath: str, filter: str):
    '''Transforms the part of the original file, which has "Statistika" equal to filter, into single DataFrame'''
    # Získání názvu souboru bez přípony, ze kterého se tahají data
    filename_raw = os.path.basename(filepath).partition('.')[0]

    # Stažení se správným encodingem a delimiterem
    rough_df = pd.read_csv(filepath, delimiter=';', encoding='windows-1250')

    # List s názvy sloupců, obsahujících hodnoty (nikoli datumy jejich dosažení)
    columns_lst = [column for column in rough_df.columns if 'Datum' not in column]

    # Slovník pro přejmenování sloupců (Hodnota leden -> leden, Hodnota rok -> rok atd.)
    rename_dict = {column : column.partition(' ')[2] for column in rough_df.columns if 'Hodnota' in column}

    # Finální DataFrame, které chybí už jenom stack a ošklivé "umoudřování" vzniklé zbytečné multiindexové struktury
    final_df = (rough_df[columns_lst][rough_df['Statistika'] == filter]
                .iloc[:, :-1]
                .rename(columns=rename_dict)
                .drop('Statistika', axis=1)
                .set_index('Rok')
                )

    # Stack a dodatečné pojmenování druhého levelu vzniklého multiindexu (proč to ta funkce stack nemá jako parametr??)
    # A k tomu ještě transformace "ohavných českých stringových jakobyfloatů s desetinnou čárkou" na floaty
    final_df = pd.DataFrame(final_df.stack(), columns=[f'{filename_raw}_{filter.lower()}'])
    final_df.index.rename('Měsíc', level=1, inplace=True)
    final_df = final_df.applymap(get_float)

    return final_df


def daily_data_to_df(filepath: str):
    '''Returns the special file with daily data to DataFrame, which is able to be joined to the monthly data'''
    months = \
        ['',
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

    rough_df = pd.read_csv(filepath, delimiter=';', encoding='windows-1250')

    # Transformace sloupce Měsíc na Měsíc_c a sloupce Hodnota na Hodnota_c (c jako correction)
    rough_df['Měsíc_c'] = rough_df['Měsíc'].apply(lambda x: months[x])
    rough_df['Hodnota_c'] = rough_df[['Hodnota']].applymap(correct_daily_data).applymap(get_float)

    # Odstranění zbytečných sloupců, přejmenování transformovaných sloupců
    intermediate_df = (rough_df
                        .drop(['Příznak', 'Měsíc', 'Hodnota'], axis=1)
                        .rename(columns={'Měsíc_c': 'Měsíc', 'Hodnota_c': 'Hodnota'})
                       )

    # Přidání sloupců s charakteristickými dny
    intermediate_df['Arctic_days'] = intermediate_df['Hodnota'].apply(lambda x: 0 if x > -10 else 1)
    intermediate_df['Ice_days'] = intermediate_df['Hodnota'].apply(lambda x: 0 if x > 0 else 1)
    intermediate_df['Summer_days'] = intermediate_df['Hodnota'].apply(lambda x: 0 if x < 25 else 1)
    intermediate_df['Tropical_days'] = intermediate_df['Hodnota'].apply(lambda x: 0 if x < 30 else 1)

    # Agregace
    final_df = intermediate_df.groupby(['Rok', 'Měsíc']).sum().drop(['Den', 'Hodnota'], axis=1)

    return final_df

class FileProcessor:

    # Class variable - dictionary containing filenames and statistics which are contained in these files
    file_stats = \
        {'Precipitations.csv': ['MAX', 'SUM'],
         'Snow_height.csv': ['MAX'],
         'Sunshine.csv': ['SUM'],
         'Temperatures.csv': ['AVG'],
         'Temperatures_max.csv': ['MAX'],
         'Temperatures_min.csv': ['MIN'],
         'Wind.csv': ['AVG']
         }

    def __init__(self, folderpath):
        self.folderpath = folderpath
        self.location = os.path.basename(folderpath)
        self.files = os.listdir(folderpath)

    def name_files(self):
        '''Gives names to original files from CHMU according to their content (like keys in variable file_stats)
        Only the files including daily maximum temperature data must be renamed to include "Daily" in their name
        It is because these data also have _TMA_ in the original name and are not distinguishable therefore'''
        rename_dict = \
            {'_F_': 'Wind.csv',
             '_SCE_': 'Snow_height.csv',
             '_SNO_': 'Snow.csv',
             '_SRA_': 'Precipitations.csv',
             '_SSV_': 'Sunshine.csv',
             '_T_': 'Temperatures.csv',
             '_TMA_': 'Temperatures_max.csv',
             '_TMI_': 'Temperatures_min.csv',
             'Daily': 'Daily_data.csv'}

        for key in rename_dict.keys():
            for file in self.files:
                if key in file:
                    oldname = os.path.join('Locations', self.location, file)
                    newname = os.path.join('Locations', self.location, rename_dict[key])
                    os.rename(oldname, newname)


    def purify_files(self):
        '''Extracts only the relevant data from the files
        (escapes the awful headers there, creates new file without the headers, with the same name).
        If new terrible impure file is added into folder in any time, it purifies this file'''

        # Existuje-li již sběrný soubor s názvem, který se shoduje s názvem složky, nechci jej čistit.
        # Proto proměnná relevant_files, která sesbírá názvy všech souborů ve složce, kromě zmíněného
        relevant_files = [file for file in self.files if file != f'{self.location}.csv']

        # A tady už čistím
        for file in relevant_files:
            pth = os.path.join(self.folderpath, file)
            start_fl = open(pth)
            reader = csv.reader(start_fl, delimiter=';')
            line = next(reader)
            if line[0][0] == '#':  # Test, zda je soubor již vyčištěn od hlaviček. Pokud ne, provede se "metoda půllitrů"
                while True:     # Cyklus, který pouze zajistí, aby kurzor přistál na správném řádku "MĚSÍČNÍ DATA"
                    line = next(reader)
                    if line in (['MĚSÍČNÍ DATA'], ['DATA']):
                        temporary_fl = open(f'{self.folderpath}/temporary.csv', 'w')
                        writer = csv.writer(temporary_fl, delimiter=';')
                        break

                while True:     # Cyklus, který přepíše relevantní řádky do nového souboru temporary.csv
                    try:
                        line = next(reader)
                        writer.writerow(line)
                    except StopIteration:
                        start_fl.close()
                        temporary_fl.close()
                        break

                # Nastavení readeru a writeru pro finální přepis obsahu temporary.csv do původního souboru
                final_fl = open(pth, 'w')
                temporary_fl = open(f'{self.folderpath}/temporary.csv')
                reader = csv.reader(temporary_fl, delimiter=';')
                writer = csv.writer(final_fl, delimiter=';')

                while True:     # Cyklus, který nahradí obsah původního souboru obsahem souboru temporary.csv
                    try:
                        line = next(reader)
                        writer.writerow(line)
                    except StopIteration:
                        final_fl.close()
                        temporary_fl.close()
                        break

            else:
                start_fl.close()

        # Když se provádí čištění, tak vzniká soubor temporary.csv, který pak chci smazat
        # Pokud ale ve složce není žádný soubor, který by se čistil, soubor nevznikne a program spadne
        # Proto následující podmínka - zjisti, jestli soubor existuje. Když ano, smaž jej.
        # Pak bych to mohl ještě přepsat do try - except, aby to nebylo tak repetitivní.
        # Pokud by ovšem za except smělo být pass
        try:
            os.remove(os.path.join(self.folderpath, 'temporary.csv'))
        except FileNotFoundError:
            pass
        # if os.path.exists(os.path.join(self.folderpath, 'temporary.csv')):
        #     os.remove(os.path.join(self.folderpath, 'temporary.csv'))


    def join_files(self):
        '''Joins all files into one file, where also data are transformed into more user-friendly configuration'''

        # Zárodek pro list, obsahující všechny dílčí DataFrames, které se ze souborů dají vytáhnout
        df_list = []

        # List pro join - je potřeba vyhodit ze self.files soubor, který obsahuje denní data
        # A ještě bych sem přidal případně přeskočení souboru, do kterého se ukládá finální join
        # Jakmile totiž tento soubor existuje, metoda se bude snažit opracovat i tento finální soubor
        # Tím pádem opět musím myslet na to, abych metodu nevolal pro adresář, kde už se joinovalo
        join_list = [file for file in self.files if file not in ('Daily_data.csv', f'{self.location}.csv')]

        # Naplnění proměnné df_list

        # Přidání DataFrames ze souborů s měsíčními daty
        for file in join_list:
            pth = os.path.join(self.folderpath, file)

            for statistic in FileProcessor.file_stats[file]:
                df_list.append(file_to_df(pth, statistic))

        # Přidání DataFrame ze souboru s denními daty (Daily_data.csv)
        pth = os.path.join(self.folderpath, 'Daily_data.csv')
        df_list.append(daily_data_to_df(pth))


        # Join všech DataFrames z proměnné df_list do final_frame
        final_frame = df_list[0]
        for frame in df_list[1:]:
            final_frame = final_frame.join(frame)

        # Přidání sloupce, který notifikuje lokaci (pro pozdější appendování souborů s daty z jiných stanic)
        final_frame.insert(loc=0, column='Stanice', value=final_frame.shape[0]*[self.location])

        # Převedení final_frame do souboru .csv
        final_frame.to_csv(f'{self.folderpath}/{self.location}.csv')


    def collect_outputs(self):
        '''Creates the file Data.csv for collection of data from all stations, if it still does not exist.
        In that case, the data for the current location (station) are in the Data.csv file.
        If the Data.csv file exists yet, data from the new location are appended, if they are still not present.'''

        # Větev pro případ, že soubor Data.csv ještě neexistuje
        # V tom případě bude založen a přijdou do něj data z lokace, uložené v atributu self.location
        if not os.path.exists('Data.csv'):
            final_df = pd.read_csv(os.path.join('Locations', self.location, f'{self.location}.csv'))
            final_df.to_csv('Data.csv', index=False)

        # Větev pro případ, že sběrný soubor na data ze všech stanic již existuje
        # V takovém případě se data pro novou stanici přidají do tohoto sběrného souboru Data.csv
        else:
            final_df = pd.read_csv('Data.csv')
            if self.location not in np.unique(final_df['Stanice']):
                final_df = final_df.append(pd.read_csv(os.path.join('Locations', self.location, f'{self.location}.csv')))
                final_df.to_csv('Data.csv', index=False)


    # def process_all_locations(self):
    #     '''Performs the complete processing of all data in the folder Locations, using sequence of above defined methods'''
    #     for location in os.listdir('Locations'):
    #         fp = FileProcessor(f'Locations/{location}')
    #         fp.name_files()
    #         fp.purify_files()
    #         fp.join_files()
    #         fp.collect_outputs()




if __name__ == '__main__':
    # Následující sekvence zpracuje komplet všechny podsložky ve složce locations, sakum prásk
    # Ve výchozím stavu jsou tyto podsložky naplněny pouze surovými .csv soubory s původními názvy
    # Musí být jen správná sestava souborů, a pro správnou lokalitu. Vše další je zajištěno

    for location in os.listdir('Locations'):
        fp = FileProcessor(f'Locations/{location}')
        fp.name_files()

    for location in os.listdir('Locations'):
        fp = FileProcessor(f'Locations/{location}')
        fp.purify_files()
        fp.join_files()
        fp.collect_outputs()







