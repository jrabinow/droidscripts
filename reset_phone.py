#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
convert servicefile xml to list of shell commands and run them
"""

from sh import fastboot

import argparse
import logging
import os
import stat
import time
import xml.etree.ElementTree as ET

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
        "--dry-run",
        action="store_true",
        help="don't do anything, just print what would be done",
    )
    parser.add_argument(
        "SRC_ROM_DIR",
        nargs="?",
        default=".",
        help="use this directory as source instead of default (current directory)",
    )
    return parser.parse_args()


def ensure_device_connected(dry_run=False):
    if dry_run:
        print("skipping check for device as dry-run mode")
    else:
        assert fastboot("devices") != "" , "no device found"


def ensure_servicefile_exists(servicefile):
    assert stat.S_ISREG(os.stat(servicefile).st_mode), "servicefile,xml doesn't exist"


def flash_device(src_rom_dir, dry_run=False):
    ensure_device_connected(dry_run)
    servicefile = "{}/servicefile.xml".format(src_rom_dir)
    ensure_servicefile_exists(servicefile)
    tree = ET.parse(servicefile)
    steps = tree.findall("./steps")
    assert len(steps) == 1, "more than 1 `steps` section found"
    steps = steps[0]

    def getvar(step):
        var = step.attrib["var"]
        cmd = "fastboot getvar {}".format(var)
        LOG.info(cmd)
        if not dry_run:
            fastboot("getvar", var)

    def oem(step):
        var = step.attrib["var"]
        cmd = "fastboot oem {}".format(var)
        LOG.info(cmd)
        if not dry_run:
            fastboot("oem", var)

    def flash(step):
        filename = step.attrib["filename"]
        partition = step.attrib["partition"]
        filepath = os.path.join(src_rom_dir, filename)
        cmd = "fastboot flash {} {}".format(partition, filepath)

        # system partition is large; reboot to make sure we're starting with a
        # clean slate
        if filename in ("system.img", "system.img_sparsechunk.0"):
            LOG.info("rebooting; sleeping 20 sec")
            LOG.info("fastboot reboot bootloader")
            if not dry_run:
                fastboot("reboot", "bootloader")
                time.sleep(20)

        LOG.info(cmd)
        if not dry_run:
            fastboot("flash", partition, filepath)

        # reload bootloader after flashing
        if filename in ("bootloader.img"):
            LOG.info("rebooting; sleeping 20 sec")
            LOG.info("fastboot reboot bootloader")
            if not dry_run:
                fastboot("reboot", "bootloader")
                time.sleep(20)

    def erase(step):
        partition = step.attrib["partition"]
        cmd = "fastboot erase {}".format(partition)
        LOG.info(cmd)
        if not dry_run:
            fastboot("erase", partition)

    operation_dispatch = {
        "getvar": getvar,
        "oem": oem,
        "flash": flash,
        "erase": erase,
    }

    for step in steps:
        op = step.attrib["operation"]
        operation_dispatch[op](step)


def main():
    args = parse_args()
    flash_device(args.SRC_ROM_DIR, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
