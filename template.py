# imports
from time import sleep
import requests
# end_imports

# variables
refresh_time = 50
no_username = 'کاربر'
CONST_STATUSES = {}
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
    return response.json()



def send_message(chat_id, text):
    url = f"https://tapi.bale.ai/bot{access_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

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
    status = CONST_STATUSES.get(chat_id)
    if status is None:
        CONST_STATUSES[chat_id] = default_status
        status = default_status
    # on_statements
    # end_on_statements
    CONST_STATUSES[chat_id] = status

# before
print("Starting bot...")
# end_before

if __name__ == "__main__":
    last_update_id = None

    while True:
        updates = update_handler(last_update_id)
        for update in updates.get("result", []):
            if "message" in update:
                handler(update["message"])
                last_update_id = update["update_id"] + 1
        sleep(1 / refresh_time)