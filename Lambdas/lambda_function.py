import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from botocore.exceptions import ClientError
import os

OPENSEARCH_HOST = os.environ['OPENSEARCH_HOST']
OPENSEARCH_USERNAME = os.environ['OPENSEARCH_USERNAME']
OPENSEARCH_PASSWORD = os.environ['OPENSEARCH_PASSWORD']

# Initialize clients
sqs_client = boto3.client('sqs', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
ses_client = boto3.client('ses', region_name='us-east-1')

# Initialize OpenSearch client
os_client = OpenSearch(
    hosts=[OPENSEARCH_HOST],
    http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),  # Add your OpenSearch credentials if necessary
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

def lambda_handler(event, context):
    try:
        # 1. Pull a message from SQS queue
        sqs_queue_url = 'https://sqs.us-east-1.amazonaws.com/863518439994/Q1'
        sqs_response = sqs_client.receive_message(
            QueueUrl=sqs_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=2
        )
        
        print(sqs_response)
        
        messages = sqs_response.get('Messages', [])

        for message in messages:
            request_data = json.loads(message['Body'])

            # Extract details from the SQS message
            location = request_data['location']
            cuisine = request_data['cuisine']
            dining_date = request_data['diningDate']
            dining_time = request_data['diningTime']
            number_of_people = request_data['numberOfPeople']
            email = request_data['email']

            # 2. Fetch a random restaurant recommendation from OpenSearch based on cuisine
            os_response = os_client.search(
                index='restaurants',
                body={
                    'query': {
                        'match': {
                            'Cuisine': cuisine
                        }
                    },
                    'size':3
                }
            )
            
            print(os_response)
            
            restaurant = os_response['hits']['hits'][0]['_source'] if os_response['hits']['hits'] else None

            if not restaurant:
                raise Exception(f'No restaurants found for cuisine: {cuisine}')

            # 3. Fetch more details from DynamoDB
            db_params = {
                'TableName': 'yelp-restaurants',
                'Key': {
                    'BusinessID': {'S': restaurant['RestaurantID']}
                }
            }
            db_response = dynamodb_client.get_item(**db_params)
            restaurant_details = db_response.get('Item', {})
            
            print(restaurant_details)

            # 4. Format the email content with location, dining time, and number of people
            email_params = {
                'Source': 'dc5415@nyu.edu',
                'Destination': {
                    'ToAddresses': [email]
                },
                'Message': {
                    'Subject': {
                        'Data': 'Your Dining Recommendation'
                    },
                    'Body': {
                        'Text': {
                            'Data': (f"Hi there,\n\n"
                                     f"Here is your dining recommendation based on your request:\n\n"
                                     f"Restaurant Name: {restaurant_details.get('Name', {}).get('S', 'N/A')}\n"
                                     f"Address: {restaurant_details.get('Address', {}).get('S', 'N/A')}\n"
                                     f"Cuisine: {restaurant['Cuisine']}\n\n"
                                     f"Location: {location}\n"
                                     f"Dining Time: {dining_time}\n"
                                     f"Dining Date: {dining_date}\n"
                                     f"Number of People: {number_of_people}\n\n"
                                     f"Enjoy your meal!")
                        }
                    }
                }
            }

            # 5. Send email via SES
            ses_client.send_email(**email_params)

            # 6. Delete message from SQS queue
            sqs_client.delete_message(
                QueueUrl=sqs_queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )

            print(f'Recommendation sent to {email}')

    except Exception as error:
        print(f'Error processing request: {error}')
        raise error
