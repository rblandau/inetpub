#!/bin/sh
# repeatthis.sh

# Execute the command given again and again every so often.
# 
# $1 = The shell command to execute repeatedly.  
#       REMEMBER to quote the command appropriately to preserve blanks
#       and to control globbing of wildcards.  
# $2 = How often to execute it, in seconds.  (E.g., 15 minutes = 900 seconds.)
# $3 = Max number of times to repeat the command.  0 => infinite, forever.  


if [ -z "$1" ]
then
    echo "Usage: $0 <shell command to execute> [<repeat time in seconds> [<maxrepeats>]]"
    exit 1
fi

timeconst="$2"
if [ -z "$2" ]
then
    timeconst = 900s    # 15 minutes
fi

maxtimes=0
if [ -n "$3" ]
then
    maxtimes=$3
fi

times=$maxtimes
while [ $maxtimes -eq 0 -o $times -gt 0 ]
do
    ($1)
    sleep "${timeconst}"
    times=$(expr $times - 1)
done

#END
