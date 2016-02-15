/**
 * Created by Bogdan on 08.01.2016.
 */

var userData;

$(function () {
    initGameInvites();
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
                userData = data;
                $.each(data, function (key, val) {
                    if (key > 50) return false;
                    /** @namespace val.name */
                    /** @namespace val.status */
                    /** @namespace val.avatar */
                    /** @namespace val.mutual_friends */
                    /** @namespace val.is_friend */
                    var userHTML = $('.hidden > .user').clone();
                    userHTML.attr('name', val.name);
                    userHTML.find('.name').text(val.name);
                    userHTML.find('.status').text(val.status);
                    userHTML.find('.mutual').text(val.mutual_friends.length);
                    userHTML.find('img.avatar').attr('src', val.avatar);
                    if (val.status == "Online")
                        userHTML.removeClass('play').addClass('online');
                    else if (val.status == "Offline")
                        userHTML.removeClass('online').removeClass('play');
                    else
                        userHTML.removeClass('online').addClass('play');
                    if (val.is_friend)
                        userHTML.find('button.add').removeClass('on')
                            .find('img').attr('src', '/static_/svg/ic_done_24px.svg');
                    else
                        userHTML.find('button.add').click(function () {
                            var this_ = this;
                            $.ajax({
                                url: "/api/users/friend_invite?user=" + val.name,
                                success: function () {
                                    $(this_).unbind('click').removeClass('on')
                                        .find('img').attr('src', '/static_/svg/ic_done_24px.svg');
                                }
                            })
                        });
                    $("#friends-two").find("#find-user-box .result .body").append(userHTML);
                });

                $('#find-user-box').find('.user .mutual').mouseenter(function () {
                    var user = $(this).parent().parent().find(".name").text();
                    var mutual = false;
                    var dialog = $('#mutual_friends_dialog');
                    dialog.find('.user').remove();
                    $.each(userData, function (key, val) {
                        if (val.name == user) {
                            mutual = val.mutual_friends;
                            return false;
                        }
                    });
                    if (mutual) {
                        $.each(mutual, function (key, val) {
                            if (key > 7) return false;
                            var elem = $('<div class="user"><img class="avatar" src=""><div class="name"/></div>');
                            elem.find('.name').text(val);
                            $.ajax({
                                url: '/api/avatar?user=' + val + '&type=round_white',
                                success: function (data) {
                                    elem.find('img').attr('src', data);
                                    dialog.append(elem);
                                },
                                async: false
                            });
                        });
                        var this_ = this;
                        setTimeout(function () {
                            showMenu(dialog, $(this_), {
                                directVert: 'top',
                                directHoriz: 'right',
                                action: 'hover'
                            });
                        }, 10);
                    }
                });
            } else {
                none.show();
            }
        }).always(function () {
            $('header .loading-bar').slideUp();
        }
    ).fail(function () {
        box.find('.None').show();
    });
}

function initFriend() {
    var friendDialog = $('#friend-dialog');
    friendDialog.add('#mutual_friends_dialog').css({transform: 'scale(0, 0)'}).hide();
    friendDialog.find('button.remove').click(function () {
        var friend = $(this).parents().find('#friend-dialog').attr('for');
        $.ajax({
            url: "/api/users/friend_invite?user=" + friend + "&reject",
            success: function () {
                friendsUnload();
                friendsLoad();
            }
        })
    });
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

var INVITED = 0, ACCEPTED = 1, REJECT = 2;
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
                        var dialog = $('#friend-dialog');
                        var a = dialog.find('a');
                        var name = $(this).parents().filter('.friend').attr('name');
                        showMenu(dialog, $(this).parents().filter('.friend'), {
                            directVert: 'top',
                            directHoriz: 'right'
                        });
                        a.attr('href', a.attr('href_tmp').replace('user', name));
                    })
                }
            }
        ).always(function () {
            loading++;
            if (loading == 2) $('header .loading-bar').slideUp();
            if (!length && loading == 2)
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
                $('.friend button.add').click(function () {
                    var user = $(this).parents().filter('.friend').attr('name');
                    $.ajax({
                        url: "/api/users/friend_invite?user=" + user + "&accept",
                        success: function () {
                            friendsUnload();
                            updateMenuInfo();
                            friendsLoad();
                        }
                    })
                });
                $('.friend button.reject').click(function () {
                    var user = $(this).parents().filter('.friend').attr('name');
                    $.ajax({
                        url: "/api/users/friend_invite?user=" + user + "&reject",
                        success: function () {
                            friendsUnload();
                            updateMenuInfo();
                            friendsLoad();
                        }
                    })
                });
            }
        }
    ).always(function () {
        loading++;
        if (loading == 2) $('header .loading-bar').slideUp();
        if (!length && loading == 2)
            $("#friends-one").hide();
        loadFriends();
    });
}

function friendsUnload() {
    $("#friends-one").find(".body").empty();
}

function initGameInvites() {
    $("#games-invites").mCustomScrollbar({
        theme: 'minimal-dark'
    });
}

function gamesInvitesLoad() {
    var gameInvites = $('#games-invites');
    gameInvites.find('.body').append($('<div class="friend" style="color: #9f9f9f;padding: 10px">' +
        'Для отправки приглашения воспользуйтесь вкладкой "Друзья"' +
        '</div>'));
    $.each(invites.game, function (index, value) {
        var userHTML = $('.hidden > .friend').clone();
        userHTML.attr('name', value);
        userHTML.find('.name').text(value);
        userHTML.find('.status').text('Приглашение в игру');
        if (value == 'root') userHTML.find('img.avatar').css({
            borderRadius: '2px'
        });
        $.ajax({
            url: '/api/avatar?user=' + value + '&type=round',
            success: function (data) {
                userHTML.find('img.avatar').attr('src', data);
            }
        });
        userHTML.find('.buttons').hide();
        userHTML.click(function () {
        });
        $("#games-invites-container").find(".body").append(userHTML);
    });

    gameInvites.find('.friend[name]').click(function () {
        var name = $(this).attr('name');
        location.href = '/arena?mode=2&for=' + name
    })
}

function gamesInvitesUnload() {
    $("#games-invites-container").find(".body").empty();
}