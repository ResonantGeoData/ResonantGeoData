from rest_framework import pagination, response


class STACPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'

    def get_paginated_response(self, data):
        data['links'].append({'rel': 'next', 'href': self.get_next_link()})
        return response.Response(data)
