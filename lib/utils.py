import yaml
cfg=yaml.safe_load("""colors:
  class_name: blue
  tag_name: green
  text: brown
""")

import logging
import subprocess


def shell(cmd): 
  out = subprocess.check_output(cmd, shell=True, text=True)
  "Required since NT splits lines and posix doesnt"
  if isinstance(out,str): 
    out = out.split('\n')
  return out
  

#color print
from IPython.display import Markdown

from IPython.display import HTML

def cstr(s, color='black'):
    return "<text style=color:{}>{}</text>".format(color, s)


def setup_env(packages,modules):
    
  import re,os
  if os.name!='nt':
      modlist=shell('pip list')
      modlist={x.split()[0]:x.split()[1] for x in modlist[2:]}
      for m in modules:
        if m in modlist:
          display(f"module {m} : {modlist[m]} already installed")
        else:
          display(f"fmodule {m} : {modlist[m]} not installed")
          shell('pip install {m} ')
      # if True:
        # !apt-get update # to update ubuntu to correctly run apt install
      pkgList=shell('apt list --installed')
      pkgList=[re.sub(r'[\x1b]\[\d+m','',x).split('/')[0] for x in pkgList ]
      for pkg in packages:
        if pkg in pkgList:
          display(f"package {pkg} already installed")
        else:
          display(f"package {pkg} not installed")
          shell('apt install {pkg} ')

  return "Environment setup"
  # if os.name!='nt' and False:
  #     !pip install nerodia
  #     !pip install pygsheets
  #     if True:
  #       !apt-get update # to update ubuntu to correctly run apt install
  #       if False:
  #         !apt install firefox-geckodriver
  #         !cp /usr/bin/geckodriver {DIR}
  #         !cp -r /usr/lib/firefox/ {DIR}
  #       if True:
  #         !apt install chromium-chromedriver
  #         !cp /usr/lib/chromium-browser/chromedriver {DIR}
  

def setLogger(logFile=None,level=logging.INFO):
    # level = logging.INFO if level is None else 
    from imp import reload
    # jupyter notebook already uses logging, thus we reload the module to make it work in notebooks
    # http://stackoverflow.com/questions/18786912/get-output-from-the-logging-module-in-ipython-notebook
    reload(logging)
    logging.basicConfig( level=level,
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
                    
    if logFile:
        logger = logging.getLogger()
        fhandler = logging.FileHandler(filename=logFile, mode='a',encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                                     ,datefmt='%Y-%m-%d %H:%M:%S')
        fhandler.setFormatter(formatter)
        logger.addHandler(fhandler)
        logger.setLevel(level)
        
    logging.info("Logger file: "+logFile if logFile else "None")
    
    
def getAttrs(t,attr,maxText):
    "internall function to get attributes of a tag"
    def colStr(text,type):
      return text

    attrs=[]
    for x in attr:
        if x in ['innertext']:
          attrs.append (colStr(t.execute_script("""
            var parent = arguments[0];
            var child = parent.firstChild;
            var ret = "";
            while(child) {
                if (child.nodeType === Node.TEXT_NODE)
                    ret += child.textContent;
                child = child.nextSibling;
            }
            return ret;
            """, t.wd),x) )
        else:
          try: 
              val=getattr(t,x)
              if type(val) in [str ]:
                  if 'text' in x: val=val.replace('\n','\\n')[:maxText]
                  attrs.append(colStr(val,x))
              else:
                  attrs.append(colStr("?"+str(type(val)),x) if val else '-')
          except AttributeError:
              attrs.append(colStr('-',x))
          except Exception as e:
              print(f'Error {e!r}')
    return attrs

def printAttrs(lvl,attr,attrs,maxText):
  "HTMl formating for tag attributes...uses cfg in the module"
  
  out='&nbsp;&nbsp;'*lvl+''
  for i,a in enumerate(attrs):
    "Truncate long strings"
    if len(a)>maxText:
      a=a[:(maxText-3)]+'...'

    if attr[i] in cfg['colors']:
      color=cfg['colors'][attr[i]] 
      out+=f'<span style="color: {color}">{a}</span> '
    else:
      out+=a+' '
  # print(out)
  display (HTML("<br>"+out))
  
def dumpChildren(tag,attr=['tag_name','class_name','text'],lvl=0,maxText=40,stopTags=['svg']):

    if lvl==0: print("|".join(attr))
    printAttrs(lvl,attr,
               getAttrs(tag,attr,maxText),
               maxText)
    # cprint(cstr(' '*lvl),cstr("|".join(
    #   getAttrs(tag,attr,maxText))))
    
    for i,t in enumerate(tag.children()):
        if not t.tag_name in stopTags:
            # print(i,t.tag_name,len(t.parent().children()))
            dumpChildren(t,attr,lvl=lvl+1,maxText=maxText,stopTags=stopTags)
    return 
        
def dumpParents(tag,attr=['tag_name','class_name','text'],lvl=0,maxText=40,maxLevels=5,stopTags=['html']):
    if lvl==0: print("|".join(attr))

    printAttrs(lvl,attr,
               getAttrs(tag,attr,maxText),
               maxText)

    for t in [tag.parent()]:
      
        if (not t.tag_name in stopTags) and lvl < maxLevels:
            dumpParents(t,attr,lvl=lvl+1,maxText=maxText,maxLevels=maxLevels,stopTags=stopTags)

    return         

# dumpchildren(b.div(id='side'),['id','tag_name','title','role','text',"data-testid"])
def dumpTag(tag,attr=['tag_name','class_name','innertext','title','data_testid'],maxText=50):
    printAttrs(999,attr,
               getAttrs(tag,attr,maxText),
               maxText)
    # print(tag.__dict__)

    return         

def getAttrsIfExists(el,attr=['text'],defaults=[]):
    try:
        el.wait_until(timeout=.1,method=lambda x:x.exists)
    except Exception as e:
        # print(f'Error getAttrsIfExists() {e!r}')
        arr=['' for x in attr]      # return all Xs
    else:
        arr=[]
        for i,a in enumerate(attr):
            try: 
                arr.append(getattr(el,a))
            except:
                if i<len(attr):
                    arr.append(attr[i])
                else:
                    arr.append('')

    # display(arr,attr,defaults)
    if len(attr)==1:
      return arr[0]
    else:
      return arr