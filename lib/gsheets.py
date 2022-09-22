import pygsheets
import json
import re
import os
import pandas as pd

class Gsheet:
    sheet=None
    def __init__(self,url,service_account_file):
        if service_account_file:
          self.client = pygsheets.authorize(service_account_file=service_account_file)   
          # print(cfg,url,re.match("^https+://",url))
          # if re.match("^https+://",url):
          self.ws=self.client.open_by_url(url)
          # else:
          #     self.sheet=cfg['sheets'][url]
          #     self.ws=self.client.open_by_url(self.sheet['url'])
    def getSheetByTitle(self,sheet):
        return self.ws.worksheet_by_title(sheet)
    def getSheetDf(self,sheet, start=None,end=None):
        if (sheet==None) and self.sheet: sheet=self.sheet['tab']
        if (start==None) and self.sheet: start=self.sheet['range'].split(':')[0]
        df= self.getSheetByTitle(sheet).get_as_df(start=start,end=end)
        df.columns
        return df
    @staticmethod
    def cleanse(df):
        if 'Unnamed:' in df.columns[0]:
            df=df.set_index(df.columns[0])
            df.index.name='row'
        
        df=df[ [x for x in df.columns if x==x] ]  #non-null column headers
        
        # remove duplicate columns
        newCols=[]
        for i,f in enumerate(df.columns):
            if f=='':
              colHdr= f'col_{i}'
            else:
              colHdr = re.sub('[()/\-#,\.\?\'\:]', '',
                             df.columns[i].strip().replace(' ', '_'))
            if list(newCols).count(f)>1:
                colHdr = colHdr+ f'_{i}'
            newCols.append(colHdr)
        df.columns=newCols

        return df