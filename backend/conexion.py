
import mysql.connector

def get_conection():
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",
        password="730@E510m",
        database="renta_inmuebles",
        port=3306
    )
    

    return conexion
