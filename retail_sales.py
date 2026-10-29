
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, trim, to_date

# --------------------------------------------------
# 1. Setup
# --------------------------------------------------
spark = SparkSession.builder.appName(
    "RetailSalesAnalyticsETL"
).getOrCreate()

BUCKET = "retail-sales-bucket-53"

SALES_INPUT = f"s3://{BUCKET}/raw/flat_files/"
API_INPUT = f"s3://{BUCKET}/raw/api/"

SALES_OUTPUT = f"s3://{BUCKET}/processed/sales/"
PRODUCTS_OUTPUT = f"s3://{BUCKET}/processed/products/"


# --------------------------------------------------
# 2. Sales CSV transformation
# --------------------------------------------------
sales = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(SALES_INPUT)
)


sales = (
    sales
    .withColumn("Quantity", col("Quantity").cast("integer"))
    .withColumn("UnitPrice", col("UnitPrice").cast("double"))
    .withColumn("InvoiceDate", trim(col("InvoiceDate")))
    .withColumn("CustomerID", col("CustomerID").cast("string"))

    # Remove rows missing essential sales information
    .filter(col("InvoiceNo").isNotNull())
    .filter(col("StockCode").isNotNull())
    .filter(col("Quantity").isNotNull())
    .filter(col("UnitPrice").isNotNull())

    # Remove invalid values
    .filter(col("Quantity") != 0)
    .filter(col("UnitPrice") >= 0)

    # Calculate sales amount
    .withColumn(
        "SalesAmount",
        col("Quantity") * col("UnitPrice")
    )

    # Convert text into a date
    .withColumn(
        "InvoiceDate",
        to_date(col("InvoiceDate"))
    )

    # Remove completely identical rows
    .dropDuplicates()
)


sales.write.mode("overwrite").parquet(SALES_OUTPUT)

print("Sales transformation completed")


# --------------------------------------------------
# 3. DummyJSON products transformation
# --------------------------------------------------

api_data = spark.read.json(API_INPUT)

products = (
    api_data
    .select(explode(col("products")).alias("product"))
    .select(
        col("product.id").cast("integer").alias("ProductID"),
        col("product.title").cast("string").alias("ProductName"),
        col("product.category").cast("string").alias("Category"),
        col("product.price").cast("double").alias("Price"),
        col("product.stock").cast("integer").alias("Stock"),
        col("product.rating").cast("double").alias("Rating")
    )
    .filter(col("ProductID").isNotNull())
    .filter(col("ProductName").isNotNull())
    .filter(col("Price").isNotNull())
    .filter(col("Price") >= 0)
    .filter(col("Stock").isNotNull())
    .filter(col("Stock") >= 0)
    .dropDuplicates(["ProductID"])
)

# Save the cleaned product data
products.write.mode("overwrite").parquet(PRODUCTS_OUTPUT)

print("Products transformation completed")


print("All two transformations completed successfully")
