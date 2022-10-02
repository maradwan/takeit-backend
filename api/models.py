import boto3
from boto3.dynamodb.conditions import Key, Attr
import decimal
import simplejson as json
from os import environ as env

table_name = env.get("TABLE_NAME")
region_name  = env.get("REGION_NAME")

query_table = boto3.resource("dynamodb", region_name= region_name, verify=True).Table(table_name)

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def add_record(item):
    return query_table.put_item(Item=item)

def get_record(username,item):
    z = {}
    x = []
    z['Items'] = []

    response= query_table.query(
        KeyConditionExpression=Key("username").eq(username) & Key("created").eq(item))

    for i in response[u'Items']:
        x.append( json.loads(json.dumps(i, cls=DecimalEncoder)))

    z['Items'] = x

    return z

def get_record_begins_with(username,item):
    z = {}
    x = []
    z['Items'] = []

    response= query_table.query(
        KeyConditionExpression=Key("username").eq(username) & Key("created").begins_with(item))


    for i in response[u'Items']:
        x.append( json.loads(json.dumps(i, cls=DecimalEncoder)))

    z['Items'] = x

    return z

def get_records(username,created=None):
    z = {}
    x = []
    z['Items'] = []
    response= query_table.query(
        KeyConditionExpression=Key("username").eq(username)
    )

    for i in response[u'Items']:
        if created=='contacts' and 'contacts' in i['created']:
            x.append( json.loads(json.dumps(i, cls=DecimalEncoder)))
        elif created=='account' and 'account' in i['created']:
            x.append( json.loads(json.dumps(i, cls=DecimalEncoder)))

        elif not created and 'contacts' not in i['created'] and 'account' not in i['created'] and 'accepted' not in i['created'] and 'pending' not in i['created'] and 'request' not in i['created'] and 'declined' not in i['created'] and 'traveleraccepted' not in i['created'] and 'travelerdeclined' not in i['created']:
            x.append( json.loads(json.dumps(i, cls=DecimalEncoder)))

    z['Items'] = x

    return z

def delete_record(username,created):
    return query_table.delete_item(
        Key={
            'username': username,
            'created' : created
            }
            )

def delete_records(username):
    items= query_table.query(
        KeyConditionExpression=Key("username").eq(username)
    )
    for i in range(len(items['Items'])):
        query_table.delete_item(
        Key={
            'username': username,
            'created' : items['Items'][i]['created']
            }
            )
    return True

def update_weight_record(username,created,update_item):
    return query_table.update_item(
                Key={'username': username, 'created': created
                },
                UpdateExpression='SET acceptfrom = :acceptfrom, acceptto = :acceptto, fromcity = :fromcity, tocity = :tocity, trdate = :trdate, allowed = :allowed, currency = :currency, fromto = :fromto, tstamp = :tstamp , updated = :updated',
                ExpressionAttributeValues={
                ':acceptfrom': update_item['acceptfrom'],
                ':acceptto': update_item['acceptto'],
                ':fromcity': update_item['fromcity'],
                ':tocity': update_item['tocity'],
                ':trdate': update_item['trdate'],
                ':allowed': update_item['allowed'],
                ':currency': update_item['currency'],
                ':fromto': update_item['fromto'],
                ':tstamp': update_item['tstamp'],
                ':updated': update_item['updated']
                }
            )

def get_global_index(index,key,city,limit,today_date,lastkey=None):

    if lastkey:

        return query_table.query(
        IndexName=index,KeyConditionExpression=Key(
            key).eq(city),Limit=int(limit),FilterExpression=Attr('acceptto').gte(today_date),ExclusiveStartKey=json.loads(lastkey))

    return query_table.query(
        IndexName=index,KeyConditionExpression=Key(
            key).eq(city),Limit=int(limit),FilterExpression=Attr('acceptto').gte(today_date))