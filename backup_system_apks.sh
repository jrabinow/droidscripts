#!/usr/bin/env bash
for app in $(pm list packages -f); do
    file=$(cut -d= -f1 <<< "${app//package://}")
    mkdir -p "./default_apps/$(dirname "$file")"
    cp -vp "${file}" "./default_apps/$(dirname "${file}")"
done
