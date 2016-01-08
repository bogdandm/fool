/**
 * Created by Bogdan on 08.01.2016.
 */

$(function () {
    initFriend();
});

function findUser(userName) {
    var box = $('#find-user-box');
    box.find('.None').hide();
    box.find('.user').remove();
    $('header .loading-bar').slideDown();
    $.getJSON('api/users/find?name=' + userName,
        function (data) {//.user
            var box = $('#find-user-box');
            var none = box.find('.None');
            if (data.length) {
                none.hide();
                data.sort(function (a, b) {
                    var d = b.mutual_friends.length - a.mutual_friends.length;
                    if (d)
                        return d;
                    else
                        return compareStrings(a.name, b.name);
                });
                $.each(data, function (key, val) {
                    if (key > 50) return false;
                    /** @namespace val.name */
                    /** @namespace val.status */
                    /** @namespace val.avatar */
                    /** @namespace val.mutual_friends */
                    var friendHTML = $('.hidden > .user').clone();
                    friendHTML.attr('name', val.name);
                    friendHTML.find('.name').text(val.name);
                    friendHTML.find('.status').text(val.status);
                    friendHTML.find('.mutual').text(val.mutual_friends.length);
                    friendHTML.find('img.avatar').attr('src', val.avatar);
                    if (val.status == "Online")
                        friendHTML.removeClass('play').addClass('online');
                    else if (val.status == "Offline")
                        friendHTML.removeClass('online').removeClass('play');
                    else
                        friendHTML.removeClass('online').addClass('play');
                    $("#friends-two").find("#find-user-box  .result .body").append(friendHTML);
                });
            } else {
                none.show();
            }
        }).always(function () {
        $('header .loading-bar').slideUp();
    }).fail(function () {
        box.find('.None').show();
    });
}

function initFriend() {
    $('#friend-dialog').css({transform: 'scale(0, 0)'}).hide();
    $("#friends-one").mCustomScrollbar({
        theme: 'minimal-dark'
    });

    $("#find-user-box").find(".result").mCustomScrollbar({
        theme: 'minimal-dark',
        axis: 'y'
    });

    $('#find-user-btn').click(function () {
        findUser($('#find-user').val());
    });

    $('#find-user').keypress(function (e) {
        if (e.which == 13)
            findUser($('#find-user').val());
    })
}

var INVITED = 0, ACCEPTED = 1;
function addFriend(user, mode) {
    /** @namespace user.name */
    /** @namespace user.status */
    /** @namespace user.avatar */
    var friendHTML = $('.hidden > .friend').clone();
    friendHTML.attr('name', user.name);
    friendHTML.find('.name').text(user.name);
    friendHTML.find('.status').text(mode == ACCEPTED ? user.status : "Приглашение в друзья");
    friendHTML.find('> img').attr('src', user.avatar);
    if (user.status == "Online")
        friendHTML.removeClass('play').addClass('online');
    else if (user.status == "Offline")
        friendHTML.removeClass('online').removeClass('play');
    else
        friendHTML.removeClass('online').addClass('play');
    if (mode == INVITED) {
        friendHTML.find('button.more').hide();
        friendHTML.addClass('invited').find('button.add').show();
        friendHTML.find('button.reject').show();
    }
    $("#friends-one").find(".body").append(friendHTML);
}

function friendsLoad() {
    $('header .loading-bar').slideDown();
    var loading = 0;
    var length = 0;

    function loadFriends() {
        $.ajax({
                dataType: "json",
                url: '/api/users/get_friend_list',
                success: function (data) {
                    length += data.length;
                    $("#friends-one").show();
                    $.each(data, function (key, val) {
                        addFriend(val, ACCEPTED);
                    });
                    $('.friend button.more').click(function (e) {
                        showMenu($('#friend-dialog'), $(this).parents().filter('.friend'), {
                            directVert: 'top',
                            directHoriz: 'right'
                        });
                    })
                }
            }
        ).
        always(function () {
            loading++;
            if (loading == 2) $('header .loading-bar').slideUp();
            if (!length && !loading)
                $("#friends-one").hide();
        });
    }

    $.ajax({
            dataType: "json",
            url: '/api/users/get_friend_list?invited',
            success: function (data) {
                length += data.length;
                $.each(data, function (key, val) {
                    addFriend(val, INVITED);
                });
                $('.friend button.add').click(function (e) {
                    //TODO
                });
                $('.friend button.reject').click(function (e) {
                    //TODO
                })
            }
        }
    ).
    always(function () {
        loading++;
        if (loading == 2) $('header .loading-bar').slideUp();
        if (!length && !loading)
            $("#friends-one").hide();
        loadFriends();
    });
}

function friendsUnload() {
    $("#friends-one").find(".body").empty();
}