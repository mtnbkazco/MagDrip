import pymysql
from data_create_insert import insert_data as insert_data
from update_data_insert import update_data_insert
import random
import time
import datetime as dt
import threading as thread


def get_sql_connection():
    conn = pymysql.connect("localhost", "root", "", "BMI6300")
    return conn


def initialize_db():
    connection = get_sql_connection()
    mydb = connection.cursor()
    mydb.execute("DROP TABLE IF EXISTS Patient_BP;")
    mydb.execute(
        "CREATE TABLE Patient_BP"
        "(Patient_Information_idPatient INT,SYSTOLIC INT,DIASTOLIC INT, HR INT, TEMP INT, PULSEOX INT,"
        "TIME_Of_BP TIMESTAMP);"
    )

    create_query = (
        "INSERT INTO Patient_BP (Patient_Information_idPatient,SYSTOLIC,DIASTOLIC,HR,TEMP,PULSEOX,TIME_Of_BP) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s);"
    )

    mydb.executemany(create_query, insert_data)
    connection.commit()


def update_db():
    connection = get_sql_connection()
    mydb = connection.cursor()
    mydb.execute("DROP TABLE IF EXISTS Current_Patient_BP;")
    mydb.execute(
        "CREATE TABLE Current_Patient_BP"
        "(Patient_Information_idPatient INT,SYSTOLIC INT,DIASTOLIC INT, HR INT, TEMP INT, PULSEOX INT,"
        "TIME_Of_BP TIMESTAMP);"
    )

    update_pt_info = (
        "INSERT INTO Current_Patient_BP (Patient_Information_idPatient,SYSTOLIC,DIASTOLIC,HR,TEMP,PULSEOX,TIME_Of_BP) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s);"
    )
    try:
        mydb.executemany(update_pt_info, update_data_insert)
        connection.commit()
    except:
        print("Error")
        connection.rollback()
        time.sleep(2)


# get_sql_connection()
# initialize_db()
# update_db()
