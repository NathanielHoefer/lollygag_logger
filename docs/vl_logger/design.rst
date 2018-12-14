Lollygag Logger
===============

Purpose
*******

Provide a library for parsing a myriad of log files to be output in a myriad of ways.

Requirements
************

* Include interface to specify how to parse log files into individual fields.
* Extract single or multi-line logs to be parsed.
* Allow customized formatting when printing to STDOUT including:

    * Filter by log type
    * Filter by field
    * Color by field
    * Specify log print length
* Allow for custom range of logs

Usage
*****

Define a log:
    formatting = [
        Condense(max_len)
        Colorize(color)
    ]

    fields = [
        DatetimeLogField(pattern="%Y-%m-%d %H:%M:%S.%f", show_date=False)
        TypeLogField()
        LogField(tag="source", pattern="\[.*:.*\]", filter=False)
    ]
    std_log = Log(tag="std", fields=fields, format=)

    log_line = "log...."
    log = std_log.get_instance(log_line)

Classes
*******

Format()
    apply(token)

    Condense(max_len)
    Colorize(color)
    Filter(pattern)

LogField(tag, pattern, filter, format)
    get_instance(token)
    pattern()
    to_str()

    DatetimeLogField(pattern, filter_date, filter_time, format)
    TypeLogField(filter_types)

Log(tag, fields, format)
    get_instance(token)
    to_str()



