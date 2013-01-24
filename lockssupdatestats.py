#!/usr/bin/python

#lockssupdatestats.py

#import needed modules. re and time are part of python, so you
#get them with an install of the language.
import re
import time
from sys import exit
#these two modules need to be installed in addition to python.
import gdata.spreadsheet.service
import requests

#doc_name is used to find the right spreadsheet inside the user's google drive acct
doc_name  = 'lockss crawl stats'
#credfile is the full path to the file that holds usernames and passwords
#To work, you need a plain text file. It should have 4 values, each on its own
#line, with no blank lines.  They need to be ordered like this:
#  email (user's gmail address)
#  password (gmail password)
#  lockssname
#  locksspassword
credfile = '/path/to/password/file'
#creds opens the file that holds usernames and passwords.
try:
    creds = open(credfile, 'r')
except IOError:
    print "Failed to open credential store at " + credfile + "\n"
    raise
else:
        email = creds.readline().rstrip()
        password = creds.readline().rstrip()
        lockssname = creds.readline().rstrip()
        locksspassword = creds.readline().rstrip()
        creds.close()
if email == "" or password == "" or lockssname == "" or locksspassword == "":
    print "Failed to read one or more of the needed credentials from " + credfile + "\n"
    #print email
    #print password
    #print lockssname
    #print locksspassword
    
#now is a variable that gets the time on the computer where the script is running.
#The LOCKSS calculations in the spreadsheet will be messed up if
#this script runs in different time zone from the original, and 
#standard time vs. daylight savings time should be handled here but it isn't.
#It's not going to throw the numbers off enough to make me want to fix it.
thistime=time.time()
now=time.localtime(thistime)

#top_level_url is the lockss server page where the latest numbers come from
top_level_url = "http://lockss.dartmouth.edu:8081/DaemonStatus"

#this chunk of code gets the page at top_level_url and digs out the numbers we want.
r = requests.get(top_level_url, auth=(lockssname, locksspassword))
#print r.text #debugging
#requestworked = re.match(".*Archival.*", r.text)
requestworked='<title>LOCKSS: Overview - Daemon Status</title>' in r.text
if not requestworked :
    #print "requestworked. got: \n" + r.text
    print "request failed. got: \n " + r.text
    exit()
    

if requestworked :
    pattern=re.compile('.*ArchivalUnitStatusTable\">(.*)Archival\sUnits\s\([\d]+\sinternal\),\s(.*)\snot\scollected,\s(.*)\sneed.*', re.MULTILINE|re.DOTALL)
    result=pattern.match(r.text)
    #print "result = " + result
    if result :
        total=result.group(1)
        notcollected=result.group(2)
        needrecrawl=result.group(3)
    else:
        print "Failed - " + top_level_url +" - " + r.text + "\n"
        exit()
else:
    print "couldn't get the lockss daemon page - check username and pword"
    exit()
#get logged in to Google Docs SpreadsheetsService
spr_client = gdata.spreadsheet.service.SpreadsheetsService()
spr_client.email = email
spr_client.password = password
spr_client.source = 'lockss update'
login = spr_client.ProgrammaticLogin()

#get the document specified in doc_name programattically
q = gdata.spreadsheet.service.DocumentQuery()
q['title'] = doc_name
q['title-exact'] = 'true'
sfeed = spr_client.GetSpreadsheetsFeed(query=q)
spreadsheet_id = sfeed.entry[0].id.text.rsplit('/',1)[1]
wfeed = spr_client.GetWorksheetsFeed(spreadsheet_id)
worksheet_id = wfeed.entry[0].id.text.rsplit('/',1)[1]


# Prepare the dictionary to write.
# I had a lot of trouble with column headers until I changed them all
# to lower-case letters only. 
lockssdict = {}
lockssdict['date'] =  str(now.tm_mon) + '/' + str(now.tm_mday) + '/' + str(now.tm_year)
lockssdict['time'] = str(now.tm_hour) + ':' + str(now.tm_min)
lockssdict['totalaus'] = total
lockssdict['notcollected'] = notcollected
lockssdict['needingrecrawl'] = needrecrawl

# push data to print lockssdict, spreadsheet_key, worksheet_id
entry = spr_client.InsertRow(lockssdict, spreadsheet_id, worksheet_id)
if not isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
  print "Insert row failed."
