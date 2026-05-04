---
layout: post
title: "拯救TinyGrab中止通过CNAME绑定域名后失效的图片"
author: Leask
date: '2010-10-07 22:00:22 +0800'
---
我曾经通过 t.leaskh.com 绑定到 grab.by 在blog上发了好些图片.  
无奈 TinyGrab 中止了解释这样形式的地址.  
于是就开始构思通过php重定向的方式试试恢复这些图片.

重新把 t.leaskh.com A记录解释到自己的主机,编写以下 index.php 文件:

> php header('Location: http://grab.by' . $_SERVER['REQUEST_URI']); ?

编写 .htaccess 文件:
> Options +FollowSymLinks  
> IndexIgnore */*  
> RewriteEngine on  
> # if a directory or a file exists, use it directly  
> RewriteCond %{REQUEST_FILENAME} !-f  
> RewriteCond %{REQUEST_FILENAME} !-d  
> # otherwise forward it to index.php  
> RewriteRule . index.php

程序调试通过,图片得以恢复.

后来实验发现通过dreamhost的redirect模式绑定域名能达到同样的目的.  
dreamhost在转发域名的时候会把后面的路径一并转发.  
问过用其他host的朋友,暂时没有发现有类似行为.

PS: 理论上通过这个思想大家可以把任意一款你喜欢的短网址服务"绑定"到自己的域名.
