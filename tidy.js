'use strict';

var fs        = require('fs');
var path      = require('path');

var files = [];
fs.readdirSync('./_posts').filter(function(file) {
    return (file.indexOf('.') !== 0);
}).forEach(function(file) {
    files.push(path.join(__dirname, '_posts', file));
});

var used = {};

for (var i in files) {
    var content = fs.readFileSync(files[i], 'UTF8');
    content = content.split('\n');
    var title = null;
    for (var j in content) {
        if (/^title: .*$/.test(content[j])) {
            title = content[j].replace(/^title: (.*)$/, '$1');
            title = title.replace(/^("|')|("|')$/g, '');
            title = title.replace(/&ldquo;/g, '"');
            title = title.replace(/&rdquo;/g, '"');
            title = title.replace(/&mdash;/g, '-');
            title = title.replace(/\ +/g, '-');
            title = title.replace(/\//g,  '-');
            title = title.replace(/\-+/g, '-');
            var oriTit = title;
            var k = 1;
            while (used[title]) {
                k++;
                title = oriTit + '-' + k;
            }
            used[title] = true;
        }
    }
    if (title) {
        var date = files[i].replace(/([0-9]{4}-[0-9]{2}-[0-9]{2})-.*/, '$1');
        var newTitle = date + '-' + title + '.html';
        fs.renameSync(files[i], newTitle);
        console.log(newTitle);
    }
}
