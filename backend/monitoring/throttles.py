from rest_framework.throttling import AnonRateThrottle


class BrowserErrorThrottle(AnonRateThrottle):
    scope = "browser_errors"
