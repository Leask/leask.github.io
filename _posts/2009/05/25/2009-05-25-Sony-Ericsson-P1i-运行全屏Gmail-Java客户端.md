---
layout: post
title: Sony Ericsson P1i 运行全屏Gmail Java客户端
author: Leask
date: '2009-05-25 06:06:28 +0800'
---
入手P1i已经一小段时间了，用得算顺手，摄像头比预想的好。遗憾的是键盘稍微偏小（可能是我的手比较大）。  

但是遇到一个问题，直接上线安装的Gmail Java客户端在最新版本系统（R10A）中不能全屏。  

于是Google了一下，发现修改gmail.jad后再安装就能解决。  

遗憾的是网上修改的jad都是中文版本的Gmail客户端，因此我特意做了这个文件，能够在你的手上安装英文版本的全屏Gmail。  

使用的时候把下面代码保存成gmail.jad文件，用这个文件传到手机引导上网安装Gmail  

Java客户端，你将得到一个全屏英文版本的Gmail Java客户端了。  

注意，如果你需要其他的语言，把倒数第三行的"EN_US"修改成你的国家语言代码就OK，例如中文为"ZH_CN"。  

剩下的大家执行探索吧。  

  

MIDlet-1: Gmail, GmailIcon.png, com.google.mail.ui.midp.GoogleMailMidlet  

MIDlet-Jar-URL: [http://m.google.com/app/v2.0.6/L1/gmail-g.jar  

MIDlet-Jar-Size](http://m.google.com/app/v2.0.6/L1/gmail-g.jar
MIDlet-Jar-Size): 262627  

MIDlet-Name: Gmail  

MIDlet-Permissions: javax.microedition.io.Connector.http,  

javax.microedition.io.Connector.https  

MIDlet-Icon: GmailIcon.png  

MIDlet-Version: 2.0.6  

MIDlet-Vendor: Google  

RequestBackgroundSupported: false  

PlatformID: Generic-Advanced MIDP2  

BackKey: -9991  

SelectKey: -9994  

MaxFlashSize: 200000  

ConversationListBlockSize: 20  

MailRefreshEnabled: true  

UseNativeMenus: false  

UseNativeTextButtons: false  

MailNoteEnabled: false  

DefaultMailDomain: [gmail.com](http://gmail.com)  

RightSoftKey: -7  

MailNotificationEnabled: true  

MenuKey: -9995  

ReverseSoftkeys: true  

MicroEdition-Profile: MIDP-2.0  

MailMultipleAccountsEnabled: true  

TalkKey: -10  

UseNativeCommands: false  

ClearKey: -8  

LeftSoftKey: -6  

DistributionChannel: gorganic  

MicroEdition-Configuration: CLDC-1.0  

DownloadLocale: EN_US  

MIDlet-Install-Notify:  

[http://m.google.com/app/gmail.install?signed=false&dc=gorganic&deviceId=Generic;Advanced%20MIDP2&dc=gorganic&ver=v2.0.6](http://m.google.com/app/gmail.install?signed=false&dc=gorganic&deviceId=Generic;Advanced MIDP2&dc=gorganic&ver=v2.0.6)
