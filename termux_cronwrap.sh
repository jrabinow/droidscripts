#!/system/bin/sh

# place me in /data and chmod +x me!
# for use with https://github.com/Faerbit/android-crond to run termux scripts in a termux environment

su -c "HOME=/data/data/com.termux/files/home PATH=/data/data/com.termux/files/home/bin:/data/data/com.termux/files/usr/local/bin:/data/data/com.termux/files/usr/bin:/bin:/sbin /data/data/com.termux/files/usr/bin/bash << EOF
${@}
EOF
"
