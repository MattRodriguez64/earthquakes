import requests
import calendar
import datetime
from config.database import get_db_instance
import psycopg


def format_data_in_row(data:dict) -> tuple:
    properties_data = data["properties"]
    geometry_data = data["geometry"]
    id_data = data["id"]
    get_datetime = datetime.datetime.now()

    return (
        id_data,
        properties_data["mag"],
        properties_data["place"],
        properties_data["time"],
        properties_data["updated"],
        properties_data["tz"],
        properties_data["url"],
        properties_data["detail"],
        properties_data["felt"],
        properties_data["cdi"],
        properties_data["mmi"],
        properties_data["alert"],
        properties_data["status"],
        properties_data["tsunami"],
        properties_data["sig"],
        properties_data["net"],
        properties_data["code"],
        properties_data["ids"],
        properties_data["sources"],
        properties_data["types"],
        properties_data["nst"],
        properties_data["dmin"],
        properties_data["rms"],
        properties_data["gap"],
        properties_data["magType"],
        properties_data["type"],
        (geometry_data["coordinates"][0], geometry_data["coordinates"][1]),
        geometry_data["coordinates"][2],
        f"{get_datetime.year}-{get_datetime.month}-{get_datetime.day}",
        f"{get_datetime.year}-{get_datetime.month}-{get_datetime.day}"
    )


def save_data(data_to_save):
    db_inst = get_db_instance()
    db_inst.connect_cursor()
    try:
        with db_inst.db_cursor.copy("""COPY earthquakes(
            event_id,
            mag,
            place,
            earthquake_time,
            updated,
            timezone,
            url,
            earthquake_detail,
            felt,
            cdi,
            mmi,
            alert,
            status,
            tsunami,
            sig,
            net,
            code,
            ids,
            sources,
            product_types,
            mag_nst,
            dmin,
            rms,
            gap,
            mag_type,
            seismic_type,
            long_lat,
            seismic_depth,
            inserted_date,
            last_modification_date )
            FROM STDIN""") as copy:
            for data in data_to_save:
                temp_data = format_data_in_row(data)
                copy.write_row(temp_data)

        db_inst.db_connection.commit()
        
    except psycopg.errors.UniqueViolation as e:
        print(f">> DATA ALREADY SAVED IN DATABASE : {e}")
        db_inst.db_connection.rollback()
    except Exception as e:
        print(f">> AN ERROR OCCURED : {e}")
        db_inst.db_connection.rollback()
    finally:
        db_inst.db_cursor.close()


def main() :
    
    current_year = 2005
    current_month = 1
    current_day = 1
    current_date = datetime.datetime(current_year, current_month, current_day)
    today = datetime.datetime.now()

    while current_date <= today:
        for i in range(1, calendar._monthlen(current_year, current_month) + 1):
            current_date = datetime.datetime(current_year, current_month, i)
            current_day = i
            start_time = f"{current_year}-{current_month}-{i}"
            if (i + 1) <= calendar._monthlen(current_year, current_month):
                end_time = f"{current_year}-{current_month}-{i + 1}"
            else:
                next_date = current_date + datetime.timedelta(days=1)
                end_time = f"{next_date.year}-{next_date.month}-{next_date.day}"
                current_year = next_date.year
                current_month = next_date.month
                current_day = next_date.day
                print(f">> next date : {next_date}")
            result  = requests.get(f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}&endtime={end_time}")
            print(f">>> STATUS : {result.status_code}")
            result_converted_json = result.json()
            if len(result_converted_json["features"]) > 0:
                save_data(result_converted_json["features"])
                
        print(f">> current_year : {current_year} : current_month : {current_month}")

if __name__ == "__main__":
    main()