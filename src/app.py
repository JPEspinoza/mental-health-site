from flask import Flask, render_template
import pandas
import geopandas
import sqlite3
import json
from shapely import wkb
import folium
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

app = Flask(__name__)

# start database connection
# we ignore thread conflicts since we are read-only
conn = sqlite3.connect("file:db.sqlite3?mode=ro", check_same_thread=False, uri=True)
cursor = conn.cursor()

# months
months = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre"
]

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/map_home/")
def map_home():
    """
    Generates the filter list and renders the map.html template
    """

    # get list of reports
    # make dict of reports {name: description}
    cursor.execute("""
    select name, description from report
    """)
    reports = cursor.fetchall()
    reports = { reports[i][0]: reports[i][1] for i in range(len(reports)) }

    # get list of regions
    cursor.execute("""
    select distinct region from commune where region != 'ZONA SIN DEMARCAR';
    """)
    regions = [region[0] for region in cursor.fetchall()]

    # get list of years
    cursor.execute("""
    select min(year), max(year) from data
    """)
    years = cursor.fetchall()
    year_min = years[0][0]
    year_max = years[0][1]

    # generate preview map
    map = cursor.execute("select geometry from commune where province = 'SANTIAGO'")
    dataframe = pandas.DataFrame(map, columns=['geometry'])
    dataframe['geometry'] = dataframe['geometry'].apply(wkb.loads) # type: ignore
    geodataframe = geopandas.GeoDataFrame(data=dataframe, geometry='geometry', crs='EPSG:3857') # type: ignore

    figure = folium.Figure(width="100%", height="100%")
    map = geodataframe.explore(cmap='OrRd', legend=True)
    figure.add_child(map)

    rendered_map = figure._repr_html_()

    return render_template("map.html", reports=reports, regions=regions, year_min=year_min, year_max=year_max, map=rendered_map)


@app.route("/map/report=<report>/region=<region>/year_low=<year_low>/year_high=<year_high>/")
def map(report: str, region: str, year_low: int, year_high: int):
    """
    Called from map.html, used to generate the map which is sent dynamically to the client
    """
    
    cursor.execute("""
    select commune.name, sum(data.value), data.cohort, commune.geometry
    from data
    join report on data.report_id = report.id
    join commune on data.commune_id = commune.id
    where
        report.name = ? and
        data.year >= ? and
        data.year <= ? and
        commune.region = ?
    group by commune.name, data.cohort;
    """, (report, year_low, year_high, region))
    data = cursor.fetchall()

    # format the data into a dataframe
    data = pandas.DataFrame(data, columns=['name', 'count', 'cohort', 'geometry'])

    # prepare geometry
    geometry = data.__deepcopy__()
    # deduplicate communes
    geometry.drop_duplicates(subset='name', inplace=True)
    # drop extra columns
    geometry = geometry[["name", "geometry"]]
    # load binary into geometry
    geometry['geometry'] = geometry['geometry'].apply(wkb.loads) # type: ignore

    # create total column per name
    total = data[["name", "count"]].groupby('name').sum()
    # rename count to total
    total.rename(columns={'count': 'Total'}, inplace=True)

    # explode cohorts into columns
    data = data.pivot(index='name', columns='cohort', values='count')

    # add geometry per commune to data
    data = pandas.merge(geometry, data, on="name")

    # add total
    data = pandas.merge(data, total, on="name")

    # remove nulls with 0
    data.fillna(0, inplace=True)

    # prepare geodataframe
    geodataframe = geopandas.GeoDataFrame(data=data, geometry='geometry', crs='EPSG:3857') # type: ignore

    # create the heatmap into a folium map
    figure = folium.Figure(width="100%", height="100%")
    map = geodataframe.explore(column='Total', cmap='OrRd', legend=True)
    figure.add_child(map)

    return figure._repr_html_()