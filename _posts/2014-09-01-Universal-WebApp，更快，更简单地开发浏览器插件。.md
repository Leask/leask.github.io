---
layout: post
title: Universal-WebApp，更快，更简单地开发浏览器插件。
author: Leask
date: '2014-09-01 23:08:39 +0800'
---
![universal webapp demo](/public/2014/09/Screen-Shot-2014-09-01-at-10.44.02-PM.jpg) 如果你开发浏览器插件，你可能常常需要解决一个问题：就是把重要逻辑放到 background 去完成，然后UI 视图写在注入脚本或者 Page Actions / Browser Actions / Popover。这样你就需要频繁访问后台数据，不同的浏览器提供了不同的消息接口。 我曾为此费时不少，于是我整理了一下，开源了一个兼容层 Universal-WebApp 可让插件前端轻松访问 background 的函数，并提供一些封装简化浏览器插件的跨平台问题。

这是一个小小的 demo，演示从注入脚本调用 background 的一个函数，做一个字符串连接，然后 callback 到前端。而且你从此不需要再关心这个流程在不同浏览器之间的差异，目前兼容 Safari 和 Chrome，将来如果有时间，我也会兼容 FireFox。

当然了，我是为了满足自己工作的需要出发的，所以最开始仅仅封装了最常用的功能，完全抹平浏览器间的消息传递差异，是很艰难很曲折的，只能挖个坑慢慢填了。

GitHub 地址： [https://github.com/Leask/Universal-WebApp](https://github.com/Leask/Universal-WebApp "Universal-WebApp")
