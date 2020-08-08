import os
import json
import requests
import time

import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '-r', '--range', help='denotes the range of message history to scrape (in days)')
args = parser.parse_args()

# defaults to scraping from 1 day ago
if args.range:
    user_time = int(args.range)
else:
    user_time = 1

"""Airtable Setup"""
AIRTABLE_RATE_LIMITER_IN_SECONDS = 5
AIRTABLE_API = os.getenv('AIRTABLE_API')
AIRTABLE_LINKS_URL = 'https://api.airtable.com/v0/app4yrWh1kXkkEsM3/Links'
AIRTABLE_HEADERS = {'Authorization': 'Bearer {}'.format(
    AIRTABLE_API), 'Content-type': 'application/json'}


def chonkify(lst, size_of_chonk=10):
    # Post to airtable can contain up to 10 records
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
CONVO_ID = 'C011ABFQQTE'
FETCH_FROM = time.time() - user_time * 24 * 60 * 60


def get_slack_messages():
    r = requests.get(
        CONVO_HISTORY_URL, {'token': SLACK_API, 'channel': CONVO_ID, 'limit': 1000, 'oldest': FETCH_FROM})
    print("Getting data from Slack:", r.status_code)
    return r.json()


"""Main"""
if __name__ == "__main__":
    filtered_slack_fields = airtable_chonkify_into_posts(get_slack_messages())
    airtable_post_with_rate_limiter(filtered_slack_fields)
