# lollygag_logger
This application is used to format the logs for better legibility and debugging. This current iteration is a very rough prototype that can be used to format Valence logs from either a log file or directly from the output of the `vl run` command. This script only affects the screen output of the logs, leaving all other aspects such as files intact.

# Usage
To format a log file, use the `-f` argument followed by the desired log file to be formatted. 
```
python lollygag_logger.py -f <log file>
Ex: python lollygag_logger.py -f test.log
```
To format the `vl run` output, execute the script within the same directory as you would if using the `vl run` command. Use the `-vl` argument followed by the suite path.
```
python lollygag_logger.py -vl <suite path>
Ex: python lollygag_logger.py -vl tests.suites_refresh.clones_snapshots_rainyday.suites.TsClonesSnapshotsRainyDaySuite
```
You may also execute the script directly by issuing the following commands
```
chmod u+x lollygag_logger.py
ln -s /home/trinidad/projects/lollygag_logger/lollygag_logger.py ~/bin/lollygag_logger
```

# Format Config File
If using the log file option, then a format_config file will be created in the same directory of the log file. This file contains various formatting options that allow you to specify how the output is to print to the screen. 
*Note: The options listed are only what is currently offered. It will be expanded in future releases.

If using the `vl run` option, then a format_config file will be created in the current working directory. This file can be updated at any point during the current test, and will reflect any changes on future logs. For example, if you decide that you wish to see debug logs, simply change the option within the format_config file and save it, and any further logs will include the debug logs.

# Notes
This is a preliminary script and is only available for convenience -- so expect small bugs. 
Do not use PDB when using this script, it will not output correctly.
