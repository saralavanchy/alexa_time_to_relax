import logging
import json
import os
import boto3
import requests
from random import randint
import datetime as dt
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

#from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.dispatch_components import AbstractResponseInterceptor
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_core.exceptions import AskSdkException
import ask_sdk_core.utils as ask_utils

logger = logging.getLogger()
#retrieve logging level from lambda environmet properties
level = os.environ['LOG_LEVEL']
logger.setLevel(int(level))

WELCOME_MESSAGE = "Welcome to your Relaxing Time! " \
    " Together we will play differents activities to rest our tired minds. On this relaxing moment, <break time='1s'/> you will " \
     "<prosody volume='x-loud'> open your mind </prosody> to start flying over the creativity world. " \
    "Let's your spirit free and fly over that code break <break time='1s' /> By the end, you will see the final solution. " \
    "Let your chair, sit on the floor, and start by saying it's time to meditate or it's time to listen relaxing music theme."

CHOOSE_METHOD_REPROMPT = "Do you want to meditate or listen relaxing music theme?"
YES_OR_N0_REPROMPTS = ['Do not stall adventurer! Please answer yes or no. If you need a travel tip, say speak to the guide.','Be careful adventurer, is your answer yes or no.','You are running out of time adventurer! Please answer yes or no.','Adventurer, is your answer yes or no. If you need a travel tip, say speak to the guide.','Yes or No, adventurer! If you need a travel tip, say speak to the guide.']
GAME_END = "This is the end of our travel. Let's go to work again! Well, only you, I'm going to take a nap."

def launch_Relaxing_Time(handler_type, handler_input):
    logger.info( "In "+ handler_type )
    response_builder = handler_input.response_builder

    speak_output = WELCOME_MESSAGE
    reprompt_output = CHOOSE_METHOD_REPROMPT

    return (
        response_builder
            .speak(speak_output)
            .ask(reprompt_output)
            .response
    )


#Handler for skill launch with no intent
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return launch_Relaxing_Time("LaunchRequestHandler", handler_input)


####### Custom Intent Handlers########
class StartRelaxingMethodIntentHandler(AbstractRequestHandler):
    """Handler for Start Adventure intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("StartRelaxingMethodIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return launch_Relaxing_Time("StartRelaxingMethodIntentHandler",handler_input)


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hi, tired programmer! It's good to see you! To start relaxing you only need to say it's time to meditate or it's time to listen relaxing music theme. " 

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "See you soon!"
        speak_output = speak_output + " Now you are ready to continue in peace with your work. <prosody volume='x-loud'> Yo can do it! <prosody> I will be looking forward to relaxing together again"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech = (
                "<prosody volume='x-loud'> Oh no! <prosody> I think my circuits crossed because I couldn't understand you. <break time='1s'/> "
                "Lets start again our relaxing time by saying it's time to meditate or it's time to listen relaxing music theme. "
            )
        reprompt = "Well, you know, I'm only a machine. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(
            reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # Any cleanup logic goes here.

        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors."""
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        logger(handler_input)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class LoggingResponseInterceptor(AbstractResponseInterceptor):
    """Invoked immediately after execution of the request handler for an incoming request. 
    Used to print response for logging purposes
    """
    def process(self, handler_input, response):
         # type: (HandlerInput, Response) -> None
        logger.debug("Response logged by LoggingResponseInterceptor: {}".format(response))

class LoggingRequestInterceptor(AbstractRequestInterceptor):
    """Invoked immediately before execution of the request handler for an incoming request. 
    Used to print request for logging purposes
    """
    def process(self, handler_input):
        logger.debug("Request received by LoggingRequestInterceptor: {}".format(handler_input.request_envelope))

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.

# Skill Builder object
sb = CustomSkillBuilder(api_client=DefaultApiClient())

# Add all request handlers to the skill.
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(StartRelaxingMethodIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(FallbackIntentHandler())

# Add exception handler to the skill.
sb.add_exception_handler(CatchAllExceptionHandler())

# Add request and response interceptors
sb.add_global_response_interceptor(LoggingResponseInterceptor())
sb.add_global_request_interceptor(LoggingRequestInterceptor())

# Expose the lambda handler function that can be tagged to AWS Lambda handler
handler = sb.lambda_handler()