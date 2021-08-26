#!/usr/bin/env bash

set -e -u
set -o pipefail

# `rundroid backup_appdata.sh --all` will auto-backup all backups in "${APPS}" defined below
# `rundroid backup_appdata.sh --user 10 com.Slack` will backup just slack appdata for user 10

readonly APPS=(
    #org.mozilla.firefox
    com.shazam.android
)

function usage ()
{
    cat << EOF
Usage: ${0##*/} [OPTION]... [PACKAGE]
Options: -h, --help: show this help dialog
         -u USER, --user USER: 0 (personal) or 10 (work profile)
         --all: restore appdata for all available apps
EOF
}

function backup_appdata ()
{
    local app="${1}"; shift
    local backupdir="${1}"; shift
    local datadir
    local app_dir
    local archive_file

    cd "/data/user/${user}/"

    datadir="/data/user/${user}"
    app_dir="${datadir}/${app}"
    archive_file="${backupdir}/${app}.txz"

    if [ -d "${app_dir}" ]; then
        echo "BACKING UP APPDATA FOR ${app}"
        tar --exclude cache -Jcf "${archive_file}" "${app_dir}"
        rm -rf "${app_dir}/cache" "${app_dir}/code_cache"
    else
        echo "appdir ${app_dir} fail"
    fi
}

function backup_all_appdata ()
{
    backupdir="${1}"; shift

    for app in "${APPS[@]}"; do
        backup_appdata "${app}" "${backupdir}"
    done
}

function main ()
{
    local user=0
    local enable_all=false

    while getopts "hu-:" opt; do
        case ${opt} in
            h)  # help message
                usage
                exit 0
                ;;
            u)
                user="${!OPTIND}"
                OPTIND=$(( OPTIND + 1 ))
                ;;
            -)
                case "${OPTARG}" in
                    help)
                        usage
                        exit 0
                        ;;
                    user)
                        user="${!OPTIND}"
                        OPTIND=$(( OPTIND + 1 ))
                        ;;
                    all)
                        enable_all=true
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

    if [ "$#" -ge 1 ]; then
        while [ $# -ge 1 ]; do
            app="${1}"; shift
            backup_appdata "${app}" "/storage/emulated/${user}/oandbackups"
        done
    elif "${enable_all}"; then
        backup_all_appdata "/storage/emulated/${user}/oandbackups"
    else
        # shellcheck disable=SC2016
        printf 'must pass in `--all` flag or specify individual package names\n' >&2
    fi
}

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
    main "$@"
fi
