from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import sum

def export_summary_to_sql():
    spark = SparkSession.builder.appName("SummaryToSQL").master("local[*]").getOrCreate()

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

    df = spark.read.csv("data/detail_record_*", schema=schema, header=False)

    # Count needed data 
    summary_df = df.groupBy("driverID", "carPlateNumber").agg(
        sum("isOverspeed").alias("overspeed_count"),
        sum("isFatigueDriving").alias("fatigue_count"),
        sum("overspeedTime").alias("total_overspeed_sec"),
        sum("neutralSlideTime").alias("total_neutral_slide_sec")
    )

    summary_rows = summary_df.collect()
    table_name = "driver_behavior_summary"
    
    with open("summary_results.sql", "w", encoding="utf-8") as f:
        f.write(f"CREATE TABLE IF NOT EXISTS {table_name} (driverID VARCHAR(50), carPlateNumber VARCHAR(20), overspeed_count INT, fatigue_count INT, total_overspeed_sec INT, total_neutral_slide_sec INT);\n")
        for r in summary_rows:
            sql = f"INSERT INTO {table_name} VALUES ('{r['driverID']}', '{r['carPlateNumber']}', {r['overspeed_count']}, {r['fatigue_count']}, {r['total_overspeed_sec']}, {r['total_neutral_slide_sec']});\n"
            f.write(sql)

    print("Success: summary_results.sql generated.")
    spark.stop()

if __name__ == "__main__":
    export_summary_to_sql()