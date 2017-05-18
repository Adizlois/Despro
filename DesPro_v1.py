# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import wx
import datetime
import sys
import os
import zipfile,StringIO
import json
import csv
""" 

Descarga de proyectos - DesPro v 1.0
(Project downloader)

Copyright (C) {2017}  {Alfonso Diz-Lois} <dizlois@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

"""
#SETTING UTF-8 AS DEFAULT, JUST IN CASE...

reload(sys)
sys.setdefaultencoding('utf-8')


 # CHOOSE CURRENT WORKING DIRECTORY...

def ask_directory(parent=None,message="",default_value=""):
    dialog = wx.DirDialog(None, "Please set working directory:",style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
    if dialog.ShowModal() == wx.ID_OK:
        print "Working directory -> ",dialog.GetPath()
    return dialog.GetPath()
    dialog.Destroy()
app1 = wx.App()
app1.MainLoop()  
os.chdir(ask_directory())

#  LOGFILE - SET STDOUT TO BOTH FILE AND CONSOLE....

print "For further information, check logfile  ",os.path.join(os.getcwd(),"Despro_log.log")
log=open('Despro_log.log', "a+",0)
class Set_log:        
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data) 
        log.write(str(data))              
    def flush(self): pass
    
sys.stderr=Set_log(sys.stderr)
sys.stdout=Set_log(sys.stdout)

#GET DATETIME AND SEND TO STDOUT...

now=datetime.datetime.now().strftime("%I%M%p%B%d%Y")
print "*****************************************************"
print now

#GOOGLE LOGIN DATA...

url_login = "https://accounts.google.com/ServiceLogin"
url_auth =  "https://accounts.google.com/ServiceLoginAuth"

def ask(parent=None, message='', default_value='',passw=None):
    if not passw:
        dlg = wx.TextEntryDialog(parent, message)
    if passw:
        dlg = wx.PasswordEntryDialog(parent, message)
    dlg.ShowModal()
    result = dlg.GetValue()
    dlg.Destroy()
    if not result:
        print "Variable has not been properly defined. ..."       
        log.close()
        sys.exit()         
    return result
    
app = wx.App()
app.MainLoop()
login=ask(message = 'Input Google Login')
pwd=ask(message= ('Input password ('+login+')'),passw=True)

#LOGIN GOOGLE & EPICOLLECT SERVER....

ses=requests.Session()
login_html = ses.get(url_login)    
soup_login = BeautifulSoup(login_html.content,"lxml").find('form').find_all('input')
my_dict = {}
for u in soup_login:
    if u.has_attr('value'):
        my_dict[u['name']] = u['value']
my_dict['Email'] = login
my_dict['Passwd'] = pwd
ses.post(url_auth, data=my_dict)
redir="https://five.epicollect.net/redirect/google"
r = ses.get(redir)
if len(r.history)<3:
    print "Login failed, please try again"
    log.close()
    sys.exit()
else:
    print "Login succeed"
    

#LOOK FOR AVAILABLE PROJECTS ON THE EPICOLLECT WEBSITE...

url="https://five.epicollect.net/myprojects"
Projects=[]
for a in BeautifulSoup(ses.get(url).content,"lxml").find_all('a', href=True):
    if "https://five.epicollect.net/project/" in a['href']:
        if a['href'].split("/")[-1] not in Projects:
            Projects.append(a['href'].split("/")[-1])
if not Projects:
    print ("No projects found")
    log.close()
    sys.exit()
                        
#SELECT PROJECTS TO DOWNLOAD....

Elecciones=()
Selected_projects=[]
class MyFrame(wx.Frame):
    def __init__(self):        
        wx.Frame.__init__(self, None, wx.ID_ANY, "Choose one or several projects",(-1, -1),wx.Size(400,300))
        self.button = wx.Button(self, -1, "Cancel")
        self.button2=wx.Button(self,-1,"Download")
        self.Bind(wx.EVT_BUTTON, self.ButtonPress, self.button)
        self.Bind(wx.EVT_BUTTON,self.Button2Press,self.button2)
        self.lb = wx.ListBox(self, -1, choices = Projects, style=wx.LB_MULTIPLE)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.lb, 0, wx.EXPAND, 1)
        box.Add(self.button, 0, wx.CENTER|wx.ALL, 5)
        box.Add(self.button2,0,wx.CENTER|wx.ALL, 5)
        self.SetSizer(box)
        self.Layout()
        self.Centre()
    def ButtonPress(self, evt):   
        self.Destroy()
    def Button2Press(self, evt):
        global Elecciones   
        Elecciones= self.lb.GetSelections()
        self.Close()
app2 = wx.PySimpleApp()
frame = MyFrame()
frame.Show()
app2.MainLoop()
if not Elecciones:
    print "Program cancelled"
    log.close()
    sys.exit()    
[Selected_projects.append(Projects[i])for i in Elecciones]       

#EPICOLLECT ALLOWS USERS TO SET LISTS AS POSSIBLE VALUE FOR SOME ATTRIBUTES. SO IN ORDER TO
#DEAL WITH IT, I DECIDED TO TURN THOSE LISTS INTO STRINGS. THAT IS WHAT THIS FUNCTION IS ABOUT...

def list_to_string(list_,separator):
    name="["
    for el in list_:
        name=name+str(el)
        if list_.index(el)!=(len(list_)-1):
            name=name+separator
    name=name+"]"
    return name
    
#GRAB ZIP FILE, EXTRACT, RENAME AND TRANSFORM INTO CSV....
#"IF FIRST" CONDITION IS USED TO WRITE HEADERS IN THE CSV FILE FROM JSON KEYS 

def get_project(project_name):
    csvlist=[]
    first=True
    headers=['\n']
    directory="./"+str(project_name)
    if not os.path.exists(project_name):
        os.makedirs(directory)
    os.chdir(directory)
    url="https://five.epicollect.net/api/internal/download-entries/"+project_name+"?format=json&map_index=0"
    Local=str(project_name)+"_"+str(now)+".json"
    zipurl = ses.get(url,stream=True)
    z=zipfile.ZipFile(StringIO.StringIO(zipurl.content))
    json_name=z.namelist()[0]
    print "Extracting file in: ",os.getcwd()
    print "Filename: ",Local, "  --> (Projectname_datetime.json)"
    z.extractall()
    os.rename(json_name,Local)
    
#OPEN JSON FILE AND ITERATE THROUGH EACH RECORD/SAMPLE...
    
    with open(Local) as data_file:    
        data = json.load(data_file)
        records=len(data["data"])
        print "Number of records: ",records 
        #ITERATE THROUGH RECORDS....
        for i in range(records):
            for a in data["data"][i].keys():     
                               
                #LOOK FOR PICTURES WITHIN RECORD FIELDS.... "..PICTURE..""..FOTO.." or "..PHOTO.."
                #AND DOWNLOAD THOSE THAT ARE NOT ALREADY AVAILABLE ON DIRECTORY
                              
                if ("picture" in a.lower()) or ("foto" in a.lower()) or ("photo" in a.lower()):
                    bigpicture_name=str(data["data"][i][a])
                    if data["data"][i][a]!='':
                        if bigpicture_name.split("/")[0]=="https:":
                            picture_name= bigpicture_name.split("&name=")[-1]
                            link=bigpicture_name
                        else:
                            picture_name=bigpicture_name                           
                            link= "https://five.epicollect.net/api/internal/media/"+project_name+"?type=photo&format=entry_original&name="+picture_name
                        
                        print "Picture found on server -> ",picture_name,
                        if os.path.isfile("./"+picture_name):
                            print "Already downloaded"
                        else:
                            print "File not found in project folder"
                            print "Downloading....",
                        
                            try:
                                pict = ses.get(link)
                                data["data"][i][a]=os.path.join(os.getcwd(),picture_name)
                                with open(picture_name, 'wb') as wt:
                                    for block in pict.iter_content(1024):
                                        if not block:
                                            break
                                        wt.write(block)
                                print "Done"
                                 
                            except:
                                print "File does not seem to be a picture"
                                print "Processing field as string..."                                
                                pass        
                                 
            #GET LATITUDE, LONGITUDE AND ACCURACY FROM JSON FILE. JSON FILES FROM EPICOLLECT STORE THEM AS DICT
            
            csvlist.append('\n')             
            for key in data["data"][i].keys():
                if isinstance(data["data"][i][key],dict):
                    if data["data"][i][key]["latitude"]!=u'':
                        Latitude=data["data"][i][key]["latitude"]
                        Longitude=data["data"][i][key]["longitude"]
                        Accuracy=data["data"][i][key]["accuracy"]
                        if first:
                            coord=["Latitude","Longitude","Accuracy"]
                            for co in coord:
                                headers.append(co)
                        coord_data=[Latitude,Longitude,Accuracy]
                        for dat in coord_data:
                            csvlist.append(dat)
                    else:
                        for z in range(3):
                            csvlist.append("")
                else:
                    
                    #IF FIRST, INSERT FIELD NAME IN HEADERS LIST. ADDFIELD VALUE TO CSVLIST
                    
                    if first:
                        headers.append((key))
                    if isinstance(data["data"][i][key],list):
                        csvlist.append(list_to_string(data["data"][i][key],";"))
                    else:
                        csvlist.append(data["data"][i][key])                        
            first=False                        
        headers.append('\n')
                
        #INSERT HEADLIST IN CSVLIST AND SAVE IT AS A CSV FILE... 
        
        for head in headers:
            csvlist.insert(headers.index(head),head)        
        print csvlist
        csvfile=Local.split(".json")[0]+".csv"
        with open(csvfile, "wb") as output:
            writer = csv.writer(output,dialect='excel',lineterminator='\n',delimiter=',')    
            writer.writerow(csvlist)
        print "Creating csv file...",csvfile                                                        
    os.chdir("..")
 
#ITERATE THROUGH PROJECTS....
 
for a in Selected_projects:
    print "Project ****", a,"****"
    get_project(a)
    print "Project ",a," done"
print "---------------------------------------------------------------"
print "***************************************************************"
log.close()