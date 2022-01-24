#!/usr/bin/env bash

set -e -u -o pipefail

DEVICE=/dev/block/mmcblk0
FATPART="${DEVICE}p1"
EXT4PART="${DEVICE}p2"
LABEL=microsd_luks

cat << EOF
WARNING: this script is setup to format a block device. This means that all
data on this block device will be irrecoverably lost. Your phone may have
different block names - MAKE SURE YOUR BLOCK NAME IS THE RIGHT ONE OR YOU MAY
END UP WITH AN EXPENSIVE PAPERWEIGHT INSTEAD OF A PHONE.

IF YOU DO NOT UNDERSTAND THE ABOVE WARNING, THEN THIS SCRIPT IS NOT MEANT FOR
YOU. DO NOT RUN IT.

Current block device: ${DEVICE}

EOF

read -p "Enter YES at the prompt to continue, or anything else to abort: "

if [ "${REPLY}" != "YES" ]; then
    echo "Aborting"
    exit 1
fi

sudo sgdisk --zap-all "${DEVICE}"
sudo sgdisk --new=0:0:10M --typecode=0:0700 --gpttombr=1 "${DEVICE}"
# we use fdisk for partition 2 because sgdisk errors out for gawd knows what reason
cat << EOF
#fdisk is messed up and can't script properly, run the following:
sudo fdisk ${DEVICE}
    n       # create new partition
    p       # type primary
    2       # number 2
    20481   # start sector
            # use default and fill sdcard
    w       # write to disk
EOF

sudo fdisk ${DEVICE}
read -rp "Once you're done with fdisk, press ENTER to continue: "
sgdisk --android-dump "${FATPART}"
mkfs.exfat -n android "${FATPART}"
sudo mkfs.exfat -n android "${FATPART}"
blkid -c /dev/null -s TYPE -s UUID -s LABEL "${FATPART}"
#In case next command doesn't work: try sudo fsck.exfat -a /dev/sdd1 
sudo fsck.exfat -a "${FATPART}"

sudo cryptsetup luksFormat "${EXT4PART}"
sudo cryptsetup luksOpen "${EXT4PART}" "${LABEL}"
sudo mkfs.ext4 "/dev/mapper/${LABEL}"

sdcard_uuid="$(blkid "${EXT4PART}" -o export|grep '^UUID='|cut -d= -f2)"
TARGET="/mnt/media_rw/${sdcard_uuid}"
sudo mkdir -p "${TARGET}"
