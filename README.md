# vl_logger
This is a tool specifically designed for formatting Valence logs for better legibility and debugging by allowing customized formatting. It is completely unobtrusive in the sense that it doesn't directly effect any of the artifacts or testing that is being produced. This is accomplished by capturing each log line as it is being printed to the console or read, and runs it through the formatter - affecting only the screen output of the logs, leaving all other aspects such as files intact. Because of this line-by-line formatting, a number of sources can be read from as explained below. When reading from a file or an AT2 Task Step Instance, you may also write the output to a file, list a specific test case step, as well as print and highlight logs with a specified string. 

# Usage
To begin a test and format the printed logs, use the `-run` argument followed by the suite path. This tool utilizes the `vl run` command, so it must be installed and you must execute it from the same directory as if running that command instead. To stop the test, issue a keyboard interupt Ctrl-C just as you would normally.
```
Ex: python vl_logger -run <path.to.suite?
```
To format and print logs from a file, use the `-r` argument followed by the file path.
```
Ex: python vl_logger -r <log file>
```
To format and print logs from a AT2 Task Step Instance, use the `-at2` argument followed by the task instance step ID.
```
python vl_logger -at2 <step id>
```

# Format Config File
The settings are accessed through the `.vl_logger.ini` file which is created on your first run of the logger. Currently, the customization is as follows found within the .ini file:
 - hide/view specific log types
 - hide/view
 - specific log fields
 - condense fields
 - condense logs to a specified length or the console width
 - collapse dictionaries and lists
 - color the log type if displayed

By default, it is stored in your home directory, but you may specify another directory by using the `-ini` argument. If using the `-run` option,the .ini file can be updated at any point during the current test, and will reflect any changes on future logs. For example, if you decide that you wish to see debug logs, simply change the option within the format_config file and save it, and any further logs will include the debug logs.
*Note: The options listed are only what is currently offered. It will be expanded in future releases.

You may also execute the script directly by issuing the following commands
```
chmod u+x lollygag_logger.py
ln -s /home/trinidad/projects/lollygag_logger/lollygag_logger.py ~/bin/lollygag_logger
```

# Notes
This is a preliminary script and is only available for convenience -- so expect small bugs. 
Do not use PDB when using this script, it will not output correctly.
