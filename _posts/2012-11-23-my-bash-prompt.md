---
layout: post
status: publish
published: true
title: My Bash Prompt
author: Leask




author_login: leask
author_email: i@leaskh.com
author_url: https://leaskh.com
wordpress_id: 1986
wordpress_url: https://leaskh.com/?p=1986
date: '2012-11-23 01:20:32 +0800'
date_gmt: '2012-11-22 17:20:32 +0800'
categories:

tags: []
comments: []
---

[![](/public/2012/11/Screen-Shot-2012-11-23-at-1.17.10-AM.png "Screen Shot 2012-11-23 at 1.17.10 AM")](/public/2012/11/Screen-Shot-2012-11-23-at-1.17.10-AM.png)

有人在 twitter 上问我的 bash prompt 是怎么写的，简单解说无效，直接把代码贴出来吧：

```
git_inspect_branch() {
    git branch 2> /dev/null | grep ^* | sed 's/^\* \(.*\)$/:\1/g'<br />
}
git_inspect_added() {
    [[ $(git status 2> /dev/null | grep 'Untracked files:') != '' ]] && echo '+'<br />
}
git_inspect_modified() {
    [[ $(git status 2> /dev/null | grep 'modified:')        != '' ]] && echo '*'<br />
}
git_inspect_deleted() {
    [[ $(git status 2> /dev/null | grep 'deleted:')         != "" ]] && echo "-"<br />
}
git_inspect_dirty() {
    echo "$(git_inspect_added)$(git_inspect_modified)$(git_inspect_deleted)"<br />
}
NME="\u"<br />
HST="\h"<br />
DIR="\w"<br />
PMT="\$"<br />
RED="\[\033[31m\]"<br />
GEN="\[\033[32m\]"<br />
YEL="\[\033[33m\]"<br />
OFF="\[\033[m\]"<br />
MOD="\`if [ \$? = 0 ]; then echo :\); else echo :\(; fi\`"<br />
GIT="\`git_inspect_branch\`"<br />
DIF="\`git_inspect_dirty\`"<br />
PMT="\`if [ "$(id -u)" = "0" ]; then echo '#'; else echo '>'; fi\`"<br />
PS1="$MOD $NME@$RED$HST$OFF:$DIR$GEN$GIT$OFF$RED$DIF$OFF$PMT "
```

PS: Prompt 不包括那头小牛，那头小牛其实是这样写的: alias cowtune='fortune | cowsay'

------- ------- -------

Updated[Dec 5, 2012]: 放到 Github 上了 [https://gist.github.com/4153091](https://gist.github.com/4153091 "Flora Prompt")
