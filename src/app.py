from flask import Flask, render_template, request, Response
import pandas
import geopandas
import sqlite3
import json
from shapely import wkb
import folium

app = Flask(__name__)

# start database connection
conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

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
    provinces = [provinces[0] for provinces in provinces]

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
def map_index_reports(province):
    # return list of reports for the selected province
    cursor.execute("""
    select report.name
    from report
    join data on data.report_id = report.id
    join commune on commune.id = data.commune_id
    where 
        commune.province = ? AND
        data.year is not null
    group by report.id
    having sum(data.value) > 0;
    """, (province,))

    reports = cursor.fetchall()

    return json.dumps({"reports": reports})

@app.route("/map_index_years/<province>/<report>/")
def map_index_years(province, report):
    # return list of years for the selected report and province
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
def map(report, year, province):
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