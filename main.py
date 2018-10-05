from json import dumps, loads
import requests
import sys


def sam_test(request):
    r = requests.get('https://gateway.vcf-test.vzw.dev.llabs.io/health')
    assert r.status_code == 200
    pass


def stav_test(request):
    print("stav test")
    pass


def rich_test(request):
    pass


def get_location(name):
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


def make_response_dict(response_str):
    """
    Return a response dictionary based on an input text to speech string.
    """
    return dict(
        payload=dict(
            google=dict(
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
        )
    )


def error():
    return "I'm sorry, something went wrong. My bad."


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

        print("XXX11 request follows")
        print(request)
        print("dict follows")
        print(request.__dict__)
        print("before TypeError (fixed?)")
        print(f"is request json: {request.is_json}")
        print("after TypeError (fixed?)")
        print(f"data: {request.data}")
        print(f"args: {request.args}")
        print(f"form: {request.form}")
        print("json follows")
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

        if (intent == 'Get Location'):
            response_str = get_location(name)
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

    except Exception as e:
        print("in exception handler")
        print("exception is")
        print(e)
        print("exc info is")
        print(sys.exc_info())
        response_str = error()

    response_dict = make_response_dict(response_str)
    response_json = dumps(response_dict)
    print("XXX11 response follows")
    print(response_json)
    # pprint.pprint(response_json)
    return response_json
