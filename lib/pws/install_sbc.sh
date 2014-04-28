#!/bin/bash

ORIG_WD=`pwd`

SCRIPT_DIR=`dirname "$0"`
SRC_DIR=`readlink -fn "$SCRIPT_DIR/../.."`

echo ""
echo "Phidget Weather Station Installer"
echo "================================="
echo ""
echo "This script will set up a new instance of the Phidget Weather Station"
echo "on a PhidgetSBC computer (or similar Debian installation)."
echo ""
echo "Usage: $0 [install_dir]"
echo "  - If install_dir is omitted, then you will be prompted to enter"
echo "    an installation directory path."
echo ""
echo "All files from $SRC_DIR will be copied to the installation"
echo "directory. Then dependencies, such as binaries, and libraries"
echo "will be installed (if missing). Finally, initd and watchdog scripts"
echo "will be installed and configured (optional)."

install_binaries()
{
    for i in $@; do
        bPath=`which "$i"`
        if [ -f "$bPath" ]; then
            echo "Binary $i already installed at $bPath"
        else
            echo "Installing $i..."
            apt-get install "$i"
        fi
    done
}

install_packages()
{
    for i in $@; do
        installed=`dpkg -s "$i" 2> /dev/null | grep -i ^version`
        if [ -n "$installed" ]; then
            echo "Package $i already installed ($installed)"
        else
            echo "Installing package $i..."
            apt-get install "$i"
        fi
    done
}


####
# Create install directory
####

DEFAULT_DIR="/usr/userapps/pws"

if [ -n "$1" ]; then

    DIR=$1
    echo ""
    echo "Are you sure you want to install the PWS application in '$DIR'? [Y/n]"
    read ANSWER
    if [ "$ANSWER" != "Y" ]; then
        exit 0
    fi

else

    echo ""
    echo "Please enter the install path for the PWS application (press enter for default '$DEFAULT_DIR'):"
    read DIR
    if [ -z "$DIR" ]; then
        DIR=$DEFAULT_DIR
    fi

fi

if [ -d "$DIR" ]; then
    echo "Directory '$DIR' already exists. Please move it aside first."
    exit 1
fi

mkdir -p "$DIR"

if [ $? -ne 0 ]; then
    echo "Could not make directory '$DIR'. Do you have permission?"
    exit 1
fi

####
# Copy files from source directory to install directory
####

echo "Copying contents of '$SRC_DIR' to '$DIR'..."
cd "$SRC_DIR"
cp -av * "$DIR"

####
# Install required binaries and packages
####

binaries=()
install_binaries ${binaries[@]}

packages=("coreutils" "python" "python-mysqldb" "gzip")
install_packages ${packages[@]}


####
# Install Phidget Python libraries
####

phidgets_mod=`python -c "from imp import *; print find_module('Phidgets')" 2> /dev/null`

if [ $? -eq 0 ]; then

    echo "Phidgets Python module appears to be installed."
    echo "- $phidgets_mod"

else

    echo ""
    echo "Do you want to install the Phidget Python libraries (wget and unzip will be installed too)? [Y/n]"
    read ANSWER

    if [ "$ANSWER" = "Y" ]; then

        # Install wget and unzip if needed
        packages=("wget" "unzip")
        install_packages ${packages[@]}

        # Download the Phidgets Python libray...
        cd /tmp
        wget http://www.phidgets.com/downloads/libraries/PhidgetsPython.zip

        # ...unzip it...
        unzip PhidgetsPython.zip -d /tmp

        # ...run the installer script...
        cd PhidgetsPython
        python setup.py install

        # ...and clean-up the temp files.
        cd /tmp
        rm PhidgetsPython.zip
        rm -rf PhidgetsPython

        cd "$ORIG_WD"
        
    else

        echo ""
        echo "You can install the Phidget Python libraries manually using the instructions at"
        echo "http://www.phidgets.com/docs/OS_-_Phidget_SBC#Install_Phidget_Python_Method_1:_Use_a_USB_Key"
        echo ""
        echo "Press 'enter' to continue..."
        read

    fi

fi

echo "Patching /usr/local/lib/python2.7/dist-packages/Phidgets/Phidget.py"
sed -i -e "s/'linux'/'linux2'/" /usr/local/lib/python2.7/dist-packages/Phidgets/Phidget.py


####
# Setup the initd scripts
####

$DIR/lib/initd/_setup.sh

####
# Setup the watchdog scripts
####

$DIR/lib/watchdog/_setup.sh

####
# Finished
####

cd "$ORIG_WD"
echo ""
echo "Done installing."

exit 0
