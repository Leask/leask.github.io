---
layout: post
title: Google Talk in Google Apps
author: Leask
date: '2011-04-17 20:03:07 +0800'
---
众所周知，Google提供强大的Google Apps套件，便于我们部署基于自定义域名的一系列Google服务。这样一方面能够使用Google一系列优质的Web应用，另一方面充分彰显个性，尤其对企业或组织机构意义重大。

Google Apps包括Gmail、Gtalk等核心应用，然而这两者也是我用得最多的Google服务。我的帐号i@leaskh.com正是使用Google Apps部署的。很多朋友看到我使用自定义邮箱名作为Gtalk帐号都很不解，他们自己也尝试过，但是登陆后只能和域名内的帐号沟通，无法和@gmail.com的帐号沟通。其实解决方法很简单，只需要在域名上添加十来条SRV记录，就可以了。

Google推荐至少需要添加的记录如下：

_xmpp-server._tcp.leaskh.com. IN SRV 5 0 5269 xmpp-server.l.google.com  
_xmpp-server._tcp.leaskh.com. IN SRV 20 0 5269 xmpp-server1.l.google.com  
_xmpp-server._tcp.leaskh.com. IN SRV 20 0 5269 xmpp-server2.l.google.com  
_xmpp-server._tcp.leaskh.com. IN SRV 20 0 5269 xmpp-server3.l.google.com  
_xmpp-server._tcp.leaskh.com. IN SRV 20 0 5269 xmpp-server4.l.google.com _jabber._tcp.leaskh.com. IN SRV 5 0 5269 xmpp-server.l.google.com  
_jabber._tcp.leaskh.com. IN SRV 20 0 5269 xmpp-server1.l.google.com  
_jabber._tcp.leaskh.com. IN SRV 20 0 5269 xmpp-server2.l.google.com _jabber._tcp.leaskh.com. IN SRV 20 0 5269 xmpp-server3.l.google.com _jabber._tcp.leaskh.com. IN SRV 20 0 5269 xmpp-server4.l.google.com

为了便于开发，你可能还需要添加以下几条记录：

_xmpp-client._tcp.leaskh.com. IN SRV 5 0 5222 talk.l.google.com  
_xmpp-client._tcp.leaskh.com. IN SRV 20 0 5222 talk1.l.google.com  
_xmpp-client._tcp.leaskh.com. IN SRV 20 0 5222 talk2.l.google.com  
_xmpp-client._tcp.leaskh.com. IN SRV 20 0 5222 talk3.l.google.com  
_xmpp-client._tcp.leaskh.com. IN SRV 20 0 5222 talk4.l.google.com

特别注意，你需要把以上所有记录中的leaskh.com替换为你自己的Google Apps域名。

**最近我在新购买的cutecute.me域名上部署了Google Apps服务，想免费拥有与众不同的个性化Gmail/Gtalk帐号的朋友，请联系我，不要错过哦。**

PS: 官方说明 http://www.google.com/support/a/bin/answer.py?answer=34143
