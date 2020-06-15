odoo.define('website_blog.s_latest_posts_editor', function (require) {
'use strict';

var core = require('web.core');
var sOptions = require('web_editor.snippets.options');

var _t = core._t;

sOptions.registry.js_get_posts_limit = sOptions.Class.extend({

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * @see this.selectClass for parameters
     */
    postsLimit: function (previewMode, value, $opt) {
        value = parseInt(value);
        this.$target.attr('data-posts-limit', value).data('postsLimit', value);
        this.trigger_up('animation_start_demand', {
            editableMode: true,
            $target: this.$target,
        });
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _setActive: function () {
        var self = this;
        this._super.apply(this, arguments);
        this.$('[data-posts-limit]').addBack('[data-posts-limit]')
            .removeClass('active')
            .filter(function () {
                return (self.$target.data('postsLimit') || 3) == $(this).data('postsLimit');
            })
            .addClass('active');
    },
});

sOptions.registry.js_get_posts_selectBlogPost = sOptions.Class.extend({
    /**
     * @override
     */
    start: function () {
        var self = this;
        console.log('js_get_posts_selectBlogPost');
        console.log(this);

        var def = this._rpc({
            model: 'blog.post',
            method: 'search_read',
            args: [[], ['name', 'id']],
        }).then(function (blogs) {
            var $menu = self.$el.find('[data-filter-by-blog-post-id="0"]').parent();
            _.each(blogs, function (blog) {
                $menu.append($('<a/>', {
                    class: 'dropdown-item',
                    'data-filter-by-blog-post-id': blog.id,
                    'data-no-preview': 'true',
                    text: blog.name,
                }));
            });
        });

        return $.when(this._super.apply(this, arguments), def);
    },

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * @see this.selectClass for parameters
     */
    filterByBlogPostId: function (previewMode, value, $opt) {
        console.log('filterByBlogPostId');
        console.log(this);
        value = parseInt(value);
        var self = this;

        var def = $.Deferred();
        this._rpc({
            route: '/blog/render_latest_posts',
            params: {
                template: 'blog_post_three.blog_column',
                domain: [['id', '=', value]],
                limit: 1,
            },
        }).then(function (posts) {
            console.log(posts);
            var $posts = $(posts).filter('.s_latest_posts_post');
            console.log($posts);
            _.each(['data-oe-model', 'data-oe-field', 'data-oe-xpath', 'data-oe-data'], function(attr){
                $posts.find("[" + attr + "]").removeAttr(attr)});
            if (!$posts.length) {
                self.$target.append($('<div/>', {class: 'col-md-6 offset-md-3'})
                    .append($('<div/>', {
                        class: 'alert alert-warning alert-dismissible text-center',
                        text: _t("No blog post was found. Make sure your posts are published."),
                    })));
                return;
            }

            // if (loading && loading === true) {
            //     // Perform an intro animation
            //     self._showLoading($posts);
            // } else {
                self.$target.replaceWith($posts);
            // }
        }, function (e) {
            if (self.editableMode) {
                self.$target.append($('<p/>', {
                    class: 'text-danger',
                    text: _t("An error occured with this latest posts block. If the problem persists, please consider deleting it and adding a new one"),
                }));
            }
        }).always(def.resolve.bind(def));



        this.$target.attr('data-filter-by-blog-id', value).data('filterByBlogId', value);
        this.trigger_up('animation_start_demand', {
            editableMode: true,
            $target: this.$target,
        });
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _setActive: function () {
        var self = this;
        this._super.apply(this, arguments);
        this.$('[data-filter-by-blog-id]').addBack('[data-filter-by-blog-id]')
            .removeClass('active')
            .filter(function () {
                return (self.$target.data('filterByBlogId') || 0) == $(this).data('filterByBlogId');
            })
            .addClass('active');
    },
});
});
