from os import environ as env
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging

#server_key  = env.get("SERVER_KEY")
server_key= {
  "type": "service_account",
  "project_id": "XXX",
  "private_key_id": "XXXX",
  "private_key": "XXX",
  "client_email": "XXX",
  "client_id": "XXX",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "XXX",
  "universe_domain": "googleapis.com"
}

cred = credentials.Certificate(server_key)
default_app = firebase_admin.initialize_app(cred)

def send_push_notification(token, title, body, data=None):
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data,
            token=token
        )
        response = messaging.send(message)
        return(response)
