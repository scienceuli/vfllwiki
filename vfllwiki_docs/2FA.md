in Eventmanager und Memberadmin eingerichtet

### Eventmanager

- Used libraries: django_otp + two_factor (-> `INSTALLED_APPS` (base.py))
- `OTPMiddleware`  in `MIDDLEWARE` (base.py)
- `two_factor.urls` imported in urls.py
- 