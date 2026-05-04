---
layout: post
title: "升级 MacBook Pro with Retina display late 2012 以支持 802.11ac 无线网络"
author: Leask
date: '2014-03-08 18:42:16 +0800'
comments:
- id: 6766
  author: DD-WRT无线设置详解 | Aj&#039;s Blog
  author_email: ''
  author_url: http://www.6zou.net/docs/dd-wrt-wireless-config-howto.html
  date: '2014-05-08 03:52:03 +0800'
  date_gmt: '2014-05-07 19:52:03 +0800'
  content: "[&#8230;] rMBP无线网卡升级 [&#8230;]"
---
2013 年 MacBook Pro with Retina display 有小幅更新，对比 2012 年款，有以下几点变动：

1：从 Intel 第三代 Core IvyBridge 处理器升级到第四代的 Core Haswell / Crystalwell；  
2：802.11ac Wi‑Fi wireless；  
3：Bluetooth 4.0 wireless；  
4：Thunderbolt 2。

从看到以上升级开始，我就开始垂涎 802.11ac 千兆无线网，但是手头的 12 年 rMBP 依然是够用的，现在追赶升级电脑有点不理智。于是萌生了升级网络模块的想法。其实早在 13 年款 MacBook Air ( MD712, MD760 ) 支持 802.11ac 以来，就有不少 geek ([@yarshure](https://twitter.com/yarshure)...) 尝试把它装到 rMBP 上。但是由于两个网卡的长短不一致，Air 的网卡 ( BCM94360CS2 ) 比较短小，所以无法通过螺丝固定在 Pro 的网卡插槽内，虽然改造后可用，但方案并不优雅。

随着 13 年 rMBP 的上市，市场上开始出现拆机网卡，淘宝搜索型号 BCM94360CSAX，几百块就能到手，于是有了本文。

改造过程相当简单，所以没有什么好详细写的，让大家看几个图吧。

首先看看千兆无线网卡长什么样：  
![IMG_0940](/public/2014/03/IMG_0940.jpg)

翻个背面看看：  
![IMG_0953](/public/2014/03/IMG_0953.jpg)

拆开 Unibody 外壳，无线模块就在左上角风扇旁边：![IMG_0949](/public/2014/03/IMG_0949.jpg)

来张近照：  
![IMG_0950](/public/2014/03/IMG_0950.jpg)

小心把上图的这个模块拆下来，然后换上新的就好了。

我们来看看升级前通过 Time Capsule 2013 的 5Ghz 802.11n 能达到的最高速度，450 Mbps：  
![BhPT-UwCIAAZLic](/public/2014/03/BhPT-UwCIAAZLic.png)

升级后，同样的网络环境，实现 802.11ac，跑满 1300 Mbps：  
[![Screen Shot 2014-03-03 at 6.21.29 PM](/public/2014/03/Screen-Shot-2014-03-03-at-6.21.29-PM.png)](/public/2014/03/Screen-Shot-2014-03-03-at-6.21.29-PM.png)

速度提升还是相当明显的，还需要留意的是，很多应用都是直接或者间接使用无线网卡的 mac 地址来作为每台电脑的唯一标识的，例如 iTunes 和 Sublime Text 等，你需要重新授权一下：  
![Screen Shot 2014-03-04 at 4.24.05 PM](/public/2014/03/Screen-Shot-2014-03-04-at-4.24.05-PM.png)

由于 Mac 的设计无线网卡和 Bluetooth 适配器是集成在一个模块里面的，所以升级无线模块后，我的机器同时也获得了 Bluetooth 4.0 功能。

这次升级应该算是小折腾见效快的便捷改造，十分推荐。如果需要查询更多拆机的细节、技巧，自行移步到 [http://www.ifixit.com](http://www.ifixit.com) 即可。

PS：最后，我还尝试了安装 MacBook Air 2013 的无线网卡到 MacBook Air 2012 的机器里，但是发现这两代机器的网卡长短不同，13 年 Air 的网卡比较长，无法安装到 12 年的机器里，看图：  
![IMG_0965](/public/2014/03/IMG_0965.jpg)
