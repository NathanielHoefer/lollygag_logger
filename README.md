# vl_logger
This is a tool specifically designed for formatting Valence logs for better legibility and debugging by allowing customized formatting. It is completely unobtrusive in the sense that it doesn't directly affect any of the artifacts or testing that is being produced. This is accomplished by capturing each log line as it is being printed to the console or read, and runs it through the formatter - affecting only the screen output of the logs, leaving all other aspects such as files intact. Because of this line-by-line formatting, a number of sources can be read from as explained below.

## Usage
**To begin a test and format the printed logs**, use the `-run` argument followed by the suite path. This tool utilizes the `vl run` command, so it must be installed and you must execute it from the same directory as if running that command instead. To stop the test, issue a keyboard interupt Ctrl-C just as you would normally.
```
Ex: python vl_logger.py -run <path.to.suite>
```
**To format and print logs from a file**, use the `-r` argument followed by the file path.
```
Ex: python vl_logger.py -r <file path>
```
**To format and print logs from a AT2 Task Step Instance**, use the `-at2` argument followed by the task instance step ID.
```
Ex: python vl_logger.py -at2 <step id>
```
### Other Features
The following features are available when using the `-r` or `-at2` arguments:

**Write output to file:** Instead of printing the formatted logs to the console, they will be written to the specified file including ACSII color additions with the `-w` argument.
```
Ex: python vl_logger.py -at2 <step id> -w <file path>
```
**List specific suite/test case/step:** To only print the logs found within a specific test header, us the `-l` argument. This includes anything that is found within that header. For example, if you wanted to print the logs found within 'Test Case 0: Starting Test...' then all of the associated steps will also be printed. Just keep in mind that the header description (the part in between all of the '-' or '=') needs to be copied exactly.
```
Ex: python vl_logger.py -r <file path> -l "<entire header description>"
```
**Find logs containing specific string:** To specify a string to look for, use the `-f` argument followed by the desired string, then only logs containing the specified string will be printed. If the string is visible after being formatted, then it will also be highlighted. 
```
Ex: python vl_logger.py -at2 <step id> -f "<string>"
```
*Note: Only the logs that are already set to be shown will be evaluated. As an example, if debug logs are set to be hidden, they will not be displayed even if they contain the specified search string. However, if the the field containing the string is hidden but the rest of the log line is set to print, then the log line will be printed - indicating a match.*


## Format Config File
The settings are accessed through the `.vl_logger.ini` file which is created on your first run of the logger. Currently, the customization is as follows found within the .ini file:
 - hide/view specific log types
 - hide/view specific log fields
 - condense fields
 - condense logs to a specified length or the console width
 - collapse dictionaries and lists
 - color the log type if displayed

By default, it is stored in your home directory, but you may specify another directory by using the `-ini` argument. If using the `-run` option,the .ini file can be updated at any point during the current test, and will reflect any changes on future logs. For example, if you decide that you wish to see debug logs, simply change the option within the format_config file and save it, and any further logs will include the debug logs.
*Note: The options listed are only what is currently offered. It will be expanded in future releases.*


## Installation
After downloading the repository, you must have at least Python 2.7 and the modules within the `requirements.txt` installed. To install the required modules, execute the following command:
```
pip install -r /path/to/requirements.txt
```

## Additional Info
To execute this tool without the initial `python` command from any directory, execute the following commands.
```
chmod u+x vl_logger.py
ln -s <explicit path to repo>/lollygag_logger/vl_logger.py ~/bin/vl_logger
```
Then you may execute the tool as follows:
```
Ex: vl_logger -at2 <step id> -f "<string>"
```
Do not use PDB when using this script, it will not output correctly.
If you find any bugs or have suggestions, feel free to contact me.
