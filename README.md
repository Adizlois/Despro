# Despro
Despro (descarga de proyectos - project downloader) makes it possible to create local backups of one or several projects from the Epicollect 5 server (json file and pictures) and creates csv excel-compatible files. 

## Script overview

Firstly, Despro asks the user to set the working directory. This sets up the location of the logfile and the project folders. Logfile (Despro_log.log) can be checked for further information about the session.

Then, Despro asks username and password of the Google account that want to be used to log in on Epicollect 5. If successful, a list of available projects from the Epicollect website will show up. One or several projects can be selected. 
For each one of them:
  - If it does not exist a folder with the name of the project already, Despro creates it.
  - It downloads the *.json file and saves it as:  "Nameoftheproject_HHMM(PM)(AM)MonthDDAAAA" (Example: "Footprints_0537PMMay112017.json")
  - It looks for pictures within the fields of the json file. More specifically, if it finds "photo", "picture" or "foto" as part of any field name (in lowercase), Despro tries to download the file unless it already exists in the project folder. 
  - And lastly, it creates an excel-compatible csv file. It does not overwrite the json file so both files are stored.

## Important Notes

- It is recommended to use always the same working directory. That way, you will have all the information of the connections (log) stored in just one file. Moreover, program can be run anytime you want as every json and csv file will not be overwritten because they are saved with different names (which depends on date and time) and only those pictures that are new will be downloaded. 
- Links to image files will be replaced by their current file path in the Local disk. 

