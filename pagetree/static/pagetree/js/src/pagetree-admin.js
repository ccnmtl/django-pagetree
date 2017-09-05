/* global pagetree: true */

pagetree.getCsrfToken = function() {
    return pagetree.$.cookie('csrftoken');
};

pagetree.saveOrderOfChildren = function(url) {
    var me = this;
    var worktodo = 0;
    pagetree.$('#children-order-list li').each(function(index, element) {
        worktodo = 1;
        var id = $(element).attr('id').split('-')[1];
        url += 'section_id_' + index + '=' + id + ';';
    });
    if (worktodo == 1) {
        pagetree.$.ajax({
            type: 'POST',
            url: url,
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', me.getCsrfToken());
            }
        });
    }
};

pagetree.saveOrderOfPageBlocks = function(url) {
    var me = this;
    var worktodo = 0;
    pagetree.$('#edit-blocks-tab>div.block-dragger').each(
        function(index, element) {
            worktodo = 1;
            var id = $(element).attr('id').split('-')[1];
            url += 'pageblock_id_' + index + '=' + id + ';';
        });
    if (worktodo == 1) {
        /* only bother submitting if there are elements to be sorted */
        pagetree.$.ajax({
            type: 'POST',
            url: url,
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', me.getCsrfToken());
            }
        });
    }
};
