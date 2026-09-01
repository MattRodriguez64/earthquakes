import psycopg


class DatabaseConnector:
    db_instance = None
    db_connection = None
    db_cursor = None

    def __init__(self):
        if(DatabaseConnector.db_instance is not None):
            raise Exception("Error : SINGLETON instance detected!")
        else:
            self.connect_database()
            if self.db_connection is not None:
                DatabaseConnector.db_instance = self
            else:
                print("Connection could not be established...")

    def connect_cursor(self):
        self.db_cursor = self.db_connection.cursor()

    def connect_database(self):
        if self.db_connection is None:
            try:
                temp_db_connection = psycopg.connect(host="localhost", dbname="earthquakes", user="", password="", port=5432)

                # if self.db_connection._check_connection_ok:
                self.db_connection = temp_db_connection
                db_info = self.db_connection.info
                print(f"DB_INFO : {db_info} \n")
                self.connect_cursor()
                self.db_cursor.close()
            except Exception as e:
                print(f"Error : {e} \n")

    def query(self, query):
        self.connect_cursor()
        result = self.db_cursor.execute(query=query).fetchall()
        self.db_connection.commit()
        self.db_cursor.close()
        return result

    def close_database(self):
        try:
            self.db_connection.close()
            print("Database closed successfully!")
        except Exception as e:
            print(f"Database already closed : {e}")

    @classmethod
    def get_instance(self):
        if DatabaseConnector.db_instance is None:
            DatabaseConnector()
        return DatabaseConnector.db_instance

def get_db_instance() -> DatabaseConnector:
    if DatabaseConnector.db_instance is None:
        DatabaseConnector()
    return DatabaseConnector.db_instance

if __name__ == "__main__":
    get_db = get_db_instance()

    if get_db:
        result = get_db.query("""
            SELECT * FROM earthquakes WHERE earthquake_time >= 1787184000000;;
        """)[0]

        print(f"RESULT : {float(result[-4].replace("(", "").replace(")", "").split(",")[0])}")
        print(f"R : {result}")
