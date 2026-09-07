from django.shortcuts import redirect


def accounts_redirect(request):
    """Redirect accounts root to admin login"""
    return redirect("admin_login")
