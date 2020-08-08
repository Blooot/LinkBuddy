import os
import json
import requests
import time

import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '-r', '--range', help='denotes the range of message history to scrape (in days)')

parser.add_argument(
    '-s', '--slack', help='specify the name of the slack channel to scrape')

parser.add_argument(
    '-a', '--airtable', help='specify the name of the Airtable Base')
args = parser.parse_args()


# defaults to scraping from 1 day ago
if args.range:
    user_time = int(args.range)
else:
    user_time = 1

if not args.slack:
    raise Exception("You must enter the target Slack channel")
if not args.airtable:
    raise Exception("You must enter the target Airtable Base")

"""Airtable Setup"""
AIRTABLE_RATE_LIMITER_IN_SECONDS = 5
AIRTABLE_API = os.getenv('AIRTABLE_API')
# Unfortunately, there's no way to programatically find all of your tables with your api key
AIRTABLE_LINKS_URL = args.airtable
AIRTABLE_HEADERS = {'Authorization': 'Bearer {}'.format(
    AIRTABLE_API), 'Content-type': 'application/json'}


def chonkify(lst, size_of_chonk=10):
    # Posts to airtable can contain up to 10 records
    for idx in range(0, len(lst), size_of_chonk):
        yield lst[idx:idx + size_of_chonk]


def airtable_chonkify_into_posts(res):
    # convert slack fields to airtable fields
    slack_to_airtable_fields = {'title': 'Name',
                                'text': "Description", 'from_url': "URL"}
    base = []
    for message in res['messages']:
        # if a post has an attachment -- the preview image
        if 'attachments' in message:
            fields = {"fields": {}}
            # a post might have multiple attachments
            for attachment in message['attachments']:
                for s in ('title', 'text', 'from_url'):
                    if s in attachment:
                        fields["fields"][slack_to_airtable_fields[s]
                                         ] = attachment[s]
                base.append(fields)
    # we can only post 10 records to airtable at a time
    return chonkify(base)


def airtable_post_with_rate_limiter(data):
    for group_of_10 in data:
        base = {"records": []}
        for item in group_of_10:
            base["records"].append(item)

        r = requests.post(AIRTABLE_LINKS_URL,
                          headers=AIRTABLE_HEADERS, data=json.dumps(base))
        print("Posting data to Airtable:", r.status_code)
        time.sleep(AIRTABLE_RATE_LIMITER_IN_SECONDS)


"""Slack Setup"""
SLACK_API = os.getenv('SLACK_API')
CONVO_HISTORY_URL = 'https://slack.com/api/conversations.history'
ALL_CHANNEL_URL = 'https://slack.com/api/conversations.list'
FETCH_FROM = time.time() - user_time * 24 * 60 * 60


def get_channel_id(name):
    r = requests.get(ALL_CHANNEL_URL, {
                     'token': SLACK_API, 'exclude_archived': True, 'types': 'public_channel, private_channel'})
    res = r.json()
    for channel in res['channels']:
        if channel["name"] == name:
            return channel["id"]
    raise KeyError("Channel does not exist")


def get_slack_messages():
    r = requests.get(
        CONVO_HISTORY_URL, {'token': SLACK_API, 'channel': get_channel_id(args.slack), 'limit': 1000, 'oldest': FETCH_FROM})
    print("Getting data from Slack:", r.status_code)
    return r.json()


"""Main"""
if __name__ == "__main__":
    get_channel_id(args.slack)

    filtered_slack_fields = airtable_chonkify_into_posts(get_slack_messages())
    airtable_post_with_rate_limiter(filtered_slack_fields)
