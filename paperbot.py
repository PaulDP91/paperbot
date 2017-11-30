# -*- coding: utf-8 -*-
"""
Created on Thu Nov 23 18:13:11 2017

@author: paul
@contact : paul.m.dutronc{at}gmail.com

Goal of this little bot: participate in automating the boring stuff.
Here the boring stuff will be considered to be retrieving 
the list of new publications from a given list of journals, with:
    authors
    title
    links to the papers
and send this in a nice, formatted way, to a desired email account.
"""

from bs4 import BeautifulSoup
import urllib.request
import easygui as eg
import smtplib
import os
import json
from email.mime.text import MIMEText

"""

Important note on email credentials :
    For security reasons, one will always have to input their password to send the email.
    This is the only part we refuse to automate because it poses too much of a risk.

The objective of this small script is to:
    once launched :

        *** offer the possibility to enter the default email address' password, 
        and send the list of new publications default
        
        *** choose from a list of journals which ones to scan for new publications
        
        *** choose a new default email address to send to

        *** save new settings
"""

cd=os.getcwd()

#Let's have the app come with a bunch of journals available
journalsref_filename=cd+"/journals.json"
if not os.path.isfile(journalsref_filename) : 
    jstart = {
            "Journal of Political Economy":"https://ideas.repec.org/s/ucp/jpolec.html",
            "Quarterly Journal of Economics":"https://ideas.repec.org/s/oup/qjecon.html",
            "Econometrica":"https://ideas.repec.org/s/wly/emetrp.html",
            "AER":"https://ideas.repec.org/s/aea/aecrev.html",
            "AEJ:Applied":"https://ideas.repec.org/s/aea/aejapp.html",
            "Review of Economic Studies":"https://ideas.repec.org/s/oup/restud.html",
            "Journal of Development Economics":"https://ideas.repec.org/s/eee/deveco.html",
            "Journal of Comparative Economics":"https://ideas.repec.org/s/eee/jcecon.html",
            "China Economic Review":"https://ideas.repec.org/s/eee/chieco.html"
            }
    with open(journalsref_filename, 'w') as jfile :
        json.dump(jstart, jfile,ensure_ascii=False)

journals = json.load(open(journalsref_filename))

#Define a 'Journal' class
class Journal :
    """
    A journal is defined by its name.
    
    Attributes:
        url : the url of the Journal's home page on Ideas
        soup : the html of 
    Methods:
        lastsoup : retrieves the last issue's soup
        get_last_papers : extracts from lastsoup the list of papers published in the last issue
        get_last_date : extracts from lastsoup the date and volume of the last issue
    """
    def __init__(self, name) :
        self.name=name
        self.url =journals[name]
        self.soup=self.lastsoup()
        
    def lastsoup(self):
        s=BeautifulSoup(urllib.request.urlopen(journals[self.name]).read(), 'lxml').find()
        return s
        
    def get_last_papers(self):
        papersoup=self.soup.find('div', {'class':"panel-body"}).find_all('li')
        papers= [[item.find('a').get_text(), item.find(text=True, recursive=False).strip(), self.url+item.find('a').get('href')]  for item in papersoup]
        return papers
        
    def get_last_date(self):
        d=self.soup.find('div', {'class':"panel-body"}).find_previous().get_text()
        return d


#Define the names of relevant settings files
dest_filename=cd+'/defaultemail.json'
journal_filename=cd+'/defaultjournals.json'
jdates_filename=cd+'/lastextract.json'
server_filename=cd+'/server.json'
neverask_filename=cd+'/neverask.json'

#Let's give default values to relevant parameters
lastrun_dest= False
lastrun_journals= False
lastrun_jdates= []
neverask_param=False
neverask_list=False

#Load previous papers, previous email information, previous dates/issues collected
if os.path.isfile(dest_filename) :
    lastrun_dest=json.load(open(dest_filename))
if os.path.isfile(journal_filename) :
    lastrun_journals=json.load(open(journal_filename))
if os.path.isfile(jdates_filename) :
    lastrun_jdates=json.load(open(jdates_filename))
    
#Load settings modif parameters, and server characteristics.
if os.path.isfile(neverask_filename) :
    neverask=json.load(open(neverask_filename))
    neverask_param=neverask[0]
    neverask_list=neverask[1]
if not os.path.isfile(server_filename) :
    server = eg.multenterbox(msg="This is the first time you are using this program on this machine.\n Please enter your (sending) email address and SMTP email server.\n This information will be stored in the app's memory.\n To modify this in the future, delete the 'server.json' file in the app's folder", fields=['Email address:','SMTP address:'])
else :
    server =json.load(open(server_filename))
with open(server_filename, 'w') as server_file :
    json.dump(server, server_file, ensure_ascii=False)

email=server[0]
smtp=server[1]

#Load a message to keep default settings or tweak around
execdefault=eg.ynbox("Do you wish to send ;\n \t - from and to the same emails \n \t - the new papers from the same reading list as last time?")

#If no tweaking, load default
if execdefault and lastrun_journals and lastrun_dest : 
    j_selected=lastrun_journals
    dest=lastrun_dest

#If tweaking ordered, tweak
if not execdefault : 
    j_selected=eg.multchoicebox(msg="Pick your papers!\n\n (the default is your last choice)", choices=journals.keys())
    dest=eg.multenterbox('Who do you want to send this email to?', title='Email dest.', fields=['Dest1','Dest2','Dest3'], values=[server[0], '', ''] )

jdatesupdate=[]

#Create temporary email body file
emailfile=os.getcwd()+'/emailbody.txt'
try: 
    os.remove(emailfile)
except :
    pass

#Create the message's body
with open(emailfile, mode='w', encoding='utf8') as message :
    message.write('Hello,\n\n You will find below the list of new articles published in the journals you have selected.\n If a paper is found that has already been sent in the previous execution of your app, it will not appear.\n\n')
    for journal in j_selected :
        j=Journal(journal)
        (j.name,j.get_last_date()) in lastrun_jdates 
        if (j.name,j.get_last_date()) in lastrun_jdates :
            message.write('\n  ---------\n'+j.name+'\n\tno new issue since your last newsletter\n')
            jdatesupdate.append((journal, Journal(journal).get_last_date()))
        else:
            message.write('\n  ---------\n'+j.name+'\n\n')
            for x in j.get_last_papers():
                message.write(x[0]+'\n\t'+x[1]+'\n\tlink:'+x[2]+'\n\n')
            jdatesupdate.append((j.name, j.get_last_date()))
    message.write('\n\n\n This is the end of the newsletter. See you next time!\n\n P.')
            
#Send out the message
pwd=eg.passwordbox('Enter your password: ', title='Email auth.')

with open(emailfile, mode='r', encoding='utf8') as m:
    msg = MIMEText(m.read(),"plain", "utf-8")
    
msg['Subject']='New papers in your favorite journals'
msg['To']=", ".join([x for x in dest if x!=''])
msg['From']=email

smtpObj=smtplib.SMTP(smtp, 587)

smtpObj.ehlo()
smtpObj.starttls()
smtpObj.login(email, pwd)
smtpObj.sendmail(email, dest, msg.as_string(), mail_options=[])
smtpObj.quit()

#Before closing the app, ask for necessary changes in the app.
if not neverask_param :
    setdefaultlist=eg.multchoicebox("What parameters do you wish to save for next time?", choices=["Destination email address", "List of selected journals", "None - never ask again"], preselect=[0,1])
if not neverask_list :
    changejournals=eg.choicebox("Do you want to change the list of available journals?", choices=["Yes", "No", "No - never ask again"], preselect=1)

#Change list of journals:

if changejournals=="Yes" :
    addone=True
    while addone :
        additional=eg.multenterbox("Add the name of the journal (you will use this name from now on), and the corresponding Ideas URL", fields=['Name or abbreviation you wish to use:', 'URL:'])
        journals.update({additional[0]:additional[1]})
        addone=eg.ynbox("Do you want to add one more?")
    with open(journalsref_filename) as jfile :
        json.dump(journals, jfile, ensure_ascii=False)

#Export choice of journals as a local certificate: will be loaded next time as default.
if "List of selected journals"==1:
    with open(journal_filename, mode='w') as outfile :
        json.dump([j_selected], outfile, ensure_ascii=False)
#Export destination email address: will be loaded next time as default.
if "Destination email address"==1:
    with open(dest_filename, mode='w') as outfile :
        json.dump([lastrun_dest], outfile, ensure_ascii=False)
#Export 'neverask' meta-parameters
with open(neverask_filename, mode='w') as outfile :
    json.dump([neverask_param, neverask_list], outfile, ensure_ascii=False)
#Export jdates
with open(jdates_filename, mode='w') as outfile :
    json.dump(jdatesupdate, outfile, ensure_ascii=False)

