#!/bin/bash

function bat()
{
    for x in "$@"; do
        type=$(file -bi "$(readlink -f "${x}")")
        case ${type} in
        "application/x-bzip2"|"application/x-bzip2; charset=binary")
            bzcat "${x}"
            ;;
        "application/x-gzip"|"application/x-gzip; charset=binary")
            zcat "${x}"
            ;;
        *)
            cat "${x}"
            ;;
        esac
    done
}

bat "$@"

