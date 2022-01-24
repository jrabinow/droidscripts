# droidscripts

Collection of random scripts for use with android phones.  

- [backup\_restore](backup_restore): backup and restore scripts
- [microsd](microsd): micro-sd setup for use with [cronenborg](https://github.com/jrabinow/homedir-scripts/blob/main/platform_specific/android/cronenborg)
- [thirdparty](thirdparty): code I didn't write
- [bootdroid](bootdroid): wrapper around `fastboot boot path/to/boot/partition.img`
- [merge\_backup\_helper.py](merge_backup_helper.py): one-off script I wrote for merging 2 backups one time and that I'm keeping for future reference
- [reset\_mtimes.py](reset_mtimes.py): use exifdata to set mtime for proper ordering of pictures on android
- [rundroid](rundroid): run the bash script of your choice in your phone's termux environment
- [stock\_flash.py](stock_flash.py): reset phone to stock using factory image downloaded from phone vendor's website
- [termux\_cronwrap.sh](termux_cronwrap.sh): place script in `/data`, `chmod +x` and run cronscripts in your termux env using [crond](https://f-droid.org/en/packages/it.faerb.crond/)

This code works but it was designed around my personal needs first and foremost. That means there aren't many safety railings. If you mess your phone up, it's your own fault.  
Consider yourself warned.  
  
I'm happy to accept code contributions or help out with getting things setup though.
