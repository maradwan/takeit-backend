from os import environ as env
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging

#server_key  = env.get("SERVER_KEY")
server_key= {
  "type": "service_account",
  "project_id": "takeit-cddd2",
  "private_key_id": "d1e50c9c286d2b32bd0e64b8b02ee5863ea55dd4",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDS6pHO2u01Ej0O\nKcKcch92MyQEIT3h/0A+tmWPYcEZ7thdYyoAFZSU9aDb+gZJNrf79VsxhQ1eBo8L\nbH4nqzudkmEm29yOkfp/76j/qjKH3nw6/5Ej7sSZvoq2UuJgmBmL5Qzkd25zNbN3\nTbBruEiYKtTE4NTEgZMZhteB7VTejMjtbb1sSF/LsjJ3Mp5zsi9laqWYDIDmLy6K\nBuHGWwJnbGPskpzo2O7mt6irsjLZTF+Dn5tihUomVNhAGXO18UuH1SHLijY4+C7p\nKFrHuFgqzq3p50UA08b0o/F63d9XcS1X6d5fgLm3KkLRb2uq3KLlc3jdJjA+wTl0\nB5A+YvebAgMBAAECggEAEkaJA9IsePYaRuk6F7GRJajLbMrZ6y823eLoF0MdJvtv\nJrMPp0TiGat+7hCoDXKpq9ytXjPCiMHWEI4CEGXh8Iayga94rlHafCNuvVh+BbqI\nK9nhNaqGwTD6y/mP7AFslUFE8Lb4jGW8JeZGwc63W5gP1PoLoEtUolhGFtf9tprM\nAP0xuKj7/hX6hrKVKy8LBUiwVDvvNw5fVEnwXGxrz6kSuLSOxBb7+IPDxAH5FHVC\n7v4IR1lt5ooCIiI75Tf4k8vY12ijiZlgsPmOTbcNByOgHX298immKpUC2bpwhF0w\nbxzDolHokcBTG5CoDebf1durAMA1yEfaJrpdYJXpAQKBgQD0qNxsTh2SqZ5fi5Me\nkzP+Tua4uoU6EQRNHRhtE1hsJGloMeCBkA2dKW0ntqwdcHlcBKO96H3l9GqnpG38\nZFIvyg1zI5WqYQCUOfoi1FItJWxjh7ZxKbxUiZTXUzqoWMFP3XANNGuDQcI8/xgt\n2xZZZfzFfFLeN/dsPxHreOiDoQKBgQDcsU8iz6oUpLk2q1FOFoU+xyAxhvYFPYDo\nZfY9mAvko5C7F9XlGal5yz99yBrU+/u79MCC5EhumFfL67eTmCJdB3QLE1yUo4MC\n/GDNSrwt3hqdhc+ogbJFNODvS2ddwiQywhIRKhyYkfo6D3s0BNaO478IK/dFYbfX\nAiUfzLkxuwKBgQDCbww12mKwMrKVNgQmUVAJs8SyXDESs4Fak1vdG3my/8DxOGo2\nLThUhR6laAwinUclNN64RvL+9B5qukdaRJP4PLgxn78Kl2pxYh4C3f+st0gLVUhN\naKCuAmTSNuev8FE42j95jwY+Wt01wnkBwFJjm6SlgacNySaN1RW1r/IA4QKBgQC8\nD+BW0s2lr8UhABZVy70aBQe7DL4DMyjxYUnXrQSdfoCr3iDojNitr/RX1DiBPIWE\n4olWQQA0Nl/CpwiVnnPSALLzaTlgdIIE/lnjNwdqsrTNfSS6/GKUtP3lDMV10SWV\nl2lb9R3PKb4o0d50Mpc/xnWYmhapqh7F+s717Tf3VwKBgEy0kKtQgS3WFLs8s0jJ\nCfN6VuFclNILOVWX8Gh2MW9NtFz34fqYEnrJPb4pwoK3dF0L/dmcyEeaG5o3L+D/\nmfQEHQKr3aREB1weQEWwZEECO6j8iw8iM31n8TOG0YYjH3h1SmakIy0iKLH3oEj9\n7XuLAvehl37IS7T7yjAOLKrE\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-vkqbo@takeit-cddd2.iam.gserviceaccount.com",
  "client_id": "104780221517820360406",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-vkqbo%40takeit-cddd2.iam.gserviceaccount.com",
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