#!/usr/bin/env python

"""Easy vlogger install."""

import sys
import os
import subprocess

install_path = os.path.abspath(__file__)
vlogger_dir = os.path.dirname(install_path)

def is_venv():
    """Return True if working in virtual environment."""
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))


def install_requirements():
    """Install all packages found in req"""
    req_path = os.path.join([vlogger_dir, "requirements.txt"])
    subprocess.call(["pip", "install", "-r", req_path])


def pull_submodules():
    """Initializes and pulls any submodules if not already pulled."""
    subprocess.call(["git", "submodule", "init"])
    subprocess.call(["git", "submodule", "update", "--recursive", "--remote"])


def create_soft_link():
    """Add soft link of vlogger.py to ~/bin/vlogger."""
    vlogger_path = os.path.join(vlogger_dir, "vlogger.py")
    dir_path = os.path.expanduser("~")
    bin_dir = os.path.join(dir_path, "bin")
    if not os.path.exists(bin_dir):
        os.mkdir(bin_dir)

    soft_path = os.path.join(bin_dir, "vlogger")
    command = ["ln", "-s", vlogger_path, soft_path]
    cmd_str = " ".join(command)
    print "Creating soft link for easy execution: %s" % cmd_str
    subprocess.call(["ln", "-s", vlogger_path, soft_path])

    export_path = ["PATH=%s:$PATH" % bin_dir, "&&", "export", "PATH"]
    print "Exporting PATH: %s" % export_path
    subprocess.call(["PATH=%s:$PATH" % bin_dir, "&&", "export", "PATH"])


if __name__ == '__main__':
    pass
