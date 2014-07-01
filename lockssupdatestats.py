#!/usr/bin/python

# lockssupdatestats.py
# gdata.spreadsheet.service uses an API to read and edit google documents.
# requests makes http requesting easier.

import re
import time
from sys import exit
# import configparser
import gdata.spreadsheet.service
import requests
import os


def main():
    # doc_name is used to find the right spreadsheet inside the user's google drive acct
    # credfile is the full path to the file that holds usernames and passwords
    # credgapi is a text file with these four values on separate lines:
    # email (user's gmail address)
    # password (gmail password)
    # lockssname
    #  locksspassword
    lockssdict = {}
    doc_name = 'lockss crawl stats'
    if os.isatty(sys.stdin.fileno()):
        # Debug mode.
        credfile = "../keys/credfile"
    else:
    # Cron mode.
        wd = os.getcwd()
        credfile = "{0}/keys/credfile".format(wd)
    try:
        creds = open(credfile, 'r')
    except IOError:
        print "Failed to open credential store at " + credfile + "\n"
        raise

    else:

        # If we opened the credentials properly, we can pull
        #each line into a variable, removing the "return" at the end of each.
        email = creds.readline().rstrip()
        password = creds.readline().rstrip()
        lockssname = creds.readline().rstrip()
        locksspassword = creds.readline().rstrip()
        creds.close()

    # next, check that we have something in each variable.

    if email == "" or password == "" or lockssname == "" or locksspassword == "":
        print "Failed to read one or more of the needed credentials from " + credfile + "\n"

    # Get current time. The LOCKSS calculations in the spreadsheet will be messed up if this script runs in a different
    # time zone from the original, and standard time vs. daylight savings time should be handled here but it isn't.
    # It's not going to throw the numbers off enough to make me want to fix it.

    thistime = time.time()
    now = time.localtime(thistime)

    daemonpage = "http://lockss2.dartmouth.edu:8081/DaemonStatus"  # lockss server page

    r = requests.get(daemonpage, auth=(lockssname, locksspassword))
    requestworked = '<title>LOCKSS: Overview - Daemon Status</title>' in r.text
    if not requestworked:
        print "request failed. got: \n " + r.text
        exit()

    else:
        # Use a regex to extract the numbers we need for our spreadsheet.
        pattern = re.compile(
            '.*ArchivalUnitStatusTable\">(.*)Archival\sUnits\s\([\d]+\sinternal\),\s(.*)\snot\scollected,\s(.*)'
            '\sneed.*', re.MULTILINE | re.DOTALL)

        # pattern2 = re.compile(
        #     '.*table=RepositorySpace\">[0-9\.]+\sdisks:\s[0-9\.]+TB\s\([0-9]+%%\sfull,\s([0-9\.]+)GB\sfree\),'
        #     '\s[0-9\.]+TB\s\([0-9]+%%\sfull,\s([0-9\.]+)GB\sfree\),\s[0-9\.]+TB\s\([0-9]+%%\sfull,\s([0-9\.]+)'
        #     'GB\sfree\)', re.MULTILINE | re.DOTALL)
        pattern2 = re.compile(
            '.*table=RepositorySpace\">[0-9\s]+disks:\s[0-9\.]+TB\s+\([0-9]+[%]\sfull,\s([0-9\.]+)GB\sfree\),'
            '\s[0-9\.]+TB\s\([0-9]+[%]\sfull,\s([0-9\.]+)GB\sfree\),\s[0-9\.]+TB\s\([0-9]+[%]\sfull,\s([0-9\.]+)GB'
            '\sfree\),\s[0-9\.]+TB\s\([0-9]+[%]\sfull,\s([0-9]+)', re.MULTILINE | re.DOTALL)
        result = pattern.match(r.text)
        result2 = pattern2.match(r.text)
        if result and result2:
            lockssdict['totalaus'] = result.group(1)
            lockssdict['notcollected'] = result.group(2)
            lockssdict['needingrecrawl'] = result.group(3)
            lockssdict['space1'] = result2.group(1)
            lockssdict['space2'] = result2.group(2)
            lockssdict['space3'] = result2.group(3)
            lockssdict['space4'] = result2.group(4)
        else:
            print "Failed - " + daemonpage + " - " + r.text + "\n"
            print "result = " + str(result) + "\n"
            print "result2 = " + str(result2) + "\n"
            exit()

    # get logged in to Google Docs SpreadsheetsService
    spr_client = gdata.spreadsheet.service.SpreadsheetsService()
    spr_client.email = email
    spr_client.password = password
    spr_client.source = 'lockss update'
    try:
        spr_client.ProgrammaticLogin()

    except IOError:
        print "login to Google Docs failed \n"
        raise

    else:
        # get the document specified in doc_name
        q = gdata.spreadsheet.service.DocumentQuery()
        q['title'] = doc_name
        q['title-exact'] = 'true'
        sfeed = spr_client.GetSpreadsheetsFeed(query=q)
        spreadsheet_id = sfeed.entry[0].id.text.rsplit('/', 1)[1]
        wfeed = spr_client.GetWorksheetsFeed(spreadsheet_id)
        worksheet_id = wfeed.entry[0].id.text.rsplit('/', 1)[1]

        # Prepare a dictionary of all the data we're going to write into the spreadsheet.
        lockssdict['date'] = str(now.tm_mon) + '/' + str(now.tm_mday) + '/' + str(now.tm_year)
        lockssdict['time'] = str(now.tm_hour) + ':' + str(now.tm_min)

        # write the data into the next available row in the spreadsheet.
        entry = spr_client.InsertRow(lockssdict, spreadsheet_id, worksheet_id)
        if not isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
            print "Insert row failed."


if __name__ == "__main__":
    main()