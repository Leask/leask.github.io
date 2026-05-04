---
layout: post
title: Flora_ssh-D Version 2.33 闪亮登场！
author: Leask
date: '2009-10-29 03:26:29 +0800'
comments:
- id: 356
  author: "上网"
  author_email: ''
  author_url: ''
  date: '2009-10-29 13:10:26 +0800'
  date_gmt: '2009-10-29 13:10:26 +0800'
  content: "希望能开发linux版的Flora_ssh-D"
---
![Screen shot 2009-10-29 at 10.10.21 AM](/assets/img/2010/09/screenshot2009-10-29at10.png "Screen shot 2009-10-29 at 10.10.21 AM")

Flora_ssh-D是什么？

1. Flora_ssh-D是一个Applescript（以app形式封装），在Mac OS上开发和运行（有计划推出针对Windows的版本）；
2. Flora_ssh-D是一个iTunes VoiveOver程序，能够像iPod shuffle那样自动报读当前正在播放的歌名和艺术家；
3. Flora_ssh-D能够自动连接ssh -D服务器，自动创建Socks代理服务器，高速访问某些如Twitter、Facebook等国外优秀站点，并在连接断开的时候自动重连，配合ssh -D服务器使用，让Wall从此透明；
4. Flora_ssh-D并不包含ssh -D服务器信息，如果你要使用第3条的功能，你需要自己购买ssh -D服务器，**做有责任感的网民，网上行为务必符合国家法律法规**；
5. Flora_ssh-D能自动更新你的Twitter状态为你正在听的歌，如：【I am listening to #Sensible by #Sun Yan-Zi in album #Leave. // Thursday, October 29, 2009 11:05:32 AM】；
6. Flora_ssh-D能自动记录你正在听的歌到Last.fm；
7. Flora_ssh-D能自动更新你DNS-O-MATIC上的动态IP地址为你的当前IP；
8. Flora_ssh-D能自动判断在线状态，自动为你开启和关闭某些软件；
9. **推荐把Flora_ssh-D设置为开机启动，只需要在开机的时候执行这一个脚本，其他的程序可以配置到脚本里面，自动根据在线状态为你自动开启和关闭；**
10. Flora_ssh-D是开源的自由软件，并已经在Google Code上创建为开源项目：[http://code.google.com/p/flora-ssh-d/](http://code.google.com/p/flora-ssh-d/)

Version 2.33有什么新改进？

1. 全新的任务调度，大大缩短iTunes VoiceOver的时间延迟；
2. 全新的配置方式，现在下载程序后无需配置就能马上执行，比较适合只需要iTunes VoiceOver功能的朋友；
3. 优化VoiceOver功能，添加音量淡入淡出功能，听起来效果更好，和iPod shuffle上基本上没有分别了；
4. 完善Twitter功能，自动在Twitter上发布你正在听的歌；
5. 完善last.fm歌曲记录功能；
6. 修正ssh -D连接的bug，让ssh -D连接更加顺畅，并在退出程序的时候自动关闭ssh –D以释放内存；
7. 进一步减少空闲时的资源占用，让脚本更轻巧，几乎感觉不到脚本的存在；
8. 全新的任务管理方式，运行更快，更稳定；
9. 添加中文配置说明，方便英文不好的朋友使用。

[Flora_ssh-D](http://code.google.com/p/flora-ssh-d/ "Flora_ssh-D on Google Code") 2.33 能够在以下地址下载到：[http://code.google.com/p/flora-ssh-d/downloads/list](http://code.google.com/p/flora-ssh-d/downloads/list "http://code.google.com/p/flora-ssh-d/downloads/list")

源代码如下：

> (* Flora_ssh-D Version 2.33  
> Open Source Project Home/开源项目主页: [http://code.google.com/p/flora-ssh-d/](http://code.google.com/p/flora-ssh-d/)  
> Code by/程序编写: 黄思夏 / Leask Huang  
> Blog: [https://leaskh.com](https://leaskh.com) (天朝访问需翻墙)  
> E-mail/GTalk/MSN/QQ: i@leaskh.com *)
>
> (* CUSTOM THESE SETTINGS BEFORE YOUR RUN THINS SCRIPT // 运行此脚本前请先配置此区域的参数  
>  LEAVE IT BLANK IF YOU DON'T NEED IT // 如你不需要其中某些功能请将设置留空 *)  
> property SSHServerName : ""  
> property SSHUserName : ""  
> property SSHPasswd : ""  
> property TwitterUsername : ""  
> property TwitterPassword : ""  
> property DNSUsername : ""  
> property DNSPassword : ""  
> property LastfmUsername : ""  
> property LastfmPassword : ""  
> property appStList : {}  
> property appQuitList : {}
>
> (* Example/示例 // English Help // 中文帮助   
> property SSHServerName : "ssh.yourdomain.com" -- ssh -D Server Address (or leave it blank) // ssh -D 翻墙服务器地址 (不使用ssh -D则留空)  
> property SSHUserName : "*******" -- ssh -D User Name (or leave it blank) // ssh -D 帐号 (不使用ssh -D则留空)  
> property SSHPasswd : "*******" -- ssh -D Password (or leave it blank) // ssh -D 密码 (不使用ssh -D则留空)  
> property TwitterUsername : "*******" -- Twitter User Name (or leave it blank) // Twitter帐号 (不使用Twitter则留空)  
> property TwitterPassword : "*******" -- Twitter Password (or leave it blank) // Twitter密码 (不使用Twitter则留空)  
> property DNSUsername : "*******" -- DNS User Name (or leave it blank) // DNS-O-MATIC动态IP帐号 (不使用动态IP则留空)  
> property DNSPassword : "*******" -- DNS Password (or leave it blank) // DNS-O-MATIC动态IP密码 (不使用动态IP则留空)  
> property LastfmUsername : "*******" -- last.fm User Name (or leave it blank) // last.fm帐号 (不使用last.fm则留空)  
> property LastfmPassword : "*******" -- last.fm Password (or leave it blank) // last.fm密码 (不使用last.fm则留空)  
> property appStList : {"App 1", "软件2","iChat"} -- these apps will launch while you are online (or leave it blank) // 填写【在线】时需【开启】的软件(不使用此功能则留空)  
> property appQuitList : {"App 1", "软件2","QQ"} -- these apps will quit while you are offline (or leave it blank) // 填写【离线】时需【关闭】的软件(不使用此功能则留空)  
> *)
>
> (* ======= Variable Declaration ======= *)  
> global timeTry  
> global DNSResponse  
> global isOLast  
> global iTsCurDBID  
> global iTsORSoundVolume  
> global strSNGArtist  
> global strSNGName  
> global strSNGAlbum  
> global strSNGTrackNumber  
> global strSNGDuration  
> global intIdleCount
>
> (* ======= Main Script ======= *)  
> on run  
>  set isOLast to ""  
>  set iTsCurDBID to ""  
>  set intIdleCount to 10  
> end run
>
> on quit  
>  if isOLast is "online" then fnTwitter("I am offline now! // " & (current date), true)  
>  fnShellSSHEnd(true)  
>  fnAppQuit()  
>  continue quit  
> end quit
>
> on idle  
>  if fnCheckNet() is true then  
>  if intIdleCount > 9 then  
>  fnSSHCnt()  
>  if isOLast is not "online" then  
>  fnAppStart()  
>  fnDNSUpdate()  
>  fnTwitter("I am online now! // " & (current date), true)  
>  end if  
>  set intIdleCount to 0  
>  end if  
>  fnMusic(true)  
>  set intIdleCount to intIdleCount + 1  
>  set isOLast to "online"  
>  else  
>  fnMusic(false)  
>  if isOLast is not "offline" then  
>  fnShellSSHEnd(true)  
>  fnAppQuit()  
>  end if  
>  set isOLast to "offline"  
>  end if  
>  return 33  
> end idle
>
> (* ======= Functions ======= *)  
> to fnCheckNet()  
>  try  
>  do shell script "curl --connect-timeout 33 "apple.com/favicon.ico  
> ""  
>  if isOLast is not "online" then SmartSay({"Online"})  
>  return true  
>  on error  
>  if isOLast is not "offline" then SmartSay({"Offline"})  
>  return false  
>  end try  
> end fnCheckNet
>
> to fnAppStart()  
>  if (count appStList) > 0 then  
>  SmartSay({"Start Apps"})  
>  try  
>  repeat with intSti from 1 to (count appStList)  
>  tell application (item intSti of appStList) to activate  
>  end repeat  
>  SmartSay({"OK"})  
>  on error  
>  SmartSay({"Failed"})  
>  end try  
>  end if  
> end fnAppStart
>
> to fnAppQuit()  
>  if (count appQuitList) > 0 then  
>  SmartSay({"Quit Applications"})  
>  try  
>  repeat with intSti from 1 to count appQuitList  
>  tell application (item intSti of appQuitList) to quit  
>  end repeat  
>  SmartSay({"OK"})  
>  on error  
>  SmartSay({"Failed"})  
>  end try  
>  end if  
> end fnAppQuit
>
> to fnSSHCnt()  
>  if (length of SSHServerName) > 0 and (length of SSHUserName) > 0 and (length of SSHPasswd) > 0 then  
>  set timeTry to 0  
>  repeat while fnCheckSSHD() is false  
>  SmartSay({"Connect SSH D"})  
>  if timeTry > 0 then if (button returned of (display dialog "ssh -D connection failed." & return & "" buttons {"Retry", "Ignore"})) is "Ignore" then exit repeat  
>  fnShellSSH()  
>  set timeTry to timeTry + 1  
>  end repeat  
>  end if  
> end fnSSHCnt
>
> to fnCheckSSHD()  
>  try  
>  do shell script "curl --socks5 127.0.0.1:7070 --connect-timeout 33 "apple.com/favicon.ico""  
>  if timeTry > 0 then SmartSay({"OK"})  
>  return true  
>  on error  
>  if timeTry > 0 then SmartSay({"Failed"})  
>  return false  
>  end try  
> end fnCheckSSHD
>
> to fnShellSSH()  
>  try  
>  try  
>  do shell script "killall Terminal"  
>  end try  
>  tell application "Terminal"  
>  activate  
>  fnShellSSHEnd(false) of me  
>  delay 1  
>  do script "nohup ssh -D 7070 " & SSHUserName & "@" & SSHServerName & " > Downloads/.Flora_ssh-D.out" in window 1  
>  end tell  
>  SmartSay({"SSH D connection request and log in request have been sent. Waiting for response from remote server."})  
>  tell application "Terminal"  
>  do script SSHPasswd in window 1  
>  delay 1  
>  quit  
>  end tell  
>  end try  
> end fnShellSSH
>
> to fnShellSSHEnd(isSay)  
>  if (length of SSHServerName) > 0 and (length of SSHUserName) > 0 and (length of SSHPasswd) > 0 then  
>  if isSay is true then SmartSay({"Disconnect SSH D"})  
>  try  
>  do shell script "killall ssh"  
>  do shell script "killall ssh-agent"  
>  do shell script "rm ~/Downloads/.Flora_ssh-D.out"  
>  end try  
>  end if  
> end fnShellSSHEnd
>
> to fnTwitter(strTwText, isSay)  
>  if (length of TwitterUsername) > 0 and (length of TwitterPassword) > 0 and (length of strTwText) > 0 then  
>  if (length of strTwText) > 140 then  
>  set strTwText to (characters 1 through 137 of strTwText as string) & "..."  
>  end if  
>  if isSay is true then SmartSay({"Update Twitter state"})  
>  try  
>  do shell script "curl --connect-timeout 33 --user " & (quoted form of (TwitterUsername & ":" & TwitterPassword)) & " --data-binary " & (quoted form of ("status=" & strTwText)) & " "[https://twitter.com/statuses/update.json""](https://twitter.com/statuses/update.json)  
>  if isSay is true then SmartSay({"OK"})  
>  on error  
>  if isSay is true then  
>  SmartSay({"Failed"})  
>  else  
>  SmartSay({"Update Twitter state failed"})  
>  end if  
>  end try  
>  end if  
> end fnTwitter
>
> to fnDNSShell()  
>  try  
>  set DNSResponse to (do shell script "curl --connect-timeout 33 "[https://"](https://) & DNSUsername & ":" & DNSPassword & "@updates.dnsomatic.com/nic/update?&wildcard=NOCHG&mx=NOCHG&backmx=NOCHG"")  
>  if first word of DNSResponse is "good" then -- (second word of DNSResponse) is IP address  
>  return true  
>  else  
>  return false  
>  end if  
>  on error  
>  return false  
>  end try  
> end fnDNSShell
>
> to fnDNSUpdate()  
>  if (length of DNSUsername) > 0 and (length of DNSPassword) > 0 then  
>  SmartSay({"Update dynamic IP"})  
>  if fnDNSShell() is true then  
>  SmartSay({"OK"})  
>  else  
>  SmartSay({"Failed"})  
>  end if  
>  end if  
> end fnDNSUpdate
>
> to fnURLec(strToUEC)  
>  return do shell script "python -c 'import sys, urllib; print urllib.quote(sys.argv[1])' "" & strToUEC & """  
> end fnURLec
>
> to fniTunesisActive()  
>  tell application "System Events" to return (name of processes contains "iTunes")  
> end fniTunesisActive
>
> to fuisiTunesNUD()  
>  if fniTunesisActive() is true then  
>  tell application "iTunes"  
>  if player state is playing then  
>  set iTsNewDBID to (get database ID of current track)  
>  if iTsNewDBID is not iTsCurDBID then  
>  set strSNGArtist to (get artist of current track)  
>  set strSNGName to (get name of current track)  
>  set strSNGAlbum to (get album of current track)  
>  set strSNGTrackNumber to (get track number of current track)  
>  set strSNGDuration to (get duration of current track as integer)  
>  set iTsCurDBID to iTsNewDBID  
>  return true  
>  else
