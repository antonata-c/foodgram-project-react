from rest_framework.filters import SearchFilter


class NameSearchFilter(SearchFilter):
    search_param = 'name'


def recipe_filter(queryset, request):
    author = request.query_params.get('author')
    if author:
        queryset = queryset.filter(author=author)
    tags = request.query_params.getlist('tags')
    if tags:
        queryset = queryset.filter(
            tags__slug__in=tags
        ).order_by('id').distinct()
    if request.user.is_anonymous:
        return queryset

    is_favorited = request.query_params.get('is_favorited')
    if is_favorited == '1':
        queryset = queryset.filter(
            favorite__user=request.user
        )
    if is_favorited == '0':
        queryset = queryset.exclude(
            favorite__user=request.user
        )

    is_in_shopping_cart = request.query_params.get(
        'is_in_shopping_cart'
    )
    if is_in_shopping_cart == '1':
        queryset = queryset.filter(
            shopping_cart__user=request.user
        )
    if is_in_shopping_cart == '0':
        queryset = queryset.exclude(
            shopping_cart__user=request.user
        )

    return queryset
