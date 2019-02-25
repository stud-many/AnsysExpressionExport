# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 17:03:06 2018

@author: Malte Nyhuis

Geschrieben in Windows, nicht getestet in Linux

PAP:

#Suche Res In Working Directory
    *.Res-Liste  mit oder ohne Unterverzeichnisse
#Lese Expressions als Liste ein
    Namen der Expressions in Liste
#Erstelle Post-Script
    Templates zum Erstellen eines Auslesescriptes werden eingelesen
    Derzeit begrenzt auf 26 maximal Expressions, ansonsten Änderung in "Letter" notwendig
    Schreibe Expression wenn gewollt
    Namen der Expressions in cst müssen vor der Auswertung bekannt und eingetgragen sein
    Ein Script-String wird erstellt
#Starte CFXPost mit Batch-Script
    Expression Export für Dateien aus *.Res-Liste 
    CFXPost speichert Tabelle in *.csv-Format
#Lese Daten ein
    *.csv werden eingelesen
#Speichere sämtliche Daten in Ergebnistabelle
"""

import os
import subprocess
import csv

cwd = os.getcwd()   #Working Directory

###########
####SETTINGS
###########
ExportUnits = False 
Subfolders = False

LoadExpressionsCST = False 
CreateExpressionsFromFile = True

AnsysModule ="ANSYS/18.0"                                                       #Modulversionsname für ANSYS auf dem Cluster
AnsysVersion =AnsysModule[6:-2]                                                 #Definiert für Post-Script
cfx5post_path_exe = os.path.join('E:\\',
                                  'ANSYS',
                                  'ANSYS Inc',
                                  'v180',
                                  'CFX',
                                  'bin',
                                  'cfx5post.exe')                               #Pfadangabe zu CFX5PRE. Anzupassen!

PostScriptName = "ExpressionExport_TMP.cse"
ExpressionCST = os.path.join('D:\\',
                                 '2018-12-02-AnsysExpressionExport',
                                 'LoadExpressionsList.csv') 
CreateExpressionsFile = "LoadExpressionsList.csv"

#############
#############

print("Script starting")


#Suche Res In Working Directory
print("finding *.res")
    
resfiles = []

if Subfolders:
        
#Suche Res in Unterverzeichnissen       
   
    for root, dirs, files in os.walk(cwd):                                      #Läuft sämtliche Unterverzeichnisse des CDW ab!
        for name in dirs:
            filelist = os.listdir(name)
            for item in filelist:
                if item[-3:] == "res":
                    resfiles.append(os.path.join(name,item))  

else :
    
    for file in os.listdir(cwd):
        if file[-3:] == "res":
            resfiles.append(file)

#Lese Expressions als Liste ein
print("reading Expressions list...")
fobj = open(os.path.join(cwd,'Expressions.csv'), 'r')
raw = fobj.read()
raw = raw.replace(' ','')
raw = raw.replace('\n','')
expressions = raw.split(',')
expressions = list(filter(None, expressions))
fobj.close()

#Erstelle PostScript
print("creating BATCH-Commands...")

ScriptTXT = ""

fobj = open(os.path.join(cwd,'templates','AuswertungPrePreamble.txt'), 'r')
ScriptTXT += fobj.read()
ScriptTXT = ScriptTXT.replace("VER",AnsysVersion)
fobj.close()

#Create Expression falls gewollt

cstloadTXT = ""

if LoadExpressionsCST:
    print("CST-File with expressions used")
    cstfilepath = os.path.join(cwd,ExpressionCST)
    fobj = open(os.path.join(cwd,'templates','AuswertungPreLoadCST.txt'), 'r')
    ScriptTXT += fobj.read()
    ScriptTXT = ScriptTXT.replace("CST_PATH_FILE",cstfilepath)
    fobj.close()
    
if CreateExpressionsFromFile:
    print("Expressions.csv will be used to create Expressions")
    
    #Lade Expressions aus Liste
    with open(os.path.join(cwd,CreateExpressionsFile), 'r') as f:
        reader = csv.reader(f)
        ExpreList = list(reader)
        for item in ExpreList:
            fobj = open(os.path.join(cwd,'templates','AuswertungPreWriteExpression.txt'), 'r')
            ScriptTXT += fobj.read()
            ScriptTXT = ScriptTXT.replace("EXPRESSIONNAME",item[0])
            ScriptTXT = ScriptTXT.replace("EXPRESSIONVALUE",item[1])
            expressions.append(item[0])
            fobj.close()        
        
fobj = open(os.path.join(cwd,'templates','AuswertungPreTable.txt'), 'r')
ScriptTXT += fobj.read()
fobj.close()

Letter = "A"
for item in expressions:
    fobj = open(os.path.join(cwd,'templates','AuswertungPreSaveExInTable.txt'), 'r')
    ScriptTXT += fobj.read()
    ScriptTXT = ScriptTXT.replace("LETTER",Letter)
    ScriptTXT = ScriptTXT.replace("EXNAME",item)
    Letter = chr(ord(Letter)+1)                                                  #Next Letter. Lese ASCII-Nummer aus, addiere +1 , wandle in ASCII-Char
    fobj.close()

fobj = open(os.path.join(cwd,'templates','AuswertungPreSaveTableInCSV.txt'), 'r')
ScriptTXT += fobj.read()
fobj.close()


#Starte CFXPost mit Batch-Script

Summary = []
for item in resfiles:
    print("starting Export for "+ item + "...")

    csvname = item[:-4]+".csv"
    BATCHCMD = ScriptTXT.replace("DIR_FILENAME",os.path.join(cwd,csvname))
    BATCHCMD = BATCHCMD.replace("LOADRES",item)

    fobj = open(os.path.join(cwd,PostScriptName) , "w")
    fobj.write(BATCHCMD)
    fobj.close()
    args = cfx5post_path_exe + " -batch " + PostScriptName
    subprocess.call(args, shell=False)  #Debugging! Während des Debuggings kann Auskommentierung sinnvoll sein. Erst nach durchgeführtem Export möglich

    #Lese Daten ein

    fobj = open(os.path.join(csvname) , "r")
    data = fobj.read()
    data = data.strip('\n') #Ansys Exportiert mit abschließendem Umbruch
    data = data.split(',')
    for idx,dataitem in enumerate(data):
        data[idx]= dataitem.strip(' ')
    Summary.append(data)
    fobj.close()

#Speichere sämtliche Daten in Ergebnistabelle
  
if ExportUnits:
    print("Saving Results with units in Summary.csv...")
    with open('Summary.csv', 'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',',
                                   quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(expressions)
        for row in Summary:
            manr = []
            for item in row:
                manr.append(item.replace(".",","))
            csvwriter.writerow(row)
else:
    print("Saving Results without units in Summary.csv...")
    for rowid,row in enumerate(Summary):
        for itemid, item in enumerate(row):
            unit_begin = item.find("[")
            if unit_begin > 0:
                Summary[rowid][itemid] = Summary[rowid][itemid][0:unit_begin].strip(" ") #Lösche Einheit[x:y] und Leerzeichen strip() in Summary[a][b]

    with open('Summary.csv', 'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',',
                                   quotechar='|', quoting=csv.QUOTE_MINIMAL)

        csvwriter.writerow(expressions)
        for row in Summary:
            manr = []
            for item in row:
                manr.append(item.replace(".",","))
            csvwriter.writerow(row)
print("Script ended")
    
    