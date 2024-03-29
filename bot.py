from flask import Flask, request, Response
from kik import KikApi, Configuration
from kik.messages import messages_from_json, TextMessage, PictureMessage, \
    SuggestedResponseKeyboard, TextResponse, StartChattingMessage


class KikBot(Flask):

    def __init__(self, kik_api, import_name, static_path=None, static_url_path=None, static_folder="static",
                 template_folder="templates", instance_path=None, instance_relative_config=False,
                 root_path=None):

        self.kik_api = kik_api

        super(KikBot, self).__init__(import_name, static_path, static_url_path, static_folder, template_folder,
                                     instance_path, instance_relative_config, root_path)

        self.route("/incoming", methods=["POST"])(self.incoming)

    def incoming(self):
        if not self.kik_api.verify_signature(
                request.headers.get("X-Kik-Signature"), request.get_data()):
            return Response(status=403)

        messages = messages_from_json(request.json["messages"])

        response_messages = []

        for message in messages:
            user = self.kik_api.get_user(message.from_user)
            # Check if its the user's first message. Start Chatting messages are sent only once.
            if isinstance(message, StartChattingMessage):

                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Hey {}, how are you?".format(user.first_name),
                    # keyboards are a great way to provide a menu of options for a user to respond with!
                    keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Good"), TextResponse("Bad")])]))

            # Check if the user has sent a text message.
            elif isinstance(message, TextMessage):
                user = self.kik_api.get_user(message.from_user)
                message_body = message.body.lower()

                if message_body.split()[0] in ["hi", "hello"]:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Hey {}, how are you?".format(user.first_name),
                        keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Good"), TextResponse("Bad"),TextResponse("Fantastic")])]))

                elif message_body == "good":
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="That's Great! :) Wanna see your profile pic?",
                        keyboards=[SuggestedResponseKeyboard(
                            responses=[TextResponse("Sure! I'd love to!"), TextResponse("No Thanks")])]))

                elif message_body == "bad":
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Oh No! :( Wanna see your profile pic?",
                        keyboards=[SuggestedResponseKeyboard(
                            responses=[TextResponse("Yep! I Sure Do!"), TextResponse("No Thank You")])]))

                elif message_body == "fantastic":
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Oh Fantastic! feeling great :( Wanna see your profile pic?",
                        keyboards=[SuggestedResponseKeyboard(
                            responses=[TextResponse("Yep! I Sure Do!"), TextResponse("No Thank You")])]))

                elif message_body in ["yep! i sure do!", "sure! i'd love to!"]:

                    # Send the user a response along with their profile picture (function definition is below)
                    response_messages += self.profile_pic_check_messages(user, message)

                elif message_body in ["no thanks", "no thank you"]:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Ok, {}. Chat with me again if you change your mind.".format(user.first_name)))
                else:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Sorry {}, I didn't quite understand that. How are you?".format(user.first_name),
                        keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Good"), TextResponse("Bad")])]))

            # If its not a text message, give them another chance to use the suggested responses
            else:

                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Sorry, I didn't quite understand that. How are you, {}?".format(user.first_name),
                    keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Good"), TextResponse("Bad")])]))

            # We're sending a batch of messages. We can send up to 25 messages at a time (with a limit of
            # 5 messages per user).

            self.kik_api.send_messages(response_messages)

        return Response(status=200)

    @staticmethod
    def profile_pic_check_messages(user, message):
        messages_to_send = []
        profile_picture = user.profile_pic_url

        if profile_picture is not None:
            messages_to_send.append(
                # Another type of message is the PictureMessage - your bot can send a pic to the user!
                PictureMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    pic_url=profile_picture
                ))

            profile_picture_response = "Here's your profile picture!"
        else:
            profile_picture_response = "It does not look like you have a profile picture, you should set one"

        messages_to_send.append(
            TextMessage(to=message.from_user, chat_id=message.chat_id, body=profile_picture_response))

        return messages_to_send


if __name__ == "__main__":
    """ Main program """
    kik = KikApi('skb1992_007', 'dffc79c9-ad98-44a3-bda5-ba98ce90f4b9')
    # For simplicity, we're going to set_configuration on startup. However, this really only needs to happen once
    # or if the configuration changes. In a production setting, you would only issue this call if you need to change
    # the configuration, and not every time the bot starts.
    kik.set_configuration(Configuration(webhook='https://a3a2fe23.ngrok.io/incoming'))
    app = KikBot(kik, __name__)
    app.run(port=8080, host='127.0.0.1', debug=True)
