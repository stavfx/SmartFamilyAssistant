from json import dumps  # , loads
import sys
from time import time

import common


def sam_test(request):
    common.auth("5551196700", "abcd1234")
    pass


def stav_test(request):
    print("stav test")
    pass


def rich_test(request):
    pass


def get_location(name, params):
    token, _ = common.auth("5551196700", "abcd1234")
    overview = common.get_overview(token)
    user = next((usr for usr in overview.users if usr.name == name), None)
    if user is None:
        return make_response_dict(f"Sorry, I don't know who {name} is.")
    location = get_last_known_location(overview, user.id)

    if location:
        return make_response_dict(f"{name} is at {location.lat},{location.lon}")
    else:
        return make_response_dict(f"Sorry, I don't know where {name} is.")


def get_last_known_location(overview, user_id):
    last_known = next(x for x in overview.lastKnowns if x.userId == user_id)
    network = last_known.lastKnownNetworkLocation
    device = last_known.lastKnownDeviceLocation
    network_time = network.observedTimestamp.timestamp() if network else 0
    device_time = device.observedTimestamp.timestamp() if device else 0
    return network if network_time > device_time else device


def login(mdn):
    # XXX this is preliminary
    # check userId
    # do we have an association for the userId
    # if so, return mdn
    # if not, prompt user for mdn
    # return f"Login as {name}"
    return make_response_dict(f"Login function is still in progress")


def pause_internet(name):
    return make_response_dict(f"Pause Internet for {name}")


def welcome(name):
    # Change to f"Hi! Welcome to Verizon Smart Family. What's your phone number?"
    response_dict = make_response_dict(f"MDN please.", continue_conversation=True)
    response_dict['payload']['google']['systemIntent'] = dict(intent="actions.intent.TEXT")
    return response_dict


def unexpected_intent(name, intent):
    return make_response_dict(f"{name}, I do not recognize the command {intent}")


def no_intent(name):
    return make_response_dict(f"{name}, I did not receive a command")


def dict_to_str(_dict):
    """
    Convert a dict to a string of equal separated key value pairs joined by commas

    Return the empty string for no dict.
    """
    if not _dict:
        return ""

    return ",".join([f"{k}={v}"
                     for k, v
                     in _dict.items()])


def str_to_dict(_str):
    """
    Convert a string of equal separated key value pairs joined by commas, to a dict

    Return None for the empty string.
    """
    if not _str:
        return None

    return {k: v
            for (k, _, v)
            in [item.partition('=')
                for item
                in _str.split(',')]}


def make_response_dict(response_str, continue_conversation=False):
    """
    Return a response dictionary based on an input text to speech string.

    user_storage is an optional dict (of simple key/value pairs, not nested) to persist
    """
    google_dict = dict(
        expectUserResponse=continue_conversation,
        richResponse=dict(
            items=[
                dict(
                    simpleResponse=dict(
                        textToSpeech=response_str
                    )
                )
            ]
        )
    )

    return dict(
        payload=dict(
            google=google_dict
        )
    )


def error():
    return "I'm sorry, something went wrong. My bad."


def id_short(long_id):
    return " ".join([x for x in long_id[0:3] + long_id[-3:]])


def hello(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/0.12/api/#flask.Flask.make_response>`.
    """
    try:
        # sam_test(request)
        # stav_test(request)
        # rich_test(request)

        print("XXX15 request follows")
        # print(request)
        # print("dict follows")
        # print(request.__dict__)
        # print(f"is request json: {request.is_json}")
        # print(f"data: {request.data}")
        # print(f"args: {request.args}")
        # print(f"form: {request.form}")
        # print("json follows")
        request_json = request.get_json()
        print(request_json)

        # request_dict = loads(request_json)
        # print("dict follows")
        # print(request_dict)

        query_result = request_json.get('queryResult', {})

        name = query_result.get('parameters', {}).get('given-name', None)
        print(f"name: {name}")
        # XXX really we probably should punt
        if not name:
            name = "No Name"

        intent = query_result.get('intent', {}).get('displayName', None)
        print(f"intent: {intent}")

        original_payload = request_json.get("originalDetectIntentRequest", {}).get("payload", {})
        conv_id = original_payload.get("conversation", {}).get("conversationId")
        user = original_payload.get("user", {})
        user_id = user.get("userId")
        print(f"conv_id={conv_id}, user_id={user_id}")

        user_storage = str_to_dict(user.get("userStorage"))
        print(f"user_storage: {user_storage}")

        if (intent == 'Get Location'):
            response_dict = get_location(name, request_json)
        elif (intent == 'Login'):
            response_dict = login(name)
        elif (intent == 'Pause Internet'):
            response_dict = pause_internet(name)
        elif (intent == 'Welcome'):
            response_dict = welcome(name)
        elif intent is not None:
            # XXX really we probably should punt
            response_dict = unexpected_intent(name)
        else:
            # XXX really we probably should punt
            response_dict = no_intent(name)

        user_storage_new = dict(name=name,
                                intent=intent,
                                time=time())
        response_dict['payload']['google']['userStorage'] = dict_to_str(user_storage_new)

        # response_str += f" , conversation I D {id_short(conv_id)} , user I D {id_short(user_id)}"
        # continue_conversation = False

    except Exception as e:
        print("in exception handler")
        print("exception is")
        print(e)
        print("exc info is")
        print(sys.exc_info())
        response_dict = error()

    response_json = dumps(response_dict)
    print("XXX15 response follows")
    print(response_json)
    # pprint.pprint(response_json)
    return response_json
