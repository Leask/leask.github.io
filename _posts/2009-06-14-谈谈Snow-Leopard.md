---
layout: post
title: "谈谈Snow Leopard"
author: Leask
date: '2009-06-14 17:30:59 +0800'
---
[![](/public/2010/09/screenshoton2009-06-13at1.png?w=300)](/public/2010/09/screenshoton2009-06-13at1.png?w=300)
WWDC在漫长的等待后主要带来了4个消息：
1：New MacBook Pro；
2：Snow Leopard的开发情况；
3：iPhone OS 3.0；
4：iPhone 3G[S]。
由于还没有钱换新的MacBook Pro，可怜的“小白”还会陪我一些日子；而且日常应用iPod touch也满足我了。
于是我的关注焦点主要集中在Snow Leopard和iPhone OS 3.0上。
于是第一时间下载到了这两个系统，iPhone OS 3.0 GM需要开发者帐号，所以暂时还没能装上，Snow Leopard就已经被我尝到了。
下面谈谈我的感受吧。
**1：安装体验**
 [![](/public/2010/09/dsc00006.jpg?w=300)](/public/2010/09/dsc00006.jpg?w=300)
只能说我的安装体验很一般，很多人说安装加快了，我没有体验到。
我用USB硬盘引导安装的，装Leopard能在10分钟内完成（不装X11，而且我只用英文界面，不装国际化）。
同样的安装方式和选项，装Snow Leopard需要大概15分钟，预测19分钟，但是最后几分钟在安装最后阶段会跳过。
**2：64bit Finder**
[![](/public/2010/09/screenshoton2009-06-13at11.png?w=300)](/public/2010/09/screenshoton2009-06-13at11.png?w=300)
[![](/public/2010/09/screenshoton2009-06-13at12.png?w=300)](/public/2010/09/screenshoton2009-06-13at12.png?w=300)
最大的改进是无处不在Quick Look。常见类型的文件上，只需要把鼠标移上，就能出现播放的图标，轻轻一点，就能立刻预览文件，速度非常快，基本上再大文件也不需要等待的时间。
//Preview的速度也大大加快，特别是对矢量格式。
[![](/public/2010/09/screenshoton2009-06-13at13.png?w=300)](/public/2010/09/screenshoton2009-06-13at13.png?w=300)
[![](/public/2010/09/screenshoton2009-06-13at14.png?w=300)](/public/2010/09/screenshoton2009-06-13at14.png?w=300)
Quick Look的性能也大大提升，并加入对多种矢量格式的支持，不再需要第三方插件，例如：EPS、AI等格式。
**3：文字输入的长足进步**
[![](/public/2010/09/screenshoton2009-06-13at15.png?w=300)](/public/2010/09/screenshoton2009-06-13at15.png?w=300)
改进的中文输入法很不错，能打句子了。但是注意，IMKQIM能安装使用，但是选项不能修改。

[![](/public/2010/09/screenshoton2009-06-13at16.png?w=300)](/public/2010/09/screenshoton2009-06-13at16.png?w=300)

全局的自动字符转换，以前只能在iWork中用。

[![](/public/2010/09/screenshoton2009-06-13at17.png?w=300)](/public/2010/09/screenshoton2009-06-13at17.png?w=300)

带屏幕提示的输入法转换。

**4：64bit带来的改变**

[![](/public/2010/09/screenshoton2009-06-13at18.png?w=300)](/public/2010/09/screenshoton2009-06-13at18.png?w=300)

系统组件大多数已经用64bit Cocoa重写了，系统效能大大提高，软件体积也缩小了不少。但iTunes等少量应用还是32bit。

[![](/public/2010/09/screenshoton2009-06-13at19.png?w=300)](/public/2010/09/screenshoton2009-06-13at19.png?w=300)

问题随之而来，64bit的System Preferences并不支持32bit的Pane，所以第三方的Pane你需要重启System Preferences到32bit模式使用（是自动的）。

[![](/public/2010/09/screenshoton2009-06-13at110.png?w=300)](/public/2010/09/screenshoton2009-06-13at110.png?w=300)

Rosetta已经不是必须组件了，你能够在系统安装的时候选择不安装Rosetta，那就能完全告别Power PC的应用程序支持了。

**5：一些遗憾**

[![](/public/2010/09/screenshoton2009-06-13at111.png?w=300)](/public/2010/09/screenshoton2009-06-13at111.png?w=300)

Time Machine的排除选项不起作用，那将导致你不能排除不需要备份的数据，造成在小硬盘上无法实现Time Machine功能。

[![](/public/2010/09/screenshoton2009-06-13at112.png?w=300)](/public/2010/09/screenshoton2009-06-13at112.png?w=300)

电池续航时间和电脑性能的平衡选项不见了，不知道为什么。

[![](/public/2010/09/screenshoton2009-06-13at113.png?w=300)](/public/2010/09/screenshoton2009-06-13at113.png?w=300)

使用指定IP地址的网络中，尽管网络使用是正常的，AirPort都无法检测到Internet网络状态，显示为惊叹号。

**6：被我发现的兼容问题**

1、无法加载第三方字体（很严重）；  
2、使用root帐号，无法保存VMware设置；  
3、VMware频繁出现无法捕获鼠标；  
4、ForkLift无法使用；  
5、VLC无法使用；  
6、QuickTime X不能播放MKV，大家可以保留Leopard中的旧版QuickTime，旧版能放MKV，而且能和新版共存。

**7：后记**  
大家要注意，本次我试用的是10.6 10A380的版本，这个版本是WWDC上发放给开发者的预览版，但是并不是演示机上安装的版本。主要体现在10A380不包含最新的Dock和Expose，大家看演示就知道了，而且我推测QuickTime X也不是最新的，因为图标还没更新。  

还有一点值得注意，Mail和iCal、Address Book三个改进都能大，iCal和Address Book都能直接同步Google帐号的数据了，但是注意，这三个应用的数据文件的升级是不可逆的，你安装Snow Leopard后，这三个应用的数据库会顺利升级，但是你再装Leopard的时候，数据就变得不能读取了。大家要做好备份。

我是Leask Huang，转载请注明。  
//成文时我已回归Leopard，万般期待Snow Leopard的完善。

/*  
FeedSky AD Code: 2b1c7ceb  
*/
