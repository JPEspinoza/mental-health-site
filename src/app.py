from flask import Flask, render_template, Response
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
conn = sqlite3.connect("db.sqlite3")
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

    # get list of provinces with data
    cursor.execute("""
    select province
    from commune
    join data on commune.id = data.commune_id
    group by province
    having sum(data.value) > 0
    """)
    provinces = cursor.fetchall()
    provinces = {province[0]: province[0].title() for province in provinces}

    # generate preview map
    map = cursor.execute("select geometry from commune where province = 'SANTIAGO'")
    dataframe = pandas.DataFrame(map, columns=['geometry'])
    dataframe['geometry'] = dataframe['geometry'].apply(wkb.loads) # type: ignore
    geodataframe = geopandas.GeoDataFrame(data=dataframe, geometry='geometry', crs='EPSG:3857') # type: ignore

    figure = folium.Figure(width="100%", height="100%")
    map = geodataframe.explore(cmap='OrRd', legend=True)
    figure.add_child(map)

    rendered_map = figure._repr_html_()

    return render_template("map.html", provinces=provinces, map=rendered_map)

@app.route("/map_index_reports/<province>/")
def map_index_reports(province: str):
    """
    returns a list of all the valid reports for the selected province
    """

    cursor.execute("""
    select report.name, report.description
    from report
    join data on data.report_id = report.id
    join commune on commune.id = data.commune_id
    where 
        commune.province = ? AND
        data.year is not null
    group by report.id
    having sum(data.value) > 0
    order by report.name;
    """, (province,))

    reports = cursor.fetchall()

    data = json.dumps({"reports": reports})

    return data

@app.route("/map_index_years/<province>/<report>/")
def map_index_years(province: str, report: str):
    """
    return list of years for the selected report and province
    """
    cursor.execute("""
    select data.year
    from data
    join commune on data.commune_id = commune.id
    join report on data.report_id = report.id
    where
        commune.province = ? AND
        report.name = ? AND
        data.year is not null
    group by year
    having sum(data.value) > 0;
    """, (province, report,))

    years = cursor.fetchall()

    return json.dumps({"years": years})

@app.route("/map/<province>/<report>/<year>/")
def map(report: str, year: int, province: str):
    """
    Called from map.html, used to generate the map which is sent dynamically to the client
    """
    
    cursor.execute("""
    select commune.name, SUM(value), commune.geometry
    from data
    join report on data.report_id = report.id
    join commune on data.commune_id = commune.id
    where
        report.name = ? and
        data.year = ? and
        province like ?
    group by commune.id;
    """, (report, year, province))
    communes = cursor.fetchall()

    # format the data into a dataframe
    dataframe = pandas.DataFrame(communes, columns=['name', 'count', 'geometry'])
    dataframe['geometry'] = dataframe['geometry'].apply(wkb.loads) # type: ignore
    geodataframe = geopandas.GeoDataFrame(data=dataframe, geometry='geometry', crs='EPSG:3857') # type: ignore

    # create the heatmap into a folium map
    figure = folium.Figure(width="100%", height="100%")
    map = geodataframe.explore(column='count', cmap='OrRd', legend=True)
    figure.add_child(map)

    return figure._repr_html_()

@app.route("/graph_index/")
def graph_home():
    """
    called from graph.html, returns an index of all valid reports
    """

    cursor.execute("""
    select name from report where name like '%Month%';
    """)

    reports = [{"name": row[0]} for row in cursor.fetchall()]

    return render_template('graph.html', reports=reports)

@app.route('/graph_per_month/<report>/<province>/<year>/')
def graph_per_month(report: str, province: str, year: int):
    cursor.execute("""
        select cohort, sum(data.value)
        from data
        join report on data.report_id = report.id
        join commune on data.commune_id = commune.id
        where
            report.name = ? AND
            commune.province = ? and
            data.year = ?
        group by cohort;
    """, (report, province, year))
    data = cursor.fetchall()

    data = pandas.DataFrame(data, columns=["cohort", "value"])

    # sort by month
    data['cohort'] = pandas.Categorical(data['cohort'], categories=months, ordered=True)
    data = data.sort_values('cohort')

    # set cohort to index
    data = data.set_index('cohort')

    # make storage in memory
    output = io.BytesIO()

    # plot data into png
    fig = Figure(figsize=(10, 8))
    ax = fig.add_subplot(111)
    ax.title.set_text(f"Consultas por mes en {province}")
    ax.axes.set_xlabel("Mes") # type: ignore
    ax.axes.set_ylabel("Consultas") # type: ignore
    data.plot(kind='bar', ax=ax)
    FigureCanvas(fig).print_png(output)

    return output.getvalue()
