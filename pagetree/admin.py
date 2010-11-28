from models import Section, Hierarchy, PageBlock
from django.contrib import admin

class PageBlockInlineAdmin(admin.StackedInline):
    model = PageBlock
    extra = 0
    fields = ('label', )
    template = 'admin/pagetree/pageblock/edit_inline/stacked.html'
    
class SectionAdmin(admin.ModelAdmin):
    list_display = ('label', 'slug')
    fields = ('label', 'slug')

    inlines = [ PageBlockInlineAdmin, ]
    
    def changelist_view(self, request, extra_context=None):
        my_context = {
            'hierarchies': Hierarchy.objects.all()
        }
        return super(SectionAdmin, self).changelist_view(request, extra_context=my_context)

admin.site.register(Section, SectionAdmin)
admin.site.register(Hierarchy)

    
