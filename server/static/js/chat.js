/*<div class="chat" id="chat">
*     <div class="msgs">
*         <div class="container"></div>
*     </div>
*     <div class="input">
*         <span class="gt">&gt;</span>
*         <input type="text">
*         <button class="send"><img src="/static_/svg/ic_keyboard_enter_24px_white.svg"></button>
*     </div>
* </div>
**/


$(function () {
    $(".chat .msgs").mCustomScrollbar({
        theme: 'minimal'
    });
    $('.chat').focusin(function () {
        $(this).addClass('on');
    }).focusout(function () {
        $(this).removeClass('on');
    });

    $('.chat input').keypress(function (e) {
        if (e.which == 13) {
            send_msg();
        }
    });

    $('.chat button').click(send_msg);
});

function send_msg() {
    var input = $('.chat input');
    var msg = input.val();
    if (!msg.length) return;
    $.post('/api/chat', {msg: msg});
    input.val('');
}

function receiveMsg(msg, from, hand) {
    var DOMmsg = $("<div class='msg" + ((hand == myHand) ? " my'" : "'") + ">" +
        "   <span class='from'>" + from + ": </span>" +
        "   <span class='body'>" + msg + "</span>" +
        "</div>").css({opacity: 0, transition: 'opacity 0.5s ease'});
    $('.chat .msgs .container').append(DOMmsg);
    setTimeout(function () {
        DOMmsg.css({opacity: 1})
    }, 16);
    $('.chat .msgs').mCustomScrollbar('update').mCustomScrollbar('scrollTo', 'bottom', {
        scrollInertia: 200
    });//.find('.mCustomScrollBox').css({maxHeight: 150});
}