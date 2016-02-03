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
    /** @namespace data.action */
    menu.attr('for', elem.attr('name'));

    function init() {
        if (data.action && data.action == 'hover') {
        }
        else
            $('html').unbind();
        menu.css({transition: '0s'});
        menu.css('transform-origin',
            (data.directHoriz == "left" ? "5%" : "95%") + ' ' + (data.directVert == "top" ? "10%" : "90%"));
        menu.addClass('transition-transform');
    }

    function step1() {
        menu.css({
            transform: 'scale(0, 0)',
            display: 'none'
        });
    }

    function step2() {
        var x = elem.position();
        menu.css({
            transition: '0.5s',
            display: 'block',
            top: x.top + (data.directVert === 'bottom' ? elem.outerHeight() - menu.outerHeight() + 3 : -3),
            left: x.left + (data.directHoriz === 'right' ? elem.outerWidth() - menu.outerWidth() + 3 : -3)
        });
        var d = $(window).height() - 15 - (menu.offset().top + menu.outerHeight());
        if (d < 0)
            menu.css({
                top: x.top + elem.outerHeight() - menu.outerHeight() + 3,
                'transform-origin': data.directHoriz + ' bottom'
            });
    }

    function step3() {
        menu.css({transform: 'scale(1, 1)'});
    }

    function step4() {
        function hide() {
            menu.css({transform: 'scale(0, 0)'});
            menu.attr('state', 'animateHide');
            setTimeout(function () {
                if (menu.attr('state') != 'animate' && menu.attr('state') != 'show') {
                    menu.hide();
                    menu.attr('state', 'hide');
                }
            }, 400);
            $(this).unbind('mouseout');
        }

        if (data.action && data.action == 'hover') {
            var hover = $(':hover');
            if (!(hover.filter(menu).length || hover.filter(elem).length)) hide();
            menu.mouseout(hide);
        }
        else
            $('html').click(function () {
                menu.css({transform: 'scale(0, 0)'});
                setTimeout(function () {
                    menu.hide();
                    menu.attr('state', 'hide');
                }, 400);
                $(this).unbind('click');
            });

        menu.click(function (event) {
            event.stopPropagation();
        });
    }

    init();
    setTimeout(step1, 16);
    menu.attr('state', 'hide');
    setTimeout(step2, 32);
    setTimeout(step3, 64);
    menu.attr('state', 'animate');
    setTimeout(function () {
        menu.attr('state', 'show');
    }, 500);
    setTimeout(step4, 600);
}