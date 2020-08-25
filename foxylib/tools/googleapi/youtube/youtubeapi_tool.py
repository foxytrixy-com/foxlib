# -*- coding: utf-8 -*-

# Sample Python code for youtube.liveChatMessages.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/guides/code_samples#python

import os
from datetime import datetime, timedelta

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pytz

from foxylib.tools.collections.collections_tool import l_singleton2obj

from foxylib.tools.googleapi.foxylib_googleapi import FoxylibGoogleapi
from foxylib.tools.json.json_tool import JsonTool

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


class YoutubeapiTool:
    @classmethod
    def credentials2service(cls, credentials):
        return googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)


class DataapiTool:
    @classmethod
    def video_id2live_streaming_data(cls, video_id):
        # https://stackoverflow.com/questions/36683878/youtube-api-how-do-i-get-the-livechatid
        # https://developers.google.com/youtube/v3/docs/videos/list

        credentials = FoxylibGoogleapi.ServiceAccount.credentials()
        service = YoutubeapiTool.credentials2service(credentials)
        request = service.videos().list(id=video_id, part='liveStreamingDetails',)
        response = request.execute()

        items = response.get("items")
        if not items:
            return None

        item = l_singleton2obj(items)

        return item.get("liveStreamingDetails")

class LiveStreamingData:
    @classmethod
    def data2chat_id(cls, data):
        return data["activeLiveChatId"]


class LivestreamingapiTool:
    @classmethod
    def live_chat_id2response(cls, credentials, live_chat_id):
        service = YoutubeapiTool.credentials2service(credentials)

        request = service.liveChatMessages().list(
            liveChatId=live_chat_id,
            part="id,snippet,authorDetails"
        )
        response = request.execute()
        return response

    @classmethod
    def response2items(cls, response):
        return response.get("items") or []

    @classmethod
    def item2id(cls, item):
        return item["id"]

    @classmethod
    def item2message(cls, item):
        msg = JsonTool.down(item, ["snippet","textMessageDetails","messageText"])
        return msg

    @classmethod
    def response2pollingIntervalMillis(cls, response):
        return response['pollingIntervalMillis']

    @classmethod
    def response2datetime_next_poll(cls, response):
        polling_interval_millis = cls.response2pollingIntervalMillis(response)
        dt_now = datetime.now(pytz.utc)
        return dt_now + timedelta(milliseconds=polling_interval_millis)





def main():
    # https://developers.google.com/youtube/v3/live/docs/liveChatMessages/list?apix=true

    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # api_service_name = "youtube"
    # api_version = "v3"
    # client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"

    # Get credentials and create an API client
    credentials = FoxylibGoogleapi.ServiceAccount.credentials()
    service = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)


    chat_id = 'Cg0KC25IUktvTk9RNTZ3KicKGFVDbXJscUZJS19RUUNzcjNGUkhhM09LdxILbkhSS29OT1E1Nnc'

    request = service.liveChatMessages().list(
        liveChatId=chat_id,
        part="id,snippet,authorDetails"
    )
    response = request.execute()

    print(response)


if __name__ == "__main__":
    main()
