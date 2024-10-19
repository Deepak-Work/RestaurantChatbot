import requests
import boto3
from datetime import datetime
import time
from decimal import Decimal

from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth

# Replace with your credentials
session = boto3.Session()
credentials = session.get_credentials()
region = 'us-east-1'

awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

# OpenSearch Endpoint
OPENSEARCH_ENDPOINT = "https://search-restaurants-xwdnrhwldbm445z6p5a7x6vi6e.us-east-1.es.amazonaws.com"

opensearch_client = OpenSearch(hosts=[OPENSEARCH_ENDPOINT], 
                                   http_auth=HTTPBasicAuth(,), use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)

# Elasticsearch index and type
INDEX_NAME = 'restaurants'
DOC_TYPE = 'Restaurant'


# Replace with your Yelp API Key
YELP_API_KEY = #<Insert your API key>

# Yelp API endpoint
YELP_API_URL = "https://api.yelp.com/v3/businesses/search"

# DynamoDB Table Name
DYNAMODB_TABLE_NAME = 'yelp-restaurants'

# AWS region for DynamoDB
AWS_REGION = 'us-east-1'

# Create a DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Function to fetch data from Yelp API
def fetch_restaurants_from_yelp(cuisine_type, location="Manhattan", offset=0, limit=50):
    headers = {
        "Authorization": f"Bearer {YELP_API_KEY}"
    }
    params = {
        "term": cuisine_type,
        "location": location,
        "limit": limit,
        "offset": offset
    }
    response = requests.get(YELP_API_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('businesses', []), cuisine_type
    else:
        print(f"Failed to fetch from Yelp: {response.status_code} - {response.text}")
        return []

def insert_data_into_opensearch(opensearch_client, restaurant):
    response = opensearch_client.index(index="restaurants", body=restaurant, refresh=True)
    print(response)
    print(f'Document indexed: {response["_id"]} for restaurant {restaurant["RestaurantID"]}')

# Function to insert data into DynamoDB
def insert_into_dynamodb(restaurant):
    try:
        # Prepare the item, converting floats to Decimal
        item = {
            'BusinessID': restaurant.get('id'),
            'Name': restaurant.get('name'),
            'Address': ", ".join(restaurant['location'].get('display_address', [])),
            'Coordinates': {
                'Latitude': Decimal(str(restaurant['coordinates'].get('latitude', 0.0))),
                'Longitude': Decimal(str(restaurant['coordinates'].get('longitude', 0.0)))
            },
            'NumberOfReviews': restaurant.get('review_count', 0),
            'Rating': Decimal(str(restaurant.get('rating', 0.0))),
            'ZipCode': restaurant['location'].get('zip_code', ''),
            'InsertedAtTimestamp': str(datetime.now())
        }
        
        # Insert into DynamoDB
        table.put_item(Item=item)
        print(f"Inserted: {restaurant.get('name')} into DynamoDB")

    except Exception as e:
        print(f"Error inserting {restaurant.get('name')}: {str(e)}")

# Function to scrape and store restaurants based on cuisine type
def scrape_restaurants(cuisine_type):
    offset = 0
    limit = 50  # Yelp API allows max 50 results per request
    total_scraped = 0
    max_results = 50  # We'll scrape 1000 restaurants for each cuisine type

    while total_scraped < max_results:
        restaurants, cuisine = fetch_restaurants_from_yelp(cuisine_type, offset=offset, limit=limit)

        if not restaurants:
            break

        for restaurant in restaurants:
            insert_into_dynamodb(restaurant)

            restaurant_json = {"RestaurantID":restaurant.get('id'),'Cuisine':cuisine}

            insert_data_into_opensearch(opensearch_client, restaurant_json)

        total_scraped += len(restaurants)
        offset += limit

        print(f"Scraped {total_scraped} {cuisine_type} restaurants so far...")

        # Yelp has a rate limit, so we may want to slow down requests
        time.sleep(1)  # Sleep for 1 second between requests

# Main function to scrape different cuisine types
def main():
    cuisine_types = ['Indian', 'Italian', 'Mexican']  # Add more cuisines if needed

    for cuisine in cuisine_types:
        print(f"Scraping restaurants for {cuisine}...")
        scrape_restaurants(cuisine)

if __name__ == "__main__":
    main()
