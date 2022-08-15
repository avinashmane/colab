from socialmediasite import SocialMediaSite
import yaml
import re
import os

class WhatsApp(SocialMediaSite):
    authType='strava'
    def __init__(self,b=None,cookieFile=None,
                 authFile=f'{os.environ["AUTH"]}/auth.yaml',
                 cfgFile =f'{os.environ["LIB"]}/cfg_whatsapp.yaml'):
      
        super().__init__(b,authFile=authFile)
        self.siteType='strava'
        
        with open(cfgFile) as file:
            cfg = yaml.safe_load(file)
            self.cfg.update(cfg['whatsapp'])