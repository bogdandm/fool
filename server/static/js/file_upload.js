function updateProgress(evt) {
    if (evt.lengthComputable) {
        var progress = $('#loading-progress');
        var percentLoaded = Math.round((evt.loaded / evt.total) * 100);
        console.log(percentLoaded);
        if (percentLoaded < 100) {
            progress.css({width: percentLoaded + '%'});
            progress.text(percentLoaded + '%');
        } else {
            progress.hide();
        }
    }
}

function onFileChange() {
    var file = this.files[0];
    if (!file.type.match(/image.*/) || file.size > maxSize * 1024) {
        this.value = '';
        $('#file').replaceWith('<input type="file" id="file">');
        $('#file').change(onFileChange);
        $('#load_text').hide();
        $('#file_error').show();
        setTimeout(function () {
            $('#load_text').show();
            $('#file_error').hide();
        }, 2000);
        return;
    }

    var reader = new FileReader();
    reader.onload = (function (theFile) {
        return function (e) {
            $('#avatar').find('> img').attr('src', e.target.result).css({padding: 0});
            var file = $('#file')[0].files[0];
            var data = new FormData();
            data.append('file', file);
            $('form .loading-bar').slideDown();
            $.ajax({
                url: '/api/add_user', //TODO
                type: 'POST',
                data: data,
                cache: false,
                dataType: 'json',
                processData: false,
                contentType: false,
                complete: function (x) {
                    data = x.responseText;

                    $('form .loading-bar').slideUp();
                }
            });
        };
    })(file);
    reader.onprogress = updateProgress;

    reader.readAsDataURL(file);
}