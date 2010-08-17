from models import Section, Hierarchy, SectionChildren, PageBlock
from django.contrib import admin

class SectionChildrenInline(admin.StackedInline):
    model = SectionChildren
    fk_name = 'parent' 
    extra = 0
    fields = ('child',)
    template = 'admin/pagetree/sectionchildren/edit_inline/stacked.html'
    
class PageBlockInline(admin.StackedInline):
    model = PageBlock
    extra = 0
    fields = ('label', )
    template = 'admin/pagetree/pageblock/edit_inline/stacked.html'

class SectionAdmin(admin.ModelAdmin):
    list_display = ('label', 'slug')
    fields = ('label', 'slug')

    inlines = [ 
            SectionChildrenInline,
            PageBlockInline,
        ]

admin.site.register(Section, SectionAdmin)

    
