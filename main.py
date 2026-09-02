from flask import Flask, render_template, request
import folium
from folium.plugins import MarkerCluster
from config.database import get_db_instance
import requests
import datetime
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.models import ColumnDataSource, LabelSet
from dateutil.relativedelta import relativedelta
import pandas
import numpy as np  

app = Flask(__name__)

BOUNDARIES_URL = (
    "https://raw.githubusercontent.com/fraxen/tectonicplates/"
    "master/GeoJSON/PB2002_boundaries.json"
)

PLATES_URL = (
    "https://raw.githubusercontent.com/fraxen/tectonicplates/"
    "master/GeoJSON/PB2002_plates.json"
)

def load_geojson(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

@app.route("/")
def main():
    boundaries = load_geojson(BOUNDARIES_URL)
    plates = load_geojson(PLATES_URL)
    year = request.args.get("year", default=datetime.datetime.now().year, type=int)
    month = request.args.get("month", default=1, type=int)
    date = datetime.datetime(year, month, 1)
    next_date = date + relativedelta(months=1)
    
    m = folium.Map(
        zoom_start=3, 
        control_scale=True,
        max_bounds=True,
        world_copy_jump=True,
        location=[-25, 0],
        min_lat=-95.0,
        max_lat=95.0,
        min_lon=-185.0,
        max_lon=185.0,
        width="100%")
    
    marker_cluster = MarkerCluster().add_to(m)

    folium.PolyLine(
        locations=[[0, longitude] for longitude in range(-180, 181)],
        color="#FFD60A",
        weight=3,
        opacity=0.9,
        tooltip="Équateur",
        dash_array="10, 6"
    ).add_to(marker_cluster)
    
    folium.GeoJson(
        plates,
        name="Plaques tectoniques",
        style_function=lambda feature: {
            "fillColor": "#C2E6FF",
            "color": "#ffffff",
            "weight": 1,
            "fillOpacity": 0.15
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["PlateName", "Code"],
            aliases=["Plaque :", "Code :"]
        )
    ).add_to(marker_cluster)

    folium.GeoJson(
        boundaries,
        name="Limites tectoniques",
        style_function=lambda feature: {
            "color": "#0090FF",
            "weight": 2,
            "opacity": 0.9
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["PlateA", "PlateB", "Type"],
            aliases=["Plaque A :", "Plaque B :", "Type :"]
        )
    ).add_to(marker_cluster)

    db_inst = get_db_instance()
    if db_inst:
        result = db_inst.query(f"""
            SELECT * FROM earthquakes WHERE earthquake_time >= {date.timestamp() * 1000.0} AND earthquake_time <= {next_date.timestamp() * 1000.0};
        """)

        temp_data = []
        for data in result:
            long_lat_str = data[-4].replace("(", "").replace(")", "").split(",")
            seismic_date = datetime.datetime.fromtimestamp(float(data[4]) / 1000.0)
            temp_data.append((float(long_lat_str[1]), float(long_lat_str[0])))
            radius = 5 * float(data[2]) if data[2] is not None else 5
            folium.CircleMarker(
                location=[float(long_lat_str[1]), float(long_lat_str[0])],
                tooltip="Seismic details",
                radius=radius,
                color="red",
                fill_opacity=0.2,
                opacity=1,
                fill_color="red",
                popup=f"""
                        <link rel="stylesheet" href="static/styles/styles.css">
                        <div class="popup_window">
                            <h3 class="popup_title"> {data[3].upper()} </h3><br>
                            <p><i><b>Id :</b> {data[1]}</i></p>
                            <p><b>Date :</b> {seismic_date.year}-{seismic_date.month}-{seismic_date.day}</p>
                            <p><b>URL :</b> <a href="{data[7]}">More Info Here.</a></p>
                            <hr>
                            <p class="popup_mag"><b>Magnitude :</b> {data[2]}</p>
                            <p><b>Depth :</b> {data[-3]} Km</p>
                            <p><b>Sources :</b> {data[19]}</p>
                            <p><b>Type :</b> {data[26]}</p>
                            <p><b>Tsunami alert :</b> {"YES" if data[14] == 1 else "NO"}</p>
                        </div>
                        """
            ).add_to(marker_cluster)
    iframe = m.get_root()._repr_html_()
    return render_template('home.html', iframe=iframe)

@app.route("/data")
def data():
    db_inst = get_db_instance()
    p = "<h1>NO DATA</h1>"
    if db_inst:
        result = db_inst.query(f"""
            SELECT mag FROM earthquakes;
        """)
        data_frame = pandas.DataFrame(result, columns=['mag'])
        magnitudes = data_frame.dropna()
        hist, edges = np.histogram(magnitudes, density=False, bins=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0])
        source = ColumnDataSource(dict(x=edges,y=hist))
        p = figure(title="Magnitudes Distribution Histogram", x_axis_label="Magnitudes", y_axis_label="Magnitudes repartition", width=900, height=600)

        p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], 
                fill_color="skyblue", line_color="black")

        p.y_range.start = 0
        p.x_range.start = 0
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None

        labels = LabelSet(x='x', y='y', text='y', level='glyph',
                  text_align='center', y_offset=15, x_offset=25, source=source, text_font_size='12px')

        p.add_layout(labels)
        script, div = components(p)
    return render_template('data.html', bokeh_resources=CDN.render(), script=script, div=div)

if __name__ == "__main__":
    app.run(debug=True)