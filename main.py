from flask import Flask, render_template_string, render_template
import folium
from config.database import get_db_instance
import sys
import requests

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
            folium.Marker(
                location=[float(long_lat_str[1]), float(long_lat_str[0])],
                tooltip="Seismic details",
                popup=f"{data[3]}",
                icon=folium.Icon(color="green"),
            ).add_to(m)
    iframe = m.get_root()._repr_html_()
    return render_template('home.html', iframe=iframe)

if __name__ == "__main__":
    app.run(debug=True)