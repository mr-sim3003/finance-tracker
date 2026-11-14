from django.contrib import admin

from .models import Category, ImportJob, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    search_fields = ('name',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'type', 'amount', 'category', 'owner')
    list_filter = ('type', 'category', 'owner')
    search_fields = ('description',)



@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'user', 'status', 'created_count', 'skipped_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('file_name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')