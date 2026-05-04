---
layout: post
title: "[Mac小技巧]使用AutoHotkey编程解决Mac上安装Windows系统的键盘布局问题"
author: Leask
date: '2009-05-25 05:48:24 +0800'
---
使用MacBook已有一段时间，和以前用的PowerPC CPU的Mac不同，MacBook的Intel  

CPU能够很方便地运行Windows系统，完全的兼容也正式我选择升级iBook到MacBook的原因，因为我的工作需要IIS，需要IE。  

可是问题也随之而来。  

MacBook上的键盘根本不适合使用Windows系统。  

  

例如经典的ALT和COMMAND键位置问题，PRINTSCREEN键问题，如果你和我一样，使用单键的Apple Mouse，你还会遇到鼠标邮件的问题。  

然而，如果你像我一样，经常要使用BootCamp在Mac和Windows之间两边跑，还会遇到热键由"Command+某按键"变成"Control+某按键"的问题，习惯了使用如Photoshop等很依赖热键操作的软件，就会变得很不方便。  

于是我想到了使用AutoHotkey，编写脚本解决这些问题，让我们的MacBook更好用，更顺手。  

  

首先在Windows系统下载并安装AutoHotkey：[http://www.autohotkey.com/](http://www.autohotkey.com/)  

然后用记事本创建以下脚本（保存为以".ahk"为后缀的文本文件）：  

  

LWin::RControl  

  

<^LButton::RButton  

  

RAlt::Del  

  

!d::Send,#d  

  

>^q::Send,!{F4}  

  

>^+1::PrintScreen  

  

>^+2::!PrintScreen  

  

当然，你也可以使用AutoHotkey把脚本转换为一个exe可执行文件并放在启动文件夹中，让系统启动的时候自动加载脚本。  

上面的脚本到底有什么用呢，通过上面的脚本设置，Windows系统上的系统热键基本上都变成Mac OS X上的系统热键了：  

  

具体如下：  

  

LWin::RControl ==>>  

设置左边的Command键为右Control键，例如按下Command+C相当于按下Control+C。（为什么不用左Control，聪明的你看完后面的程序就明白了）  

  

<^LButton::RButton ===>>  

设置左Control+Click为右键单击，如果你在Mac使用单键鼠标，那么一定已经很习惯这个操作了，把它弄到Windows上，一样方便。  

  

RAlt::Del ===>> 设置右Alt为Del健，很简单，因为Mac键盘没有Del键。  

  

!d::Send,#d ===>> 设置Alt+D为显示桌面，你会发现，这个键位刚刚就是Windows键盘的键位，绝吧！？  

  

>^q::Send,!{F4} ===>> 设置Command+q为Alt+F4，这个不用解释了。  

  

>^+1::PrintScreen ===>> 设置Command+Shift+1为截取整个屏幕的截屏健，符合Mac用户的习惯。  

  

>^+2::!PrintScreen ===>> 设置Command+Shift+2为截取当前程序画面的截屏健，符合Mac用户的习惯。  

  

好了，我就写到这里，只求抛砖引玉，有自己热键习惯的朋友可以自行完善。
