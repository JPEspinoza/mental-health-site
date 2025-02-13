from flask import Flask, render_template, g, json, Response
import pandas
import geopandas
import sqlite3
from shapely import wkb
import folium

app = Flask(__name__)

def get_db() -> sqlite3.Connection:
    db: sqlite3.Connection = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db: sqlite3.Connection = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def map():
    """
    Generates the filter list and renders the map.html template
    """
    cursor = get_db().cursor()

    # get list of categories
    # make dict of reports {name: description}
    cursor.execute("""
    select distinct category from report;
    """)
    categories = cursor.fetchall()
    categories = [category[0] for category in categories]

    # get list of years
    cursor.execute("""
    select min(year), max(year) from data
    """)
    years = cursor.fetchall()
    year_min = years[0][0]
    year_max = years[0][1]

    # get list of regions
    cursor.execute("""
    select distinct region from commune where region != 'ZONA SIN DEMARCAR';
    """)
    regions = [region[0] for region in cursor.fetchall()]

    # generate preview map
    map = cursor.execute("select geometry from commune where region = 'REGION METROPOLITANA DE SANTIAGO'")
    dataframe = pandas.DataFrame(map, columns=['geometry'])
    dataframe['geometry'] = dataframe['geometry'].apply(wkb.loads) # type: ignore
    geodataframe = geopandas.GeoDataFrame(data=dataframe, geometry='geometry', crs='EPSG:3857') # type: ignore

    figure = folium.Figure(width="100%", height="100%")
    map = geodataframe.explore(cmap='OrRd', legend=True)
    figure.add_child(map)

    rendered_map = figure._repr_html_()

    return render_template("map.html", categories=categories, year_min=year_min, year_max=year_max, regions=regions, map=rendered_map)

@app.route('/category=<category>/')
def category(category: str):
    cursor = get_db().cursor()

    # get list of years
    cursor.execute("""
    select min(year), max(year) from data
    join report on data.report_id = report.id
    where report.category = ?;
    """, (category,))
    years = cursor.fetchall()
    year_min = years[0][0]
    year_max = years[0][1]

    cursor.execute("select name, description from report where category = ?", (category,))
    reports = cursor.fetchall()

    return json.dumps({
        "reports": reports,
        "year_min": year_min,
        "year_max": year_max
    })

@app.route("/report=<report>/region=<region>/year_low=<year_low>/year_high=<year_high>/normalize=<normalize>/")
def map_report(report: str, region: str, year_low: int, year_high: int, normalize: str):
    """
    Called from map.html, used to generate the map which is sent dynamically to the client
    """
    cursor = get_db().cursor()

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
    total['Cada 10.000 personas'] = total['Total'] * 10000 / total['population']
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
        color_column = "Cada 10.000 personas"
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

    # get list of cohorts
    cursor.execute("""
    select distinct data.cohort
    from data
    join report on data.report_id = report.id
    join commune on data.commune_id = commune.id
    where
        report.name = ? and
        data.year >= ? and
        data.year <= ? and
        commune.region = ?
    """, (report, year_low, year_high, region))
    cohorts = cursor.fetchall()
    cohorts = [x[0] for x in cohorts]

    return json.dumps({
        "map": figure._repr_html_(),
        "cohorts": cohorts
    })