from django.http import JsonResponse
from firebase_admin import auth
from django.urls import resolve


class FirebaseAuthMiddleware:
    """
    Verifica el token Firebase en el header Authorization
    """

    PUBLIC_PATHS = [
        "/",
        "/admin/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Permitir rutas públicas
        for public_path in self.PUBLIC_PATHS:
            if path.startswith(public_path):
                return self.get_response(request)

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Authorization header missing or invalid"},
                status=401
            )

        token = auth_header.split("Bearer ")[1]

        try:
            decoded_token = auth.verify_id_token(token)
            request.firebase_user = decoded_token
        except Exception:
            return JsonResponse(
                {"error": "Invalid or expired Firebase token"},
                status=401
            )

        return self.get_response(request)
