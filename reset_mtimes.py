#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manually set mtimes on all pictures taken with camera (/sdcard/DCIM/Camera)

Necessary for AOSP gallery to display pictures in right order. To be run on the
phone itself (see rundroid)
"""

from datetime import datetime, timedelta

import argparse
import logging
import os
import re

import exiftool

LOG = logging.getLogger()
LOG.setLevel("INFO")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(formatter)
LOG.addHandler(ch)
filech = logging.FileHandler("traceback.txt")
filech.setFormatter(formatter)
LOG.addHandler(filech)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="enable debug logging information",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="don't actually perform any operations, just print out `touch` commands",
    )
    parser.add_argument(
        "--no-exif",
        action="store_true",
        help="don't attempt to use exif data (typically good for screenshots)"
    )
    parser.add_argument(
        "DIR",
        nargs="+",
        default=["/storage/emulated/0/DCIM/Camera"],
        help="directory(ies) on which to run script",
    )
    args = parser.parse_args()
    if args.debug:
        LOG.setLevel(logging.DEBUG)
    return args


def gen_filename_date_extraction_regex(matching_file_prefix):
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
    extension = r"\.[a-z0-9]{3}"
    extract_date = (
            f"^{matching_file_prefix}{year}-?{month}-?{day}(?:_|-){hour}-?{minute}-?"
        f"{second}{millisec_opt}{timestamp_opt}{burst_suffix_opt}{suffix_opt}"
        f"{extension}$"
    )
    extract_date_re = re.compile(extract_date)
    return extract_date_re


MATCHING_FILE_PREFIX = r"(IMG|PANO|TINYPLANET_PANO|VID|Screenshot)_"
MATCHING_FILE_PREFIX_RE = re.compile(MATCHING_FILE_PREFIX)
EXTRACT_DATE_RE = gen_filename_date_extraction_regex(MATCHING_FILE_PREFIX)


class MediaFile:
    def __init__(self, filepath, filename=None):
        self.filepath = filepath
        self.filename = filename or os.path.basename(filepath)

    def set_mtime(self, create_time, dry_run=False):
        cmd = "touch -m -d '{}' {}".format(create_time, self.filepath)
        if dry_run:
            print(cmd)
        else:
            ret = os.system(cmd)
            if ret != 0:
                LOG.warning("FAILED FOR FILE {}".format(self.filepath))

    def calc_create_time(self, use_exifdata=True):
        try:
            self.filename_date = extract_filename_date(self.filename)
        except ValueError as e:
            LOG.warning(f"{self.filepath}: {e}")
            self.filename_date = datetime.min
        if use_exifdata:
            try:
                self.exifdata_date = extract_exifdata_date(self.filepath)
            except (KeyError, ValueError) as e:
                LOG.warning(f"{self.filepath}: {e}")
                self.exifdata_date = datetime.min
            else:
                if self.exifdata_date is not None:
                    if self.filename.startswith("VID_"):
                        # videos are sometimes messed up and use UTC in metadata. Go figure.
                        # Allow 6min (360sec) diff for encoding, absolute difference of 12h = 43200s
                        tdelta = abs(self.exifdata_date - self.filename_date)
                        assert self.filename.startswith("VID_") and tdelta.seconds < 43200 \
                                and (tdelta.seconds % 1800 <= 360 or tdelta.seconds % 1800 >= 1440), \
                            f"{self.filename}: filename_date {self.filename_date} and " \
                            f"exifdata_date {self.exifdata_date} differ by " \
                            f"{tdelta.seconds} seconds: % 1800 == {tdelta.seconds % 1800}"
                    else:
                        assert self.filename_date - self.exifdata_date < timedelta(seconds=5), (
                            f"{self.filepath} exif data ({self.exifdata_date}) and filename "
                            f"dating attempts ({self.filename_date}) don't match!"
                        )


def extract_filename_date(filename):
    match = EXTRACT_DATE_RE.match(filename)
    if match:
        year = int(match.group(2))
        month = int(match.group(3))
        day = int(match.group(4))
        hour = int(match.group(5))
        minute = int(match.group(6))
        second = int(match.group(7))
        LOG.debug(
            "YEAR = {}\nMONTH = {}\nDAY = {}\nHOUR = {}\nMINUTE = {}\nSECOND = {}".format(
                year, month, day, hour, minute, second
            )
        )
        return datetime(
            year=year, month=month, day=day, hour=hour, minute=minute, second=second
        )
    else:
        raise ValueError("could not extract datetime from filename %s" % filename)


def extract_exifdata_date(filepath):
    with exiftool.ExifTool() as et:
        exifdata = et.get_metadata(filepath)
    match exifdata["File:MIMEType"]:
        case "video/mp4":
            key = "QuickTime:CreateDate"
        case "image/png" | "image/jpeg":
            possible_keys = [
                "EXIF:CreateDate",
                "EXIF:DateTimeOriginal",
                "EXIF:ModifyDate",
            ]
            bug = False
            for k in possible_keys:
                if k in exifdata:
                    # for some weird reason, I have ~50 pics whose CreateDate == 2002-12-08 12:00:00.
                    # Pics were created between 2013-08-26 23:46:41 and 2013-12-03 21:03:43 on Nexus S
                    # Workaround by using DateTimeOriginal exif data key
                    if exifdata[k] != "2002:12:08 12:00:00":
                        key = k
                        break
                    else:
                        bug = True
            else:
                if bug:
                    return None
                raise KeyError(f"no relevant key for file {filepath}")

    LOG.info(filepath)
    return datetime.strptime(exifdata[key], "%Y:%m:%d %H:%M:%S")


def walkdir(dirname, match_regex=None, ignore_regex=None):
    for subdir, _, files in os.walk(dirname):
        for filename in files:
            if match_regex is not None and match_regex.search(filename) is None:
                continue
            if ignore_regex is not None and ignore_regex.search(filename) is not None:
                continue
            filepath = os.path.join(subdir, filename)
            yield filepath, filename


def reset_mtimes(dirname, use_exifdata, dry_run=False):
    for filepath, filename in walkdir(dirname, match_regex=MATCHING_FILE_PREFIX_RE):
        mediafile = MediaFile(filepath, filename)
        try:
            mediafile.calc_create_time(use_exifdata=use_exifdata)
        except AssertionError as e:
            LOG.error(e)
            breakpoint
        mediafile.set_mtime(mediafile.filename_date, dry_run)


def main():
    args = parse_args()

    for dirname in args.DIR:
        reset_mtimes(dirname, not args.no_exif, args.dry_run)


if __name__ == "__main__":
    main()
