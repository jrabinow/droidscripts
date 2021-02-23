#!/data/data/com.termux/files/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manually set mtimes on all pictures taken with camera (/sdcard/DCIM/Camera)

Necessary for AOSP gallery to display pictures in right order. To be run on the
phone itself (see rundroid)
"""

import logging
import os
import re

LOG = logging.getLogger()
LOG.setLevel("INFO")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(formatter)
LOG.addHandler(ch)


def walkdir(dirname, match_regex=None, ignore_regex=None, invert=False):
    for subdir, dirs, files in os.walk(dirname):
        for filename in files:
            if match_regex is not None:
                if invert ^ (not match_regex.search(filename) is not None):
                    continue
            elif ignore_regex is not None:
                if invert ^ (ignore_regex.search(filename) is not None):
                    continue
            filepath = os.path.join(subdir, filename)
            yield filepath, filename


def main():
    matching_file = r"(IMG|PANO|VID)_"

    matching_file_re = re.compile(matching_file)
    extract_date_re = re.compile(r"(IMG|PANO|VID)_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(\d{3})?(_(BURST\d\d)?\d)?(_HDR)?\.")

    for filepath, filename in walkdir("/storage/emulated/0/DCIM/Camera", match_regex=matching_file_re, invert=False):
        #print(filepath)
        match = extract_date_re.match(filename)
        if match:
            year = match.group(2)
            month = match.group(3)
            day = match.group(4)
            hour = match.group(5)
            minute = match.group(6)
            second = match.group(7)
            #print("YEAR = {}\nMONTH = {}\nDAY = {}\nHOUR = {}\nMINUTE = {}\nSECOND = {}".format(
            #    year, month, day, hour, minute, second
            #))
            date_str = "{}-{}-{} {}:{}:{}".format(year, month, day, hour, minute, second)
            ret = os.system("touch -m -d '{}' {}".format(date_str, filepath))
            if ret != 0:
                print("FAILED FOR FILE {}".format(filepath))
        else:
            print("invalid file {}".format(filepath))


if __name__ == "__main__":
    main()
