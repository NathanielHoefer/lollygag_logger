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

The configuration settings are accessed through the `.vlogger.ini` file which is created in the home directory.
If `~/.vlogger.ini` doesn't exist, it will be created using the default values specified below. 

*Note - To pull logs from AT2, all of the fields under `AT2 LOG CREDENTIALS` must be manually entered.*
 
##### AT2 LOG CREDENTIALS
Credentials used for pulling logs from AT2 task instances
* `username`: AT2 Username
* `password`: AT2 Password
* `fetch-task-instance-script-path`: Path to `fetch-task-instance-step-log.py` script.

##### DISPLAY LOG TYPES
Log types marked as `True` will display, otherwise the log lines will be filtered.
* `debug` [False]: Standard VL Debug logs 
* `info` [True]: Standard VL Info logs 
* `notice` [True]: Standard VL Notice logs 
* `warning` [True]: Standard VL Warning logs 
* `error` [True]: Standard VL Error logs 
* `critical` [True]: Standard VL Critical logs 
* `traceback` [True]: Any traceback following conventional format
* `other` [True]: Select logs not covered by the above types
* `step_headers` [True]: Headers that describe a VL test step
* `test_case_headers` [True]: Headers that describe a VL test case
* `suite_headers` [True]: Headers that describe a VL suite
* `general_headers` [True]: Any other headers found within the logs.

##### DISPLAY FIELDS
Fields within logs that fit the standard VL log pattern, will be filtered if not marked `True`.
* `date` [False]
* `time` [True]
* `type` [True]
* `source` [True]
* `thread` [False]
* `details` [True]

##### GENERAL
Any other configuration options available to modify.
* `use_defaults` [False]: Override all options specified in the config file, and use the defaults.
* `use_unformatted` [False]: Override all options specified in the config file, and don't use any formatting.
* `use_colors` [True]: Color escape characters will be added per description above.
* `format_api` [False]: Format API requests and responses found in `DEBUG` logs.
* `condense_line` [True]: Truncate standard VL logs to the console length or a max length specified below.
* `shorten_fields` [True]: Truncate the contents of the `Source` and `Thread` fields to 30 characters.
* `display_summary` [True]: Append a summary of the logs.
* `use_console_len` [True]: If `True`, the console length will override the max line length for the standard VL logs.
* `max_line_len` [200]: Specifies the max line length of standard VL logs if `use_console_len` is set to `False`.

*Note: The options listed are only what is currently offered. It will be expanded in future releases.*

## Installation
After downloading the repository, you must have at least Python 2.7 and the modules within the `requirements.txt` installed. To install the required modules, execute the following command:
```
pip install -r /path/to/requirements.txt


1. Download the repository:
    git clone --recurse-submodules git@github.com:NathanielHoefer/lollygag_logger.git
    

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
