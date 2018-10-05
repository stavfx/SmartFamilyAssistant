from json import dumps
import sys
import places
import ring

# really we'd use oauth
# just hardcode for now
PASSWORD = "abcd1234"


def get_location(mdn, name):
    if not mdn:
        return make_response_dict("Sorry, you must be signed in as a parent to get location",
                                  continue_conversation=False)

    token, _ = ring.auth(mdn, PASSWORD)
    overview = ring.get_overview(token)
    user = ring.get_user_by_name(overview.users, name)
    if user is None:
        return make_response_dict(f"Sorry, I don't know who {name} is.")

    location = ring.get_last_known_location(overview.lastKnowns, user.id)
    if location:
        if overview.places:
            (place_name, distance_meters, at_place) = places.get_nearest_place_at_info(
                overview.places, location.lat, location.lon, location.accuracyMeters)
            if at_place:
                return make_location_response(f"{name} is at {place_name}", user, location)
            else:
                return make_location_response(f"{name} is {distance_meters} meters from {place_name}", user, location)
        else:
            return make_location_response(f"{name} is at {location.lat},{location.lon}", user, location)
    else:
        return make_response_dict(f"Sorry, I don't know where {name} is.")


def make_location_response(message, user, location):
    location_str = f"{location.lat},{location.lon}"
    map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={location_str}&zoom=15&size=1050x600" \
              "&markers=anchor:center|icon:https://f8bkee3ht8.execute-api.us-west-2.amazonaws.com/live/images" \
              f"/{user.imageId}/64/64?format=png|{location_str}&key=AIzaSyDS2nG7-Aec721rRJ_lw9zoeJsrUkFTmNE"
    result = make_response_dict(message, continue_conversation=False)
    result['payload']['google']['richResponse']['items'].append(
        dict(
            basicCard=dict(
                image=dict(url=map_url),
                buttons=[
                    dict(
                        title="Launch Verizon Smart Family",
                        openUrlAction=dict(url="https://bnc.lt/vzsf")
                    )
                ]
            )
        )
    )
    return result


def _do_pause_internet(mdn, name, pause):
    """
    :return: error message, or None upon success
    """
    token, _ = ring.auth(mdn, PASSWORD)
    overview = ring.get_overview(token)
    user = ring.get_user_by_name(overview.users, name)
    if user is None:
        return f"Sorry, I don't know who {name} is."

    if not ring.is_child(overview.group.members, user):
        return f"You can only {'pause' if pause else 'un-pause'} the internet for a child."

    ring.update_controls_settings(token, overview.group.id, user.id, block_all_internet=pause)


def pause_internet(mdn, name):
    if not mdn:
        return make_response_dict("Sorry, you must be signed in as a parent to pause Internet.",
                                  continue_conversation=False)

    errorMsg = _do_pause_internet(mdn, name, pause=True)
    msg = errorMsg if errorMsg else f"I have blocked the Internet for {name}"
    return make_response_dict(msg, continue_conversation=False)


def unpause_internet(mdn, name):
    if not mdn:
        return make_response_dict("Sorry, you must be signed in as a parent to turn Internet back on.",
                                  continue_conversation=False)

    errorMsg = _do_pause_internet(mdn, name, pause=False)
    msg = errorMsg if errorMsg else f"{name} can browse the Internet again"
    return make_response_dict(msg, continue_conversation=False)


def welcome(query_result, storage):
    # try storage
    mdn = storage.get('mdn', None)
    if mdn:
        name = welcome_mdn(mdn, storage)
        return make_response_dict(f"Hi {name}! Welcome back!")
    else:
        # try query params
        mdn = query_result.get('parameters', {}).get('mdn', None)
        if mdn:
            name = welcome_mdn(mdn, storage)
            return make_response_dict(
                f"Welcome {name}!\n"
                "In the real world, we'd have you log in with OAuth2 using your phone.\n"
                "But this is a demo, so we just logged you in with your super secure password...\n"
                "NOT!")

    # No stored or provided mdn, ask for it
    return prompt_user_for_mdn()


def prompt_user_for_mdn():
    response_dict = make_response_dict(
        "Hi! Welcome to Verizon Smart Family. What's your phone number?")
    response_dict['payload']['google']['systemIntent'] = dict(intent="actions.intent.TEXT",
                                                              parameterName="mdn")
    return response_dict


def welcome_mdn(mdn, storage):
    """
    Log in with the provided mdn. Upon success save mdn to storage.

    Return the name of the user that just logged in.
    """
    token, _ = ring.auth(mdn, PASSWORD)
    overview = ring.get_overview(token)
    user = ring.get_user_by_id(overview.users, overview.me.userId)
    storage['mdn'] = mdn
    return user.name


def show_possible_actions(mdn):
    if not mdn:
        return make_response_dict("You must be signed in as a parent to use Verizon Smart Family.",
                                  continue_conversation=False)

    token, _ = ring.auth(mdn, PASSWORD)
    overview = ring.get_overview(token)
    current_user_id = overview.me.userId

    current_user = ring.get_user_by_id(overview.users, current_user_id)
    other_user_names = [u.name for u in overview.users if u.id != current_user_id]
    children_names = [u.name for u in overview.users if ring.is_child(overview.group.members, u)]

    all_but_last_child = children_names[:-1]
    last_child = children_names[-1]
    return make_response_dict(
        f"You can locate {', '.join(other_user_names)}, or even your own device,"
        + f" {current_user.name}!\n"
        + f"You can also Pause and Un-pause internet access for {', '.join(all_but_last_child)}"
        + f" and {last_child}.")


def logout():
    """
    Used administratively for clearing user storage.
    """
    response_dict = make_response_dict("Goodbye",
                                       continue_conversation=False)
    # XXX this might not work?
    response_dict['payload']['google']['resetUserStorage'] = True
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

    Return Empty dict for a None string.
    """
    if not _str:
        return dict()

    return {k: v
            for (k, _, v)
            in [item.partition('=')
                for item
                in _str.split(',')]}


# XXX try default True for now, so all True
# continue_conversation=False
def make_response_dict(response_str, continue_conversation=True):
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
    return make_response_dict("I'm sorry, something went wrong. My bad.", continue_conversation=False)


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
        print("XXX15 request follows")
        request_json = request.get_json()
        print(request_json)

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
        google_user_id = user.get("userId")
        print(f"conv_id={conv_id}, google_user_id={google_user_id}")

        user_storage = str_to_dict(user.get("userStorage"))
        mdn = user_storage.get('mdn', None)
        print(f"read user_storage: {user_storage} mdn={mdn}")

        if (intent == 'get_location'):
            response_dict = get_location(mdn, name)
        elif (intent == 'pause_internet'):
            response_dict = pause_internet(mdn, name)
        elif (intent == 'unpause_internet'):
            response_dict = unpause_internet(mdn, name)
        elif (intent == 'welcome'):
            response_dict = welcome(query_result, user_storage)
        elif intent == 'what_can_i_do':
            response_dict = show_possible_actions(mdn)
        elif intent == 'logout':
            response_dict = logout()
        elif intent is not None:
            # XXX really we probably should punt
            response_dict = unexpected_intent(name, intent)
        else:
            # XXX really we probably should punt
            response_dict = no_intent(name)

        if 'resetUserStorage' in response_dict['payload']['google']:
            print("Resetting user storage")
            response_dict['payload']['google']['userStorage'] = dict_to_str(mdn="")
        else:
            print(f"write user_storage: {user_storage}")
            response_dict['payload']['google']['userStorage'] = dict_to_str(user_storage)

        # response_str += f" , conversation I D {id_short(conv_id)} , user I D {id_short(google_user_id)}"

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
