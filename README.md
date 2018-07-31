# vlogger
This is a tool specifically designed for formatting Valence logs for better legibility and debugging by allowing customized formatting. It is completely unobtrusive in the sense that it doesn't directly affect any of the artifacts or testing that is being produced. This is accomplished by capturing each log line as it is being printed to the console or read, and runs it through the formatter - affecting only the screen output of the logs, leaving all other aspects such as files intact. Because of this line-by-line formatting, a number of sources can be read from as explained below.

## Usage

### Formatting

`vlogger` is capable of formatting VL logs in a number of ways and allows for configuration.
The configuration is explained in detail below. 

**Display Specified Log Types**

There are a number of log types such as `DEBUG`, `ERROR`, `WARNING`, etc., each displaying certain information.
Often, there are log types that list unnecessary information for triage, so providing a way for filtering those logs speed up the process. 
By default, only `DEBUG` logs are filtered.

**Display Specified Log Fields**

The majority of VL log lines follow a similar pattern, each with the same fields such as `Date`, `Time`, etc.
Just as with the log types, certain fields can convolute the triage process, so log fields can be filtered.

**Color**

The addition of color can greatly improve the visual processing of logs. 
The following items are colored when the option is selected in the `.ini` configuration file.
* Type field in standard VL log lines.
* Headers that identify Suites, Test cases, Steps and other general sections.
* Key traceback information
* API requests and responses when specified via argument
* Test summary
    
**Log Line Length**

Frequently, a single log line extends past the console width, wrapping many times - leaving the screen cluttered.
By default, each standard log line is condensed to the length of the console. 
This ensures that each standard log line doesn't wrap. 
If the log is not in the standard pattern, then it will not be condensed.
Also, certain fields are shorted by default to display the most important information.

**Test Summary**

Since the VL log summary information tends to be somewhat vague, a test summary is appended by default.
This summary describes all headers (Suites, Test Cases, etc.) found in the log source, 
and displays their runtime, status (Passed, Failed, Passed with Errors) and concise exceptions.

### Log Sources

**Execute local VL run (Not Currently Available)** 

Use the `-run` argument followed by the suite path. This tool utilizes the `vl run` command, so it must be installed and you must execute it from the same directory as if running that command instead. To stop the test, issue a keyboard interupt Ctrl-C just as you would normally.

```
python vlogger.py <path.to.suite>
    Ex: python vlogger.py TsTest
```

**Local Log file**

Enter the filepath to a specific log file ending in `.log`. 

```
python vlogger.py <file path to .log file>
    Ex: python vlogger.py ~/logs/test.log
```

**AT2 Task Step Instance**

Enter the task instance step ID of the desired AT2 task instance.

*__Note__ - the AT2 information must be provided in the configuration file.*

```
python vlogger.py <step id>
    Ex: python vlogger.py 123456
```
### Other Features

**Specify Test Case and Step** 

A specific test case or step can be passed to print only logs found in them.
The specified logs are first parsed from the original log file and stored in a new file found in `tc_logs/`.
If `tc_logs/` doesn't exist, it will be created. 

```
python vlogger.py <log_source> -t (testcase_name|testcase_num)[:step_num]
    Ex: python vlogger test.log -t TcTesting
    Ex: python vlogger test.log -t TcTesting:1
    Ex: python vlogger test.log -t 2
    Ex: python vlogger test.log -t 2:1
```

**Format API Calls** 

Since API calls can convolute logs, they are not formatted by default. 
However, there are cases where clearly seeing the API requests and responses will allow for better triage.
By using the `-a` argument, the API calls will be clearly displayed.

```
python vlogger.py <log_source> -a
    Ex: python vlogger test.log -a
```
**Output Formatted Logs to a File** 

The formatted logs can be redirected to a file rather than STDOUT. 
Specify a filepath where the logs are to be stored. 

```
python vlogger.py <log_source> -o <filepath>
    Ex: python vlogger test.log -o test_formatted.log
```

### Format Config File

The configuration settings are accessed through the `.vlogger.ini` file which is created on your first run of the logger. 
Currently, the customization is as follows found within the .ini file:
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
