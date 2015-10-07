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
    $('#hand1').find('.card').last().remove();
}

function delCard2(str) {
    $('#hand2').find('.card[value=' + str + ']').remove();
}

function addCard1() {
    var hand = $('#hand1');
    var card = $('.hidden > .card').clone();
    card.find('img').attr({src: "./static_/svg/Blue_Back.svg"});
    card.attr({value: 0});
    hand.append(card).hide().fadeIn();
}

function addCard2(str) {
    var hand = $('#hand2');
    var card = $('.hidden > .card').clone();
    card.find('img').attr({src: "./static_/svg/" + str + ".svg"});
    card.attr({value: str});
    hand.append(card).hide().fadeIn();
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
    if (n == 0) {
        $('#set').find('.card').hide();
    } else if (n <= (39 - 39 / 3 * 2)) {
        $('#set').find('.card:not(:last)').hide();
    } else if (n <= (39 - 39 / 3)) {
        $('#set').find('.card:last').hide();
    }
}