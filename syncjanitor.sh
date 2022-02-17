#!/usr/bin/env -S bash

set -e -u
set -o pipefail

# delete expected files after syncthing sync
# run me on laptop

function usage()
{
    cat << EOF
Usage: ${0##*/}" [OPTION]...
Options: --help, -h: show this help dialog
EOF
}

function sync_janitor ()
{
    user="${1}"; shift
    basedir="${android}/storage/emulated/${user}/TRASH"
    whitelisted_deletions=(
        WhatsApp/Backups
        WhatsApp/Databases
        Documents/Media/Signal
        Documents/oandbackups
    )
    rmdir_p=(
        Documents/Media
        Documents
    )

    for i in "${whitelisted_deletions[@]}"; do
        rm -r "${basedir}/$i" 2>/dev/null || true
    done

    cd "${basedir}"
    for i in "${rmdir_p[@]}"; do
        rmdir -p "${i}" 2>/dev/null || true
    done

    rmdir "${basedir}"
}

function main()
{
    user=0

    while getopts "hu:-:" opt; do
        case ${opt} in
            h) # help message
                usage
                exit 0
                ;;
            u)
                user="${OPTARG}"
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

    sync_janitor "${user}"
}

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
    main "$@"
fi
