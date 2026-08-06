# throttles.py

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

#AnonRateThrottle for annonymous
#Annon uses IP address cause dey are not authenticated

#UserRateThrottle for authenticated user
#authenticated user ID


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class RegisterThrottle(AnonRateThrottle):
    scope = "register"


class MessageThrottle(UserRateThrottle):
    scope = "message"