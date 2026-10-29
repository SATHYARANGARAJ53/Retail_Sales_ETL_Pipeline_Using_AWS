
import json
import os
import urllib.request
from datetime import datetime, timezone

import boto3

s3 = boto3.client("s3")


API_URL = "https://dummyjson.com/products?limit=10"


def lambda_handler(event, context):
    bucket = os.environ["BUCKET_NAME"]

    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "RetailSalesAnalytics/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    key = f"raw/api/dummyjson_products_{timestamp}.json"

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json"
    )

    return {
        "statusCode": 200,
        "message": "DummyJSON data saved to S3",
        "s3_bucket": bucket,
        "s3_key": key,
        "products_received": len(data.get("products", [])),
        "total_available": data.get("total")
    }
