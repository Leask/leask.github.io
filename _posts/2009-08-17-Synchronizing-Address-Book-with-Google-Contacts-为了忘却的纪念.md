---
layout: post
title: Synchronizing Address Book with Google Contacts // 为了忘却的纪念
author: Leask
date: '2009-08-17 05:51:47 +0800'
---
// 以下Script的作者是Riobard Zhan，作用是能够让Apple的Address Book实现与Google Contacts实现同步，而不仅仅是当iPod touch或者iPhone连接iTunes的时候同步。  
// 不过仅仅是在使用10.5.x的时候，你需要这个脚本，如果是10.6的话，Address Book和Google Contacts已经能自动同步了，当然，还包括iCal和Goolge Calendar。  
// 贴上来仅仅是为了忘却的纪念吧，使用Snow Leopard已经好几天了，不知道10A342是不是GM，也不知道GM和Retail Version会不会有差异，我只知道距离上一个版本，10A342已经把几乎所有的Bug都修正了，系统能够作为日常工作和使用的系统了。除了VMware的鼠标捕捉还有一点点不流畅。不过影响不大。  
// 不过每次告别上一代的Mac OS，我都会伤感一下子，感叹时光又一去不返了。

![Screen shot 2009-08-17 at 1.18.44 PM](/public/2010/09/screenshot2009-08-17at1.png?w=245 "Screen shot 2009-08-17 at 1.18.44 PM")

好了，如果你还在用10.5，又和我一样，喜欢Apple和Google，那么，下面的脚本适合你：

------------------------- gconsync.sh ---------------------------

#!/bin/bash

#############################################################################  
# Synchronizing Address Book with Google Contacts  
#  
# Author: Riobard Zhan  
# Email: me@riobard.com  
# Web: [http://riobard.com](http://riobard.com)  
# Version: 0.1  
#  
# This script will modify your system to synchronize your Address Book with   
# Google Contacts without needing an iPhone/iPod. The synchronization is done   
# periodically in the background using `launchd`.   
#  
# WARNING: I WILL NOT BE RESPONSABLE FOR ANY DATA LOSS OR DAMAGES CAUSED BY   
# THIS SCRIPT. USE AT YOUR OWN RISK!  
#############################################################################

# location of the gconsync command  
GCONSYNC=/System/Library/PrivateFrameworks/GoogleContactSync.framework/Resources/gconsync

# trick OS X to think there is an iPod attached

echo "{ Devices = { red-herring = { 'Family ID' = 10001; }; }; }" > ~/Library/Preferences/com.apple.iPod.plist

# enable Address Book synchronization with Google  
echo  
echo Now open "Address Book" and click "Preferences" in the menu. Check "Synchronize with Google" box. It will ask for your Google account and password.   
echo  
read -p "Did you check the box and enter your Google account and password? (Yes/No): " answer  
if [[ "$answer" != [Yy]* ]]; then  
 echo Bye.  
 exit  
fi

# start initial sync  
echo  
echo Initial synchronization started, please wait ...   
$GCONSYNC --sync gconclid

echo Initial synchronization done. You may open Address Book and your Gmail Contacts page to check the result.

# enable perodic sync  
echo  
echo How often do you want the synchronization to happen periodically?

while true; do  
 read -p "Enter a number in seconds [Default: 300]: " INTERVAL  
 if [[ $INTERVAL == "" ]]; then  
 INTERVAL=300  
 break  
 elif [[ $INTERVAL =~ ^[0-9]+$ ]]; then  
 break  
 else  
 echo Invalid number!  
 fi  
done

# create launchd job file  
cd ~/Library/LaunchAgents/  
echo "xml version="1.0" encoding="UTF-8"?  
http://www.apple.com/DTDs/PropertyList-1.0.dtd">  

  
 Label  
 com.google.contacts.sync.addressbook  
 ProgramArguments  

 $GCONSYNC  
 --sync  
 gconclid  
 --syncmode  
 fast  

 StartInterval  
 $INTERVAL  

" > com.google.contacts.sync.addressbook.plist

# load the job  
launchctl load com.google.contacts.sync.addressbook.plist

echo Done.
