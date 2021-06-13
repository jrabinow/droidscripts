#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Write_description_and_usage_example_here
"""

import argparse
import logging
import os
import re
import shutil

LOG = logging.getLogger()
LOG.setLevel("INFO")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(formatter)
LOG.addHandler(ch)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="enable debug logging information",
    )
    parser.add_argument(
        "dir1",
        #type=int,
        help="WRITE_SOMETHING_SMART_HERE"
    )
    parser.add_argument(
        "dir2",
        #type=int,
        help="WRITE_SOMETHING_SMART_HERE"
    )
    return parser.parse_args()

def assemble_extraction_regex():
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
    extract_date = f".*{year}{month}{day}_{hour}{minute}{second}{millisec_opt}{timestamp_opt}{burst_suffix_opt}{suffix_opt}\."
    extract_date_re = re.compile(extract_date)
    return extract_date_re

def assemble_date_regex(year, month, day):
    return re.compile(".*{}{}{}.*".format(year, month, day))


def find_similar_times(filename, otherfiles, dir2):
    extract_date_re = assemble_extraction_regex()
    match = extract_date_re.match(filename)
    if not match:
        raise Exception("wtf no match")
    year = match.group(1)
    month = match.group(2)
    day = match.group(3)
    hour = match.group(4)
    minute = match.group(5)
    second = match.group(6)

    datere = assemble_date_regex(year, month, day)
    candidates = ["{}{}".format(dir2, img) for img in otherfiles if datere.search(img) is not None]
    return candidates


def actionmenu(m, dir2_contents, dir2, dir1):
    ret = 0
    print("\u001b[2J")
    while ret < 4:
        print("restore {}?".format(m))
        ret = input("""Action:
1 - view candidate files
2 - open candidate files
3 - reopen
4 - figure it out later
5 - restore file
6 - add to deletion queue
7 - exit
Your choice [1-6]: """)
        try:
            ret = int(ret)
        except ValueError as e:
            ret = 0
        if ret == 1:
            print("\u001b[2J")
            candidates = find_similar_times(m, dir2_contents, dir2)
            if len(candidates) == 0:
                print("no candidates found for {}!".format(m))
            print("similar time range")
            for c in candidates:
                print(c)
        elif ret == 2:
            print("\u001b[2J")
            candidates = find_similar_times(m, dir2_contents, dir2)
            os.system("open -F {}".format(" ".join(candidates)))
        elif ret == 3:
            print("\u001b[2J")
            os.system("open -F {}{}".format(dir1, m, dir2))
    return ret


def main():
    args = parse_args()
    dir1_contents = set(os.listdir(args.dir1))
    dir2_contents = set(os.listdir(args.dir2))
    missing = sorted(dir1_contents - dir2_contents)

    deleteme = []
    restoreme = []

    for m in missing:
        if m == ".DS_Store":
            os.unlink("{}{}".format(args.dir1, m))
            continue
        os.system("open -F {}{}".format(args.dir1, m, args.dir2))
        ret = actionmenu(m, dir2_contents, args.dir2, args.dir1)
        if ret == 4:
            continue
        elif ret == 5:
            print("ADDING FILE {} TO RESTORE QUEUE".format(m))
            restoreme.append(m)
        elif ret == 6:
            print("ADDING FILE {} TO DELETE QUEUE".format(m))
            deleteme.append(m)
        elif ret == 7:
            break
        os.system("pkill Preview VLC")


    if len(restoreme) > 0:
        print("restore queue: {}".format(restoreme))
        ret = input("proceed with restore? [y/N] ")
        if ret.lower() == "y":
            for dm in restoreme:
                filepath = "{}{}".format(args.dir1, dm)
                print("restoring {} to {}{}".format(filepath, args.dir2, dm))
                shutil.move(filepath, args.dir2)
        else:
            print("restore aborted")

    if len(deleteme) > 0:
        print("deletion queue: {}".format(deleteme))
        ret = input("proceed with deletion? [y/N] ")
        if ret.lower() == "y":
            for dm in deleteme:
                filepath = "{}{}".format(args.dir1, dm)
                os.unlink(filepath)
        else:
            print("deletion aborted")



if __name__ == "__main__":
    main()
