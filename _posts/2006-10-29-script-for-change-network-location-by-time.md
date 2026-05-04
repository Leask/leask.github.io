---
layout: post
title: Script for Change Network Location by time
author: Leask
date: '2006-10-29 18:57:50 +0800'
categories:
- Computers and Internet
---
我们学校的网络是PPPoE加网卡MAC地址验证，早上8点开网，晚上11点断网。  

由于断网后需要用iChat和另外一个Mac用户通讯，而iChat的Bonjour协议无法通过路由器，登陆iChat前需要删除网络设置中的Router选项。  

而且本人有用Google Notifier自动检查邮件的习惯，于是也需要在开网的时候自动启动Google Notifier，断网的时候自动关闭。  

于是打算用Apple Script结合iCal的自动执行功能解决这个问题。  

经过构思写下以下的程序，很幸运地，调试通过了。  

  

if hours of (current date) > 7 and hours of (current date) < 24 then  

 tell application "Finder"  

 activate  

 end tell  

 tell application "System Events"  

 click menu item "SCNU_ZCC_2#4008_Online" of menu "Location" of menu item "Location" of menu "Apple" of menu bar 1 of   
process "Finder"  

 end tell  

 tell application "Google Notifier"  

 activate  

 end tell  

else  

 tell application "Finder"  

 activate  

 end tell  

 tell application "System Events"  

 click menu item "SCNU_ZCC_2#4008_Offline" of menu "Location" of menu item "Location" of menu "Apple" of menu bar 1 of   
process "Finder"  

 end tell  

 tell application "Google Notifier"  

 quit  

 end tell  

end if  

  

其实Apple Script的编写很简单，不需要额外的学习，功能却很强大，通过应用程序类库调用，可是实现很多很有趣的功能。  

希望可以抛砖引玉给大家一点灵感吧。  

  

程序下载：  

  

[![](http://www.box.net/lite/image/787v5aons8.png)](http://www.box.net/lite/787v5aons8)
