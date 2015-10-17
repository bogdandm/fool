/**
 * Created by Bogdan on 07.10.2015.
 */

function attack(str) {
    var arena = $('#arena');
    var pair = $('.hidden > .pair').clone();
    var card = $('.hidden > .card').clone();
    card.find('img').attr({src: "./static_/svg/" + str + ".svg"});
    card.attr({value: str});
    pair.append(card);
    arena.append(pair);
}

function defense(str) {
    var pair = $('#arena').find('.pair').last();
    var card = $('.hidden > .card').clone();
    card.find('img').attr({src: "./static_/svg/" + str + ".svg"});
    card.attr({value: str});
    pair.append(card);
}

function delCard1() {
    var card = $('#hand1').find('.card').last().css({width: 0}).find('img').css({opacity: 0});
    setTimeout(function () {
        $('#hand1').find('.card').last().remove();
    }, 400)
}

function delCard2(str) {
    var card = $('#hand2').find('.card[value=' + str + ']').css({width: 0}).find('img').css({opacity: 0});
    setTimeout(function () {
        $('#hand2').find('.card[value=' + str + ']').last().remove();
    }, 400)
}

function addCard1(mode) {
    mode = mode || 'SET';
    var body = $('body');
    var hand = $('#hand1');
    var card = $('.hidden > .card').clone();
    card.find('img').attr({src: "./static_/svg/Blue_Back.svg"});
    hand.append(card);
    if (mode == 'SET')
        card.attr({value: 0}).css({
            left: body.width() * 1.5 + 'px',
            top: body.height() / 2 + 'px'
        });
    else if (mode == 'TABLE')
        card.attr({value: 0}).css({
            top: body.height() / 4 + 'px'
        });
    card.animate({left: '0', top: '0', opacity: 1}, {duration: 4000, easing: 'swing'});
}

function addCard2(str, mode) {
    mode = mode || 'SET';
    var body = $('body');
    var hand = $('#hand2');
    var card = $('.hidden > .card').clone();
    card.find('img').attr({src: "./static_/svg/" + str + ".svg"});
    hand.append(card);
    if (mode == 'SET')
        card.attr({value: str}).css({
            left: body.width() * 1.5 + 'px',
            top: -body.height() / 2 + 'px'
        });
    else if (mode == 'TABLE')
        card.attr({value: str}).css({
            top: -body.height() / 4 + 'px'
        });
    card.animate({left: '0', top: '0', opacity: 1}, {
        duration: 4000, easing: 'swing',
        complete: function () {
            $(this).css({left: '', top: '', opacity: ''});
        }
    });
}

function setTrump(str) {
    var card = $('#trump').find('.card');
    if (str != 'None')
        card.find('img').attr({src: "./static_/svg/" + str + ".svg"});
    else
        card.hide();
    data['trump_suit'] = new RegExp('[A-Z]').exec(str)[0]
}

function decrSet(n) {
    if (n == 0)
        $('#set').find('.card').eq(0).hide();
    if (n <= (39 - 39 / 3 * 2))
        $('#set').find('.card').eq(1).hide();
    if (n <= (39 - 39 / 3))
        $('#set').find('.card').eq(2).hide();
}