import json
import logging
import os
import boto3

from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DB_TABLE = os.getenv('DB_TABLE')

dynamodb = boto3.resource('dynamodb')
postsTable = dynamodb.Table(DB_TABLE)

def response(body, statusCode=200):
    return {
        'statusCode': statusCode,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    } 

def list(event, context):
    result = postsTable.scan()
    all_posts = result['Items']
    
    while 'LastEvaluatedKey' in result:
        result = postsTable.scan(ExclusiveStartKey=result['LastEvaluatedKey'])
        all_posts.extend(result['Items'])

    return response(all_posts)

def get(event, context):
    post_id = event['pathParameters']['id']
    result = postsTable.get_item(Key={'id': post_id})
    
    if 'Item' in result:
        return response(result['Item'])

    return response('not found', 404)

def create(event, context):
    post = json.loads(event['body'])
    
    item = {
        'id': str(uuid4()),
        'created_at': datetime.now().isoformat(),
        'post': post
    }
    
    result = postsTable.put_item(Item=item)
    
    if result['ResponseMetadata']['HTTPStatusCode'] == 200:
        return response(item)
        
    logger.error(result)
    
    return response('Oops something went wrong.', 500)

def update(event, context):
    post_id = event['pathParameters']['id']
    result = postsTable.get_item(Key={'id': post_id})
    
    if not 'Item' in result:
        return response('not found', 404)
    
    post = json.loads(event['body'])
    item = result['Item']
    item['post'] = post
    item['updated_at'] = datetime.now().isoformat()
    
    postsTable.put_item(Item=item)
    
    if result['ResponseMetadata']['HTTPStatusCode'] == 200:
        return response(item)
    
    logger.error(result)
    
    return response('Oops something went wrong.', 500)
    

def delete(event, context):
    post_id = event['pathParameters']['id']
    result = postsTable.delete_item(Key={'id': post_id})

    if result['ResponseMetadata']['HTTPStatusCode'] == 200:
        return response(True, 204)
    
    logger.error(result)
    
    return response('Oops something went wrong.', 500)