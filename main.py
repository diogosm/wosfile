import csv
import glob
import wosfile
from collections import Counter, defaultdict
from tinydb import TinyDB, Query, where
from geopy.geocoders import Nominatim
import pycountry
from more_itertools import locate
import folium
from folium.plugins import MarkerCluster
import plotly.graph_objects as go
import matplotlib.pyplot as plt
## para usar o basemap no Windows ##
import os

os.environ["PROJ_LIB"] = r'C:\Users\User\miniconda3\Library\share'
from mpl_toolkits.basemap import Basemap

## para usar o basemap no Windows ##

subject_cats = Counter()
# Create a list of all relevant files. Our folder may contain multiple export files.
files = glob.glob("data/bioeconoma.txt")
paises = []  ## lista de paises por trabalho. Cada item é uma lista com 1 ou mais paises de cada trabalho
contaGlobal = 0
contaDE = 0

def getPosicao(country):
    geolocator = Nominatim(user_agent="teste")

    try:
        loc = geolocator.geocode(country)
        return loc.latitude, loc.longitude
    except:
        return -1, -1


def salvaPaisesBanco(elem, qtdPorPais, countryCode, pos):
    db = TinyDB('paises.json')

    db.insert(
        {
            'countryName': elem,
            'countAuthors': qtdPorPais,
            'countryCode': countryCode,
            'latitude': pos[0],
            'longitude': pos[1]
        }
    )
    db.close()


def mostraPaisesBanco():
    db = TinyDB('paises.json')
    db.all()


def apagaBanco(name):
    db = TinyDB(name)
    try:
        db.drop_tables()
        db.all()
    except Exception as e:
        print(f'erro ao apagar banco. {e}')


def europeMapPlot():
    my_dpi = 96
    plt.figure(figsize=(800 / my_dpi, 400 / my_dpi), dpi=my_dpi)
    db = TinyDB('paisesVersaoCorreta.json')

    m = Basemap(llcrnrlon=-15.201129, llcrnrlat=37.462259, urcrnrlon=54.584023, urcrnrlat=67.686744, width=1.6E7,
                height=1.2E7, resolution='l')
    m.drawmapboundary(fill_color='#A6CAE0', linewidth=0.1)
    m.fillcontinents(color='coral', lake_color='white', alpha=0.3)
    m.drawcoastlines(linewidth=0.25)
    m.drawcountries(linewidth=0.25)

    for elem in db:
        lat = elem['latitude']
        lon = elem['longitude']
        if not (lat > 37.462259 and lat < 67.686744 and lon > -15.201129 and lon < 54.584023):
            continue
        # print(f"ELEM: {elem['countryCode']} - {elem['countAuthors']}")
        x, y = m(lon, lat)

        plt.text(x, y, s=elem['countryCode'], fontsize=7)
        m.scatter(x,
                  y,
                  s=elem['countAuthors'] * 20,
                  alpha=0.5,
                  # c=data['labels_enc'],
                  cmap="Set1")
    plt.savefig('europaBubbleMap.png', bbox_inches='tight')


def worldMapPlot():
    #
    # https://plotly.com/python/bubble-maps/
    # https://plotly.github.io/plotly.py-docs/generated/plotly.graph_objects.Scattergeo.html
    # https://anaconda.org/anaconda/basemaphttps://python-graph-gallery.com/315-a-world-map-of-surf-tweets/
    my_dpi = 96
    # world
    plt.figure(figsize=(2600 / my_dpi, 1800 / my_dpi), dpi=my_dpi)
    # europe
    # plt.figure(figsize=(800 / my_dpi, 400 / my_dpi), dpi=my_dpi)
    db = TinyDB('paisesVersaoCorreta.json')

    # world
    m = Basemap(llcrnrlon=-180, llcrnrlat=-65, urcrnrlon=180, urcrnrlat=80, resolution='c')
    # europe
    # m = Basemap(llcrnrlon=-15.201129, llcrnrlat=37.462259, urcrnrlon=54.584023, urcrnrlat=67.686744, width=1.6E7, height=1.2E7)
    m.drawmapboundary(fill_color='#A6CAE0', linewidth=0.1)
    m.fillcontinents(color='coral', lake_color='white', alpha=0.3)
    m.drawcoastlines(linewidth=0.25)
    m.drawcountries(linewidth=0.25)

    for elem in db:
        lat = elem['latitude']
        lon = elem['longitude']
        ## if europa
        # if not (lat > 37.462259 and lat < 67.686744 and lon > -15.201129 and lon < 54.584023):
        #    continue
        # print(f"ELEM: {elem['countryCode']} - {elem['countAuthors']}")
        x, y = m(lon, lat)

        plt.text(x, y, s=elem['countryCode'], fontsize=12)
        m.scatter(x,
                  y,
                  s=elem['countAuthors'] * 20,
                  alpha=0.5,
                  # c=data['labels_enc'],
                  cmap="Set1")

    # plt.colorbar(label=r'$\log_{10}({\rm population})$')
    # plt.clim(0, 600)

    plt.savefig('paisesBubbleMap.png', bbox_inches='tight')
    # plt.savefig('europaBubbleMap.png', bbox_inches='tight')


def worldMapRoutesPlot(grafo):
    my_dpi = 96
    # world
    plt.figure(figsize=(2600 / my_dpi, 1800 / my_dpi), dpi=my_dpi)
    # europe
    # plt.figure(figsize=(800 / my_dpi, 400 / my_dpi), dpi=my_dpi)
    db = TinyDB('paisesVersaoCorreta.json')
    countries = Query()

    # world
    m = Basemap(llcrnrlon=-180, llcrnrlat=-65, urcrnrlon=180, urcrnrlat=80)
    # europe
    # m = Basemap(llcrnrlon=-15.201129, llcrnrlat=37.462259, urcrnrlon=54.584023, urcrnrlat=67.686744, width=1.6E7, height=1.2E7)
    m.drawmapboundary(fill_color='#A6CAE0', linewidth=0.1)
    m.fillcontinents(color='coral', lake_color='white', alpha=0.3)
    m.drawcoastlines(linewidth=0.25)
    m.drawcountries(linewidth=0.25)

    for key, values in grafo.items():
        for value in values:
            try:
                from_country = db.search(countries['countryName'] == key)
                to_country = db.search(countries['countryName'] == value)

                if from_country[0]['countAuthors'] < 50 or to_country[0]['countAuthors'] < 50:
                    continue

                print(from_country)
                print(to_country)

                x1, y1 = m(from_country[0]['longitude'], from_country[0]['latitude'])
                x2, y2 = m(to_country[0]['longitude'], to_country[0]['latitude'])

                m.drawgreatcircle(x1, y1, x2, y2, linewidth=0.25, color='black', del_s=50)
            except:
                print(f"FAILED: {key} - {value}")

    for elem in db:
        lat = elem['latitude']
        lon = elem['longitude']
        ## if europa
        # if not (lat > 37.462259 and lat < 67.686744 and lon > -15.201129 and lon < 54.584023):
        #    continue
        # print(f"ELEM: {elem['countryCode']} - {elem['countAuthors']}")
        x, y = m(lon, lat)

        plt.text(x, y, s=elem['countryCode'], fontsize=12)
        m.scatter(x,
                  y,
                  s=elem['countAuthors'] * 20,
                  alpha=0.5,
                  # c=data['labels_enc'],
                  cmap="Set1")

    plt.savefig('paisesRoutesMap.png', bbox_inches='tight')
    # plt.savefig('europaBubbleMap.png', bbox_inches='tight')


def europeMapRoutesPlot(grafo):
    my_dpi = 96
    plt.figure(figsize=(800 / my_dpi, 400 / my_dpi), dpi=my_dpi)
    db = TinyDB('paisesVersaoCorreta.json')
    countries = Query()

    m = Basemap(llcrnrlon=-15.201129, llcrnrlat=37.462259, urcrnrlon=54.584023, urcrnrlat=67.686744, width=1.6E7,
                height=1.2E7, resolution='l')
    m.drawmapboundary(fill_color='#A6CAE0', linewidth=0.1)
    m.fillcontinents(color='coral', lake_color='white', alpha=0.3)
    m.drawcoastlines(linewidth=0.25)
    m.drawcountries(linewidth=0.25)

    for key, values in grafo.items():
        for value in values:
            try:
                from_country = db.search(countries['countryName'] == key)
                to_country = db.search(countries['countryName'] == value)

                if from_country[0]['countAuthors'] < 50 or to_country[0]['countAuthors'] < 50:
                    continue

                if not (37.462259 < from_country[0]['latitude'] < 67.686744 and
                        -15.201129 < from_country[0]['longitude'] < 54.584023):
                    continue

                if not (37.462259 < to_country[0]['latitude'] < 67.686744 and
                        -15.201129 < to_country[0]['longitude'] < 54.584023):
                    continue

                x1, y1 = m(from_country[0]['longitude'], from_country[0]['latitude'])
                x2, y2 = m(to_country[0]['longitude'], to_country[0]['latitude'])

                m.drawgreatcircle(x1, y1, x2, y2, linewidth=0.25, color='black')
            except:
                print(f"FAILED: {key} - {value}")

    for elem in db:
        lat = elem['latitude']
        lon = elem['longitude']
        ##if europa
        if not (lat > 37.462259 and lat < 67.686744 and lon > -15.201129 and lon < 54.584023):
            continue
        # print(f"ELEM: {elem['countryCode']} - {elem['countAuthors']}")
        x, y = m(lon, lat)

        plt.text(x, y, s=elem['countryCode'], fontsize=7)
        m.scatter(x,
                  y,
                  s=elem['countAuthors'] * 20,
                  alpha=0.5,
                  # c=data['labels_enc'],
                  cmap="Set1")

    plt.savefig('europaRoutesMap.png', bbox_inches='tight')


def contaPaises():
    countries = {}
    for country in pycountry.countries:
        countries[country.name] = country.alpha_2

    paisesCounter = Counter()
    grafo = defaultdict(set)
    # print(contaGlobal)
    for lista in paises:
        for i, item in enumerate(lista):
            if 'USA' == item:
                lista[i] = 'United States'
            if 'England' == item or 'Wales' == item or 'Scotland' == item:
                lista[i] = 'United Kingdom'
            if 'SouthKorea' == item:
                lista[i] = 'Korea, Republic of'
            if 'CzechRepublic' == item:
                lista[i] = 'Czechia'
            if 'NewZealand' == item:
                lista[i] = 'New Zealand'
            if 'SouthAfrica' == item:
                lista[i] = 'South Africa'
            if 'Vietnam' == item:
                lista[i] = 'Viet Nam'
            if 'SaudiArabia' == item:
                lista[i] = 'Saudi Arabia'
            if 'Tanzania' == item:
                lista[i] = 'Tanzania, United Republic of'
            if 'StKittsNevi' == item:
                lista[i] = 'Saint Kitts and Nevis'
            if 'Russia' == item:
                lista[i] = 'Russian Federation'
            if 'BurkinaFaso' == item:
                lista[i] = 'Burkina Faso'
            if 'Iran' == item:
                lista[i] = 'Iran, Islamic Republic of'
            if 'FrenchGuiana' == item:
                lista[i] = 'French Guiana'
            if 'NethAntilles' == item:
                lista[i] = 'Netherlands'
            if 'BosniaHerceg' == item:
                lista[i] = 'Bosnia and Herzegovina'
            if 'NorthMacedonia' == item:
                lista[i] = 'North Macedonia'
            if 'NorthIreland' == item:
                lista[i] = 'Ireland'
            if 'SolomonIslands' == item:
                lista[i] = 'Solomon Islands'
            if 'UArabEmirates' == item:
                lista[i] = 'United Arab Emirates'
            if 'Laos' == item:
                lista[i] = 'Lao People\'s Democratic Republic'
            if 'Venezuela' == item:
                lista[i] = 'Venezuela, Bolivarian Republic of'
            if 'NewCaledonia' == item:
                lista[i] = 'New Caledonia'
            if 'Taiwan' == item:
                lista[i] = 'Taiwan, Province of China'
        lista.sort()
        for i in range(len(lista) - 1):
            for j in range(i + 1, len(lista)):
                grafo[lista[i]].add(lista[j])
        paisesCounter.update(lista)
        # print(lista)
    print(paisesCounter.most_common(5))
    ''' grafo das rotas
    for key, values in grafo.items():
        for value in values:
            print(f"{key} - {value}")
    '''
    '''
    for elem in paisesCounter:
        ## tenta converter
        ans = countries.get(elem, 'Unknown code')
        pos = getPosicao(ans)

        if ans == 'Unknown code' or pos == (-1, -1):
            print(f"### ERROR: {elem} - {paisesCounter[elem]} - {ans} ###")
        else:
            # print(f"POS: {elem} - {paisesCounter[elem]} - {ans} - {pos}")
            salvaPaisesBanco(elem, paisesCounter[elem], ans, pos)
    '''
    '''
        @TODO
            salvar num tinydb https://www.idkrtm.com/using-tinydb-with-python/
            pegar a localizacao por gps https://pypi.org/project/geopy/
            montar o mapa por quantidade https://towardsdatascience.com/using-python-to-create-a-world-map-from-a-list-of-country-names-cd7480d03b10
    '''
    mostraPaisesBanco()
    worldMapRoutesPlot(grafo)
    europeMapRoutesPlot(grafo)
    # worldMapPlot()
    print('END')


def getPaises(listaLocs):
    x = 1
    if listaLocs is not None:  ## pais eh listado no artigo

        if len(listaLocs) > 1:  ## possui uma ou mais localizacoes de autores
            paisesPaper = {}
            paisesPaperAux = []
            if type(listaLocs) is list:  ## apenas loc generica sem identificar o autor
                for paisAux in listaLocs:
                    pais = str(paisAux).split(',')
                    pais = pais[len(pais) - 1]
                    if pais.__contains__('USA.'):
                        # contaGlobal+=1
                        pais = pais.split(' ')
                        pais = pais[len(pais) - 1]
                    pais = ''.join(e for e in pais if e.isalnum())
                    if pais == 'PeoplesRChina':
                        pais = 'China'
                    paisesPaper[pais] = (0 if paisesPaper.__contains__(pais) == False else paisesPaper[pais]) + 1
            else:
                for k, v in listaLocs.items():
                    # print(f"{k} - {v}")
                    for paisAux in v:
                        pais = str(paisAux).split(',')
                        pais = pais[len(pais) - 1]
                        if pais.__contains__('USA.'):
                            # contaGlobal += 1
                            pais = pais.split(' ')
                            pais = pais[len(pais) - 1]
                        pais = ''.join(e for e in pais if e.isalnum())
                        if pais == 'PeoplesRChina':
                            pais = 'China'
                        paisesPaper[pais] = (0 if paisesPaper.__contains__(pais) == False else paisesPaper[pais]) + 1
            for k, v in paisesPaper.items():  ## add na lista auxiliar para juntar na lista geral
                paisesPaperAux.append(k)
            paises.append(paisesPaperAux)
        else:  ## possui apenas 1 localizacao de autor ou 1 uma localizacao generico em lista
            paisesPaper = {}
            paisesPaperAux = []
            if type(listaLocs) is list:  ## apenas loc generica sem identificar o autor
                pais = str(listaLocs[0]).split(',')
                pais = pais[len(pais) - 1]
                if pais.__contains__('USA.'):
                    # contaGlobal += 1
                    pais = pais.split(' ')
                    pais = pais[len(pais) - 1]
                pais = ''.join(e for e in pais if e.isalnum())
                if pais == 'PeoplesRChina':
                    pais = 'China'
                paisesPaperAux.append(pais)
                paises.append(paisesPaperAux)
            else:  ## loc por autor
                for k, v in listaLocs.items():
                    if len(v) < 2:  ## autor tem 1 loc
                        pais = str(v).split(',')
                        pais = pais[len(pais) - 1]
                        if pais.__contains__('USA.'):
                            # contaGlobal += 1
                            pais = pais.split(' ')
                            pais = pais[len(pais) - 1]
                        pais = ''.join(e for e in pais if e.isalnum())
                        if pais == 'PeoplesRChina':
                            pais = 'China'
                        paisesPaper[pais] = 1
                    else:  ## autor tem multiplas localizacoes
                        for paisAux in v:
                            pais = str(paisAux).split(',')
                            pais = pais[len(pais) - 1]
                            if pais.__contains__('USA.'):
                                # contaGlobal += 1
                                pais = pais.split(' ')
                                pais = pais[len(pais) - 1]
                            pais = ''.join(e for e in pais if e.isalnum())
                            if pais == 'PeoplesRChina':
                                pais = 'China'
                            paisesPaper[pais] = 1
                for k, v in paisesPaper.items():  ## add na lista auxiliar para juntar na lista geral
                    paisesPaperAux.append(k)
                paises.append(paisesPaperAux)
    else:
        x = 1  ## do nothing


'''
Para ver os mapas:
    https://scitools.org.uk/cartopy/docs/latest/matplotlib/intro.html#adding-data-to-the-map
    https://www.google.com/search?q=network+graph+plot+world+map+python&rlz=1C1CHZL_pt-BRBR722BR722&source=lnms&tbm=isch&sa=X&ved=2ahUKEwj3vpHBw5jqAhXKF7kGHfwiBToQ_AUoAXoECA0QAw
    https://stackoverflow.com/questions/19915266/drawing-a-graph-with-networkx-on-a-basemap
    https://python-graph-gallery.com/category/map/
    http://www.sociology-hacks.org/?p=67
    https://python-graph-gallery.com/300-draw-a-connection-line/
'''

# wosfile will read each file in the list in turn and yield each record
# for further handling
apagaBanco('paises.json')  ## reseta os paises


def saveCsvScopus(authors, title, year, affiliations, author_keywords, rec):
    global contaDE
    with open('convertidoScopus.csv', 'a') as csv_file:
        try:
            line = ''
            first = False
            for author in authors:
                if first:
                    line += ', '
                line += str(author).replace(',', '').split(' ')[0]
                secondPart = str(author).replace(',', '').split(' ')[1]
                line += ' '
                for i in range(len(secondPart)):
                    line += secondPart[i]
                    line += '.'
                first = True
            line += ';' + title.replace('"', '').replace(';', '').replace('\'', '').replace(':', '') \
                    + ';' + year + ';' + affiliations + ';"'

            first = False
            for author_keyword in author_keywords:
                if first:
                    line += '; '
                line += str(author_keyword).replace('"', '').replace('\'', '')
                first = True
            line += '"\n'

            csv_file.write(line)
        except:
            contaDE += 1
            print(f"{authors}")
            print(f"{author_keywords}")
            print(rec)
            #raise


def saveCsvScopusHeader():
    with open('convertidoScopus.csv', 'w') as csv_file:
        csv_file.write('Authors;Title;Year;Affiliations;Author Keywords\n')


saveCsvScopusHeader()
for rec in wosfile.records_from(files):
    #print(rec)
    listaLocs = rec.get("C1")  ## pega localizacao dos autores
    #Authors;Title;Year;Affiliations;Author Keywords
    authors = rec.get('AU') #list
    title = rec.get('TI')  #str
    year = rec.get('PY')    #str
    affiliations = 'none'
    author_keywords = rec.get('DE') #list
    saveCsvScopus(authors, title, year, affiliations, author_keywords, rec)

    getPaises(listaLocs)

    # Records are very thin wrappers around a standard Python dict,
    # whose keys are the WoS field tags.
    # Here we look at the SC field (subject categories) and update our counter
    # with the categories in each record.
    subject_cats.update(rec.get("SC"))

# Show the five most common subject categories in the data and their number.
print(subject_cats.most_common(5))
contaPaises()
# mostraPaisesBanco()
worldMapPlot()
europeMapPlot()
