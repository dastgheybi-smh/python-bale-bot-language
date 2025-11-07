# imports
from json.decoder import JSONDecodeError
from time import sleep
import requests
from colorama import Fore, init
# end_imports

init(autoreset=True)

# variables
refresh_time = 50
no_username = 'کاربر'
CONST_STATUSES = {}
access_token = "TOKEN"
default_status = ""
# end_variables

# functions

def delete_message(chat_id, message_id):
    url = f"https://tapi.bale.ai/bot{access_token}/deleteMessage"
    payload = {
        'chat_id': chat_id,
        'message_id': message_id
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except JSONDecodeError:
        return None


def send_message(chat_id, text, inline_keyboard=None):
    url = f"https://tapi.bale.ai/bot{access_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }

    if inline_keyboard:
        payload['reply_markup'] = {
            'inline_keyboard': inline_keyboard
        }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except JSONDecodeError:
        return None

# end_functions


def update_handler(offset=None):
    url = f"https://tapi.bale.ai/bot{access_token}/getUpdates"
    if offset:
        url += f"?offset={offset}"
    response = requests.get(url)
    return response.json()

def handler(message):
    chat_id = message['chat']['id']
    message_id = message['message_id']
    text = message.get('text', '')
    user_fullname = message['from'].get('first_name', no_username)
    # series
    status = CONST_STATUSES.get(chat_id)
    if status is None:
        CONST_STATUSES[chat_id] = default_status
        status = default_status
    # end_series
    # on_statements
    # end_on_statements
    # series_setter
    CONST_STATUSES[chat_id] = status
    # end_series_setter
    # status_checker_redirect
    # end_status_checker_redirect

# before
print("Starting bot...")
# end_before

if __name__ == "__main__":
    last_update_id = None
    updates = update_handler(last_update_id)
    for update in updates.get("result", []):
        if "message" in update:
            last_update_id = update["update_id"] + 1

    while True:
        try:
            # mainloop
            # end_mainloop
            updates = update_handler(last_update_id)
            for update in updates.get("result", []):
                if "message" in update:
                    handler(update["message"])
                    last_update_id = update["update_id"] + 1
        except Exception as e:
            print(Fore.RED + "Exception: ", Fore.YELLOW + repr(e))
        sleep(1 / refresh_time)
