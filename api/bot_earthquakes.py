import requests


def main() :
    start_time = "2014-01-01"
    end_time = "2014-01-02"
    result  = requests.get(f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}&endtime={end_time}")
    print(result.status_code)
    result_converted_json = result.json()
    print(len(result_converted_json["features"]))

if __name__ == "__main__":
    main()