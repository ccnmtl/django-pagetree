/* global pagetree: true */

pagetree.getCsrfToken = function() {
    return pagetree.$('[name=csrfmiddlewaretoken]').val();
};

pagetree.saveOrderOfChildren = function(url) {
    const me = this;
    const params = {};
    let worktodo = false;

    pagetree.$('#children-order-list li').each(function(index, element) {
        worktodo = true;
        const id = pagetree.$(element).attr('id').split('-')[1];
        params['section_id_' + index] = id;
    });

    if (worktodo) {
        pagetree.$.ajax({
            type: 'POST',
            url: url + (url.indexOf('?') === -1 ? '?' : '&') + pagetree.$.param(params),
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', me.getCsrfToken());
            }
        });
    }
};

pagetree.saveOrderOfPageBlocks = function(url) {
    const me = this;
    const params = {};
    let worktodo = false;

    pagetree.$('#edit-blocks-tab>div.block-dragger').each(
        function(index, element) {
            worktodo = true;
            const id = pagetree.$(element).attr('id').split('-')[1];
            params['pageblock_id_' + index] = id;
        });

    if (worktodo) {
        /* only bother submitting if there are elements to be sorted */
        pagetree.$.ajax({
            type: 'POST',
            url: url + (url.indexOf('?') === -1 ? '?' : '&') + pagetree.$.param(params),
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', me.getCsrfToken());
            }
        });
    }
};
