from django.contrib import admin
from .models import Concept, ConceptRelation

@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ('title', 'uri', 'created_at')
    search_fields = ('title', 'description')

@admin.register(ConceptRelation)
class ConceptRelationAdmin(admin.ModelAdmin):
    list_display = ('source', 'relation_type', 'target')
    list_filter = ('relation_type',)
    autocomplete_fields = ['source', 'target']
