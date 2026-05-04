---
layout: post
status: publish
published: true
title: "在Mac上通过Terminal截取网页全图 / Full Page Screenshots by Terminal On a Mac"
author: Leask




author_login: leask
author_email: i@leaskh.com
author_url: https://leaskh.com
wordpress_id: 52
wordpress_url: http://leaskh.wordpress.com/2009/11/06/%e5%9c%a8mac%e4%b8%8a%e9%80%9a%e8%bf%87terminal%e6%88%aa%e5%8f%96%e7%bd%91%e9%a1%b5%e5%85%a8%e5%9b%be-full-page-screenshots-by-terminal-on-a-mac
date: '2009-11-06 14:49:38 +0800'
date_gmt: '2009-11-06 14:49:38 +0800'
categories:

tags: []
comments: []
---

其实很多人都知道，如果说Snow Leopard和Windows 7的图形界面是可口的点心的话，那么在*nix系统里面，命令行Shell简直就是系统的灵魂。

笔者是从事网站开发和设计的，俗称的D&D（Design and Development），经常遇到需要把制作效果汇报给上级，或者发Demo给客户的情况。然而由于Web pages脱离了Web server通常是无法完整预览的，这就需要截图了。

Mac上截图是很方便的，系统自带的截图功能就异常强大（和Windows上残废的截图功能无法类比），而且通过便利的热键就能使用。关键是Mac上的截图工具并不能截取网页的全图，也就是遇到你的网页尺寸大于你的浏览器窗口尺寸的时候，就无能为力了，难不成还要开个Photoshop来拼接？这样做很山寨，一点都不专业，而且效率相当低。于是我也尝试过使用Paparazzi和Little Snapper。说实话，这两个软件都是很优秀的，特别是华丽的Little Snapper，但是那就需要多安装一个软件了，有没有什么环保一点的办法呢？

经过一番研究，其实是有的，就是使用基于python的webkit2png，然而事实上Paparazzi和Little Snapper都是基于webkit2png项目的。  
webkit2png可以在这里下载到：[http://www.paulhammond.org/webkit2png/](http://www.paulhammond.org/webkit2png/ "http://www.paulhammond.org/webkit2png/")  
如果你和我一样，有命令行癖，那么打开Terminal，使用CURL获取，命令如下：

> *curl* [*http://www.paulhammond.org/2009/03/webkit2png-0.5/webkit2png-0.5.txt*](http://www.paulhammond.org/2009/03/webkit2png-0.5/webkit2png-0.5.txt) *> webkit2png*

于是你就得到webkit2png了。怎么用呢？  
首先检查你的系统，你必须使用Mac OS X 10.2或以上系统，Safari 1.0或以上，PyObjC库1.1或以上。当然了，如果你的系统是Mac OS X 10.5 Leopard或更高版本，那么以上所有组件，你都已经安装过上了。如果不满足条件，可以升级Safari，并下载PyObjC的源代码自己编译。

webkit2png的使用很简单，Terminal执行：

> *python /Users/Leask/webkit2png* [*https://leaskh.com/*](https://leaskh.com/)

执行效果如下：  
![Screen shot 2009-11-06 at 9.57.57 PM](/public/2010/09/screenshot2009-11-06at9.png?w=300 "Screen shot 2009-11-06 at 9.57.57 PM")   
然后你就会发现网页已经被截图放在你的home文件夹了。

当然你还可以通过参数控制webkit2png的行为，你可以通过 *--help* 获得以下使用帮助：

> *Flora:~ Leask$ python /Users/Leask/webkit2png --help  
> Usage: webkit2png [options] [*[*http://example.net/*](http://example.net/) *...]* 
>
> *examples:  
> webkit2png* [*http://google.com/*](http://google.com/) *# screengrab google  
> webkit2png -W 1000 -H 1000* [*http://google.com/*](http://google.com/) *# bigger screengrab of google  
> webkit2png -T* [*http://google.com/*](http://google.com/) *# just the thumbnail screengrab  
> webkit2png -TF* [*http://google.com/*](http://google.com/) *# just thumbnail and fullsize grab  
> webkit2png -o foo* [*http://google.com/*](http://google.com/) *# save images as "foo-thumb.png" etc  
> webkit2png - # screengrab urls from stdin  
> webkit2png -h | less # full documentation* 
>
> *Options:  
>  --version show program's version number and exit  
>  -h, --help show this help message and exit  
>  -W WIDTH, --width=WIDTH  
>  initial (and minimum) width of browser (default: 800)  
>  -H HEIGHT, --height=HEIGHT  
>  initial (and minimum) height of browser (default: 600)  
>  --clipwidth=WIDTH width of clipped thumbnail (default: 200)  
>  --clipheight=HEIGHT height of clipped thumbnail (default: 150)  
>  -s SCALE, --scale=SCALE  
>  scale factor for thumbnails (default: 0.25)  
>  -m, --md5 use md5 hash for filename (like del.icio.us)  
>  -o NAME, --filename=NAME  
>  save images as NAME-full.png,NAME-thumb.png etc  
>  -F, --fullsize only create fullsize screenshot  
>  -T, --thumb only create thumbnail sreenshot  
>  -C, --clipped only create clipped thumbnail screenshot  
>  -d, --datestamp include date in filename  
>  -D DIR, --dir=DIR directory to place images into  
>  --delay=DELAY delay between page load finishing and screenshot  
>  --noimages don't load images*

这里我就不一一翻译了。如果你懂一点Shell Script语言，还可以把这个命令再封装一下，例如我就把这个命令封装为：

> *websnap [URL]*

的形式，很便利地得到截图，如输入：

> *websnap* [*[https://leaskh.com](https://leaskh.com/)*](https://leaskh.com)/

至于Shell Script怎么写？也不难，Unix和Linux上的Shell Script其实都大致一样，如：

> *#!/bin/bash  
> echo "Leask's WebSnap based on webkit2png"  
> echo ""  
> python /Users/Leask/webkit2png $1;  
> exit;*

保存上面的代码片段为以websnap为名文件，注意以上的Leask为我的用户名，你还需要自己改为自己的用户名呢。放脚本的目录和脚本本身都需要有执行权限。

就先写这些吧，Enjoy。

// 如果你是Linux用户，你通常没有Webkit，那么你有Firefox就可以了，Google一下另外一个基于Mozilla Firefox的项目叫做khtml2png，和webkit2png大同小异。
