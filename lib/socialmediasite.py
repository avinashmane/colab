###
# Module of all web elements
#
#
# structure:  page->feed->post->post components
#

import yaml
import nerodia
from nerodia.browser import Browser
from nerodia.wait.wait import TimeoutError, Wait
from nerodia.exception import Error, NoMatchingWindowFoundException, ObjectDisabledException, \
    ObjectReadOnlyException, UnknownFrameException, UnknownObjectException
# import KEYS
from selenium.webdriver.common.keys import Keys
import re
import os
import time
import utils
import pandas as pd
import logging
import sys
sys.tracebacklimit = 3

# import KEYS
from selenium.webdriver.common.keys import Keys

ifExists=lambda x:x.exists

class SocialMediaSite:
    """Generic website 
    test page link: https://testpages.herokuapp.com/styled/index.html
    
    >>> x=SocialMediaSite(b=None,browser='chrome')
    
    >>> x.browser.goto("https://testpages.herokuapp.com/styled/index.html")

    >>> x.browser.title
    Selenium Test Pages    
    """
    authType=None
    delay=0.25
    cfg={}

    def __init__(self,b=None,browser='firefox',authFile=None,delay=None):# 29aug f'{os.environ["AUTH"]}/auth.yaml'
        # create brwoser unless provided
        """ create instance

        """
        self.browser=Browser(browser) if b==None else b
        nerodia.default_timeout=10
        
        if delay: self.delay=delay
                
        if authFile:
          with open(authFile) as file:
              # The FullLoader parameter handles the conversion from YAML
              # scalar values to Python the dictionary format
              auth = yaml.safe_load(file)
              self.auth={x:auth[x] for x in auth if x in ['strava','facebook','linkedin']}
        
    def login():
      raise NotImplemented
      
    def loadCookie(self,cookieFile):
        if cookieFile and os.path.exists(cookieFile):
          self.browser.cookies.load(file=cookieFile)
          
    def saveCookie(self,cookieFile):
        return self.browser.cookies.save(file=cookieFile)
    def clearCookie(self,cookieFile):
        return self.browser.cookies.clear()
    def close(self):
        return self.browser.close()
    @staticmethod
    def getParent(el,tag,patClass):
      """
      Get parents with tag and patterm of class matching
      Parameters
      ----------
      - el : reference node
      - tag : tag_type (e.g. div)
      - patClass : class of patterns (re.compile)
      Returns
      -------
      - Single element than meets the requirements
      """
      return el._xpath_adjacent( tag_name='div',class_name=re.compile(patClass), adjacent='ancestor', plural=False)

    def goto(self,url):
      return self.browser.goto(url)
    
    @staticmethod
    def getLinkByClassPatt(tag,classPattern): 
        x= tag.link(class_name=re.compile(classPattern))
        return x.href,x.text
    
    @staticmethod
    def _dumptag(el,tags=None,level=0):
      for c in (el.children(tag_name=tags) if tags else el.children()):
          print(' '*level,c.tag_name,c.id,c.text.split("\n")[0][:50])
          try:SocialMediaSite._dumptag(c,level+1)
          except: pass

    def scrolldown(self,pages):
      for i in range(pages):
        self.browser.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        # b.send_keys(Keys.CONTROL  + Keys.END )     
        # b.driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(1)
    
Web=SocialMediaSite

class Strava(SocialMediaSite):
    authType='strava'
    giveKudosPattern=re.compile(r'.*ive kudos')    

    logGSheet=None
    def __init__(self,b=None,cookieFile=None,authFile=f"{os.environ['AUTH']}/auth.yaml",
                                             cfgFile=f'{os.environ["LIB"]}/cfg_strava.yaml',
                delay=None):

        super().__init__(b,authFile=authFile,delay=delay)
        self.siteType='strava'
        
        with open(cfgFile) as file:
            cfg = yaml.safe_load(file)
            self.cfg.update(cfg['strava'])

    def login(self,login):
        auth=self.auth[self.authType][login]
        self.browser.goto('https://www.strava.com/login')

        try: # reject cookies
          rejButton=self.browser.button(value="Reject")
          if rejButton.exists:
            rejButton.click()
        except Exception as e:
            logging.warning( f"Error login1 {e!r}") #logging.warning 
      
        try:
          self.browser.text_field(id='email').value=auth['username']  #timeout did not work
          self.browser.text_field(id='password').value=auth['password']
          self.browser.button(id='login-button').click()
        except Exception as e:
          if 'dashboard' in self.browser.url:
            logging.info( f"Logged in with {auth['username']}") #logging.warning 
          else:
            logging.warning( f"Error Login2 {e!r}") #logging.warning 
    
    def logout(self):
      menu=self.browser.li(class_name="user-menu") #drop-down-menu
      self.browser.execute_script("arguments[0].click();", menu)
      if 'active' in menu.class_name:
          menu.link(text="Log Out").click()
          logging.info( f"Logged out")
        
    def getClubs(self):
        self.browser.goto('https://www.strava.com/clubs/search')
        grps=[]

        for f in self.browser.ul(class_name="clubs").lis():
          # print(f.div().attribute_value("original-title"))
          for c in f.div().links():
            grps.append({"name":f.div().attribute_value("original-title"),
                         "link":c.attributes['href']})
        return (grps)
      
    def postInClub(self,club,title,text,imagePath):
        self.browser.goto(f'{club}/discussion')
        self.browser.link(id='new-post').click()
        self.browser.textarea(name='title').value=title
        self.browser.textarea(name='text').value=text
        self.browser.file_field(type='file',index=0).value=imagePath #working
        self.browser.div(class_name="dropzone-previews").img().wait_until(method=lambda e: e.complete)
        time.sleep(3)
        self.browser.button(text='Publish').click()
        
    def getPostIds(self,club):
        self.browser.goto(f'{club}/discussion')
        return [{'id':x.parent().id,
          'title':   x.div(class_name='post-body').link().text,
          'link':    x.link(class_name='str-click-self-js').href,
          'userlink':x.link(class_name='str-click-name-js').href,
          'username':x.link(class_name='str-click-name-js').text,
          'time':    x.time().text,
          'kudos':   x.span(class_name="count-kudos").text,
          'comments':x.span(class_name="count-comments").text,
          } for x in self.browser.divs(class_name='topic')]
      
    def deletePost(self,id):
        "@id like post-19361836"
        self.browser.li(id=id).div(class_name='drop-down-menu').click()
        self.browser.li(id=id).button(text='Delete').click()
        self.browser.alert.ok()

    def deleteCurrentPost(self):
        "delete current post"
        self.browser.div(id="options-menu").click()
        self.browser.div(id="options-menu").link(text="Edit").click()

        self.browser.button(text='Delete').click()
        self.browser.alert.ok()
        
    def getPostData(self,actEl):
        ath,athUrl=utils.getAttrsIfExists( actEl.link(data_testid="owners-name"),
                               ['text','href'])#,)
        loc=utils.getAttrsIfExists( actEl.div(data_testid="location"))
        act,actUrl=utils.getAttrsIfExists( actEl.link(data_testid="activity_name"),
                               ['text','href'])#,)
        kudoCount=utils.getAttrsIfExists( actEl.button(data_testid="kudos_count"))
        return ath,athUrl,loc,act,actUrl,kudoCount

    def giveKudo(self,kudoTag,i=''):
        try:
            self.browser.execute_script("arguments[0].click();", kudoTag)
            kudoTag.svg(data_testid="filled_kudos").wait_until(method=lambda x: x.exists)
            
            actEl=kudoTag.parent(class_name=re.compile('^EntryFooter')
                               ).parent()
            try:
                ath,athUrl,loc,act,actUrl,kudoCount=self.getPostData(actEl)
                # print(ath,athUrl,act,actUrl,kudoCount,loc)
                try:
                  athId = int(re.findall(".*\/([0-9]*)",athUrl)[0])
                  if athId not in self.StravaMembers:
                    athId='nonMember'
                except Exception as e:
                  athId=f'not valid {e}'
            except Exception as e:
                logging.warning(f"giveKudos(): Data Error {e!r}")
        except TimeoutError as e:
          logging.warning(f"giveKudos: {i} error clicking {e!r}")
          raise TimeoutError('Error 423?:',e)
        except Exception as e: 
          logging.warning(f"giveKudos: {i} error clicking {e!r}")
        else:
            if not self.logGSheet is None:
              self.logGSheet.append_table([[pd.Timestamp.now().isoformat(),"INFO","giveKudos",athId,athUrl,ath,actUrl,loc,]]) 
            logging.info(f"giveKudos: {i},{athId},{athUrl} {ath},{actUrl} {act}")

    def giveKudos(self):
      "Give Kudos in current screen new"
      _=self.browser.buttons(title=self.giveKudosPattern)
      count=len(_)
      for i,x in enumerate(_):
        self.giveKudo(x,i)
        time.sleep(self.delay)
      return {'count':count}
    
    def postComment(self,commentButtonEl,text):
      commentButtonEl.execute_script("arguments[0].click();", commentButtonEl)
      try:
          footer=commentButtonEl.parent(class_name='EntryFooter--entry-footer--Gy+uP'
                                       ).wait_until(timeout=1,method=lambda x:x.exists)
          ta=footer.textarea().wait_until(timeout=1,method=lambda x:x.exists)
          ta.value=text
          postButton=footer.button(data_testid='post-comment-btn').wait_until(timeout=1,method=lambda x:x.exists)
          postButton.execute_script("arguments[0].click();", postButton)
      except: 
          raise Exception("Something went wrong while posting comment")

    def image(self):
      self.browser=self.browser
      self.browser.execute_script("window.scrollTo(0,0)")
      return Image(self.browser.screenshot.png())
    
    def getReactProps(self,reactTags):
      "Parses react-feed-component "
      from pprint import pprint as pp
      import json
      _cfg_map=yaml.safe_load("""
      Skip:
      - mapAndPhotos
      - twitterUrl
      - achievements
      - segAndBestEffortAchievements
      - highlighted_kudosers
      athlete:
      - All
      kudosAndComments: 
      - kudosCount
      #- comments
      timeAndLocation:
      - All
      test:
          All:
          - +All
          - -FewRemoves
          -something:


      """)
      # display(cfg)
      def actFlatten(act):
          for _cfg in _cfg_map:
              if _cfg=='Skip':
                  for key in _cfg_map[_cfg]:
                      if key in act:
                          del act[key]
              if _cfg in act:
                  for fld in _cfg_map[_cfg]:
                      if fld=='All':
                          act.update(act[_cfg])
                          break
                      act.update({fld:act[_cfg][fld]})
                  del act[_cfg]
          return act
        
      if isinstance(reactTags,nerodia.elements.html_elements.HTMLElement):
        reactTags=[reactTags]
        
      for _al in reactTags:
          _data=json.loads(_al.data_react_props)['preFetchedEntries']
          # print(len(_data))
          acts=[]
          # pp(_data,depth=3)
          for x in _data:
              if x['entity']== 'Activity':
                  acts.append(actFlatten(x['activity']))
              if x['entity']== 'GroupActivity':
                  acts = acts + [actFlatten(act) 
                                 for act in x['rowData']['activities']]

      # for x in acts:
      #     pp(x,depth=3,indent=2)
      #     pass
      return acts


class Linkedin(SocialMediaSite):
    "Linked in website"
    
    authType='linkedin'
    logGSheet=None
    def __init__(self,b=None,cookieFile=None,authFile=f"{os.environ['AUTH']}/auth.yaml",cfgFile=None, delay=None):
        super().__init__(b,authFile=authFile,delay=delay)
        self.siteType='linkedin'
        
        if  cfgFile is not None: #=f'{os.environ["LIB"]}/cfg_strava.yaml'
          with open(cfgFile) as file:
            cfg = yaml.safe_load(file)
            self.cfg.update(cfg['linkedin'])

    def login(self,login):
        if 'username' in login:
          auth=login
        else:
          auth=self.auth[self.authType][login]
          
        self.browser.goto('https://www.linkedin.com/login')

        # try: # reject cookies ! copy from Strava       
      
        try:
          try:self.browser.text_field(name='session_key').value=auth['username']  #timeout did not work
          except:pass
          _pwd=self.browser.text_field(name='session_password')
          _pwd.value=auth['password']
          _pwd.send_keys(Keys.ENTER)
        except Exception as e:
          if 'dashboard' in self.browser.url:
            logging.info( f"Logged in with {auth['username']}") #logging.warning 
          else:
            logging.warning( f"Error Login2 {e!r}") #logging.warning 
    
    def logout(self):
      try:
        self.browser.goto('https://www.linkedin.com/feed')
        menu=self.browser.element(class_name='global-nav__me'
                                 ).wait_until(timeout=2,method=ifExists)
        menu.click()
        self.browser.execute_script("arguments[0].click();", menu)
        if 'artdeco-dropdown--is-open' in menu.class_name:
            self.browser.element(text='Sign Out').click()
            # self.browser.element(text='Sign Out').click()
            logging.info( f"Logged out")
        else:
            logging.info( f"Error: Log out menu did not open")
      except TimeoutError:
            logging.info( f"Error: Perhap not signed in")

    def getPostData(self,postTag):
      "Return data regarding one post in linkedin feed"
      post={}
      if not postTag.exists:
        return
      _map={
          'post':'postTag.parent().element(class_name="visually-hidden").text',
          'urn':'postTag.attributes["data_urn"]',
          'name':'postTag.element(class_name="feed-shared-actor__name").text',
          'userUrl':'postTag.link(class_name="feed-shared-actor__container-link").href.split("?")[0]',
          'likes':'postTag.element(class_name="social-details-social-counts__reactions-count").text',
            # len('.div(class_name='feed-shared-social-actions').buttons(text='Like'))',
              # 'react-button--active' in 'react-button__text--like' in 
          'liked':'"react-button--active" in postTag.div(class_name="feed-shared-social-actions").button(text="Like").class_name',
          # print(name','.element(class_name='feed-shared-social-actions'
          #                                                            ).button(text='Like').class_name)
          'text':'postTag.element(class_name="feed-shared-update-v2__commentary").text',
          'desc':'postTag.element(class_name="feed-shared-actor__description").text',
          'subdesc':'postTag.element(class_name="feed-shared-actor__sub-description").text',
          # if post['subdesc'] not in ['Promoted']:
          'deg':'postTag.span(class_name="feed-shared-actor__supplementary-actor-info").text',
      }
      for key,evl in _map.items():
        try:
            print (evl.split(').')[0]+').exists')
            # post[key]=eval(evl,{"postTag":postTag})
        except (nerodia.exception.UnknownObjectException,Exception) as e:
            pass
            print(f"Error {e!r} {key} {evl}")
      return post    

        
    def getPostIds(self):
      "Get list of all feed posts"
      nerodia.default_timeout=.1
      posts=[]

      for x in self.browser.elements(class_name='feed-shared-update-v2',
                          ):#data_id=re.compile("urn:li:activity:")):
          if re.match(r"^urn:li:activity:",x.data_urn):
            print (x.exists)
            try:
                post=self.getPostData(x)
                post.update({'el':x})
                posts.append( post)
            except Exception as e:
                # Logs the error appropriately. 
                print(f">>{e!r}")
          else:
            print(">",x.data_urn)

      return posts
      
class Facebook(SocialMediaSite):
    authType='facebook'
    logGSheet=None
    def __init__(self,b=None,cookieFile=None,authFile=f"{os.environ['AUTH']}/auth.yaml",cfgFile=None,delay=None):
        super().__init__(b,authFile=authFile,delay=delay)
        self.siteType='facebook'
        
        if  cfgFile is not None: #=f'{os.environ["LIB"]}/cfg_strava.yaml'
          with open(cfgFile) as file:
            cfg = yaml.safe_load(file)
            self.cfg.update(cfg['facebook'])

    def login(self,login):
        if 'username' in login:
          auth=login
        else:
          auth=self.auth[self.authType][login]
          
        self.browser.goto('https://m.facebook.com/login')

        # try: # reject cookies ! copy from Strava       
      
        try:
          try:self.browser.text_field(name='session_key').value=auth['username']  #timeout did not work
          except:pass
          _pwd=self.browser.text_field(name='session_password')
          _pwd.value=auth['password']
          _pwd.send_keys(Keys.ENTER)
        except Exception as e:
          if 'dashboard' in self.browser.url:
            logging.info( f"Logged in with {auth['username']}") #logging.warning 
          else:
            logging.warning( f"Error Login2 {e!r}") #logging.warning 
    
    def logout(self):
      try:
        self.browser.goto('https://www.linkedin.com/feed')
        menu=self.browser.element(class_name='global-nav__me'
                                 ).wait_until(timeout=2,method=ifExists)
        menu.click()
        self.browser.execute_script("arguments[0].click();", menu)
        if 'artdeco-dropdown--is-open' in menu.class_name:
            self.browser.element(text='Sign Out').click()
            self.browser.element(text='Sign Out').click()
            logging.info( f"Logged out")
        else:
            logging.info( f"Error: Log out menu did not open")
      except TimeoutError:
            logging.info( f"Error: Perhap not signed in")

    def getPostData(self,postTag):
      "Return data regarding one post in linkedin feed"
      post={}
      if not postTag.exists:
        return
      _map={
          'post':'postTag.parent().element(class_name="visually-hidden").text',
          'urn':'postTag.attributes["data_urn"]',
          'name':'postTag.element(class_name="feed-shared-actor__name").text',
          'userUrl':'postTag.link(class_name="feed-shared-actor__container-link").href.split("?")[0]',
          'likes':'postTag.element(class_name="social-details-social-counts__reactions-count").text',
            # len('.div(class_name='feed-shared-social-actions').buttons(text='Like'))',
              # 'react-button--active' in 'react-button__text--like' in 
          'liked':'"react-button--active" in postTag.div(class_name="feed-shared-social-actions").button(text="Like").class_name',
          # print(name','.element(class_name='feed-shared-social-actions'
          #                                                            ).button(text='Like').class_name)
          'text':'postTag.element(class_name="feed-shared-update-v2__commentary").text',
          'desc':'postTag.element(class_name="feed-shared-actor__description").text',
          'subdesc':'postTag.element(class_name="feed-shared-actor__sub-description").text',
          # if post['subdesc'] not in ['Promoted']:
          'deg':'postTag.span(class_name="feed-shared-actor__supplementary-actor-info").text',
      }
      for key,evl in _map.items():
        try:
            print (evl.split(').')[0]+').exists')
            # post[key]=eval(evl,{"postTag":postTag})
        except (nerodia.exception.UnknownObjectException,Exception) as e:
            print(f"Error {e!r} {key} {evl}")
            pass
      return post    
        
    def getPostIds(self):
      "Get list of all feed posts"
      nerodia.default_timeout=.1
      posts=[]

      for x in self.browser.elements(class_name='feed-shared-update-v2',
                          ):#data_id=re.compile("urn:li:activity:")):
          if re.match(r"^urn:li:activity:",x.data_urn):
            print (x.exists)
            try:
                post=self.getPostData(x)
                post.update({'el':x})
                posts.append( post)
            except Exception as e:
                # Logs the error appropriately. 
                print(f">>{e!r}")
          else:
            print(">",x.data_urn)

      return posts
      
