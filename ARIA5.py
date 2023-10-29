from flask import Flask, request, jsonify
import requests
import json
import instabot
import discord
from discord.ext import commands
import nest_asyncio
import os
from instabot import Bot
import time

# Discord bot setup
intents = discord.Intents.all()
intents.members = True
TOKEN = 'MTE1NzM4Njc0ODEyMTMzNzg4Nw.GoUHiy.YK0IZDKmvsUW0LvycoX2TkVCNi0jkHF0dXnyo4'  # Replace with your Discord bot token
bot = commands.Bot(command_prefix='!', intents=intents)
nest_asyncio.apply()

# Instagram Webhook Verification Token
INSTAGRAM_VERIFY_TOKEN = '3d4da2e723697d925d423dbcbb0acada'  # Replace with your actual verification token
#check 'Instagram Webhook Settings' below to add webhook info

# OpenAI API Key
OPENAI_API_KEY = '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'  # Replace with your actual API key

# Instagram bot setup
INSTAGRAM_USERNAME = 'business_usually'  # Replace with your Instagram username
INSTAGRAM_PASSWORD = '@Onuoha99'  # Replace with your Instagram password
instagram_bot = Bot()
instagram_bot.login(username=INSTAGRAM_USERNAME, password=INSTAGRAM_PASSWORD)

# Instagram bot functionality
accounts = ["Artist"]
amt = 150

"""for acc in accounts:
    followers = instagram_bot.get_user_followers(acc)
    follow_count = 1200

    while follow_count <= len(followers):
        follow_count += follow(instagram_bot, followers, follow_count, amt)
        time.sleep(3600)
        unfollow(instagram_bot, amt)
        time.sleep(3600)
        accounts.append(filter(instagram_bot, amt))"""

print("Instagram automation completed.")

# Create a Flask app for the Instagram webhook
app = Flask(__name__)

# Instagram Webhook Settings
webhook_base_url = 'https://yourdomain.com'  # Replace with your actual domain
webhook_path = '/instagram-webhook'
webhook_url = webhook_base_url + webhook_path

@app.route(webhook_path, methods=['POST'])
def instagram_webhook():
    data = request.get_json()
    message_text = data['message']['content']
    sender_id = data['sender_id']
    response = send_to_chatgpt(message_text)
    send_response_to_instagram(sender_id, response)
    return "OK"

@app.route(webhook_path, methods=['GET'])
def verify_webhook():
    if request.args.get("hub.verify_token") == INSTAGRAM_VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    else:
        return "Verification failed."

# Discord bot event handler for when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

# Discord bot event handler for messages
@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if the message is in the "MIDjourney" chat room
    if message.channel.name == 'MIDjourney':
        # Check if the message doesn't start with /imagine
        if not message.content.startswith('/imagine'):
            # Append /imagine to the beginning of the message
            message.content = '/imagine ' + message.content

        # Check if there are attachments (images) in the message
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith('image'):
                    # Download the image and save it to a file
                    await attachment.save('image.png')
                    await message.channel.send("Image received and saved as 'image.png'.")
                    await message.channel.send("You can add a prompt by entering your text after /imagine.")
        else:
            await message.channel.send("Please attach an image file with the /imagine command.")
        await bot.process_commands(message)

# Discord bot command for sending text to a specific channel
@bot.command()
async def send_to_channel(ctx):
    channel_name = "general"
    channel = discord.utils.get(ctx.guild.channels, name=channel_name)

    if channel:
        await channel.send("Hello from the bot to this channel!")

@bot.command()
async def imagine(ctx, *, input_text):
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]

        if attachment.content_type.startswith('image'):
            await attachment.save('image.png')
            await ctx.send("Image received and saved as 'image.png'.")
            await ctx.send(f"You entered the prompt: '{input_text}'")
            await upload_to_instagram(input_text)
        else:
            await ctx.send("The attached file is not an image.")
    else:
        await ctx.send("Please attach an image file with the /imagine command.")

# New Discord bot command for sending custom messages
@bot.command()
async def send_message(ctx, *, message):
    try:
        sent_message = await ctx.send(message)
        print(f"Message sent successfully with content: {sent_message.content}")
    except discord.DiscordException as e:
        print(f"An error occurred: {str(e)}")

# Function to upload the saved image to Instagram
async def upload_to_instagram(caption):
    try:
        instagram_bot.upload_photo("image.png", caption=caption)
    except Exception as e:
        print(f"Error uploading to Instagram: {str(e)}")
# Function to send a JSON request to an API
def send_json_request(url, data, headers):
    try:
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            # Request was successful
            response_data = response.json()  # Parse the JSON response
            print(response_data)
        else:
            print(f"Request failed with status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error sending JSON request: {str(e)}")

# Function to send the message to ChatGPT
def send_to_chatgpt(message):
    api_url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}' 
    }
    payload = {
        'messages': [{'role': 'system', 'content': 'Your USER_ID'}, {'role': 'user', 'content': message}]
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    response_data = response.json()
    return response_data['choices'][0]['message']['content']

# Function to send the response back to Instagram
def send_response_to_instagram(recipient_id, response):
    # Step 1: Save the ChatGPT response to a text file
    response_file = f'chatgpt_response_{recipient_id}.txt'

    with open(response_file, 'w', encoding='utf-8') as file:
        file.write(response)
    print("ChatGPT DM ON.")
    # Step 2: Upload the saved response text file to Instagram
    try:
        instagram_bot.upload_photo(response_file, caption=response)

        # Clean up: delete the temporary text file
        os.remove(response_file)

        print(f"ChatGPT response saved to {response_file} and uploaded to Instagram.")
    except Exception as e:
        print(f"Error uploading to Instagram: {str(e)}")

if __name__ == '__main__':
    bot.run(TOKEN)  # Start the Discord bot
    app.run(debug=True)  # Start the Flask app for the Instagram webhook

