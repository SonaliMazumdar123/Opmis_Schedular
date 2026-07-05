# OPMIS Scheduler

Automates daily execution of `D2D_Delete_Old_Log.ksh` on `prodlnx0123` using a Python wrapper script and cron.

## Files
- `opmis_cleanup_monitor.py` - Runs the cleanup script, monitors the generated `store_log_cleanup_*.log`, waits up to 30 minutes, and retries if validation fails.
- `D2D_Delete_Old_Log.ksh` - Existing cleanup script from server (included here for reference/source control).

## Schedule
- Daily at **10:00 PM IST**
- Equivalent to **5:30 PM BST**

## Recommended validation
The wrapper validates success by checking:
1. A new `store_log_cleanup_*.log` file is created
2. The file contains `Completed at:`
3. The file size is within the expected range (default `45-46 KB`)

## Deploy on `prodlnx0123`
Place these files under:

```text
/export/home/users/bmadmin/bmadmin/Automation_Testing/
```

## Manual test
```bash
cd /export/home/users/bmadmin/bmadmin/Automation_Testing
python opmis_cleanup_monitor.py
```

## Cron
If server timezone is IST:
```cron
0 22 * * * /usr/bin/python /export/home/users/bmadmin/bmadmin/Automation_Testing/opmis_cleanup_monitor.py >> /export/home/users/bmadmin/bmadmin/Automation_Testing/log/opmis_cleanup_cron.log 2>&1
```

## Notes
- Verify path consistency between `/export/home/users/...` and `/users/...` inside `D2D_Delete_Old_Log.ksh` before deploying.
- If daily log size varies over time, widen the validation threshold in the Python script.
