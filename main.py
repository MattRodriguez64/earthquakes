from flask import Flask, render_template_string, render_template
import folium
from config.database import get_db_instance
import requests
import datetime
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
import random

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

    folium.PolyLine(
        locations=[[0, longitude] for longitude in range(-180, 181)],
        color="#FFD60A",
        weight=3,
        opacity=0.9,
        tooltip="Équateur",
        dash_array="10, 6"
    ).add_to(m)
    
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
    ).add_to(m)

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
    ).add_to(m)

    db_inst = get_db_instance()
    if db_inst:
        result = db_inst.query("""
            SELECT * FROM earthquakes WHERE earthquake_time >= 1787184000000;
        """)

        for data in result:
            long_lat_str = data[-4].replace("(", "").replace(")", "").split(",")
            print(float(data[4]))
            seismic_date = datetime.datetime.fromtimestamp(float(data[4]) / 1000.0)
            folium.Marker(
                location=[float(long_lat_str[1]), float(long_lat_str[0])],
                tooltip="Seismic details",
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
                        """,
                icon=folium.Icon(color="green"),
            ).add_to(m)
    iframe = m.get_root()._repr_html_()
    return render_template('home.html', iframe=iframe)

@app.route("/data")
def data():
    x = [1, 2, 3, 4, 5]
    y = [4, 7, 2, 8, 5]

    graphique = figure(
        title="Exemple de graphique Bokeh",
        x_axis_label="Valeur X",
        y_axis_label="Valeur Y",
        height=400,
        sizing_mode="stretch_width",
        tools="pan,wheel_zoom,box_zoom,reset,save"
    )
    
    graphique.line(
        x,
        y,
        line_width=3,
        color="#2563eb",
        legend_label="Mes données"
    )

    graphique.scatter(
        x,
        y,
        size=10,
        color="#dc2626"
    )
    
    script, div = components(graphique)
    return render_template('data.html', bokeh_resources=CDN.render(), script=script, div=div)

if __name__ == "__main__":
    app.run(debug=True)