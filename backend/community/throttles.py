from django.conf import settings
from rest_framework.throttling import UserRateThrottle


class CommunityUserRateThrottle(UserRateThrottle):
    def allow_request(self, request, view):
        if not getattr(settings, "COMMUNITY_THROTTLES_ENABLED", True):
            return True
        return super().allow_request(request, view)


class CommunityPostWriteThrottle(CommunityUserRateThrottle):
    scope = "community_posts"
    rate = "10/hour"


class CommunityCommentWriteThrottle(CommunityUserRateThrottle):
    scope = "community_comments"
    rate = "60/hour"


class CommunityInteractionThrottle(CommunityUserRateThrottle):
    scope = "community_interactions"
    rate = "120/hour"


class CommunityReportThrottle(CommunityUserRateThrottle):
    scope = "community_reports"
    rate = "10/hour"


class CommunityBlockThrottle(CommunityUserRateThrottle):
    scope = "community_blocks"
    rate = "30/hour"
