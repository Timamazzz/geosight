from rest_framework import viewsets, filters
from geosight.utils.OptionsMetadata import OptionsMetadata


class ModelViewSet(viewsets.ModelViewSet):
    serializer_list = {}
    metadata_class = OptionsMetadata
    filter_backends = [filters.SearchFilter]

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_list.get(self.action, self.serializer_class)
