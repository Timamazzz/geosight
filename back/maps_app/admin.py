from django.contrib import admin
from .models import Map, MapLayer, Feature, MapStyle, POIConfig, CreateScoringMapLayerTask
from geosight.celery import app


@admin.register(Map)
class MapAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'creator', 'created_at', 'updated_at']
    list_filter = ['creator', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['users']


@admin.register(MapLayer)
class MapLayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'creator', 'created_at', 'updated_at', 'is_active']
    list_filter = ['creator', 'created_at']
    search_fields = ['name', 'description']

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'creator', 'maps', 'is_active')
        }),
        ('Point Style', {
            'fields': (
                'point_radius', 'point_opacity',
                'point_solid_color', 'point_value_field_name', 'point_color_palette',
            ),
            'classes': ('collapse',),
        }),
        ('Line Style', {
            'fields': (
                'line_opacity', 'line_size', 'line_style',
                'line_solid_color', 'line_value_field_name',
                'line_color_palette',
            ),
            'classes': ('collapse',),
        }),
        ('Polygon Style', {
            'fields': (
                'polygon_opacity', 'polygon_label', 'polygon_label_font',
                'polygon_label_font_style', 'polygon_label_font_size',
                'polygon_label_font_color', 'polygon_label_font_opacity',
                'polygon_border_style', 'polygon_border_size',
                'polygon_border_color', 'polygon_border_opacity',
                'polygon_solid_color',
                'polygon_value_field_name', 'polygon_color_palette',
            ),
            'classes': ('collapse',),
        }),
    )


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['map_layer', 'type', 'geometry']
    list_filter = ['map_layer', 'type']
    search_fields = ['type']
    readonly_fields = ['geometry']


@admin.register(MapStyle)
class MapStyleAdmin(admin.ModelAdmin):
    list_display = ['name', 'url']
    search_fields = ['name', 'url']


class POIConfigInline(admin.TabularInline):
    model = POIConfig
    extra = 1


@admin.register(POIConfig)
class POIConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'scoring_configuration', 'max_score', 'max_distance']
    list_filter = ['scoring_configuration']
    search_fields = ['name', 'scoring_configuration__id']


@admin.register(CreateScoringMapLayerTask)
class CreateScoringMapLayerTaskAdmin(admin.ModelAdmin):
    list_display = ['task_id', 'layer', 'status', 'calculate_scoring_progress', 'polygon_import_progress', 'error_message']
    list_filter = ['status']
    search_fields = ['task_id', 'layer__name']
    actions = ['kill_task']

    def kill_task(self, request, queryset):
        for task in queryset:
            if task.status == 'in_progress':
                app.control.revoke(task.task_id, terminate=True)

                task.status = 'killed'
                task.save()

                task.layer.delete()
        self.message_user(request, "Выбранные задачи были убиты и соответствующие слои удалены.")

    kill_task.short_description = "Убить выбранные задачи в работе и удалить соответствующие слои"

