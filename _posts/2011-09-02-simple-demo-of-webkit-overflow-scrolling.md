---
layout: post
title: simple demo of -webkit-overflow-scrolling
author: Leask
date: '2011-09-02 11:56:33 +0800'
categories:
- Computers and Internet
- Mobile
comments:
- id: 2749
  author: f
  author_email: feiin@qq.com
  author_url: ''
  date: '2012-09-05 15:30:42 +0800'
  date_gmt: '2012-09-05 07:30:42 +0800'
  content: "容器内有float元素时 内容过长时 子元素会隐藏"
---
昨天看 iOS 5 beta 7 的 release log 看到 iOS 的 webkit 支持 -webkit-overflow-scrolling 。  
虽然后来 @virushuo 提醒其实 beta 1 时就已引入，且是通过 GPU 加速的。  
不过我还是很兴奋，同时感觉类 Scrollability 的 js 阻尼滚动模拟库快完成其使命了。

今天用几分钟时间写了一个 demo，感觉效果还是相当理想的。  
Demo 很粗糙，在这里分享一下，希望对有兴趣实现类似效果的朋友有用。

source code:

```
<!DOCTYPE html>
<html>
    <head>
        <title>simple demo of -webkit-overflow-scrolling</title>
    </head>
    <body>
<div style="width:400px; height:400px; border-style:solid; overflow: scroll; -webkit-overflow-scrolling: touch;">
            <img src="/assets/img/2011/07/qingyuan_city_09_06_181.jpg">
        </div>
    </body>
</html>
```

其实重要的也就这两句：

```
overflow: scroll;
-webkit-overflow-scrolling: touch;
```

点击以下链接直接体验（仅适合运行 iOS 5 beta 的设备）：  
[simple demo of -webkit-overflow-scrolling](/public/2011/09/overflowScrolling.html)
