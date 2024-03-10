from rest_framework import viewsets, generics

from geosight.utils.OptionsMetadata import OptionsMetadata


class ModelViewSet(viewsets.ModelViewSet):
    serializer_list = {}
    metadata_class = OptionsMetadata

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_list.get(self.action, self.serializer_class)


class RetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_list = {}
    metadata_class = OptionsMetadata

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        action = self.action.lower()  # Получаем имя действия (action) из атрибута action
        return self.serializer_list.get(action, self.serializer_class)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.action = self.request.method.lower()  # Устанавливаем атрибут action на основе HTTP метода запроса
