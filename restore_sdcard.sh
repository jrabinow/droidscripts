#!/usr/bin/env bash

set -e -u
set -o pipefail

# backup android sdcard, both personal and work profiles

function usage ()
{
    cat << EOF
Usage: $(basename "$0") [OPTION]...
Options: --help, -h: show this help dialog
         --dry-run: do not do anything - just show what would be done
EOF
}

function main ()
{
    local dry_run=""
    while getopts "h-:" opt; do
        case ${opt} in
            h)  # help message
                usage
                exit 0
                ;;
            -)
                case "${OPTARG}" in
                    help)
                        usage
                        exit 0
                        ;;
                    dry-run)
                        dry_run="--dry-run"
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
    [[ "${1:-}" == '--' ]] && shift

    # shellcheck disable=SC2154
    cd "${android}/storage/emulated/0"
    "${android}/droidscripts/adb-sync/adb-sync" . /storage/emulated/0/ --delete ${dry_run}
    cd "${android}/storage/emulated/10"
    remount_script=$(mktemp)
    # source: https://android.stackexchange.com/questions/221122/how-to-access-storage-emulated-10-multi-users-env-in-adb-shell-on-android-9
    cat > "${remount_script}" << EOF
umount /mnt/runtime/*/emulated; /system/bin/sdcard -u 1023 -g 1023 -m -w -G /data/media emulated
EOF
    chmod +x "${remount_script}"
    rundroid "${remount_script}"
    rm "${remount_script}"
    "${android}/droidscripts/adb-sync/adb-sync" . /storage/emulated/10/ --delete ${dry_run}
}

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
    main "$@"
fi
