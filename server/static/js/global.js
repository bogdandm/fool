function addLoadBar(element, data){
    var bar = $('<div class="loading-bar"><div class="loading"></div><div class="background"></div></div>');
    if (data) {
        if (data.position && data.position=='top') bar.css({bottom: '', top: 0});
        if (data.color) bar.children().css({color: data.color});
    }
    return element.append(bar).find('.loading-bar');
}
