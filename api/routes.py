import json
from flask import request, jsonify
import boto3
from os import environ as env
from api.auth import gen_time, token_username, today_date
from api.models import get_record, add_record, get_records, delete_record, delete_records, update_weight_record, get_global_index, get_record_begins_with
from api.subscription import add_subscription, get_subscriptions, delete_subscription 
from api import app
from time import mktime
from datetime import datetime, timedelta

from api.notification import send_push_notification

subscription_limit = int(env.get("SUBSCRIPTION_LIMIT"))
weight_limit = int(env.get("WEIGHT_LIMIT"))
region_name  = env.get("REGION_NAME")
subj_remove_account = env.get("SUBJ_REMOVE_ACCOUNT")
source_email = env.get("SOURCE_EMAIL")
userpoolid = env.get("USERPOOLID")
trips_queue_url = env.get("TRIPS_QUEUE_URL")

def message_body_deleted_account(name):
    return """Hello {},

We deleted your account as requested.


Sincerely,
TakeIT Team""".format(name)

def notification(to_addresses, msg, subj,source_email=source_email):
    email_client = boto3.client('ses',region_name= region_name, verify=True)
    return email_client.send_email(
        Destination={
            'ToAddresses': [to_addresses],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': msg,
                        },
                        },
                        'Subject': {
                            'Charset': 'UTF-8',
                            'Data': subj,
                            },
                            },
                            Source=source_email,
    )

def user_limit_weight():
    """
    User Limit
    """
    get_weight()
    if weight_limit > get_weight.item_limit:
        return False
    return True

def check_username(username):
    try:
        cognito = boto3.client('cognito-idp',region_name = region_name, verify=True)
        cognito.admin_get_user(UserPoolId=userpoolid,Username = username)
        return True
    except:
        return False

def tstamp(date,days):
    datestamp = date
    #change date to Epoch
    epoch_time= int(mktime(datetime.strptime(datestamp, "%Y-%m-%d").timetuple()))

    #Add days to the date
    orig = datetime.fromtimestamp(epoch_time)
    new = orig + timedelta(days=days)
    return int(new.timestamp())

def get_device_token(username):

    try:
        response = get_record(username,'devices')
        if response['Items'] ==[]:
            return jsonify('no records found'),404

        token = response['Items'][0]['token']
        return (token)
    except:
        return jsonify('Misunderstood Request'),400

def get_trip_info(username,tripid):
    try:
        response = get_record(username,tripid)
        if response['Items'] ==[]:
            return jsonify('no records found'),404

        return (response['Items'][0])
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/devices', methods=['POST'])
def add_device():

    user = token_username()
    username = user['cognito:username']


    try:
        data = request.json
        if data['deviceID'] and data['token'] and len(data) == 2:
            data['username'] = username
            data['created'] = "devices"

            #data['tstamp'] = tstamp(data['trdate'], 30)

            add_record(data)
            return jsonify(data),201

        return jsonify('You must fill in all of the required fields *'),400
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/weight', methods=['POST'])
def add_weight():

    user = token_username()
    username = user['cognito:username']

    if (user_limit_weight()):
        return jsonify('{} Records Limit Reached'.format(get_weight.item_limit)),426

    try:
        data = request.json

        if data['acceptfrom'] and data['acceptto'] and data['fromcity'] and data['tocity'] and data['trdate'] and data['allowed'] and data['currency'] and len(data) == 7:
            data['username'] = username
            data['created'] = gen_time()
            data['fromto'] =  data['fromcity'] + '_' + data['tocity']

            data['tstamp'] = tstamp(data['trdate'], 30)

            add_record(data)
            
            # Send to SQS the trip details
            sqs = boto3.client('sqs')
            sqs.send_message(QueueUrl=trips_queue_url,MessageBody=json.dumps(data))                                                                                                                                                            

            return jsonify(data),201

        return jsonify('You must fill in all of the required fields *'),400
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/weight', methods=['GET'])
def get_weight():

      user = token_username()
      username = user['cognito:username']

      try:
          response = get_records(username)

          get_weight.item_limit =len(response['Items'])


          if response['Items'] ==[]:
                return jsonify('no records found'),404

          return jsonify(response),200
      except:
          return jsonify('Misunderstood Request'),400

@app.route('/weight/<created>', methods=['DELETE'])
def delete_weight(created):

  user = token_username()
  username = user['cognito:username']

  try:
      delete_record(username,created)
      return jsonify("Deleted: {}".format(created)),200
  except:
      return jsonify('Misunderstood Request'),400

@app.route('/weight/<created>', methods=['PUT'])
def update_weight(created):
    user = token_username()
    username = user['cognito:username']

    try:
        data = request.json

        if data['acceptfrom'] and data['acceptto'] and data['fromcity'] and data['tocity'] and data['trdate'] and data['allowed'] and data['currency'] and len(data) == 7:
            data['username'] = username
            data['created'] = created
            data['fromto'] =  data['fromcity'] + '_' + data['tocity']

            data['tstamp'] = tstamp(data['trdate'], 30)
            data['updated'] = gen_time()

            update_weight_record(username, created, data)
            return jsonify(data),201

        return jsonify('You must fill in all of the required fields *'),400
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/trip/<trip_id>', methods=['GET'])
def get_trip(trip_id):


      tripid = trip_id.split('_')[0]
      username = trip_id.split('_')[-1]

      try:
          response = get_record(username,tripid)
          if response['Items'] ==[]:
                return jsonify('no records found'),404

          return jsonify(response),200
      except:
          return jsonify('Misunderstood Request'),400


@app.route('/contacts', methods=['POST'])
def add_contacts():

    user = token_username()
    username = user['cognito:username']

    try:
        data = request.json
        contact = {}

        if 'mobile' in data:
            contact['mobile'] = (data['mobile'])
        if 'fb' in data:
            contact['fb'] = (data['fb'])
        if 'twitter' in data:
            contact['twitter'] = (data['twitter'])
        if 'instagram' in data:
            contact['instagram'] = (data['instagram'])
        if 'linkedin' in data:
            contact['linkedin'] = (data['linkedin'])
        if 'telegram' in data:
            contact['telegram'] = (data['telegram'])
        if 'email' in data:
            contact['email'] = (data['email'])
        if 'cname' in data:
            contact['cname'] = (data['cname'])

        if len(data) <= 8:

            contact['username'] = username
            contact['created'] = "contacts"

            add_record(contact)
            return jsonify(contact),201

        return jsonify('You must fill in all of the required fields *'),400
    except:
        return jsonify('Misunderstood Request'),400


@app.route('/contacts', methods=['GET'])
def get_contacts():

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record(username, 'contacts')
        if response['Items'] == []:
            return jsonify('Not Found'),404

        return jsonify(response),200

    except:
        return jsonify('Misunderstood Request'),400

@app.route('/contacts', methods=['DELETE'])
def delete_contacts():

    user = token_username()
    username = user['cognito:username']

    try:
        delete_record(username, 'contacts')
        return jsonify("Deleted: {}".format('contacts')),200

    except:
        return jsonify('Misunderstood Request'),400


@app.route('/share-request', methods=['POST'])
def share_request():

    user = token_username()
    username = user['cognito:username']

    try:
        data = request.json

        # Adding request to the sender
        if data['traveleruser'] and data['tripid'] and data['trdate'] and len(data) == 3:

            tripid = data['tripid']
            request_user = data['traveleruser']

            data['tstamp'] = tstamp(data['trdate'], 30)


            #Check the request_user exsit
            if not check_username(request_user):
                return jsonify('traveleruser is not registered'),400

            #Check if user requester request to his username
            if request_user == username:
                return jsonify('cannot send requestuser to yourself'),400


            #Check if the traveler has declined requester
            declined_traveler = 'travelerdeclined' + "_" + tripid + '_' + request_user
            check_declined = get_record(username, declined_traveler)

            if len(check_declined['Items']) >= 1:

                if declined_traveler in check_declined['Items'][0]['created']:
                    return jsonify('traveleruser already declined your request'),200

            #Check only one requester has been sent
            requester_accepted = "request" + "_" + tripid + "_" + request_user
            check_requester = get_record(username, requester_accepted)

            if len(check_requester['Items']) >= 1:

                if requester_accepted in check_requester['Items'][0]['created']:
                    return jsonify('already traveleruser has your request'),200

            #Check only one traveleraccepted has been sent
            requester_traveleraccepted = "traveleraccepted" + "_" + tripid + "_" + request_user
            check_traveleraccepted = get_record(username, requester_traveleraccepted)

            if len(check_traveleraccepted['Items']) >= 1:

                if requester_traveleraccepted in check_traveleraccepted['Items'][0]['created']:
                    return jsonify('already requester accepted from traveleruser'),200

            tripid = data['tripid']
            del data['traveleruser']
            del data['trdate']
            #del data['tripid']

            data['username'] = username
            data['created'] = "request" + "_" + tripid + "_" + request_user
            data['dtime'] = gen_time()

            add_record(data)


        # Adding pending to the traveler
            #data['fromuser'] = username
            data['created'] = "pending" + "_" + tripid + "_" + username
            data['tripid'] = tripid

            data['username'] = request_user
            add_record(data)

            try:
                token = get_device_token(request_user)
                trip= get_trip_info(request_user,tripid)
                title = "New Contact Request for your Trip"
                body = "Your Trip From {} To {}, and The Travel date {}".format(trip['fromcity'],trip['tocity'],trip['trdate'])
                send_push_notification(token,title,body)
                return jsonify('request has been sent'),201
            except:
                return jsonify('request has been sent'),201


        return jsonify('You must fill in all of the required fields *'),400
    except:
        return jsonify('Misunderstood Request'),400



@app.route('/share-request/traveler/<created>', methods=['POST'])
def traveler_accept_request(created):

    user = token_username()
    username = user['cognito:username']

    try:

        response = get_record(username, created)
        if response['Items'] == []:
            return jsonify('Not Found'),404

        tstamp = response['Items'][0]['tstamp']
        tripid = response['Items'][0]['tripid']

        data = {}
        data['username'] = username
        data['dtime']    = gen_time()
        data['tstamp']   = tstamp
        data['tripid']   = tripid

        request_creator = created.split('_')[-1]

        acceptor = 'accepted' + "_" + tripid + "_" + request_creator
        data['created'] = acceptor

        add_record(data)
        delete_record(username, created)

        # Delete the request from the sender
        receiver_id = 'request' + "_" + tripid + "_" + username
        delete_record(request_creator, receiver_id)

        # Add traveleraccepted to the requester from the traveler
        receiver_accepted = 'traveleraccepted' + "_" + tripid + "_" + username

        data['username'] = request_creator
        data['created'] = receiver_accepted

        add_record(data)

        try:
            token = get_device_token(request_creator)
            trip  = get_trip_info(username,tripid)
            title = "Package Accepted From {} To {}".format(trip['fromcity'],trip['tocity'])
            body  = "Traveler Accepted Your Package For The Trip From {} To {}, and The Travel Date {}".format(trip['acceptfrom'],trip['acceptto'],trip['trdate'])
            send_push_notification(token,title,body)
            return jsonify('request has been accepted'),201
        except:
            return jsonify('request has been accepted'),201
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/traveler/<created>', methods=['DELETE'])
def traveler_reject_request(created):

    user = token_username()
    username = user['cognito:username']

    try:
        data = {}
        data['username'] = username
        data['created'] = created

        response = get_record(username, created)
        tstamp = response['Items'][0]['tstamp']
        tripid = response['Items'][0]['tripid']

        data['tstamp'] = tstamp
        data['tripid'] = tripid
        data['dtime']  = gen_time()

        if response['Items'] == []:
            return jsonify('Not Found'),404

        delete_record(username, created)

        # Delete the request from the requester
        request_creator = created.split('_')[-1]
        receiver_id = 'request' + "_" + tripid + "_" + username

        delete_record(request_creator, receiver_id)

        # declined the requester in the traveler view
        declined_requester = 'declined' + "_" + tripid  + "_" + request_creator
        data['created'] = declined_requester
        add_record(data)

        # declined traveler in the requester view
        declined_traveler = 'travelerdeclined' + "_" + tripid + "_" + username
        data['created'] = declined_traveler
        data['username'] = request_creator
        add_record(data)

        try:
            token = get_device_token(request_creator)
            trip  = get_trip_info(username,tripid)
            title = "Package Declined From {} To {}".format(trip['fromcity'],trip['tocity'])
            body  = "Traveler Declined Your Package For The Trip From {} To {}, and The Travel Date {}".format(trip['acceptfrom'],trip['acceptto'],trip['trdate'])
            send_push_notification(token,title,body)
            return jsonify("Deleted: {}".format(created)),200
        except:
            return jsonify("Deleted: {}".format(created)),200

    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/traveler/declined/<contact>', methods=['DELETE'])
def traveler_delete_declined(contact):

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record(username, contact)
        if response['Items'] == []:
            return jsonify('Not Found'),404

        delete_record(username, contact)

        # Delete the sharing between traveler and requester
        receiver_id = contact.split('_')[-1]
        tripid = contact.split('_')[1]

        request_creator = "travelerdeclined" + "_" + tripid + "_" + username
        delete_record(receiver_id, request_creator)

        try:
            token = get_device_token(receiver_id)
            trip  = get_trip_info(username,tripid)
            title = "The traveler declined your contacts"
            body  = "Traveler is not interested in the trip from {} to {}, and the travel date {}".format(trip['fromcity'],trip['tocity'],trip['trdate'])
            send_push_notification(token,title,body)
            return jsonify("Deleted: {}".format(contact)),200
        except:
            return jsonify("Deleted: {}".format(contact)),200

    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/traveler/accepted/<contact>', methods=['DELETE'])
def traveler_delete_accept(contact):

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record(username, contact)
        if response['Items'] == []:
            return jsonify('Not Found'),404

        delete_record(username, contact)

        # Delete the sharing between traveler and requester
        receiver_id = contact.split('_')[-1]
        tripid = contact.split('_')[1]
        request_creator = "traveleraccepted" + "_" + tripid + "_" + username
        delete_record(receiver_id, request_creator)

        try:
            token = get_device_token(receiver_id)
            trip  = get_trip_info(username,tripid)
            title = "The traveler removed the shared contacts"
            body  = "Traveler is not interested in the trip from {} to {}, and the travel date {}".format(trip['fromcity'],trip['tocity'],trip['trdate'])
            send_push_notification(token,title,body)
            return jsonify("Deleted: {}".format(contact)),200
        except:
            return jsonify("Deleted: {}".format(contact)),200

    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/requester/accepted/<contact>', methods=['DELETE'])
def requester_delete_traveleraccepted(contact):

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record(username, contact)
        if response['Items'] == []:
            return jsonify('Not Found'),404

        delete_record(username, contact)

        # Delete the sharing between requester and traveler
        receiver_id = contact.split('_')[-1]
        tripid = contact.split('_')[1]
        request_creator = "accepted" + "_" + tripid + "_" + username
        delete_record(receiver_id, request_creator)

        try:
            token = get_device_token(receiver_id)
            trip  = get_trip_info(receiver_id,tripid)
            title = "The requester removed the shared contacts"
            body  = "Requester is not interested in the trip from {} to {}, and the travel date {}".format(trip['fromcity'],trip['tocity'],trip['trdate'])
            send_push_notification(token,title,body)
            return jsonify("Deleted: {}".format(contact)),200
        except:
            return jsonify("Deleted: {}".format(contact)),200


    except:
        return jsonify('Misunderstood Request'),400


@app.route('/share-request/requester/request/<request_id>', methods=['DELETE'])
def delete_requester(request_id):

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record(username, request_id)
        if response['Items'] == []:
            return jsonify('Not Found'),404

        #Delete request from requester
        delete_record(username, request_id)

        #Delete pending from receiver
        traveler_user = request_id.split('_')[-1]
        tripid = request_id.split('_')[1]
        traveler_pending = 'pending' + "_" + tripid + "_" + username
        delete_record(traveler_user, traveler_pending)

        try:
            token = get_device_token(traveler_user)
            trip  = get_trip_info(traveler_user,tripid)
            title = "The requester is not sending the package"
            body  = "Requester is not interested in the trip from {} to {}, and the travel date {}".format(trip['fromcity'],trip['tocity'],trip['trdate'])
            send_push_notification(token,title,body)
            return jsonify("Deleted: {}".format(request_id)),200
        except:
            return jsonify("Deleted: {}".format(request_id)),200

    except:
        return jsonify('Misunderstood Request'),400


@app.route('/share-request/traveler/pending', methods=['GET'])
def pending_traveler():

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record_begins_with(username,'pending')
        if response['Items'] ==[]:
            return jsonify('Not Found'),404

        return jsonify(response),200

    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/traveler/accepted', methods=['GET'])
def accepted_traveler():

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record_begins_with(username,'accepted')
        if response['Items'] ==[]:
            return jsonify('Not Found'),404

        return jsonify(response),200

    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/traveler/declined', methods=['GET'])
def declined_traveler():

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record_begins_with(username,'declined')
        if response['Items'] ==[]:
            return jsonify('Not Found'),404

        return jsonify(response),200

    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/requester/<requester_id>', methods=['GET'])
def get_requester_request(requester_id):

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record(username,requester_id)
        if response['Items'] ==[]:
            return jsonify('no records found'),404

        return jsonify(response),200
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/requester/accepted/<requester_id>', methods=['GET'])
def get_requester_accept(requester_id):

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record(username,requester_id)
        if response['Items'] ==[]:
            return jsonify('no records found'),404

        return jsonify(response),200
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/requester/declined/<requester_id>', methods=['GET'])
def get_requester_decalined(requester_id):

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record(username,requester_id)
        if response['Items'] ==[]:
            return jsonify('no records found'),404

        return jsonify(response),200
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/requester/accepted', methods=['GET'])
def accepted_requester():

    user = token_username()
    username = user['cognito:username']

    try:

        response = get_record_begins_with(username,'traveleraccepted')
        if response['Items'] ==[]:
            return jsonify('Not Found'),404

        return jsonify(response),200

    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/requester/pending', methods=['GET'])
def pending_requester():

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record_begins_with(username,'request')
        if response['Items'] ==[]:
            return jsonify('Not Found'),404

        return jsonify(response),200
    except:
        return jsonify('Misunderstood Request'),400


@app.route('/share-request/requester/declined', methods=['GET'])
def declined_requester():

    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record_begins_with(username,'travelerdeclined')
        if response['Items'] ==[]:
            return jsonify('Not Found'),404

        return jsonify(response),200

    except:
        return jsonify('Misunderstood Request'),400



@app.route('/contacts/requester/<contact>', methods=['GET'])
def get_requester(contact):

    user = token_username()
    username = user['cognito:username']

    try:

        tripid = contact.split('_')[0]
        requester_username = contact.split('_')[-1]
        contact_id_traveleraccepted = 'traveleraccepted' + "_" + tripid + "_" + username

        record_traveleraccepted = get_record(requester_username, contact_id_traveleraccepted)

        if len(record_traveleraccepted['Items']) >= 1:
            traveleraccepted = record_traveleraccepted['Items'][0]['created'].split('_')[-1]
        else:
            traveleraccepted = None

        contact_id_request = 'request' + "_" + tripid + "_" + username
        record_request = get_record(requester_username, contact_id_request)

        if len(record_request['Items']) >= 1:
            requester = record_request['Items'][0]['created'].split('_')[-1]
        else:
            requester = None


        if username in [ traveleraccepted, requester ]:
           return get_record(requester_username, 'contacts')

        return jsonify('You are not allowed to see user contacts'),403
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/contacts/traveler/<contact>', methods=['GET'])
def get_traveler(contact):

    user = token_username()
    username = user['cognito:username']

    try:
        tripid = contact.split('_')[0]
        traveler_username = contact.split('_')[-1]
        contact_id = 'accepted' + "_" + tripid + "_" + username
        record = get_record(traveler_username, contact_id)


        if username in record['Items'][0]['created'].split('_')[-1]:

           return get_record(traveler_username, 'contacts')

        return jsonify('You are not allowed to see user contacts'),403
    except:
        return jsonify('Misunderstood Request'),400


@app.route('/fromcity/<city>', methods=['GET'])
def get_fromcity(city):

        limit = request.args.get('limit', default = 10, type = int)
        lastkey = request.args.get('lastkey', default = None, type = str)

        return get_global_index('fromcity-trdate-index','fromcity',city,limit,today_date(),lastkey)

@app.route('/tocity/<city>', methods=['GET'])
def get_tocity(city):

    try:
        limit = request.args.get('limit', default = 10, type = int)
        lastkey = request.args.get('lastkey', default = None, type = str)

        return get_global_index('tocity-trdate-index','tocity',city,limit,today_date(),lastkey)
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/fromto/<city>', methods=['GET'])
def fromto(city):

    try:
        limit = request.args.get('limit', default = 10, type = int)
        lastkey = request.args.get('lastkey', default = None, type = str)

        return get_global_index('fromto-trdate-index','fromto',city,limit,today_date(),lastkey)
    except:
        return jsonify('Misunderstood Request'),400


##@app.route('/test_notify', methods=['GET'])
#def test_notify():
#    try:
        #trip=get_trip_info('b5cd3208-a01f-439b-af9b-a35728cfab75','2024-05-06-00-05-09-663545')
#        token = get_device_token('6391159b-dc53-40c3-bd64-35516236f933')
#        print (token)
        #title = "Package Accepted From {} To {}".format(trip['fromcity'],trip['tocity'])
        #body = "Traveler Accepted Your Package For The Trip From {} To {}, and The Travel date {}".format(trip['acceptfrom'],trip['acceptto'],trip['trdate'])
#        send_push_notification(token,title,body)
#        return jsonify(token),200
#    except:
#        return True

@app.route('/account', methods=['GET'])
def user_account():
      try:
          user = token_username()
          username = user['cognito:username']

          data = get_record(username,item='account')

          # Add account to the user
          if data['Items'] == []:
              user = {'username': username, 'created': 'account'}
              add_record(user)
              data['Items'] = [user]
              return jsonify(data['Items'])

          return jsonify(data['Items']),200
      except:
          return jsonify('Misunderstood Request'),400

@app.route('/account', methods=['DELETE'])
def delete_account():
    user = token_username()
    username = user['cognito:username']
    email = user['email']
    name = user['name']

    try:
        cognito = boto3.client('cognito-idp',region_name = region_name, verify=True)
        cognito.admin_delete_user(UserPoolId= userpoolid, Username= username)

        delete_records(username)

        msg = message_body_deleted_account(name)
        notification(email, msg, subj_remove_account)

        return jsonify('Removing account has been requested'),200
    except:
        return jsonify('Misunderstood Request'),400

    
def user_limit_subscription():
    """
    User Limit Subscription
    """
    list_subscription()
    if subscription_limit > list_subscription.item_limit:
        return False
    return True    

    
@app.route('/subscription', methods=['POST'])
def create_subscription():
    
    user = token_username()
    username = user['cognito:username']
    
    if (user_limit_subscription()):
        return jsonify('{} Records Limit Reached'.format(list_subscription.item_limit)),426

    try:
        data = request.json

        if  data['fromcity'] and data['tocity'] and len(data) == 2:
            data['username'] = username
            data['created'] = gen_time()
            data['fromto'] =  data['fromcity'] + '_' + data['tocity']
            
            #Today Date
            data['tstamp'] = tstamp(datetime.now().strftime("%Y-%m-%d"),30)
            
            add_subscription(data)
            return jsonify(data),201

        return jsonify('You must fill in all of the required fields *'),400
    except:
        return jsonify('Misunderstood Request'),400


@app.route('/subscription', methods=['GET'])
def list_subscription():

      user = token_username()
      username = user['cognito:username']

      try:
          response = get_subscriptions(username)

          list_subscription.item_limit =len(response['Items'])


          if response['Items'] ==[]:
                return jsonify('no records found'),404

          return jsonify(response),200
      except:
          return jsonify('Misunderstood Request'),400


@app.route('/subscription/<created>', methods=['DELETE'])
def remove_subscription(created):
    
  user = token_username()
  username = user['cognito:username']
  try:
      delete_subscription(username, created)
      return jsonify("Deleted: {}".format(created)),200
  except:
      return jsonify('Misunderstood Request'),400
  
  