import yaml
cfg=yaml.safe_load("""colors:
  class_name: blue
  tag_name: green
  text: brown
""")
import os
import logging
import subprocess
#color print
from IPython.display import Markdown, HTML



def extractDict(obj,attrs,notFound=None):
    """
    Extract list of ttributes at any level
    """
    import dpath.util
    if isinstance(attrs,str): attrs=[attrs]
    d={}
    for x in attrs:
        try:
            d[x]=dpath.util.get(obj,f"**/{x}")
        except:
            d[x]=notFound
    return d
  
def counterCheck(counterName,maxCount):
    """Maintain counter of in env variable
    >>> for i in range(10): print(i,counterCheck('KUD',5))
    0 True
    1 True
    2 True
    3 True
    4 True
    5 False
    6 False
    7 False
    8 False
    9 False
    """
    if 'COUNTER_' not in counterName: counterName=f'COUNTER_{counterName}'
    if counterName in os.environ:
        counter=int(os.environ[counterName])
        if counter>=maxCount:
            return False
        else:
            # print(counterName)
            os.environ[counterName] = str(counter + 1)
            return True
    else:
        os.environ[counterName]=str(1)
        return True
            
            

  


def cstr(s, color='black'):
    """ Print with color
    
    >>> cstr("test")    
    '<text style=color:black>test</text>'
    """
    return "<text style=color:{}>{}</text>".format(color, s)

import subprocess


def shell(cmd): 
  """"""
  out = subprocess.check_output(cmd, shell=True, text=True)
  "Required since NT splits lines and posix doesnt"
  if isinstance(out,str): 
    out = out.split('\n')
  return out
  
def setup_env(packages,modules):
  """Sets up APT packages and Python modules
  
  >>> setup_env([],['pandas'])
  'Environment setup'
  """
  import re,os
  if os.name!='nt':
      modlist=shell('pip list')
      print(modules)

      modlist={x.split()[0]:x.split()[1]
                 for x in modlist[2:] if x}
      for m in modules:
        if m in modlist:
          display(f"Module {m} : {modlist[m]} already installed")
        else:
          display(f"Installing module {m} ")
          shell(f'pip install {m} ')
      # if True:
        # !apt-get update # to update ubuntu to correctly run apt install
      pkgList=shell('apt list --installed')
      pkgList=[re.sub(r'[\x1b]\[\d+m','',x).split('/')[0] for x in pkgList ]
      for pkg in packages:
        if pkg in pkgList:
          display(f"package {pkg} already installed")
        else:
          display(f"Installing package {pkg}")
          shell(f'apt install {pkg} ')

  return "Environment setup"

  

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
    """Get attributes id tag exists
    - el : tag
    - attr : str, list of attributes
    - detaults : default for each attributes, '' (blank if not provided)
    """
    if isinstance(attr,str):
        attr=[attr]
      
    try:
        el.wait_until(timeout=.1,method=lambda x:x.exists)
    except Exception as e:
        # print(f'Error getAttrsIfExists() {e!r}')
        arr=[None for x in attr]      # return all Xs
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
    
def findfile(file,recursive=False,pathlist=os.environ['PATH'].split(";")):
    """
    >>> findfile("cmd.exe",pathlist=os.environ['PATH'].split(';'))
    ['C:\\\\WINDOWS\\\\system32/cmd.exe']
    >>> findfile("config.yaml")
    ['config.yaml']
    >>> findfile("utils.py")
    ['utils.py']
    """
    def log(*kws): pass#print(*kws)
    filelist=[]
    "Find file in current directory + subdirectories + path"
    for root, dirs, files in os.walk(".",topdown=False):  
    # print(f"searching in  {path1}")
        if file in files:
            filelist.append(file)
            log(f"{file} exists {root}")
    else:
        log(f"not in {root}")

    for path1 in pathlist:
        # topdown=True, onerror=None, followlinks=False
        _file="/".join([path1.strip("/"),file])
        if os.path.isfile(_file) and path1:
            log(f"{file} exists in {path1}")
            filelist.append(_file)
        else:
            log(f"not in {path1}")
    return filelist
  
  
def insp(obj):
    arr=[]
    def pp(a,s,v): 
        # print(f"{a}\t{s}\t{v}")
        arr.append([type(getattr(obj,a,)).__name__,a,s,v[:50]])
    for a in dir(obj):
        # print(a)
        try: 
            _attr = getattr(obj,a,)
            if callable(_attr):
                pp(a,':',_attr())
            else:
                pp(a,'=',_attr)
        except Exception as e: pp(a,'-',f"{e!r}")
    return arr
        