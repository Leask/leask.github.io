---
layout: post
title: Camino + Windows Live
author: Leask
date: '2006-11-11 12:27:55 +0800'
categories:
- Computers and Internet
---
Mac下通过Camino使用Windows Live服务。  

  

Microsoft声明，访问Windows Live服务需要IE6或Firefox 1.5以上浏览器。  

Mac上，我们发现原生的Camino基于与Firefox一样的内核，  

而且同样是Mozilla.org的项目，在Mac环境中运行更快更稳定。  

但是用Camino却无法完美兼容Windows Live服务。  

  

通过研究发现类Firefox的浏览器都可以在地址栏打开about:config配置页。  

于是通过修改general.useragent.vendor为Firefox；  

修改general.useragent.vendorSub为2.0。  

通过以上修改，强制使服务器识别浏览器为Firefox 2.0。  

  

一切都很顺利，访问Windows Live Mail终于不是Lite Edition了，  

访问Live Spaces也可以使用更多的细节和功能了。  

  

希望本文对使用Mac又需要访问Windows Live服务的朋友有用。
