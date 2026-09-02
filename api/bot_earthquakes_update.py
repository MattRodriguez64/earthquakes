import requests
from config.database import get_db_instance


def main():
    db_inst = get_db_instance()
    db_inst.connect_cursor()
    try:
        result = db_inst.query("""
            SELECT * FROM earthquakes WHERE mag IS NULL;
        """)

        for data in result:
            request_result  = requests.get(f"{data[8]}")
            result_converted_json = request_result.json()
            temp_mag_value = result_converted_json["properties"]["mag"]
            unique_id = data[1]
            print(unique_id)
            if temp_mag_value is not None:
                db_inst.query_update(f"""
                        UPDATE earthquakes SET mag = %s WHERE event_id = '%s';
                    """, (temp_mag_value, unique_id))

    except Exception as e:
        print(f">> AN ERROR OCCURED : {e}")
        db_inst.db_connection.rollback()
    finally:
        db_inst.db_cursor.close()


if __name__ == "__main__":
    main()