#!/bin/sh
# copylog_start.sh
#                           RBLandau 20200802

now=$(date +%Y%m%d_%H%M%S)

bash repeatthis.sh "copylogextract.sh"  900 


#END
