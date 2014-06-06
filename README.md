locksstracking

I was interested in how long it would take my local LOCKSS node to collect all the Archival Units that my institution
has selected.

My google docs spreadsheet has a bunch of formulas in it to calculate an average time to successfully collect the 
Archival Units that have been selected for collection.

This python script looks up the appropriate numbers on the lockss node's website, parses them, and dumps
them into the spreadsheet. I've been running the script daily via a cron job on my local machine.

Requirements:
I'm using Python 2.7 on a mac (and haven't tested this in any other environment). The script requires the 'requests'
python module and a few other pieces, listed in the early part of the script. The usernames and passwords required are
in a separate text file, credgapi.

TO-DO:

Find a way to update the formula cells in the spreadsheet. Right now I let the script put the numbers in, and then
I manually open the document once in a while and use command-D to fill the formulas down from the last filled in line.
It would be better to do this each time the sheet is updated with new numbers.

Replace password authentication with something else - OAuth2?

Build a set-up module that would ask the user for the relevant info - usernames, passwords, url's, when to run the
script, etc. The set-up module would then create the passwords text file, urls, etc, and install a cron job.

This software is available for anyone to use, copy, modify, and/or redistribute at will. Attribution would be
appreciated but is not required.

