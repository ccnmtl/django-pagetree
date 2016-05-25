$(document).ready(function() {
    var $container = $('.pagetree-clone-form');
    var $button = $container.find('button[type="submit"]');
    $button.click(function() {
        var isValid = true;
        $(this).closest('form').find('input[type="text"]')
            .each(function(k, v) {
                if ($.trim($(v).val()) === '') {
                    isValid = false;
                }
            });

        if (isValid) {
            $container.find('.pagetree-loading').css('visibility', 'visible');
        }
    });
});
