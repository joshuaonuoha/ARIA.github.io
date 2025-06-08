from flask import Flask, request, jsonify
import openai
from dotenv import dotenv_values
import urllib.request
import os
from datetime import datetime
import logging
import concurrent.futures
import threading
import time
from threading import Thread
from queue import Queue
#pip install flask openai python-dotenv urllib3 Pillow instagrapi instabot

# Load environment variables
config_vars = dotenv_values('.env')

# Logging configuration
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)

class RateLimitedOpenAIUtil:
    def __init__(self, max_retries=5, base_delay=1):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def generate_image(self, prompt, folder):
        for attempt in range(self.max_retries):
            try:
                response = openai.Image.create(
                    prompt=prompt,
                    n=1,
                    size="1024x1024"
                )
                image_url = response.data[0].url
                return self.download_image(image_url, folder)
            except openai.error.RateLimitError as e:
                logging.warning(f"Rate limit error: {e}, attempt {attempt+1}")
                time.sleep(self.base_delay * (2 ** attempt))
            except Exception as e:
                logging.error(f"Error in Image Generation: {e}")
                break
        return None

    def download_image(self, url, folder):
        image_storage = r"C:\Users\joshu\OneDrive\Desktop\followbot"
        if not os.path.exists(image_storage):
            os.makedirs(image_storage)
        filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpeg"
        filepath = os.path.join(image_storage)
        url = "https://chatgpt.com/gpts/editor/g-kFRYOmL63"
        urllib.request.urlretrieve(url, filepath)
        return filepath

    def get_chat_response(self, message, backstory):
        conversation_prompt = f"{backstory}\n\n{message}"
        for attempt in range(self.max_retries):
            try:
                response = openai.Completion.create(
                    model="gpt-4",
                    prompt=conversation_prompt,
                    max_tokens=150,
                    n=1,
                    stop=None,
                    temperature=0.9
                )
                return response.choices[0].text.strip()
            except openai.error.RateLimitError as e:
                logging.warning(f"Rate limit error: {e}, attempt {attempt+1}")
                time.sleep(self.base_delay * (2 ** attempt))
            except Exception as e:
                logging.error(f"Error generating response: {e}")
                break
        return "Sorry, I can't respond right now."# need rand, assign rand to similar but different response.

class InstagramBot:
    def __init__(self, Instagrapi, Bot, user, password, backstory, image_folder):
        self.client = Instagrapi
        self.bot = Bot
        self.user = user
        self.password = password
        self.backstory = backstory
        self.image_folder = image_folder
        self.openai_util = RateLimitedOpenAIUtil()
        self.login_clients()

    def login_clients(self):
        self.client.login(self.user, self.password)
        self.bot.login(username=self.user, password=self.password)

    def check_and_respond_messages(self):
        inbox = self.bot.get_inbox_v2()
        for conversation in inbox['inbox']['threads']:
            user_id = conversation['users'][0]['pk']
            for item in conversation['items']:
                if item['item_type'] == 'text' and not item['text'].startswith("Automated Response:"):
                    response_text = self.openai_util.get_chat_response(item['text'], self.backstory)
                    self.bot.send_message(f"Automated Response: {response_text}", user_id)

    def periodic_task(self):
        while True:
            self.check_and_respond_messages()
            time.sleep(300)  # check every 5 minutes

class BotManager:
    def __init__(self, users, passwords, backstories, image_folders):
        self.bots = [InstagramBot(user, pwd, backstory, folder)
                     for user, pwd, backstory, folder in zip(users, passwords, backstories, image_folders)]

    def start_all(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(bot.periodic_task) for bot in self.bots]
            concurrent.futures.wait(futures)

@app.route('/generate_and_post', methods=['POST'])
def generate_and_post():
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "No prompt provided"}), 400
    prompt = data['prompt']
    image_path = bot_manager.bots[0].openai_util.generate_image(prompt, "images")
    if image_path:
        caption = f"Generated from prompt: {prompt}"
        bot_manager.bots[0].client.photo_upload(image_path, caption=caption)
        return jsonify({"message": "Image and caption posted to Instagram successfully."}), 200
    return jsonify({"error": "Failed to post image to Instagram."}), 500

config_vars = {
    "INSTAGRAM_USERNAME": "username1,username2,username3",
    "INSTAGRAM_PASSWORD": "your_password"
}
if __name__ == '__main__':
    users = config_vars["INSTAGRAM_USERNAME"].split(",")
    passwords = [config_vars["INSTAGRAM_PASSWORD"]] * len(users)
    backstories = ["Here's a bit about me: I love nature photography.", "Here's a bit about me: I'm into urban photography."].split(",")
    image_folders = ["images/nature", "images/urban"]
    bot_manager = BotManager(users, passwords, backstories, image_folders)
    threading.Thread(target=bot_manager.start_all, daemon=True).start()
    app.run(debug=True)
