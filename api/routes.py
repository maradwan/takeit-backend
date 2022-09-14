from flask import request, jsonify
import boto3
from os import environ as env
from api.auth import gen_time, token_username, today_date
from api.models import get_record, add_record, get_records, delete_record, delete_records, update_weight_record, get_global_index, get_record_begins_with
from api import app
from time import mktime, time
from datetime import datetime, timedelta

#weight_limit = env.get("WEIGHT_LIMIT")
#region_name  = env.get("REGION_NAME")
userpoolid = env.get("USERPOOLID")


region_name = "eu-west-1"
weight_limit = 100
userpoolid = "eu-west-1_1vDh1VG69"


def user_limit_weight():
    """
    Get User Limit from DB, if not use global limit
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

            update_weight_record(username, created, data)
            return jsonify(data),201
            
        return jsonify('You must fill in all of the required fields *'),400
    except:
        return jsonify('Misunderstood Request'),400


@app.route('/contacts', methods=['POST'])
def add_contacts():
    
    user = token_username()
    username = user['cognito:username']
    name     = user['name']

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
        if 'e-mail' in data:
            contact['e-mail'] = (data['e-mail'])             
        
        if len(data) <= 7:
                        
            contact['username'] = username
            contact['created'] = "contacts"
            contact['name'] = name
            
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
            #del data['tripid']
            
            data['username'] = username
            data['created'] = "request" + "_" + tripid + "_" + request_user
            data['dtime'] = gen_time()
            
            add_record(data)         
  
            
        # Adding pending to the traveler
            data['fromuser'] = username
            data['created'] = "pending" + "_" + tripid + "_" + username 
            data['tripid'] = tripid

            data['username'] = request_user
            add_record(data)   
  
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
           
        return jsonify("Deleted: {}".format(contact)),200
             
    except:
        return jsonify('Misunderstood Request'),400
    
            
@app.route('/share-request/requester/request/<contact>', methods=['DELETE'])
def delete_requester(contact):
    
    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record(username, contact)        
        if response['Items'] == []:
            return jsonify('Not Found'),404
        
        #Delete request from requester
        delete_record(username, contact)
        
        #Delete pending from receiver
        traveler_user = contact.split('_')[-1]
        tripid = contact.split('_')[1]
        traveler_pending = 'pending' + "_" + tripid + "_" + username
        delete_record(traveler_user, traveler_pending)
               
        return jsonify("Deleted: {}".format(contact)),200
             
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
    
    try:
        cognito = boto3.client('cognito-idp',region_name = region_name, verify=True)
        cognito.admin_delete_user(
            UserPoolId= userpoolid,
            Username= username
            )
        
        # delete all requests from other users
        pending = 'pending' + '_' + username
        request = 'request' + '_' + username
        accept = 'accepted' + '_' + username
        declined = 'declined' + '_' + username
        travelerdeclined = 'travelerdeclined' + '_' + username
        traveleraccepted = 'traveleraccepted' + '_' + username
                        
        
        delete_request = get_record_begins_with(username,'request_')
        if len(delete_request['Items']) >= 1:
            for i in range(len(delete_request['Items'])):
                delete_record(delete_request['Items'][i]['created'].split('_')[-1], pending)
        
        delete_pending = get_record_begins_with(username,'pending_')
        if len(delete_pending['Items']) >= 1:
            for i in range(len(delete_pending['Items'])):
                delete_record(delete_pending['Items'][i]['created'].split('_')[-1], request)
        
        
        response_accepted = get_record_begins_with(username,'accepted_')
        if len(response_accepted['Items']) >= 1:
            for i in range(len(response_accepted['Items'])):
                delete_record(response_accepted['Items'][i]['created'].split('_')[-1], traveleraccepted)
          
        response_traveleraccepted = get_record_begins_with(username,'traveleraccepted')
        if len(response_traveleraccepted['Items']) >= 1:
            for i in range(len(response_traveleraccepted['Items'])):
                delete_record(response_traveleraccepted['Items'][i]['created'].split('_')[-1], accept)        
        
        response_declined = get_record_begins_with(username,'travelerdeclined')
        if len(response_declined['Items']) >= 1:
            for i in range(len(response_declined['Items'])):
                delete_record(response_declined['Items'][i]['created'].split('_')[-1], declined)
     
        declined_request = get_record_begins_with(username,'declined_')
        if len(declined_request['Items']) >= 1:
            for i in range(len(declined_request['Items'])):
                delete_record(declined_request['Items'][i]['created'].split('_')[-1], travelerdeclined)               
        
        delete_records(username)       
        
        #msg = message_body_deleted_account(username)
        #notification(username, msg, subj_remove_account)
        
        return jsonify('Removing account has been requested'),200
    except:
        return jsonify('Misunderstood Request'),400