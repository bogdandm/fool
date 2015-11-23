/**
 * Created by Bogdan on 07.10.2015.
 */

function disableAllCards() {
    $('#hand2').find('.card').removeClass('on');
}

function attack(str) {
    var arena = $('#arena');
    var pair = $('.hidden > .pair').clone();
    var card = $('.hidden > .card').clone();
    card.find('img').attr({src: "/static_/svg/" + str + ".svg"});
    card.attr({value: str});
    pair.append(card);
    arena.append(pair);
}

function defense(str) {
    var pair = $('#arena').find('.pair').last();
    var card = $('.hidden > .card').clone();
    card.find('img').attr({src: "/static_/svg/" + str + ".svg"});
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
    card.find('img').attr({src: "/static_/svg/Blue_Back.svg"});
    hand.append(card);
    if (mode == 'SET')
        card.attr({value: 0}).css({left: body.width() + 40, top: body.height() / 2});
    else if (mode == 'TABLE')
        card.attr({value: 0}).css({top: body.height() / 4}, 0);
    card.animate({
        left: 0, top: 0,
        complete: function () {
            $(this).css({left: '', top: ''});
        }
    }, ((mode == 'SET') ? 1000 : 100));
}

function addCard2(str, mode) {
    mode = mode || 'SET';
    var body = $('body');
    var hand = $('#hand2');
    var card = $('.hidden > .card').clone();
    card.find('img').attr({src: "/static_/svg/" + str + ".svg"});
    hand.append(card);
    if (mode == 'SET')
        card.attr({value: str}).css({left: body.width() * 1.1, top: -body.height() / 2});
    else if (mode == 'TABLE')
        card.attr({value: str}).css({top: -body.height() / 4});
    card.animate({
        left: 0, top: 0,
        complete: function () {
            $(this).css({left: '', top: ''});
        }
    }, ((mode == 'SET') ? 1000 : 100));
}

function setTrump(str) {
    var card = $('#trump').find('.card');
    if (str != 'None') {
        card.find('.card_border').css({transform: ''});
        card.find('img').attr({src: "/static_/svg/" + str + ".svg"});
        data['trump_suit'] = getCardSuit(str);
    }
    else {
        card.find('.card_border').css({transform: 'rotate(-90deg)'});
        card.find('img').attr({src: "/static_/svg/" + data['trump_suit'] + ".svg"});
    }
}

function decrSet(n) {
    if (n == 0)
        $('#set').find('.card').eq(0).hide();
    if (n <= (39 - 39 / 3 * 2))
        $('#set').find('.card').eq(1).hide();
    if (n <= (39 - 39 / 3))
        $('#set').find('.card').eq(2).hide();
}