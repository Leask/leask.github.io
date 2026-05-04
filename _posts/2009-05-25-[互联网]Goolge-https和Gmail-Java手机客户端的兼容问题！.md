---
layout: post
title: "[互联网]Goolge https和Gmail Java手机客户端的兼容问题！"
author: Leask
date: '2009-05-25 05:37:43 +0800'
---
GMail可选强制启用https本是个很好的主意，因为https虽然会增大客户端的运算量，但是https带来了更稳定和更安全的邮件体验。  

所以一开始的时候我就开启了这个选项，但可怕的事情出现了，Java客户端从此无法收取邮件了!!  

经过反复测试，的确就是https的问题。  

  

大家要注意了哦，Gmail Java无法使用的时候检查你是否使用了https协议登陆。  

  

*PS:  

1:Gmail Java客户端需要手机网络配置cmnet连接。  

2:我的Gmail Java客户端版本是1.5.0大小是356KB，关闭https后使用正常。  
[![](/public/2010/09/https.jpg?w=300)](/public/2010/09/https.jpg?w=300)
