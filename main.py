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
    return f"Get the location of {name}"


def login(name):
    return f"Login as {name}"


def pause_internet(name):
    return f"Pause Internet for {name}"


def welcome(name):
    return f"{name}, welcome to Verizon Smart Family"


def unexpected_intent(name, intent):
    return f"{name}, I do not recognize the command {intent}"


def no_intent(name):
    return f"{name}, I did not receive a command"


def make_response_dict(response_str, user_storage=None):
    """
    Return a response dictionary based on an input text to speech string.

    user_storage is an optional dict to persist
    """
    google_dict = dict(
        expectUserResponse=True,
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

    if user_storage:
        google_dict['userStorage'] = dumps(user_storage)

    return dict(
        payload=dict(
            google=google_dict
        )
    )


def error():
    return "I'm sorry, something went wrong. My bad."


def id_short(long_id):
    return long_id[0:3] + long_id[-3:]


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
        sam_test(request)
        stav_test(request)
        rich_test(request)

        print("XXX13 request follows")
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

        name = request_json.get('queryResult', {}).get('parameters', {}).get('given-name', None)
        print(f"name: {name}")
        # XXX really we probably should punt
        if not name:
            name = "No Name"

        intent = request_json.get('queryResult', {}).get('intent', {}).get('displayName', None)
        print(f"intent: {intent}")

        original_payload = request_json.get("originalDetectIntentRequest", {}).get("payload", {})
        conv_id = original_payload.get("conversation", {}).get("conversationId")
        user_id = original_payload.get("user", {}).get("userId")

        if (intent == 'Get Location'):
            response_str = get_location(name, request_json)
        elif (intent == 'Login'):
            response_str = login(name)
        elif (intent == 'Pause Internet'):
            response_str = pause_internet(name)
        elif (intent == 'Welcome'):
            response_str = welcome(name)
        elif intent is not None:
            # XXX really we probably should punt
            response_str = unexpected_intent(name)
        else:
            # XXX really we probably should punt
            response_str = no_intent(name)

        response_str += f" conversation id {id_short(conv_id)} user id {id_short(user_id)}"

    except Exception as e:
        print("in exception handler")
        print("exception is")
        print(e)
        print("exc info is")
        print(sys.exc_info())
        response_str = error()

    user_storage = dict(name=name,
                        intent=intent,
                        time=time())
    response_dict = make_response_dict(response_str, user_storage)
    response_json = dumps(response_dict)
    print("XXX13 response follows")
    print(response_json)
    # pprint.pprint(response_json)
    return response_json
