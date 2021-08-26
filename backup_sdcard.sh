#!/usr/bin/env bash

set -e -u
set -o pipefail

# backup android sdcard, both personal and work profiles

function usage ()
{
    cat << EOF
Usage: ${0##*/} [OPTION]...
Options: --help, -h: show this help dialog
         --dry-run: do not do anything - just show what would be done
         --user, -u : backup
EOF
}

function android_users ()
{
    adb shell pm list users|awk 'match($0, /^\s*UserInfo\{([0-9]+):.*:[0-9]+}/, arr) {print arr[1]}'
}

function remount_readable ()
{
    dry_run="${1}"; shift
    cmd="umount /mnt/runtime/*/emulated; /system/bin/sdcard -u 1023 -g 1023 -m -w -G /data/media emulated"
    remount_script=$(mktemp)
    # source: https://android.stackexchange.com/questions/221122/how-to-access-storage-emulated-10-multi-users-env-in-adb-shell-on-android-9
    cat > "${remount_script}" << EOF
${cmd}
EOF
    chmod +x "${remount_script}"
    rundroid "${remount_script}"
    rm "${remount_script}"
}

function backup_sdcard_for_user ()
{
    user="${1}"; shift
    cd "${user}"
    # shellcheck disable=SC2086
    adb-sync --reverse -t "/storage/emulated/${user}/" . --delete ${dry_run} --exclude Android,osmand
}

function main ()
{
    local dry_run=""
    # shellcheck disable=SC2154
    local basedir="${android}/storage/emulated"
    local user=""

    while getopts "u:h-:" opt; do
        case ${opt} in
            h)  # help message
                usage
                exit 0
                ;;
            -)
                case "${OPTARG}" in
                    basedir)
                        basedir="${!OPTIND}"
                        OPTIND=$((OPTIND+1))
                        ;;
                    help)
                        usage
                        exit 0
                        ;;
                    dry-run)
                        dry_run="--dry-run"
                        ;;
                    user)
                        user="${!OPTIND}"
                        OPTIND=$((OPTIND + 1))
                        ;;
                    *)
                        printf 'Unknown option, exiting now\n' >&2
                        exit 1
                        ;;
                esac
                ;;
            u)
                echo "${OPTARG}"
                exit 0
                ;;
            ?)
                printf 'Unknown option, exiting now\n' >&2
                exit 1
                ;;
        esac
    done
    shift $((OPTIND - 1))
    [[ "${1:-}" == '--' ]] && shift
    basedir="$(realpath "${basedir}")"

    remount_readable "$dry_run"

    if [ -n "${user}" ]; then
        cd "${basedir}"
        backup_sdcard_for_user "${user}"
    else
        for u in $(android_users); do
            cd "${basedir}"
            backup_sdcard_for_user "${u}"
        done
    fi
}

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
    main "$@"
fi
