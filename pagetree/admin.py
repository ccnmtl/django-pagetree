from models import Section, Hierarchy, PageBlock
from django.contrib import admin

class PageBlockInline(admin.StackedInline):
    model = PageBlock
    extra = 0
    fields = ('label', )
    template = 'admin/pagetree/pageblock/edit_inline/stacked.html'

class SectionAdmin(admin.ModelAdmin):
    list_display = ('label', 'slug')
    fields = ('label', 'slug')

    inlines = [ 
            PageBlockInline,
        ]

admin.site.register(Section, SectionAdmin)

    
