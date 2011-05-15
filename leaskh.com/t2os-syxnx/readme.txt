提醒：如果启用了同步到多个微博，请不要再在这几个微博间设置同步，不然会照成信息循环同步的问题。同时，请确保tw2other所在目录和所在目录之下的cookies文件夹具有可写权限。不然也有可能照成信息重复同步。

升级版本的时候，请直接覆盖，不要删除以前目录下的tweet.id文件（非常重要），否者会导致重复同步的倒霉事情发生。

由于有的推油们没有正确设置，导致大量的重复信息发送，导致follow5的api_key被封掉。所以现在follow5模块中不再公开提供api_key,如果有需求，请联系我索取并注意保密。具体请见：http://cuies.com/post/now-the-follow5-model-in-tw2other-is-not-public.html 


关于Tw2other:

一个用PHP编写的同步tweets到国内其他微博的小程序。暂时只支持digu/sina/zuosa/follow5/9911/豆瓣广播/鲜果联播/人间网/人人网/网易微博。后面考虑会加入其他的微博支持。
如果不用某个微博的同步服务，留空对应的用户名和密码

受用方法：在任何地方支持php的虚拟主机一个（最好支持Cron的，而且服务器所在地最好在国外，国内也行，不过需要提供一个twitter api，国外空间则不需要）上传Tw2other，配置好config.php中你的twitter帐号和需要同步的服务中的账号和密码，还有如果需要使用Cron来激活同步的需要配置cron.php中的URL参数。

在使用cron.php的时候，如果不想程序有输出,可以在请求中加入echo=false的参数（在页面嵌入使用的时候很有效果）

程序默认是每间隔50秒一次更新的，如果需要修改更新间隔，可以修改config.php中的INTERVAL参数。

有人反映说config.php/cron.php文件用记事本打开看不到格式，所有代码都在一行中了。 这是因为这些文件是使用unix的换行标记，和windows下的换行标志不一样导致的 大家可以使用editplus、UltraEdit?、notepad++这类文本编辑软件来打开

关于cron的配置，一般国外主机使用cPanel的都可以很简单的配置：在管理界面进入【时钟守护作业】，根据自己的水平选择配置模式(个人推荐选择标准模式)，然后选择你要执行的时间间隔，让后输入让php解析cron.php脚本就OK了，推荐每分钟运行一次，基本上可以做到即时同步。

提示：嘀咕对推的关键字过滤比较严重，所以含有某些关键字的tweet同步到嘀咕的时候可能会被河蟹。

有问题可以再我的博客留言：http://cuies.com

或者在twitter上follow我 ：http://twitter.com/cluries
