from flask import request, jsonify
import boto3
from os import environ as env
from api.auth import gen_time, token_username, today_date
from api.models import get_record, add_record, get_records, delete_record, delete_records, update_weight_record, get_global_index, get_record_begins_with
from api import app
from time import time

#weight_limit = env.get("WEIGHT_LIMIT")
#region_name  = env.get("REGION_NAME")
userpoolid = env.get("USERPOOLID")


region_name = "eu-west-1"
weight_limit = 100
userpoolid = "eu-west-1_02tYu4pUt"


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
            data['tstamp'] = int(time())

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
            data['tstamp'] = int(time())

            update_weight_record(username, created, data)
            return jsonify(data),201
            
        return jsonify('You must fill in all of the required fields *'),400
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
        if 'e-mail' in data:
            contact['e-mail'] = (data['e-mail'])             
        
        if len(data) <= 7:
                        
            contact['username'] = username
            contact['created'] = "contacts"
            contact['name'] = user['name']
            
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
        if data['requestuser'] and len(data) == 1:
            
            request_user = data['requestuser']
            
            #Check the request_user exsit
            if not check_username(request_user):
                return jsonify('requestuser is not registered'),400
 
            
            #Check only one request has been sent
            sender_accepted = "accepted" + "_" + request_user
            check_record = get_record(username, sender_accepted)

            if len(check_record['Items']) >= 1:

                if sender_accepted in check_record['Items'][0]['created']:
                    return jsonify('already requestuser has your request'),200
            
            del data['requestuser']
            data['username'] = username
            data['created'] = "request" + "_" + request_user
            data['dtime'] = gen_time()
            add_record(data)         
            
        # Share the contacts of sender with the receiver
            data['created'] = "accepted" + "_" + request_user
            add_record(data) 
            
        # Adding pending to the receiver
            data['fromuser'] = username
            data['created'] = "pending" + "_" + username

            data['username'] = request_user
            add_record(data)   
  
            return jsonify('request has been sent'),201
       
            
        return jsonify('You must fill in all of the required fields *'),400
    except:
        return jsonify('Misunderstood Request'),400
    
    
    
@app.route('/share-request/accept/<created>', methods=['POST'])
def accept_request(created):
    
    user = token_username()
    username = user['cognito:username']

    try:
        data = {}

        data['username'] = username
        data['dtime'] = gen_time()
        
        request_creator = created.split('pending_')[1]
        acceptor = 'accepted' + '_' + request_creator
        data['created'] = acceptor

        add_record(data)
        delete_record(username, created)
        
        # Delete the request from the sender
        receiver_id = 'request' + '_' + username
     
        delete_record(request_creator, receiver_id)
            
        return jsonify('request has been accepted'),201
    except:
        return jsonify('Misunderstood Request'),400
    
@app.route('/share-request/accept', methods=['GET'])
def get_accept():
    
    user = token_username()
    username = user['cognito:username']

    try:
        
        response = get_record_begins_with(username,'accepted')
        if response['Items'] ==[]:
            return jsonify('Not Found'),404
        
        return jsonify(response),200
                      
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/accept/<contact>', methods=['DELETE'])
def delete_accept(contact):
    
    user = token_username()
    username = user['cognito:username']

    try:
        delete_record(username, contact)
        
        # Delete the sharing between requester and receiver
        receiver_id = contact.split('accepted_')[1]
        request_creator = "accepted_" + username 
        delete_record(receiver_id, request_creator)
           
        return jsonify("Deleted: {}".format(contact)),200
             
    except:
        return jsonify('Misunderstood Request'),400

@app.route('/share-request/pending', methods=['GET'])
def pending_request():
    
    user = token_username()
    username = user['cognito:username']

    try:
        response = get_record_begins_with(username,'pending')
        if response['Items'] ==[]:
            return jsonify('Not Found'),404
        
        return jsonify(response),200             
    except:
        return jsonify('Misunderstood Request'),400        
    
@app.route('/share-request/request', methods=['GET'])
def get_request():
    
    user = token_username()
    username = user['cognito:username']
    
    try:
        response = get_record_begins_with(username,'request')
        if response['Items'] ==[]:
            return jsonify('Not Found'),404
        
        return jsonify(response),200
             
    except:
        return jsonify('Misunderstood Request'),400        
            
@app.route('/share-request/request/<contact>', methods=['DELETE'])
def delete_request(contact):
    
    user = token_username()
    username = user['cognito:username']

    try:
        #Delete request from sender
        delete_record(username, contact)
        
        #Delete pending from receiver
        receiver_user = contact.split('pending_')[1]
        receiver_pending = 'pending' + '_' + username
        delete_record(receiver_user, receiver_pending)
        
        #Delete the sharing between sender and receiver
        receiver_accepted = 'accepted' + '_' + receiver_user
        delete_record(username, receiver_accepted)
               
        return jsonify("Deleted: {}".format(contact)),200
             
    except:
        return jsonify('Misunderstood Request'),400               
    
@app.route('/share-request/<created>', methods=['DELETE'])
def reject_request(created):
    
    user = token_username()
    username = user['cognito:username']

    try:
       data = {}

       data['username'] = username
       data['created'] = created 
       
       delete_record(username, created)
       
       # Delete the request from the sender
       request_creator = created.split('pending_')[1]
       receiver_id = 'request' + '_' + username
      
       delete_record(request_creator, receiver_id)
       
       #Delete the sharing between sender and receiver
       receiver_accepted = 'accepted' + '_' + username
       delete_record(request_creator, receiver_accepted)
        
        
       return jsonify("Deleted: {}".format(created)),200
             
    except:
        return jsonify('Misunderstood Request'),400
    

@app.route('/contacts/<contact>', methods=['GET'])
def get_contact(contact):
    
    user = token_username()
    username = user['cognito:username']

    try:
        contact_id = 'accepted' + '_' + username
        record = get_record(contact, contact_id)

        
        if username in record['Items'][0]['created'].split('accepted_')[-1]:
           return get_record(contact, 'contacts')
        
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
        delete_records(username)       
        
        #msg = message_body_deleted_account(username)
        #notification(username, msg, subj_remove_account)
        
        return jsonify('Removing account has been requested'),200
    except:
        return jsonify('Misunderstood Request'),400