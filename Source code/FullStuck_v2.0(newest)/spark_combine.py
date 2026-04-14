from pyspark.sql import SparkSession
from pyspark.sql.types import *

def export_raw_data_to_sql():
    spark = SparkSession.builder.appName("RawToSQL").master("local[*]").getOrCreate()

    # Schema
    schema = StructType([
        StructField("driverID", StringType(), True),
        StructField("carPlateNumber", StringType(), True),
        StructField("Latitude", FloatType(), True),
        StructField("Longitude", FloatType(), True),
        StructField("Speed", FloatType(), True),
        StructField("Direction", StringType(), True),
        StructField("siteName", StringType(), True),
        StructField("Time", StringType(), True),
        StructField("isRapidlySpeedup", IntegerType(), True),
        StructField("isRapidlySlowdown", IntegerType(), True),
        StructField("isNeutralSlide", IntegerType(), True),
        StructField("isNeutralSlideFinished", IntegerType(), True),
        StructField("neutralSlideTime", IntegerType(), True),
        StructField("isOverspeed", IntegerType(), True),
        StructField("isOverspeedFinished", IntegerType(), True),
        StructField("overspeedTime", IntegerType(), True),
        StructField("isFatigueDriving", IntegerType(), True),
        StructField("isHthrottleStop", IntegerType(), True),
        StructField("isOilLeak", IntegerType(), True)
    ])

    # Read data from csv
    df = spark.read.csv("data/detail_record_*", schema=schema, header=False)

    # Convert to SQL INSERT
    table_name = "raw_driving_records"
    rows = df.collect()
    
    with open("setup_raw_data.sql", "w", encoding="utf-8") as f:
        # Setup table
        f.write(f"CREATE TABLE IF NOT EXISTS {table_name} (driverID VARCHAR(50), carPlateNumber VARCHAR(20), Speed FLOAT, Time DATETIME, isOverspeed INT, isFatigueDriving INT, overspeedTime INT, neutralSlideTime INT);\n")
        
        for r in rows:
            # convert needed data into SQL
            sql = f"INSERT INTO {table_name} (driverID, carPlateNumber, Speed, Time, isOverspeed, isFatigueDriving, overspeedTime, neutralSlideTime) VALUES ('{r['driverID']}', '{r['carPlateNumber']}', {r['Speed']}, '{r['Time']}', {r['isOverspeed']}, {r['isFatigueDriving']}, {r['overspeedTime']}, {r['neutralSlideTime']});\n"
            f.write(sql)

    print("Success: setup_raw_data.sql generated.")
    spark.stop()

if __name__ == "__main__":
    export_raw_data_to_sql()