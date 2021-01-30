import logging
import os
import re
from maigret.maigret import maigret
from maigret.result import QueryStatus
from maigret.sites import MaigretDatabase
from mock import Mock
from telethon.sync import TelegramClient, events

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

MAIGRET_DB_URL = 'https://raw.githubusercontent.com/soxoj/maigret/main/maigret/resources/data.json'
USERNAME_REGEXP = r'^[a-zA-Z0-9-_\.]{5,}$'
ADMIN_USERNAME = '@soxoj'

TOP_SITES_COUNT = 1500
TIMEOUT = 30
MAX_TG_MSG_CHARS = 4000

DB = MaigretDatabase().load_from_url(MAIGRET_DB_URL)


async def maigret_search(username):
    """
        Main Maigret search function
    """
    global DB

    log_level = logging.WARNING
    logging.basicConfig(
        format='[%(filename)s:%(lineno)d] %(levelname)-3s  %(asctime)s %(message)s',
        datefmt='%H:%M:%S',
        level=log_level
    )
    logger = logging.getLogger('maigret')
    logger.setLevel(log_level)

    # workaround to update database from git master
    try:
        db = MaigretDatabase().load_from_url(MAIGRET_DB_URL)
        DB = db
    except Exception as e:
        logger.error(e)
        db = DB

    site_data = db.ranked_sites_dict(top=TOP_SITES_COUNT)
    # can be object with editing tg msg handler to show search progress
    query_notify = Mock()

    results = await maigret(username,
                            dict(site_data),
                            query_notify,
                            timeout=TIMEOUT,
                            logger=logger,
                            no_progressbar=True,
                            )
    return results


def merge_sites_into_messages(found_sites):
    """
        Join links to found accounts and make telegram messages list
    """
    if not found_sites:
        return ['No accounts found!']

    found_accounts = len(found_sites)
    found_sites_messages = []
    found_sites_entry = found_sites[0]

    for i in range(len(found_sites) - 1):
        found_sites_entry = ', '.join([found_sites_entry, found_sites[i + 1]])

        if len(found_sites_entry) > MAX_TG_MSG_CHARS:
            found_sites_messages.append(found_sites_entry)
            found_sites_entry = ''

    if found_sites_entry != '':
        found_sites_messages.append(found_sites_entry)

    output_messages = [f'{found_accounts} accounts found:\n{found_sites_messages[0]}'] + found_sites_messages[1:]
    return output_messages


async def search(username):
    """
        Do Maigret search on a chosen username
        :return:
            - list of telegram messages
            - list of dicts with found results data
    """
    try:
        results = await maigret_search(username)
    except Exception as e:
        logging.error(e)
        return ['An error occurred, send username once again.'], []

    found_exact_accounts = []

    for site, data in results.items():
        if data['status'].status != QueryStatus.CLAIMED:
            continue
        url = data['url_user']
        account_link = f'[{site}]({url})'

        # filter inaccurate results
        if not data.get('is_similar'):
            found_exact_accounts.append(account_link)

    if not found_exact_accounts:
        return [], []

    messages = []
    messages += merge_sites_into_messages(found_exact_accounts)

    # full found results data
    results = list(filter(lambda x: x['status'].status == QueryStatus.CLAIMED, list(results.values())))

    return messages, results


with TelegramClient('name', API_ID, API_HASH) as client:
    @client.on(events.NewMessage())
    async def handler(event):
        msg = event.message.message

        # checking for username format
        msg = msg.lstrip('@')
        username_regexp = re.search(USERNAME_REGEXP, msg)
        if not username_regexp:
            await event.reply('Username must be more than 4 characters '
                              'and can only consist of Latin letters, '
                              'numbers, minus and underscore.')
            return

        async with client.action(event.chat_id, 'typing'):
            await event.reply(f'Searching by username `{msg}`...')

        # call Maigret
        output_messages, _ = await search(msg)

        if not output_messages:
            await event.reply('No accounts found!')
        else:
            for output_message in output_messages:
                try:
                    await event.reply(output_message)
                except Exception as e:
                    logging.error(e, exc_info=True)
                    await event.reply('Unexpected error has been occurred. '
                                      f'Write a message {ADMIN_USERNAME}, he will fix it.')

    # uncomment to send you message on each script launch
    # client.send_message(ADMIN_USERNAME, 'Go!')
    client.run_until_disconnected()
