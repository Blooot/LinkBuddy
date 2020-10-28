# Slack->Airtable Link Salvager

### Motivation

I share a Slack workspace with a few friends. We use it to coordinate our weekly book club, keep in touch, and post interesting articles/links (mostly in the domain of software, design, leadership, startups, tools for thought).

The free plan of slack means that old messages get deleted. Because of this, we've been losing links that we'd much rather keep. So, I decided to build this simple and not very robust scraper to fix this problem. It does the job (and is run daily as a cron job).

### Setting up
Airtable doesn't expose the ability to request a list of your Airtable Bases. This means the link to the airtable base needs to be handled some other way. I chose to make it a command line argument. Find your Airtable base URL at https://airtable.com/api.

Slack makes you set up a bot since May 2020 rather than giving you a web API. So, you'll need a slack bot with the proper scope/permissions for this to work. This program uses two endpoints: https://slack.com/api/conversations.history and https://slack.com/api/conversations.list. Make sure your bot has the correct permissions for them

Caveat: LinkBuddy only supports posting to three fields in Airtable, namely "Name", "URL", and "Description". These fields show up in a URL preview in Slack.

### How to run it

I recommend running it with a shell script. Mine looks something like:

`export AIRTABLE_API=YOUR_AIRTABLE_API_HERE && export SLACK_API=YOUR_SLACK_API_HERE && python3 PATH_TO_FILE -s TARGET_SLACK_CHANNEL_NAME -a AIRTABLE_BASE_API_URL`

LinkBuddy defaults to pulling links from 24 hours ago.

You can also pass an optional argument `-r NUMBER_OF_DAYS` to pull links from NUMBER_OF_DAYS up until the current time.
