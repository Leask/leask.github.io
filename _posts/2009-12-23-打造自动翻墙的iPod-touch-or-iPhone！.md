---
layout: post
title: "打造自动翻墙的iPod touch or iPhone！"
author: Leask
date: '2009-12-23 16:58:14 +0800'
comments:
- id: 361
  author: Leask
  author_email: ''
  author_url: ''
  date: '2009-12-29 17:01:32 +0800'
  date_gmt: '2009-12-29 17:01:32 +0800'
  content: "看清楚啦！我写了，用pac文件，倒数第5行。jjgod看文章要认真呀。"
- id: 362
  author: jiang
  author_email: ''
  author_url: ''
  date: '2009-12-29 03:51:29 +0800'
  date_gmt: '2009-12-29 03:51:29 +0800'
  content: "你还得改代理服务器吧，没写这个步骤怎么翻。"
---
最近天朝越来越“墙大”了，Twitter最后一组IP地址也已经耗尽。  
不知道大家有没有和我一样，有在移动设备上翻墙的需要。  
由于iPhone OS基于完整的UNIX，那么想象的空间就很大了，ssh -D直接跑在iPhone OS上已经不是什么新鲜事情，但是ssh的链接有一点脆弱，碰上网络不稳定的时候还真的挺郁闷的。  
既然Desktop UNIX上有autossh（实现ssh断线或者无响应的时候自动重新发起连接，注意如果想实现自动身份验证，你需要上传你的公匙【方法自行Google，十分简单】。），那么是不是iPhone OS也能编译一个对应的autossh呢？打开xcode，正打算对autossh的代码开刀。突然想起上Cydia上看看，果然已经有人编译好了，于是站在巨人的肩膀上：

[![](/public/2009/12/ipodssh1.png "ipodssh1")](/public/2009/12/ipodssh1.png)

简单编辑一下以下的脚本，并上传到设备上（注意设置权限为“可执行”）：

> *#!/bin/bash  
> killall autossh;  
> killall ssh;  
> autossh -M20000 -f -q -N –D **yourPort** -g **yourUserName@yourSSHServer**;  
> echo Flora tssh [Done];  
> exit 0;*

当然了，脚本名字和提示信息等个性化的东西你随便写就可以，执行效果如下：

[![](/public/2009/12/ipodssh02.png "ipodssh02")](/public/2009/12/ipodssh02.png)

可爱的Facebook又回来了：

[![](/public/2009/12/f964bfa1c9b8d9bb33047cea1ca2a1d8.png "f964bfa1c9b8d9bb33047cea1ca2a1d8")](/public/2009/12/f964bfa1c9b8d9bb33047cea1ca2a1d8.png)

当然你也是可以配合pac文件用。pac文件和电脑上的语法完全一样，几乎不用做什么修改就能用到iPhone OS上了。  
现在开始只需要启动一次脚本，就永远自动挂着ssh-D了哦，和电脑上翻墙一样方便了。

PS 1 ：硬启动以后需要运行一次脚本哦，休眠醒来后不需要，千万不要忘记上传公匙。  
PS 2 ：有兴趣的朋友还可以把autossh放在启动项目上。  
PS 3 ：脚本其实不是必要的，autossh比较必要，脚本是为了让大家免去每次输入繁琐的命令。
