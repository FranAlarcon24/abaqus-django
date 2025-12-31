import firebase_admin
from firebase_admin import auth
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


if not firebase_admin._apps:
    firebase_admin.initialize_app(
        firebase_admin.credentials.Certificate(
            settings.FIREBASE_SERVICE_ACCOUNT
        )
    )


class FirebaseAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        path = request.path

        if path == "/" or path.startswith("/admin"):
            return None

        if not path.startswith("/api/"):
            return None

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Authorization header missing or invalid"},
                status=401,
            )

        token = auth_header.replace("Bearer ", "")

        try:
            decoded_token = auth.verify_id_token(token)
            request.firebase_user = decoded_token
        except Exception:
            return JsonResponse(
                {"error": "Invalid or expired token"},
                status=401,
            )
