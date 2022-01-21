#!/usr/bin/env bash

set -e -u
set -o pipefail

# `rundroid restore_appdata.sh --all` will auto-restore all backups in /storage/emulated/$user/$BACKUPDIR
# `rundroid restore_appdata.sh --user 10 com.Slack` will restore just slack appdata for user 10

BACKUPDIR="Documents/oandbackups/"


function usage ()
{
    cat << EOF
Usage: ${0##*/} [OPTION]... [PACKAGE]
BACKUPDIR=$BACKUPDIR

Options: -h, --help: show this help dialog
         -u USER, --user USER: 0 (personal) or 10 (work profile)
         --all: restore appdata for all available apps
EOF
}

function restore_appdata ()
{
    local user="${1}"; shift
    local app="${1}"; shift
    local app_name
    local datadir
    local app_dir
    local archive_file
    local appuser
    local appgroup

    cd "/data/user/${user}/"

    app_name="${app##*/}"
    datadir="/data/user/${user}"
    app_dir="${datadir}/${app_name}"
    archive_file="${app}/data.tar.gz"

    if [ -d "${app_dir}" ] && [ -r "${archive_file}" ]; then
        echo "RESTORING APPDATA FOR ${app_dir} from ${archive_file}"
        pkg_uid="$(pm list packages -U --user "${user}"|grep "${app_name}"|cut -d: -f3)"
        appuser="$(stat -c "%U" "${app_dir}" || "${pkg_uid}")"
        appgroup="$(stat -c "%G" "${app_dir}" || "${pkg_uid}")"
        rm -r "${app_dir:?}"/* || true
        tar -C "${app_dir}" -zxf "${archive_file}" || true
        cd "${app_dir}"
        rm -rf "./cache" "./code_cache"
        chown -R "${appuser}:${appgroup}" "./"
        restorecon -R "${app_dir}"
    else
        [ -d "${app_dir}" ] || echo "appdir ${app_dir} fail"
        [ -r "${archive_file}" ] || echo "archive ${archive_file} fail"
    fi
}

function restore_all_appdata ()
{
    user="${1}"; shift
    backupdir="${1}"; shift

    for app in "${backupdir}"/*; do
        if [ "${app##*/}" != "oandbackup.log" ]; then
            restore_appdata "${user}" "${app}"
        fi
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
            restore_appdata "${user}" "/storage/emulated/${user}/${BACKUPDIR}/${app}"
        done
    elif "${enable_all}"; then
        restore_all_appdata "${user}" "/storage/emulated/${user}/${BACKUPDIR}"
    else
        # shellcheck disable=SC2016
        printf 'must pass in `--all` flag or specify individual package names\n' >&2
    fi
}

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
    main "$@"
fi
