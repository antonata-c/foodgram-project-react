from rest_framework.filters import SearchFilter


class CustomSearchFilter(SearchFilter):
    search_param = 'name'
