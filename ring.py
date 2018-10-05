"""
Common code for schedule check tools
"""

from client import clients


def auth(username, password):
    """
    Authenticate, returning a tuple of (access_token, refresh_token)
    """
    UsernamePasswordAuth = clients.gateway.get_model('UsernamePasswordAuth')
    AuthRequest = clients.gateway.get_model('AuthRequest')

    username_password_auth = UsernamePasswordAuth(username=username,
                                                  password=password)
    auth_request = AuthRequest(usernamePasswordAuth=username_password_auth)
    response = clients.gateway.auth.authenticate(request=auth_request).result()

    return (response.accessToken, response.refreshToken)


# This isn't used yet
def refresh_tokens(refresh_token):
    """
    Given a refresh token, return a new tuple of (access_token, refresh_token)

    This assumes that the refresh token is valid. Errors are not explicitly checked.
    """
    response = clients.gateway.tokens.refresh(
        refreshToken=refresh_token).result()

    return (response.accessToken, response.refreshToken)


def get_overview(access_token):
    """
    Return the overview for the user associated with the access token.
    """
    sections = ["me", "systemInfo", "group",
                "places", "lastKnowns", "users",
                "controlsSettingsList", "devices"]
    return clients.gateway.overview.getOverview(
        accessToken=access_token,
        sections=sections).result()


def get_user_by_name(users, name):
    """
    Given a list of users, return the user with the matching name.

    Return None if not found.
    """
    return next((user for user in users if user.name.lower() == name.lower()), None)


def get_user_by_id(users, user_id):
    """
    Given a list of users, return the user with the matching id.

    Return None if not found.
    """
    return next((user for user in users if user.id == user_id), None)


def get_member(members, user):
    """
    Given a list of members, return the member that matches the user

    Return None if not found
    """
    return next((member for member in members if member.userId == user.id), None)


def is_parent(members, user):
    """
    Given a list of members, is the given user a parent (admin)
    """
    member = get_member(members, user)

    if member:
        return member.admin

    return False


def is_child(members, user):
    """
    Given a list of members, is the given user a child (managed)
    """
    member = get_member(members, user)

    if member:
        return member.managed

    return False


def update_controls_settings(access_token, group_id, user_id, block_all_internet):
    """
    Selectively update controls settings for the specified user, who must be a
    managed user.

    The only setting actually supported (b/c that's all we need currently
    here) is block internet.
    """
    clients.gateway.controls.updateControlsSettings(
        accessToken=access_token,
        groupId=group_id,
        userId=user_id,
        request=dict(
            blockAllInternet=block_all_internet,
            predefinedPolicyIds=[],  # required
            customPolicies=[],       # required
        )).result()


def get_last_known_location(last_knowns, user_id):
    """
    Given a list of last known objects for a group, return the last known
    location for a given user id.
    """
    last_known = next(lk for lk in last_knowns if lk.userId == user_id)
    network = last_known.lastKnownNetworkLocation
    device = last_known.lastKnownDeviceLocation
    if not network and not device:
        return None

    network_time = network.observedTimestamp.timestamp() if network else 0
    device_time = device.observedTimestamp.timestamp() if device else 0
    return network if network_time > device_time else device
