"""
Common code for schedule check tools
"""

import os
from pprint import pprint
import shlex
import subprocess

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
    sections = ["me", "systemInfo", "group", "users"]
    return clients.gateway.overview.getOverview(
        accessToken=access_token,
        sections=sections).result()


def is_test_account(group):
    """
    Does the given group correspond to a test account

    Compare to: schedule_check/requester/requester.py:Requester._is_test_account()
    The null form is slightly different here
    """
    if 'extras' not in group or 'llTestAccount' not in group.extras:
        return False

    return group.extras['llTestAccount'].lower() == 'true'


def do_print(message):
    """
    Wrapper around print() to facilitate lint ignore.
    """
    print(message)  # noqa: T001


def do_pprint(message):
    """
    Wrapper around pprint() to facilitate lint ignore.
    """
    pprint(message)  # noqa: T003


def do_call(cmd):
    """
    Call a command in a subprocess.

    stdout and stderr are visible in the terminal of the calling process
    """
    args = shlex.split(cmd)
    subprocess.call(args)


def do_exec(cmd):
    """
    Execute a command in a subprocess.

    :return: A tuple of (stdout, stderr)
    """
    args = shlex.split(cmd)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    return (stdout, stderr)


def vault_auth():
    """
    Authenticate with vault. Uses LDAP.
    """
    if 'VAULT_ADDR' not in os.environ:
        os.environ['VAULT_ADDR'] = 'https://vault.tools.llabs.io'
    do_print('Enter your LDAP password below to authenticate with Hashicorp Vault')
    do_call('vault auth -method=ldap')
    do_print('')


def vault_read(path):
    """
    Read a value from vault.

    This assumes you have already authenticated via vault_auth()
    """
    (stdout, _) = do_exec("vault read -field=value {}".format(path))
    return stdout


def update_config_pubnub(config, env):
    """
    Update a config dict with pubnub related env vars, based on the chosen environment.
    """
    # We could get AUTH keys from the overview (within me), but that would be
    # a bit of a pain to get both the admin and managed keys (we could
    # probably get by with only one of LL vs. not, whichever was needed, but
    # using it would be a little hacky). So get from vault instead, where we
    # can easily query all of them.
    if env == 'vcf-prod':
        cluster_namespace_path = 'k8s.vzw.llabs.io/vcf-prod'
    else:
        # local uses vcf-test pubnub credentials
        cluster_namespace_path = 'vzw.kube.dev.llabs.io/vcf-test'

    secret_path = "/secret/kubernetes/kube_secrets/{}/secret".format(cluster_namespace_path)
    vault_auth()

    pubnub_admin_auth_key = vault_read("{}/{}".format(
        secret_path, "pubnub-admin-auth-key"))
    pubnub_managed_auth_key = vault_read("{}/{}".format(
        secret_path, "pubnub-managed-auth-key"))

    if env == 'vcf-prod':
        pubnub_ll_admin_auth_key = vault_read("{}/{}".format(
            secret_path, "pubnub-ll-admin-auth-key"))
        pubnub_ll_managed_auth_key = vault_read("{}/{}".format(
            secret_path, "pubnub-ll-managed-auth-key"))
    else:
        pubnub_ll_admin_auth_key = pubnub_admin_auth_key
        pubnub_ll_managed_auth_key = pubnub_managed_auth_key

    if env == 'vcf-prod':
        config.update(dict(
            PUBNUB_ADMIN_PUBLISH_KEY='pub-c-c040242d-2a1c-4bbe-9d5a-1264ef1d1519',
            PUBNUB_ADMIN_SUBSCRIBE_KEY='sub-c-5b2b999e-f706-11e7-847e-5ef6eb1f4733',
            PUBNUB_ADMIN_AUTH_KEY=pubnub_admin_auth_key,
            PUBNUB_MANAGED_PUBLISH_KEY='pub-c-0c4a48d6-9b9a-4535-b53a-677ae1a86dae',
            PUBNUB_MANAGED_SUBSCRIBE_KEY='sub-c-87267a00-f706-11e7-a7db-e6c6e9cd0a3f',
            PUBNUB_MANAGED_AUTH_KEY=pubnub_managed_auth_key,
            # test keysets are actually different in prod
            PUBNUB_LL_ADMIN_PUBLISH_KEY='pub-c-705ff11b-d751-4c49-b810-0eddf4e02b19',
            PUBNUB_LL_ADMIN_SUBSCRIBE_KEY='sub-c-b09bf4c2-2303-11e8-ac36-6a07bc1dd800',
            PUBNUB_LL_ADMIN_AUTH_KEY=pubnub_ll_admin_auth_key,
            PUBNUB_LL_MANAGED_PUBLISH_KEY='pub-c-d7d14aff-31bc-4532-881d-af2c7e75b278',
            PUBNUB_LL_MANAGED_SUBSCRIBE_KEY='sub-c-ba890bf0-2303-11e8-bb29-5a43d096f02f',
            PUBNUB_LL_MANAGED_AUTH_KEY=pubnub_ll_managed_auth_key))

    else:
        config.update(dict(
            PUBNUB_ADMIN_PUBLISH_KEY='pub-c-b375a935-acb7-448d-a80a-e0acca6c5e55',
            PUBNUB_ADMIN_SUBSCRIBE_KEY='sub-c-f46e1898-e1ee-11e7-b7e7-02872c090099',
            PUBNUB_ADMIN_AUTH_KEY=pubnub_admin_auth_key,
            PUBNUB_MANAGED_PUBLISH_KEY='pub-c-306a1235-656b-4cce-93d3-dc4be5997d8e',
            PUBNUB_MANAGED_SUBSCRIBE_KEY='sub-c-b48d9da4-e1f1-11e7-8753-72edb1f6dd80',
            PUBNUB_MANAGED_AUTH_KEY=pubnub_managed_auth_key,
            # test keysets duplicated in test
            PUBNUB_LL_ADMIN_PUBLISH_KEY='pub-c-b375a935-acb7-448d-a80a-e0acca6c5e55',
            PUBNUB_LL_ADMIN_SUBSCRIBE_KEY='sub-c-f46e1898-e1ee-11e7-b7e7-02872c090099',
            PUBNUB_LL_ADMIN_AUTH_KEY=pubnub_ll_admin_auth_key,
            PUBNUB_LL_MANAGED_PUBLISH_KEY='pub-c-306a1235-656b-4cce-93d3-dc4be5997d8e',
            PUBNUB_LL_MANAGED_SUBSCRIBE_KEY='sub-c-b48d9da4-e1f1-11e7-8753-72edb1f6dd80',
            PUBNUB_LL_MANAGED_AUTH_KEY=pubnub_ll_managed_auth_key))
