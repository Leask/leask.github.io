// Flora AntiGFW PAC
// by Leask Huang
// www.leaskh.com

function FindProxyForURL(url, host)
{
    // 0 direct
    // 1 proxy
    var list = [
        // Google
        [1, 'google'],
        [1, 'blogger.com'],
        [1, 'appspot.com'],
        [1, 'blogspot.com'],
        [1, 'youtube.com'],
        [1, 'ytimg.com'],
        [1, 'emailintervention.com'],
        [1, 'feedburner.com'],

        [1, 'dropbox.com'],
        [1, 'doctype.tv'],
        [1, 'twitter'],
        [1, 't.co'],
        [1, 'facebook.com'],
        [1, 'fbcdn.net'],
        [1, 'bullogger.com'],
        [1, 'rthk.'],
        [1, 'nextmedia.com'],
        [1, 'cl.ly'],
        [1, 'ow.ly'],
        [1, 'sparrowmailapp.com'],
        [1, 'w3schools.com'],
        [1, 'box.net'],
        [1, 'bit.ly'],
        [1, 'klip.me'],
        [1, 'j.mp'],
        [1, 'vimeo.com'],
        [1, 'mediafire.com'],
        [1, 'wordpress.com'],
        [1, 'tistory.com'],
        [1, 'aol.com'],
        [1, 'aim.com'],
        [1, 'cnn.com'],
        [1, 'dw-world.de'],
        [1, 'hellotxt.com'],
        [1, 'iphone-dev.org'],
        [1, 'imzdl.com'],
        [1, 'twitpic.com'],
        [1, 'chinagfw.org'],
        [1, 'zhufeng.me'],
        [1, 'openvpn.net'],
        [1, 'simplenoteapp.com'],
        [1, 'yfrog.com'],
        [1, 'yegle.net'],
        [1, 'myspace.com'],
        [1, '6park.com'],
        [1, 'hutianyi.net'],
        [1, 'drinkbrainjuice.com'],
        [1, 'childsown.com'],
        [1, 'filesonic.com'],
        [1, 'wezone.net'],
        [1, 'globalvoices'],
        [1, 'wikipedia'],
        [1, 'appleactionews.com'],
        [1, 'foursquare.com'],
        [1, 'blog.sparrowmailapp.com'],
        [1, 'tumblr.com'],
        [1, 'xanga.com'],
        [1, 'xuite.net'],
        [1, 'ht.ly'],
        [1, 'hotfile.com'],

        // speed up 
        [1, 'leaskh.com'],
        [1, 'tinygrab.com'],
        [1, 'amazon.com'],
        [1, 'panic.com'],
        [1, 'taskant.com'],
        [1, 'instagr.am'],
        [1, 'd.pr'],
        [1, 'droplr.com'],
        [1, 'cld.me'],

        // international version
        [1, 'skype.com']
    ];

    var rule = [
        'DIRECT',
        {flora        : 'SOCKS 127.0.0.1:8964',
         x            : 'SOCKS 10.0.1.254:8964',
         syxnx        : 'SOCKS 127.0.0.1:8964',
         flora_debian : 'SOCKS5 127.0.0.1:8964'}
    ];

    // get rule id
    var rid   = 0,
        lcUrl = url.toLowerCase();
    for (var i in list) {
        if (shExpMatch(lcUrl, '*' + list[i][1] + '*')) {
            rid = list[i][0];
            break;
        }
    }

    // get local host name
    var local = 'x';
    switch (dnsResolve('whereami')) {
        case '6.11.26.0':
            local = 'flora';
            break;
        case '6.11.26.1':
            local = 'syxnx';
            break;
        case '6.11.26.4':
            local = 'flora_debian';
    }

    // get proxy
    var proxy = rule[0];
    switch (typeof rule[rid]) {
        case 'string':
            proxy = rule[rid];
            break;
        case 'object':
            if (typeof rule[rid][local] !== 'undefined') {
                proxy = rule[rid][local];
            }
    }

    // return
    if (local === 'flora_debian') {
        alert('[' + local + ' ' + rid + ' ' + proxy + '] ' + url);
    }
    return proxy;
}
