#!/system/bin/sh

# https://blog.ja-ke.tech/2020/04/04/android-luks2.html
PARTITION=/dev/block/mmcblk0p2
LABEL=microsd_luks

set -e -u
set -o pipefail

function usage()
{
    cat << EOF
Usage: ${0##*/}" [OPTION]...
Options: --help, -h: show this help dialog
EOF
}

function main()
{
    while getopts "h-:" opt; do
        case ${opt} in
            h) # help message
                usage
                exit 0
                ;;
            -)
                case "${OPTARG}" in
                    help)
                        usage
                        exit 0
                        ;;
                    *)
                        printf 'Unknown option, exiting now\n' >&2
                        exit 1
                        ;;
                esac
                ;;
            ?)
                printf 'Unknown option, exiting now\n' >&2
                exit 1
                ;;
        esac
    done
    shift $((OPTIND - 1))
    [[ ${1:-} == '--' ]] && shift

    if [ "$(id -u)" != 0 ]; then
        echo "Aborting: This script needs root." >&2
        exit 1
    fi

    sdcard_uuid="$(blkid "${PARTITION}" -o export|grep '^UUID='|cut -d= -f2)"
    TARGET="/mnt/media_rw/${sdcard_uuid}"

    # Try to open container
    if [ ! -b "/dev/mapper/${LABEL}" ]; then
        cryptsetup luksOpen "${PARTITION}" "${LABEL}"
    else
        echo "Container already open, skipped cryptsetup..." >&2
    fi

    # Mounting
    nsenter -t 1 -m sh << EOF
# https://blog.ja-ke.tech/2020/04/04/android-luks2.html

mkdir -p $TARGET
mountpoint "${TARGET}" >/dev/null || mount -t ext4 -o nosuid,nodev,noatime "/dev/mapper/${LABEL}" "${TARGET}"

EOF
    am broadcast -a android.intent.action.MEDIA_MOUNTED -d "file:///storage/emulated/0"
}

main "$@"
