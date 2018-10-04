from json import dumps


def hello(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/0.12/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    print("XXX request follows")
    print(request_json)
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
    response_dict = dict(
        payload=dict(
            google=dict(
                expectUserResponse=True,
                richResponse=dict(
                    items=[
                        dict(
                            simpleResponse=dict(
                                textToSpeech="this is a simple response"
                            )
                        )
                    ]
                )
            )
        )
    )

    response_json = dumps(response_dict)
    print("XXX response follows")
    print(response_json)
    return response_json
