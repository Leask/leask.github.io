---
layout: post
title: "[原创]浅谈iPod touch OS 2.2固件初步破解"
author: Leask
date: '2009-05-25 05:57:55 +0800'
---
Apple如期带来了iPhone OS 2.2，各种新特性这里就不一一叙述了。  
我是使用iPod touch的，习惯在新固件发布的时候凑凑热闹，于是第一时间升级到2.2。  
试着按照俄罗斯高手破解iPhone OS 2.2的方法（[http://russianiphone.ru/archives/2538](http://russianiphone.ru/archives/2538)）折腾我的touch。  
可惜的是经过几次的尝试，无论使用Mac还是Windows上的quickpwn均无法顺利写入破解文件。  
万念俱灰之际，仔细研究了破解的原理，留意到俄罗斯高手所使用的quickpwn 2.1版本并不高，理论上2.1版的quickpwn只能破解OS 2.1。  
我推断在引导程序上，OS 2.1和2.2的差别并不大，所以可以这样轻易忽悠过去。  
iPhone如此，那么iPod touch应该更简单才是，但是为什么高手所修改的QuickPwn21-VTX偏偏不适合iPod呢？  
分析发现，QuickPwn21-VTX是一个特殊的mod版本，作者人为地把识别iPhone固件版本的程序作了修改，从而让QuickPwn把2.2版本的iPhone识别成2.1版本的iPhone。  
然后QuickPwn调用破解2.1固件的程序写入2.2固件的机器中，从而达到破解的目的。  
那么问题就有头绪了，理论上把touch 2.1的破解文件写入touch 2.2的机器中，也能达到破解2.2版本的iPod touch。  
于是我想到了用版本检查相对不严格的quickpwn-gui-120版本，然后伪造一个固件识别文件，达到破解iPod touch 2.2的目的。  
而事实上，过程是出乎意料的顺利完成了。  

准备以下文件：  
A:quickpwn-gui-120（下载页面为：[http://weiphone.com/viewthread.php?tid=206287](http://weiphone.com/viewthread.php?tid=206287)）  
B:touch OS 2.1固件官方恢复文件：iPod1,1_2.1_5F137_Restore.ipsw  
C:固件识别文件（下载地址为：[iPod1,1_2.1_5F137.bundle.zip](iPod1,1_2.1_5F137.bundle.zip)）  

  
具体步骤如下（过程必须在Windows上完成，我的Windows是Vista Business SP1，相信XP问题不大）：  
1：你需要有曾经PWN过并运行正常的的iPod touch 2.1；  
2：用新版本的iTunes直接升级你的touch到2.2固件，注意是升级不是恢复；  
3：把固件识别文件解压放到quickpwn-gui-120PwnmetheusBundles文件夹下；  
4：运行quickpwn.exe按照提示步骤完成破解，值得注意的是由于是当作2.1破解，因此在选择当前固件的时候需要选择2.1的固件文件：iPod1,1_2.1_5F137_Restore.ipsw；  

经过以上四步骤，你的touch 2.2应该能达到初步破解的目的了，原来安装的各种第三方软件基本上都能运行了。  
但是这个做法还存在问题，因为cydia还无法在2.2固件中运行，因此暂时无法通过cydia安装新的软件。  
如何取舍就看你自己了。  
不过相信pwn的高手们不会闲着，更完善的方法应该很快就能出炉了。  

本文仅献给和我一样，迫不及待体验Apple最新软件的fans们。  
最后祝大家刷机愉快。  
如有问题可以到我的博客（[https://leaskh.com](https://leaskh.com/)）找到我的联系方式和我讨论，或者电邮给我（[i@leaskh.com](mailto:i@leaskh.com)）。  

谢谢支持！

[![](https://2ax6iq.bay.livefilestore.com/y1mC7a7-CvBVlq5KQiic2UgMXTq-q_CFX0naLTTmZrdfJGaUTLy1i4DPmbYOHUoEBdzdYe2yf50xuUcqgYAlmZIiy00pK0rJNzCZlNNByh80SYnBqA1uMWcyEZ0gHvwcz433EYSHIHZs4lz6BMhl0x0vQ/IMG_0002970.PNG)](https://2ax6iq.bay.livefilestore.com/y1mC7a7-CvBVlq5KQiic2UgMXTq-q_CFX0naLTTmZrdfJGaUTLy1i4DPmbYOHUoEBdzdYe2yf50xuUcqgYAlmZIiy00pK0rJNzCZlNNByh80SYnBqA1uMWcyEZ0gHvwcz433EYSHIHZs4lz6BMhl0x0vQ/IMG_0002970.PNG)

[![](/public/2010/09/img_0001470.png?w=200)](/public/2010/09/img_0001470.png?w=200)
