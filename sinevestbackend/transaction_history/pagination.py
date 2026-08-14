from rest_framework.pagination import PageNumberPagination


class TransactionPagination(PageNumberPagination):
    """
    Standard PageNumberPagination works fine here even though the input is
    a plain Python list (merged from three querysets) rather than a single
    queryset — DRF's pagination slices and measures length generically, it
    doesn't require a real QuerySet.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100