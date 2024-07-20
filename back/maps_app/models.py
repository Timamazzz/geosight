import random
from decimal import Decimal

from django.contrib.gis.db import models as gis_models
from users_app.models import Company, User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField


def generate_random_color():
    """
    Generates a random color in HEX format.
    """
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


class MapStyle(models.Model):
    name = models.CharField(max_length=256)
    url = models.URLField(max_length=256)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'maps_app'
        verbose_name = "Стиль карты"
        verbose_name_plural = "Стили карты"


class Map(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата и время последнего редактирования")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создатель")
    users = models.ManyToManyField(User, related_name='allowed_maps', verbose_name="Разрешенные пользователи")
    company = models.ForeignKey(Company, related_name='maps', on_delete=models.CASCADE, verbose_name="Компания")
    style = models.ForeignKey(MapStyle, related_name='maps', on_delete=models.CASCADE, verbose_name="Стиль")

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'maps_app'
        verbose_name = "Карта"
        verbose_name_plural = "Карты"
        ordering = ['-created_at']


class MapLayer(models.Model):
    LINE_STYLE_CHOICES = [
        ('solid', 'Сплошная'),
        ('dash', 'Пунктирная'),
    ]
    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата и время последнего редактирования")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создатель")
    maps = models.ManyToManyField(Map, related_name='layers', verbose_name="Карты")

    is_active = models.BooleanField(default=False)

    # Point style
    point_radius = models.FloatField(verbose_name="Радиус точки", default=5)
    point_opacity = models.DecimalField(
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('1.00'))],
        default=1, max_digits=3, decimal_places=2, verbose_name="Прозрачноть точки",
    )
    point_solid_color = models.CharField(max_length=7, default=generate_random_color, null=True, blank=True,
                                         verbose_name="Цвет сплошной заливки")
    point_value_field_name = models.CharField(max_length=256, null=True, blank=True, verbose_name="Поле для расчета")
    point_color_palette = models.JSONField(default=dict, null=True, blank=True, verbose_name="Цветовая палитра (JSON)")

    # Line style
    line_opacity = models.DecimalField(
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('1.00'))],
        default=1, max_digits=3, decimal_places=2, verbose_name="Прозрачноть линии",
    )
    line_size = models.FloatField(default=1, validators=[MinValueValidator(0)], verbose_name="Толщина линии")
    line_style = models.CharField(max_length=5, choices=LINE_STYLE_CHOICES, default='solid',
                                  verbose_name="Стиль линии", )
    line_solid_color = models.CharField(max_length=7, default=generate_random_color, null=True, blank=True,
                                        verbose_name="Цвет сплошной заливки")
    line_value_field_name = models.CharField(max_length=256, null=True, blank=True, verbose_name="Поле для расчета")
    line_color_palette = models.JSONField(default=dict, null=True, blank=True, verbose_name="Цветовая палитра (JSON)")

    # Polygon style
    polygon_opacity = models.DecimalField(
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('1.00'))],
        default=1, max_digits=3, decimal_places=2, verbose_name="Прозрачноть полигона",
    )

    polygon_label = models.CharField(max_length=1024, null=True, blank=True, verbose_name="Метка полигона")
    polygon_label_font = models.CharField(max_length=256, default="arial", null=True, blank=True,
                                          verbose_name="Шрифт метки полигона")
    polygon_label_font_style = models.CharField(max_length=256, default="medium", null=True, blank=True,
                                                verbose_name="Стиль шрифта метки полигона")
    polygon_label_font_size = models.PositiveIntegerField(default=1, null=True, blank=True,
                                                          verbose_name="Размер шрифта метки полигона")
    polygon_label_font_color = models.CharField(max_length=7, default='#000000', null=True, blank=True,
                                                verbose_name="Цвет шрифта метки полигона")
    polygon_label_font_opacity = models.DecimalField(
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('1.00'))],
        default=1, max_digits=3, decimal_places=2, verbose_name="Прозрачность шрифта метки полигона",
        null=True, blank=True
    )

    polygon_border_style = models.CharField(max_length=5, choices=LINE_STYLE_CHOICES, default='solid',
                                            verbose_name="Стиль границы полигона", )
    polygon_border_size = models.FloatField(default=1, validators=[MinValueValidator(0)],
                                            verbose_name="Толщина границы")
    polygon_border_color = models.CharField(max_length=7, default='#000000', verbose_name="Цвет границы полигона")
    polygon_border_opacity = models.DecimalField(
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('1.00'))],
        default=1, max_digits=3, decimal_places=2, verbose_name="Прозрачноть границы полигона",
    )
    polygon_solid_color = models.CharField(max_length=7, default=generate_random_color, null=True, blank=True,
                                           verbose_name="Цвет сплошной заливки")
    polygon_value_field_name = models.CharField(max_length=256, null=True, blank=True, verbose_name="Поле для расчета")
    polygon_color_palette = models.JSONField(default=dict, null=True, blank=True,
                                             verbose_name="Цветовая палитра (JSON)")

    class Meta:
        app_label = 'maps_app'
        verbose_name = "Слой"
        verbose_name_plural = "Слои"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def serialize_styles(self):
        return {
            'point': {
                'point_solid_color': self.point_solid_color,
                'point_radius': self.point_radius,
                'point_opacity': self.point_opacity,
                'point_value_field_name': self.point_value_field_name,
                'point_color_palette': self.point_color_palette,
            },
            'line': {
                'line_opacity': self.line_opacity,
                'line_size': self.line_size,
                'line_style': self.line_style,
                'line_solid_color': self.line_solid_color,
                'line_value_field_name': self.line_value_field_name,
                'line_color_palette': self.line_color_palette,
            },
            'polygon': {
                'polygon_opacity': self.polygon_opacity,
                'polygon_label': self.polygon_label,
                'polygon_label_font': self.polygon_label_font,
                'polygon_label_font_style': self.polygon_label_font_style,
                'polygon_label_font_size': self.polygon_label_font_size,
                'polygon_label_font_color': self.polygon_label_font_color,
                'polygon_label_font_opacity': self.polygon_label_font_opacity,
                'polygon_border_style': self.polygon_border_style,
                'polygon_border_size': self.polygon_border_size,
                'polygon_border_color': self.polygon_border_color,
                'polygon_border_opacity': self.polygon_border_opacity,
                'polygon_solid_color': self.polygon_solid_color,
                'polygon_value_field_name': self.polygon_value_field_name,
                'polygon_color_palette': self.polygon_color_palette,
            }
        }


class Feature(models.Model):
    map_layer = models.ForeignKey(MapLayer, related_name='features', on_delete=models.CASCADE, verbose_name="Слой")
    type = models.CharField(max_length=50, verbose_name="Тип объекта")
    properties = models.JSONField(verbose_name="Свойства")
    geometry = gis_models.GeometryField(srid=4326, verbose_name="Геометрия", null=True, blank=True)

    def __str__(self):
        return f"Feature in {self.map_layer.name}"

    class Meta:
        verbose_name = "Объект"
        verbose_name_plural = "Объекты"
        ordering = ['id']


class POIConfig(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название POI")
    max_score = models.IntegerField(verbose_name="Максимальный балл")
    max_distance = models.IntegerField(verbose_name="Максимальное расстояние")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Конфигурация POI"
        verbose_name_plural = "Конфигурации POI"


class CreateScoringMapLayerTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('in_progress', 'В обработке'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
        ('killed', 'Убит')
    ]

    task_id = models.CharField(max_length=255, verbose_name="ID задачи")
    layer = models.ForeignKey(MapLayer, on_delete=models.SET_NULL, verbose_name="Слой карты", null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    error_message = models.TextField(blank=True, null=True, verbose_name="Сообщение об ошибке")
    calculate_scoring_progress = models.FloatField(default=0, verbose_name="Прогресс расчета баллов")
    polygon_import_progress = models.FloatField(default=0, verbose_name="Прогресс импорта полигонов")

    def __str__(self):
        return f'Task {self.task_id} - {self.get_status_display()}'

    class Meta:
        verbose_name = "Задача создания слоя карты"
        verbose_name_plural = "Задачи создания слоев карт"


class MapLayerFilter(models.Model):
    map_layer = models.ForeignKey(MapLayer, on_delete=models.CASCADE, related_name='filters', verbose_name="Слой карты")
    field_name = models.CharField(max_length=256, verbose_name="Имя поля")

    # Для int и float полей
    min_value_int = models.BigIntegerField(null=True, blank=True, verbose_name="Минимальное значение (int)")
    max_value_int = models.BigIntegerField(null=True, blank=True, verbose_name="Максимальное значение (int)")
    min_value_float = models.FloatField(null=True, blank=True, verbose_name="Минимальное значение (float)")
    max_value_float = models.FloatField(null=True, blank=True, verbose_name="Максимальное значение (float)")

    # Для string полей
    string_values = ArrayField(models.CharField(max_length=256), blank=True, default=list, verbose_name="Значения (строки)")

    def __str__(self):
        return f'{self.map_layer.name} - {self.field_name}'

    class Meta:
        verbose_name = "Фильтр слоя карты"
        verbose_name_plural = "Фильтры слоев карт"