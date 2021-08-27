from rest_framework import pagination, response


class STACPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'

    def get_paginated_response(self, data):
        next_link = self.get_next_link()
        if not next_link:
            return response.Response(data)
        if 'links' not in data:
            data['links'] = []
        data['links'].append({'rel': 'next', 'href': self.get_next_link()})
        return response.Response(data)
