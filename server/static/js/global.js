function addLoadBar(element, data) {
    /** @namespace val.position */
    /** @namespace val.color */
    var bar = $('<div class="loading-bar"><div class="loading"></div><div class="background"></div></div>');
    if (data) {
        if (data.position && data.position == 'top') bar.css({bottom: '', top: 0});
        if (data.color) bar.children().css({color: data.color});
    }
    return element.append(bar).find('.loading-bar');
}

function compareStrings(str1, str2) {
    var rx = /([^\d]+|\d+)/ig;
    var str1split = str1.match(rx);
    var str2split = str2.match(rx);
    for (var i = 0, l = Math.min(str1split.length, str2split.length); i < l; i++) {
        var s1 = str1split[i],
            s2 = str2split[i];
        if (s1 === s2) continue;
        if (isNaN(+s1) || isNaN(+s2))
            return s1 > s2 ? 1 : -1;
        else
            return +s1 - s2;
    }
    return 0;
}

function showMenu(menu, elem, data) {
    /** @namespace data.directVert */
    /** @namespace data.directHoriz */
    menu.css({
        transform: 'scale(0, 0)',
        display: 'none',
        transition: 'transform 0s easy'
    });
    menu.css('transform-origin', data.directHoriz + ' ' + data.directVert);
    menu.addClass('transition-transform');

    var x = elem.position();
    menu.css({
        transition: '0.5s',
        display: 'block',
        top: x.top + (data.directVert === 'bottom' ? elem.height() - menu.outerHeight() + 3 : -3),
        left: x.left + (data.directHoriz === 'right' ? elem.width() - menu.outerWidth() + 3 : -3)
    });

    $('html').unbind();

    setTimeout(function () {
        menu.css({transform: 'scale(1, 1)'});

        $('html').click(function () {
            menu.css({transform: 'scale(0, 0)'});
            setTimeout(function () {
                menu.hide();
            }, 500);
            $(this).unbind('click');
        });

        menu.click(function (event) {
            event.stopPropagation();
        });

    }, 32);
}