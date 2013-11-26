from django.conf.urls import patterns, include

urlpatterns = patterns(
    '',
    (r'^pagetree/', include('pagetree.urls')),
)
