import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

class Firebase:
    def __init__(self,databaseName,configFile):
        # Fetch the service account key JSON file contents
        self.cred = credentials.Certificate(configFile)

        # Initialize the app with a service account, granting admin privileges
        self.app=firebase_admin.initialize_app(self.cred,{
             'databaseURL': f'https://{databaseName}.firebaseio.com'
         })
        self.db = db
    def get(self,path):
        # As an admin, the app has access to read and write all data, regradless of Security Rules
        ref = db.reference(path)
        return(ref.get())

    

