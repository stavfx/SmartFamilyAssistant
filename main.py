from json import dumps, loads
import requests


def sam_test(request):
    print(requests)
    print("successfully imported requests")
    pass


def stav_test(request):
    print("stav test")
    pass


def rich_test(request):
    pass


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

        print("XXX7 request follows")
        print(request)
        print("hmmm")
        print(request.__dict__)
        print("before TypeError")
        print(f"is request json: {request.is_json()}")
        print("after TypeError")
        print(f"data: {request.data}")
        print(f"args: {request.args}")
        print(f"form: {request.form}")
        # pprint.pprint(request_json)
        # response_dict = dict(
        #     conversationToken="conversation_token",
        #     userStorage="user_storage",
        #     resetUserStorage=False,
        #     expectUserResponse=False,
        #     # expectedInputs=[],
        #     # finalResponse=None,
        #     # customPushMessage=None,
        #     isInSandbox=True,
        # )
        tts = "this is a simple response from github"
    except Exception:
        print("in exception handler")
        tts = "I'm sorry, something went wrong. My bad."

    response_dict = dict(
        payload=dict(
            google=dict(
                expectUserResponse=True,
                richResponse=dict(
                    items=[
                        dict(
                            simpleResponse=dict(
                                textToSpeech=tts
                            )
                        )
                    ]
                )
            )
        )
    )

    response_json = dumps(response_dict)
    print("XXX7 response follows")
    print(response_json)
    # pprint.pprint(response_json)
    return response_json
