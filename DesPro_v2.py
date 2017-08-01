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

Descarga de proyectos - DesPro v 2.0
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
    dialog = wx.DirDialog(None, "Elija el directorio de trabajo:",style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
    if dialog.ShowModal() == wx.ID_OK:
        print "Directorio de trabajo: ",dialog.GetPath()
    return dialog.GetPath()
    dialog.Destroy()
app1 = wx.App()
app1.MainLoop()  
os.chdir(ask_directory())
print "Consultar archivo ",os.path.join(os.getcwd(),"Despro_log.log"), "para mas informacion sobre la sesion...."
#SET STDOUT TO BOTH FILE AND CONSOLE....
log=open('Despro_log.log', "a+",0)
class Unbuffered:
        
    def __init__(self, stream):

        self.stream = stream

    def write(self, data):
        self.stream.write(data) 
        log.write(str(data))              
    def flush(self): pass
    
sys.stderr=Unbuffered(sys.stderr)
sys.stdout=Unbuffered(sys.stdout)

now=datetime.datetime.now().strftime("%I%M%p%B%d%Y")
print "**************Despro_v2.0 desarrollado por Alfonso Diz-Lois(dizlois@gmail.com)**************"
print now

#SET SOME VARIABLES...

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
        print "No se ha definido la variable..."       
        log.close()
        sys.exit() 
            
    return result
app = wx.App()
app.MainLoop()
login=ask(message = 'Introduzca Login (Google)')
pwd=ask(message= ('Introduzca password ('+login+')'),passw=True)

#LOGIN GOOGLE & EPICOLLECT SERVER

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
    print "Hubo un error en la autentificacion. Intentelo de nuevo."
    log.close()
    sys.exit()
else:
    print "Login correcto"
    

#LOOK FOR PROJECTS ON THE WEBSITE...
url="https://five.epicollect.net/myprojects"
Projects=[]
for a in BeautifulSoup(ses.get(url).content,"lxml").find_all('a', href=True):
    if "https://five.epicollect.net/project/" in a['href']:
        if a['href'].split("/")[-1] not in Projects:
            Projects.append(a['href'].split("/")[-1])
if not Projects:
    print ("No se encuentran proyectos o no se ha conseguido acceder correctamente")
    log.close()
    sys.exit()
                        
#SELECT PROJECTS TO DOWNLOAD....
Elecciones=()
Selected_projects=[]
class MyFrame(wx.Frame):
    def __init__(self):        
        wx.Frame.__init__(self, None, wx.ID_ANY, "Elija uno o varios proyectos",(-1, -1),wx.Size(400, 300))
        self.button = wx.Button(self, -1, "Cancelar")
        self.button2=wx.Button(self,-1,"Descargar proyecto")
        self.Bind(wx.EVT_BUTTON, self.ButtonPress, self.button)
        self.Bind(wx.EVT_BUTTON,self.Button2Press,self.button2)
        self.lb = wx.ListBox(self, -1, choices = Projects, style=wx.LB_MULTIPLE)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.lb, 0, wx.EXPAND, 0)
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
    print "Programa cancelado / No se han especificado proyectos para descargar"
    log.close()
    sys.exit()
[Selected_projects.append(Projects[i])for i in Elecciones]       

#GRAB ZIP FILE, EXTRACT, RENAME AND TRANSFORM INTO CSV....
def list_to_string(list_,separator):
    name="["
    for el in list_:
        name=name+str(el)
        if list_.index(el)!=(len(list_)-1):
            name=name+separator
    name=name+"]"
    return name
   
def get_project(project_name):
    csvlist=[""]
    first=True
    headers=[]
    directory="./"+str(project_name)
    if not os.path.exists(project_name):
        os.makedirs(directory)
    os.chdir(directory)
    url="https://five.epicollect.net/api/internal/download-entries/"+project_name+"?format=csv&map_index=0"
    Local=str(project_name)+"_"+str(now)+".csv"
    zipurl = ses.get(url,stream=True)
    z=zipfile.ZipFile(StringIO.StringIO(zipurl.content))
    csv_name=z.namelist()[0]
    print "Extrayendo en directorio: ",os.getcwd()
    print "Nombre de archivo: ",Local, "  --> (Nombre del proyecto_HORAYFECHA.csv)"
    z.extractall()
    os.rename(csv_name,Local)
    
#OPEN JSON FILE AND LOOK FOR PICTURES...
    
    
    with open(Local,'rb') as data_file: 
        data = csv.reader(data_file,delimiter=",")
        alldata = list(data)
        records = len(alldata)-1
        headers = alldata[0]
        del alldata[0]        
        print "Number of records is ",records              
        for sample in alldata:
            for a in headers:           
                if ("picture" in a.lower()) or ("foto" in a.lower()) or ("photo" in a.lower()):
                    bigpicture_name=sample[headers.index(a)]
                    print bigpicture_name

                    if bigpicture_name!='':
                        if bigpicture_name.split("/")[0]=="https:":
                            picture_name= bigpicture_name.split("&name=")[-1]
                            link=bigpicture_name
                        else:
                            picture_name=bigpicture_name
                            link= "https://five.epicollect.net/api/internal/media/"+project_name+"?type=photo&format=entry_original&name="+picture_name
                        sample[headers.index(a)]=os.path.join(os.getcwd(),picture_name)
                        print "Fotografia encontrada en servidor -> ",picture_name
                        if os.path.isfile("./"+picture_name):
                            print "Ya disponible"
                        else:
                            print "No existe en el disco duro"
                            print "Descargando....",
                                                 
                            r = ses.get(link)
                            with open(picture_name, 'wb') as wt:
                                for block in r.iter_content(1024):
                                    if not block:
                                        break
                                    wt.write(block)
                            print "Hecho"

                        
    csvlist=[headers]+alldata                                                                                                                                        
    with open(Local, 'wb') as myfile:
        wr = csv.writer(myfile, lineterminator='\n',delimiter=",")
        for a in csvlist:
            wr.writerow(a)                                                        
    os.chdir("..")
    
for a in Selected_projects:
    print "Proyecto ****", a,"****"
    get_project(a)
    print "Proyecto ",a," finalizado"
print "---------------------------------------------------------------"
print "***************************************************************"
log.close()
