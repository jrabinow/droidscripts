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


def assemble_extraction_regex(matching_file_prefix):
    year = r"(\d{4})"
    month = r"(\d{2})"
    day = r"(\d{2})"
    hour = r"(\d{2})"
    minute = r"(\d{2})"
    second = r"(\d{2})"
    millisec_opt = r"(\d{3})?"
    timestamp_opt = r"(_\d{13})?"
    burst_suffix_opt = r"(_(BURST\d\d)?\d)?"
    suffix_opt = r"(_(HDR|COVER(_TOP)?|TOP))?"
    extract_date = f"{matching_file_prefix}{year}{month}{day}_{hour}{minute}{second}{millisec_opt}{timestamp_opt}{burst_suffix_opt}{suffix_opt}\."
    extract_date_re = re.compile(extract_date)
    return extract_date_re


def main():
    matching_file_prefix = r"(IMG|PANO|TINYPLANET_PANO|VID)_"
    matching_file_prefix_re = re.compile(matching_file_prefix)
    extract_date_re = assemble_extraction_regex(matching_file_prefix)

    for filepath, filename in walkdir("/storage/C358-0D11/DCIM/Camera", match_regex=matching_file_prefix_re, invert=False):
        LOG.debug(filepath)
        match = extract_date_re.match(filename)
        if match:
            year = match.group(2)
            month = match.group(3)
            day = match.group(4)
            hour = match.group(5)
            minute = match.group(6)
            second = match.group(7)
            LOG.debug("YEAR = {}\nMONTH = {}\nDAY = {}\nHOUR = {}\nMINUTE = {}\nSECOND = {}".format(
                year, month, day, hour, minute, second
            ))
            date_str = "{}-{}-{} {}:{}:{}".format(year, month, day, hour, minute, second)
            ret = os.system("touch -m -d '{}' {}".format(date_str, filepath))
            if ret != 0:
                print("FAILED FOR FILE {}".format(filepath))
        else:
            if not os.path.isdir(filepath):
                print("invalid file {}".format(filepath))


if __name__ == "__main__":
    main()
