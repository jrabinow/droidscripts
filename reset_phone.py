#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
convert servicefile xml to list of shell commands and run them
"""

import argparse
import logging
import os
import stat
import time
import xml.etree.ElementTree as ET
import sh

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
        "-d",
        "--debug",
        action="store_true",
        help="enable debug logging information",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="don't do anything, just print what would be done",
    )
    parser.add_argument(
        "--max-retries",
        default=3,
        type=int,
        help="retry the shell command NUM times in case of failure",
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
        assert fastboot("devices", dry_run=dry_run, timeout=5) != "", "no device found"


def ensure_servicefile_exists(servicefile):
    assert stat.S_ISREG(os.stat(servicefile).st_mode), "servicefile.xml doesn't exist"


def fastboot(*args, num_retries=3, timeout=None, dry_run=False):
    for i in range(num_retries):
        try:
            LOG.info(" ".join(args))
            if not dry_run:
                ret = sh.fastboot(*args, _timeout=timeout)
            return ret
        except sh.TimeoutException as e:
            LOG.warning("fastboot timeout: {}. try {}/{}".format(e, i, num_retries))
    LOG.fatal(
        "FASTBOOT FAILURE; max_retries = {} exceeded. Bailing now".format(num_retries)
    )
    raise sh.TimeoutException("max retries exceeded", full_cmd=" ".join(args))


def reboot_device(dry_run=False):
    LOG.info("rebooting; sleeping 20 sec")
    fastboot("reboot", "bootloader", timeout=20, dry_run=dry_run)
    if not dry_run:
        time.sleep(20)


def flash_device(
    src_rom_dir, preprocessing=None, postprocessing=None, retries=3, dry_run=False
):
    preprocessing = preprocessing or {}
    postprocessing = postprocessing or {}
    ensure_device_connected(dry_run)
    servicefile = "{}/servicefile.xml".format(src_rom_dir)
    ensure_servicefile_exists(servicefile)
    tree = ET.parse(servicefile)
    steps = tree.findall("./steps")
    assert len(steps) == 1, "more than 1 `steps` section found"
    steps = steps[0]

    def getvar(step):
        var = step.attrib["var"]
        fastboot("getvar", var, timeout=5, dry_run=dry_run)

    def oem(step):
        var = step.attrib["var"]
        fastboot("oem", var, timeout=5, dry_run=dry_run)

    def flash(step):
        filename = step.attrib["filename"]
        partition = step.attrib["partition"]
        filepath = os.path.join(src_rom_dir, filename)

        if filename in preprocessing:
            preprocessing[filename](dry_run)

        fastboot("flash", partition, filepath, dry_run=dry_run, timeout=60)

        if filename in postprocessing:
            postprocessing[filename](dry_run)

    def erase(step):
        partition = step.attrib["partition"]
        fastboot("erase", partition, dry_run=dry_run, timeout=20)

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

    # system partition is large; reboot to make sure we're starting with a
    # clean slate
    preprocessing = {
        "system.img": reboot_device,
        "system.img_sparsechunk.0": reboot_device,
    }

    postprocessing = {
        # reload bootloader after flashing
        "bootloader.img": reboot_device
    }

    flash_device(
        args.SRC_ROM_DIR,
        preprocessing=preprocessing,
        postprocessing=postprocessing,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
