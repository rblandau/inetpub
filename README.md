# inetpub

## CheckNetPy project to monitor network: is it up and running?
This has been running in one form or another since 1994.  The new Python3 version is fully fleshed out and reasonably reliable.  

Intended application: use cron or similar to schedule this to run regularly.
The program executes once and exits.  

Requires an existing (and accessible) log file.  
The program records that it is running, with date and time stamp of the form 
YYYYMMDD_HHMMSS.  Any errors encountered are also logged.

The program pings a few nodes, DNS-translates a few names, and finally accesses a few web pages.  Feel free to change the lists of sites, names, and pages to be used to meet current needs and personal preferences.  





