from flask import Flask, render_template, redirect
import pandas
import geopandas
import sqlite3
from shapely import wkb
import folium

app = Flask(__name__)

# start database connection
# we ignore thread conflicts since we are read-only
conn = sqlite3.connect("file:db.sqlite3?mode=ro", check_same_thread=False, uri=True)
cursor = conn.cursor()

@app.route("/")
def map():
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
    map = cursor.execute("select geometry from commune where region = 'REGION METROPOLITANA DE SANTIAGO'")
    dataframe = pandas.DataFrame(map, columns=['geometry'])
    dataframe['geometry'] = dataframe['geometry'].apply(wkb.loads) # type: ignore
    geodataframe = geopandas.GeoDataFrame(data=dataframe, geometry='geometry', crs='EPSG:3857') # type: ignore

    figure = folium.Figure(width="100%", height="100%")
    map = geodataframe.explore(cmap='OrRd', legend=True)
    figure.add_child(map)

    rendered_map = figure._repr_html_()

    return render_template("map.html", reports=reports, regions=regions, year_min=year_min, year_max=year_max, map=rendered_map)


@app.route("/report=<report>/region=<region>/year_low=<year_low>/year_high=<year_high>/normalize=<normalize>")
def map_report(report: str, region: str, year_low: int, year_high: int, normalize: str):
    """
    Called from map.html, used to generate the map which is sent dynamically to the client
    """

    cursor.execute("""
    select commune.name, commune.population, sum(data.value), data.cohort, commune.geometry
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
    data = pandas.DataFrame(data, columns=['name', 'population', 'count', 'cohort', 'geometry'])

    if(data.empty):
        return render_template("empty.html")

    # prepare geometry
    geometry = data.copy(deep=True)
    # deduplicate communes
    geometry = geometry.drop_duplicates(subset='name')
    # drop extra columns
    geometry = geometry[["name", "geometry"]]
    # load binary into geometry
    geometry['geometry'] = geometry['geometry'].apply(wkb.loads) # type: ignore

    # create total and per capita column per name
    total = data[["name", "count", "population"]].groupby('name').sum()
    total.rename(columns={'count': 'Total'}, inplace=True)
    total['Per capita'] = total['Total'] * 10000 / total['population']
    total.drop(columns='population', inplace=True)

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

    if(normalize == "true"):
        color_column = "Per capita"
    else:
        color_column = "Total"

    # create the heatmap into a folium map
    figure = folium.Figure(width="100%", height="100%")
    map = geodataframe.explore(
        column=color_column, 
        cmap='plasma', 
        legend=True,
    )
    figure.add_child(map)

    return figure._repr_html_()