from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import logging
from events.Sharingan_Summarizer import Sharingan_Summarizer
from bs4 import BeautifulSoup
from newspaper import Article
from transformers import pipeline
from rouge_score import rouge_scorer


logger = logging.getLogger(__name__)

SLACK_VERIFICATION_TOKEN = getattr(settings, 'SLACK_VERIFICATION_TOKEN', None)
SLACK_BOT_USER_TOKEN = getattr(settings, 'SLACK_BOT_USER_TOKEN', None)
Client = WebClient(SLACK_BOT_USER_TOKEN)

# Global variable to store bot user ID
bot_user_id = None

recent_message_ts = None

# Retrieve bot user ID when server starts
try:
    response = Client.auth_test()
    bot_user_id = response['user_id']
except SlackApiError as e:
    logger.error(f"Error fetching bot user ID: {e.response['error']}")

class Events(APIView):
    def post(self, request, *args, **kwargs):
        global recent_message_ts  # Declare the global variable

        try:
            slack_message = json.loads(request.body.decode('utf-8'))
            logger.info(f'Received Slack message: {slack_message}')
            
            if slack_message.get('token') != SLACK_VERIFICATION_TOKEN:
                logger.warning('Invalid verification token')
                return Response(status=status.HTTP_403_FORBIDDEN)
            
            if slack_message.get('type') == 'url_verification':
                return Response(data=slack_message, status=status.HTTP_200_OK)
            
            if 'event' in slack_message:
                event_message = slack_message.get('event')
                
                # Ensure this is a message event and not a bot message
                if event_message.get('type') != 'message' or event_message.get('subtype') == 'bot_message':
                    return Response(status=status.HTTP_200_OK)
                
                # Ignore messages without user
                if 'user' not in event_message or event_message.get('user') == bot_user_id:
                    logger.info('Ignoring bot\'s own message or message without user')
                    return Response(status=status.HTTP_200_OK)
                
                user = event_message.get('user')
                text = event_message.get('text')
                channel = event_message.get('channel')
                print(f"{channel}")
                event_ts = float(event_message.get('ts'))

                if 'Hi ' in text:
                    if recent_message_ts != None and event_ts - recent_message_ts < 60:
                        logger.info('Ignoring duplicate message')
                        return Response(status=status.HTTP_200_OK)
                    else:
                        recent_message_ts = event_ts

                    sources = [
                        "https://www.cnn.com/",
                        "https://www.foxnews.com/",
                        "https://www.nbcnews.com/"
                    ]
                    css_selectors = [
                        ".container__headline-text",  # Updated selector: targets the headline titles
                        ".title",
                        ".multistoryline__headline"
                    ]
                    # Create Bot Message
                    tomoe_summarizer = Sharingan_Summarizer(sources, css_selectors)
                    # Define the file path
                    file_path = tomoe_summarizer.get_save_path()

                    # Open and read the file
                    with open(file_path, 'r') as file:
                        content = file.read()

                    bot_text = f'Hello <@{user}> :wave:\nHere is today\'s news:\n{content}'

                    try:
                        Client.chat_postMessage(channel=channel, text=bot_text)
                        logger.info(f'Sent message to channel {channel}')
                    except SlackApiError as e:
                        logger.error(f"Error posting message: {e.response['error']}")
                    return Response(status=status.HTTP_200_OK)
            
            return Response(status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
