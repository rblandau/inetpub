#!/bin/sh
# copylogextract.sh
#                           RBLandau 20200730

# Make a copy of the interesting part of the checknet log file 
#  on the file server.  
# Windows does not like to run as services scripts that are not
#  on the system's hard disks.  So the real, long log file ends
#  up on the system disk.  Put the last few thousand lines of it
#  on the file server where everyone can see it.  
# 
# Three CLI args, all with sensible defaults if absent.
#  - $1 = max number of log file extract files to keep. Default=4.
#  - $2 = location, in Cygwin syntax, of the giant log file that
#         is constantly updated.
#         Example: /cygdrive/d/Inetpub/Scripts/somegiantlogfile.log
#  - $3 = directory into which to place the extract file, again
#         in Cygwin syntax.  


# How many copies of the log tail file shall we keep?
if [ -z "$1" ]
then
    nmaxfiles=4
else
    nmaxfiles=$1 
fi

# Where is the real main log file?
if [ -z "$2" ]
then
    loginputfile=/cygdrive/d/Inetpub/Scripts/checknetpy.log
else
    loginputfile=$2
fi

# Where do the tail extracts go on the file server?
if [ -z "$3" ]
then
    logoutputdir=/cygdrive/s/Landau/Python/dev/inetpub
else
    logoutputdir=$3
fi

# Tail extract files under what name?  (with timestamp appended)
logoutputname="checknetpy_tailextract"

now=$(date +%Y%m%d_%H%M%S)

# Use private log file for all output from this script.  
# Do this, I think, because redirection gets a little iffy 
#  if you're down too many levels of process from the root.  
privlog=./copyextractPRIVATE.log

# Test that we can see the intended output directory.  
if [ ! -d ${logoutputdir} ]
then
    echo "GACK - $now cannot see output dir $logoutputdir" >> $privlog
fi

# Don't leave more than some number of copies of the extract files
#  in the destination directory.  
while true
    do
    nf=$(ls $logoutputdir/${logoutputname}*.log | wc -l)
    if [ $nf -ge $nmaxfiles ] 
    then
        for ff in $(ls $logoutputdir/${logoutputname}*.log)
        do 
            echo "$now Deleting old file  $ff" >>$privlog
            rm -f $ff
            break
        done
    else
        break
    fi
done

#tail -10000 ./goodold.log > $logoutputdir/${logoutputname}_$now.log  # testing
tail -10000 $loginputfile > $logoutputdir/${logoutputname}_$now.log
echo "$now New log extract in $logoutputdir/${logoutputname}_$now.log" >>$privlog


#END
