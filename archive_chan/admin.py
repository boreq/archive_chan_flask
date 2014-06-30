from django.contrib import admin
from archive_chan.models import Board, Thread, Post, Image, Tag, Trigger, TagToThread, Update
from django.conf import settings

class BoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'active']
    list_filter = ['active']

class ThreadAdmin(admin.ModelAdmin):
    list_display = ['board', 'number', 'saved', 'auto_saved', 'replies', 'images', 'first_reply', 'last_reply']
    list_filter = ['board']
    search_fields = ['number']

class PostAdmin(admin.ModelAdmin):
    list_display = ['number', 'time', 'name', 'trip', 'email', 'subject', 'comment']
    search_fields = ['number']

class TagAdmin(admin.ModelAdmin):
    pass

class TagToThreadAdmin(admin.ModelAdmin):
    pass

class TriggerAdmin(admin.ModelAdmin):
    list_display = ['field', 'event', 'phrase', 'case_sensitive', 'post_type', 'save_thread', 'tag_thread']

class UpdateAdmin(admin.ModelAdmin):
    list_display = ['board', 'start', 'end', 'used_threads', 'total_time', 'wait_time', 'download_time', 'processed_threads', 'added_posts', 'removed_posts', 'downloaded_images', 'downloaded_thumbnails', 'downloaded_threads', 'status']
    list_filter = ['status']


admin.site.register(Board, BoardAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Trigger, TriggerAdmin)

if (settings.DEBUG):
    admin.site.register(Thread, ThreadAdmin)
    admin.site.register(Post, PostAdmin)
    admin.site.register(TagToThread, TagToThreadAdmin)
    admin.site.register(Update, UpdateAdmin)
