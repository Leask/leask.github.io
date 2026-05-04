---
layout: post
title: Flora_ssh-D Version 2.47发布！//主要修正：iTunes更新大量Podcast的时候脚本超时的Bug。
author: Leask
date: '2009-11-16 10:27:18 +0800'
---
这个版本早就做好了，但是一直徘徊要不要放出来。因为这段时间我在尝试修改autossh的源代码。autossh是一个很优秀的开源项目，我希望build一个带有更完善翻墙功能的autossh版本，目前还是遇到很多问题。由于工作比较忙，可能一时三刻还完成不了，所以还是放出这个版本。这个版本对于一般的用户已经比较完美了，但是对于用Terminal比较多的用户，还是会有一点不适应的，因为脚本中连接ssh的时候会独占Terminal，这个问题我暂时还没有比较好的解决办法。

另外为了提高安全性，我尝试把各种用户名和密码保存在Mac的Keychain里面，但是不知道是不是因为Mac OS X 10.6.x中比较烦人的脚本安全规则作怪，脚本每次访问Keychain都需要弹出对话框让用户确认，所以最终还是放弃了这个做法，希望有解决办法的朋友指教一下。

![Screen shot 2009-10-28 at 8.33.53 PM](/public/2010/09/screenshot2009-10-28at8.png?w=300 "Screen shot 2009-10-28 at 8.33.53 PM")![Screen shot 2009-10-28 at 8.34.34 PM](/public/2010/09/screenshot2009-10-28at81.png?w=300 "Screen shot 2009-10-28 at 8.34.34 PM")

好了，不多说，最后还是放出源代码（和往常一样，我将在Google Code放出封装好的app和源代码，有需要的朋友直接去下载更新吧）：

> *(* Flora_ssh-D Version 2.47  
> Open Source Project Home/开源项目主页:* [*http://code.google.com/p/flora-ssh-d/*](http://code.google.com/p/flora-ssh-d/)  
> *Code by/程序编写: 黄思夏 / Leask Huang  
> Blog:* [*https://leaskh.com*](https://leaskh.com) *(天朝访问需翻墙)  
> E-mail/GTalk/MSN/QQ: i@leaskh.com *)*
>
> *(* CUSTOM THESE SETTINGS BEFORE YOUR RUN THINS SCRIPT // 运行此脚本前请先配置此区域的参数  
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
> property appQuitList : {}* 
>
> *(* Example/示例 // English Help // 中文帮助   
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
> *)* 
>
> *(* ======= Variable Declaration ======= *)  
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
> global intIdleCount* 
>
> *(* ======= Main Script ======= *)  
> on run  
>  set isOLast to ""  
>  set iTsCurDBID to ""  
>  set intIdleCount to 10  
> end run* 
>
> *on quit  
>  with timeout of 3600 seconds  
>  if isOLast is "online" then fnTwitter("I am offline now! // " & (current date), true)  
>  fnShellSSHEnd(true)  
>  fnAppQuit()  
>  continue quit  
>  end timeout  
> end quit* 
>
> *on idle  
>  with timeout of 3600 seconds  
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
>  end timeout  
>  return 60  
> end idle* 
>
> *(* ======= Functions ======= *)  
> to fnCheckNet()  
>  try  
>  do shell script "curl --connect-timeout 30 "apple.com/favicon.ico""  
>  if isOLast is not "online" then SmartSay({"Online"})  
>  return true  
>  on error  
>  if isOLast is not "offline" then SmartSay({"Offline"})  
>  return false  
>  end try  
> end fnCheckNet* 
>
> *to fnAppStart()  
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
> end fnAppStart* 
>
> *to fnAppQuit()  
>  if (count appQuitList) > 0 then  
>  SmartSay({"Quit Applications"  
> ;})  
>  try  
>  repeat with intSti from 1 to count appQuitList  
>  tell application (item intSti of appQuitList) to quit  
>  end repeat  
>  SmartSay({"OK"})  
>  on error  
>  SmartSay({"Failed"})  
>  end try  
>  end if  
> end fnAppQuit* 
>
> *to fnSSHCnt()  
>  if (length of SSHServerName) > 0 and (length of SSHUserName) > 0 and (length of SSHPasswd) > 0 then  
>  set timeTry to 0  
>  repeat while fnCheckSSHD() is false  
>  SmartSay({"Connect SSH D"})  
>  if timeTry > 0 then if (button returned of (display dialog "ssh -D connection failed." & return & "" buttons {"Retry", "Ignore"})) is "Ignore" then exit repeat  
>  fnShellSSH()  
>  set timeTry to timeTry + 1  
>  end repeat  
>  end if  
> end fnSSHCnt* 
>
> *to fnCheckSSHD()  
>  try  
>  do shell script "curl --socks5 127.0.0.1:7070 --connect-timeout 30 "apple.com/favicon.ico""  
>  if timeTry > 0 then SmartSay({"OK"})  
>  return true  
>  on error  
>  if timeTry > 0 then SmartSay({"Failed"})  
>  return false  
>  end try  
> end fnCheckSSHD* 
>
> *to fnShellSSH()  
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
> end fnShellSSH* 
>
> *to fnShellSSHEnd(isSay)  
>  if (length of SSHServerName) > 0 and (length of SSHUserName) > 0 and (length of SSHPasswd) > 0 then  
>  if isSay is true then SmartSay({"Disconnect SSH D"})  
>  try  
>  do shell script "killall ssh"  
>  do shell script "killall ssh-agent"  
>  do shell script "rm ~/Downloads/.Flora_ssh-D.out"  
>  end try  
>  end if  
> end fnShellSSHEnd* 
>
> *to fnTwitter(strTwText, isSay)  
>  if (length of TwitterUsername) > 0 and (length of TwitterPassword) > 0 and (length of strTwText) > 0 then  
>  if (length of strTwText) > 140 then  
>  set strTwText to (characters 1 through 137 of strTwText as string) & "..."  
>  end if  
>  if isSay is true then SmartSay({"Update Twitter state"})  
>  try  
>  do shell script "curl --connect-timeout 30 --user " & (quoted form of (TwitterUsername & ":" & TwitterPassword)) & " --data-binary " & (quoted form of ("status=" & strTwText)) & " "*[*https://twitter.com/statuses/update.json""*](https://twitter.com/statuses/update.json)  
>  *if isSay is true then SmartSay({"OK"})  
>  on error  
>  if isSay is true then  
>  SmartSay({"Failed"})  
>  else  
>  SmartSay({"Update Twitter state failed"})  
>  end if  
>  end try  
>  end if  
> end fnTwitter* 
>
> *to fnDNSShell()  
>  try  
>  set DNSResponse to (do shell script "curl --connect-timeout 30 "*[*https://"*](https://) *& DNSUsername & ":" & DNSPassword & "@updates.dnsomatic.com/nic/update?&wildcard=NOCHG&mx=NOCHG&backmx=NOCHG"")  
>  if first word of DNSResponse is "good" then -- (second word of DNSResponse) is IP address  
>  return true  
>  else  
>  return false  
>  end if  
>  on error  
>  return false  
>  end try  
> end fnDNSShell* 
>
> *to fnDNSUpdate()  
>  if (length of DNSUsername) > 0 and (length of DNSPassword) > 0 then  
>  SmartSay({"Update dynamic IP"})  
>  if fnDNSShell() is true then  
>  SmartSay({"OK"})  
>  else  
>  SmartSay({"Failed"})  
>  end if  
>  end if  
> end fnDNSUpdate* 
>
> *to fnURLec(strToUEC)  
>  return do shell script "python -c 'import sys, urllib; print urllib.quote(sys.argv[1])' "" & strToUEC & """  
> end fnURLec* 
>
> *to fniTunesisActive()  
>  tell application "System Events" to return (name of processes contains "iTunes")  
> end fniTunesisActive* 
>
> *to fuisiTunesNUD()  
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
>  return false  
>  end if  
>  else  
>  return false  
>  end if  
>  end tell  
>  else  
>  return false  
>  end if  
> end fuisiTunesNUD* 
>
> *to SmartSay(strToSay)  
>  set isiTPing to false  
>  if fniTunesisActive() is true then  
>  tell application "iTunes" to if player state is playing then set isiTPing to true  
>  end if  
>  if isiTPing is true then  
>  tell application "iTunes"  
>  set iTsORSoundVolume to sound volume  
>  set timeTry to 0  
>  repeat while timeTry < 10  
>  set timeTry to timeTry + 1  
>  set sound volume to iTsORSoundVolume *  
> (15 - timeTry) / 15  
>  delay 0.1  
>  end repeat  
>  end tell  
>  repeat with intSti from 1 to (count strToSay)  
>  say "" & (item intSti of strToSay)  
>  if intSti < (count strToSay) then delay 1  
>  end repeat  
>  tell application "iTunes"  
>  set timeTry to 10  
>  repeat while timeTry > 0  
>  set timeTry to timeTry - 1  
>  set sound volume to iTsORSoundVolume * (15 - timeTry) / 15  
>  delay 0.1  
>  end repeat  
>  end tell  
>  else  
>  say "" & strToSay  
>  end if  
> end SmartSay* 
>
> *to fnMusic(isOnline)  
>  if fuisiTunesNUD() is true then  
>  SmartSay({strSNGName, strSNGArtist})  
>  if isOnline is true then  
>  if (length of LastfmUsername) > 0 and (length of LastfmPassword) > 0 then  
>  try  
>  do shell script "curl --connect-timeout 30 "*[*http://lastfmstats.livefrombmore.com/universalscrobbler/scrobble.php?submissionType=track"*](http://lastfmstats.livefrombmore.com/universalscrobbler/scrobble.php?submissionType=track) *& "&username=" & LastfmUsername & "&password=" & LastfmPassword & "&artist=" & fnURLec(strSNGArtist) & "&track=" & fnURLec(strSNGName) & "&album=" & fnURLec(strSNGAlbum) & "&number=" & strSNGTrackNumber & "&duration=" & strSNGDuration & """  
>  on error  
>  SmartSay({"Scrobbling Failed"})  
>  end try  
>  fnTwitter("I am listening to #" & strSNGName & " by #" & strSNGArtist & " in album #" & strSNGAlbum & ". // " & (current date), false)  
>  end if  
>  end if  
>  end if  
> end fnMusic*
