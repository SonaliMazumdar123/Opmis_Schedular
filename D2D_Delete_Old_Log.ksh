#!/bin/ksh

set -o pipefail
 
NUMBER_OF_DAYS_TO_LIVE=7

REMOTE_ARCHIVE_PATH="/var/opt/d2d/apache-tomcat-9.0.0.M26/logs/archive"

StoresList="/users/bmadmin/bmadmin/Automation_Testing/D2DOldLogStore.txt"
 
TODAY=$(date '+%Y%m%d-%H%M%S')

OUTPUT_LOG="/users/bmadmin/bmadmin/Automation_Testing/log/store_log_cleanup_${TODAY}.log"
 
echo "------------------------------------------------------------" >> "$OUTPUT_LOG"

echo "Store Log Cleanup Run on: $(date)" >> "$OUTPUT_LOG"

echo "Days to purge: ${NUMBER_OF_DAYS_TO_LIVE}" >> "$OUTPUT_LOG"

echo "------------------------------------------------------------" >> "$OUTPUT_LOG"

echo "Store,Reachable,SSH,OldLogsDeleted,Count" >> "$OUTPUT_LOG"
 
exec 3< "$StoresList"
 
while IFS= read -r store <&3; do

    store=$(echo "$store" | tr -d '\r')

    HOST="${store}lx3001.bc.jsplc.net"
 
    echo "------------------------------------------------------------" >> "$OUTPUT_LOG"

    echo "Checking Store: ${store} (${HOST})" >> "$OUTPUT_LOG"
 
    # PING CHECK

    if ! ping -c 1 -w 10 "$HOST" >/dev/null 2>&1; then

        echo "${store},NO,NO,NO,0" >> "$OUTPUT_LOG"

        continue

    fi
 
    # SSH CONNECTIVITY

    if ! ssh -o BatchMode=yes -o StrictHostKeyChecking=no d2dusr@"$HOST" "echo OK" >/dev/null 2>&1; then

        echo "${store},YES,NO,NO,0" >> "$OUTPUT_LOG"

        continue

    fi
 
    # SINGLE SSH SESSION FOR PERFORMANCE

    RESULT=$(ssh -o BatchMode=yes d2dusr@"$HOST" "

        # Count files

        OLD_COUNT=\$(find ${REMOTE_ARCHIVE_PATH} -type f -name '*.log*' -mtime +${NUMBER_OF_DAYS_TO_LIVE} 2>/dev/null | wc -l)

        echo \"COUNT:\$OLD_COUNT\"

        if [ \"\$OLD_COUNT\" -gt 0 ]; then

            echo \"Deleting files...\"

            find ${REMOTE_ARCHIVE_PATH} -type f -name '*.log*' -mtime +${NUMBER_OF_DAYS_TO_LIVE} -print -delete

        fi

    ")
 
    OLD_COUNT=$(echo "$RESULT" | awk -F: '/COUNT/ {print $2}' | tr -cd '0-9')

    OLD_COUNT=${OLD_COUNT:-0}
 
    if [ "$OLD_COUNT" -gt 0 ]; then

        echo "${store},YES,YES,YES,${OLD_COUNT}" >> "$OUTPUT_LOG"

        echo "Deleted ${OLD_COUNT} old log files." >> "$OUTPUT_LOG"

    else

        echo "${store},YES,YES,NO,0" >> "$OUTPUT_LOG"

    fi
 
done
 
exec 3<&-
 
echo "" >> "$OUTPUT_LOG"

echo "Completed at: $(date)" >> "$OUTPUT_LOG"
 
exit 0
