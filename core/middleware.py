class ThemeMiddleware:
    """Middleware to handle theme from cookies"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
