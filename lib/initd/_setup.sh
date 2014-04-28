#!/bin/bash

if [ ! -d "/etc/init.d" ]; then
    echo "ERROR: $0 will install init scripts into /etc/init.d on Linux systems that use the initd startup system."
    echo "ERROR: /etc/init.d is not accessible and may not be available on this operating system."
    exit 1
fi

ORIG_WD=`pwd`

SCRIPT_DIR=`dirname "$0"`
DIR=`readlink -fn "$SCRIPT_DIR/../.."`

####
# Modify directory paths in init scripts and link in /etc/init.d
####

daemons=("pws_main" "pws_display")
for i in ${daemons[@]}; do

    file="$DIR/lib/initd/$i.sh"
    link="/etc/init.d/$i"

    if [ -f $file ]; then

        # Update DIR path in daemon script
        echo "Updating 'DIR=' in '$file'..."
        sed -i "s:^DIR=.*$:DIR=$DIR:" "$file"

        # Ask user if they want to install this script
        echo ""
        echo "Do you want to install the init script '$file'? [Y/n]"
        read ANSWER

        if [ "$ANSWER" = "Y" ]; then

            # Link daemon script in /etc/init.d
            echo "Linking '$file' to '$link'..."
            rm -f $link
            ln -s "$file" "$link"

            # Ask user if they want install init script into rc startup directories
            echo ""
            echo "Do you want to enable the init script '$link' to run at startup? [Y/n]"
            read ANSWER
            cmd="/usr/sbin/update-rc.d $i defaults"

            if [ "$ANSWER" = "Y" ]; then
                # Install the rc scripts
                echo `$cmd`
                for r in `ls /etc/rc?.d/*$i*`; do
                    echo "$r"
                done
            else
                # Remove any rc scripts that may be linked already
                echo `update-rc.d -f $i remove`
                echo ""
                echo "You may enable the startup script later with '$cmd'"
                echo ""
                echo "Press 'enter' to continue..."
                read
            fi

        fi

    else
        echo "WARNING: Daemon init script '$file' not found."
    fi
        
done


exit 0
