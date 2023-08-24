import os
from flask import Flask, render_template, request, jsonify
import openai
import BingImageCreator
import time
import requests
from PIL import Image
from io import BytesIO
import base64
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

# Replace "your API KEY from `/key get` Discord command" with your actual OpenAI API key
openai.api_key = os.environ['OPENAI_API_KEY']
openai.api_base = "https://chimeragpt.adventblocks.cc/api/v1"  # Corrected API Base URL
BING_KEY = os.environ['BING_KEY']
BING_KEY_SRC = os.environ['BING_KEY_2']
REPLICATE_KEY = os.environ['REPLICATE_KEY']
correct_key = os.environ['WEB_KEY']


size_ratios = {
    "1:1": ["512", "512"],
    "16:9": ["1024", "576"],
    "9:16": ["576", "1024"],
    "3:2": ["960", "640"],
    "2:3": ["640", "960"]
}
size_ratios_sdxl = {
    "1:1": [1024, 1024],
    "16:9": [1024, 576],
    "9:16": [576, 1024],
    "3:2": [960, 640],
    "2:3": [640, 960]
}

def split_image(image):
    width, height = image.size
    quarter_width = width // 2
    quarter_height = height // 2
    quarters = []

    for i in range(2):
        for j in range(2):
            left = j * quarter_width
            top = i * quarter_height
            right = left + quarter_width
            bottom = top + quarter_height
            quarter = image.crop((left, top, right, bottom))
            quarters.append(quarter)

    return quarters

@app.route("/", methods=["POST", "GET"])
def index():
    return render_template("index.html")
@app.route("/api", methods=["POST", "GET"])
def api():
    if request.method == "POST":
        prompt = request.form["prompt"]
        size_ratio = request.form["size_ratio"]  # Get the size ratio from the form
        n = int(request.form["count"])  # Get the count from the form
        model = request.form["model"]
        key = request.form["key"]
        try:
            if size_ratio not in size_ratios:
                return jsonify({"error": "Invalid size ratio."})
            if model == "kandinsky-r":
                size = size_ratios[size_ratio]
                width, height = size
                data = {
                    "version": "ea1addaab376f4dc227f5368bbd8eff901820fd1cc14ed8cad63b29249e9d463",
                    "input": {
                        "prompt": prompt,
                        "num_outputs": n,
                        "width": int(width),
                        "height": int(height),
                    }
                }
                headers = {
                    "Authorization": f"Token {REPLICATE_KEY}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=data)
                response_data = response.json()
                prediction_id = response_data["id"]
                prediction_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
                
                while True:
                    prediction_response = requests.get(prediction_url, headers=headers)
                    prediction_data = prediction_response.json()
                    if prediction_data["status"] == "succeeded":
                        output = prediction_data["output"]
                        dict = []
                        for url in output:
                            dict.append({"url": url})
                        return dict
                    if prediction_data["status"] == "failed":
                        return jsonify({"error": "Model failed generating."})
                    time.sleep(2)
            elif model == "kandinsky-c":
                size = size_ratios[size_ratio]
                width, height = size
                response = openai.Image.create(prompt=prompt, n=n, size=f"{width}x{height}")
                images_data = response["data"]
                print(images_data)
                return jsonify(images_data)
            elif model == "dalle":
                size = size_ratios[size_ratio]
                width, height = size
                response = openai.Image.create(prompt=prompt, n=n, size=f"{width}x{height}", model="dall-e")
                images_data = response["data"]
                print(images_data)
                return jsonify(images_data)
            elif model == "sd15":
                size = size_ratios[size_ratio]
                width, height = size
                response = openai.Image.create(prompt=prompt, n=n, size=f"{width}x{height}", model="stable-diffusion-1.5")
                images_data = response["data"]
                print(images_data)
                return jsonify(images_data)
            elif model == "sd21":
                size = size_ratios[size_ratio]
                width, height = size
                response = openai.Image.create(prompt=prompt, n=n, size=f"{width}x{height}", model="stable-diffusion-2.1")
                images_data = response["data"]
                print(images_data)
                return jsonify(images_data)
            elif model == "if":
                size = size_ratios[size_ratio]
                width, height = size
                response = openai.Image.create(prompt=prompt, n=n, size=f"{width}x{height}", model="deepfloyd-if")
                images_data = response["data"]
                print(images_data)
                return jsonify(images_data)
            elif model == "midjourney":
                if key != correct_key:
                    return jsonify({"error": "Incorrect Key."})
                
                response = openai.Image.create(prompt=prompt, n=n, model="midjourney")
                images_data = response["data"]
                print(images_data)
                return jsonify(images_data)
                
                # Unused splitting images
                image_url = images_data[0]['url']
                image_response = requests.get(image_url)
        
                if image_response.status_code:
                    image_bytes = BytesIO(image_response.content)
                    image = Image.open(image_bytes)
                    quarters = split_image(image)
                    quarter_images_base64 = []
        
                    for quarter in quarters:
                        quarter_bytes = BytesIO()
                        quarter.save(quarter_bytes, format="PNG")
                        quarter_base64 = base64.b64encode(quarter_bytes.getvalue()).decode('utf-8')
                        quarter_images_base64.append(quarter_base64)
        
                    return jsonify({"quarter_images_base64": quarter_images_base64, "base64": True})
                else:
                    return jsonify({"error": "Failed to download image."})
            elif model == "bing":
                print(BING_KEY)
                bing_client = BingImageCreator.ImageGen(auth_cookie=BING_KEY, quiet=True, auth_cookie_SRCHHPGUSR=BING_KEY_SRC)
                output = bing_client.get_images(prompt)
                print(output)
                dict = []
                for url in output:
                    dict.append({"url": url})
                return dict
            elif model == "sdxl":
                size = size_ratios_sdxl[size_ratio]
                width, height = size
                data = {
                    "version": "2b017d9b67edd2ee1401238df49d75da53c523f36e363881e057f5dc3ed3c5b2",
                    "input": {
                        "prompt": prompt,
                        "num_outputs": n,
                        "width": width,
                        "height": height,
                    }
                }
                headers = {
                    "Authorization": f"Token {REPLICATE_KEY}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=data)
                response_data = response.json()
                prediction_id = response_data["id"]
                prediction_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
                
                while True:
                    prediction_response = requests.get(prediction_url, headers=headers)
                    prediction_data = prediction_response.json()
                    if prediction_data["status"] == "succeeded":
                        output = prediction_data["output"]
                        dict = []
                        for url in output:
                            dict.append({"url": url})
                        return dict
                    if prediction_data["status"] == "failed":
                        return jsonify({"error": "Model failed generating."})
                    time.sleep(2)
            elif model == "dreamshaper":
                size = size_ratios[size_ratio]
                width, height = size
                data = {
                    "version": "6197db9cdf865a7349acaf20a7d20fe657d9c04cc0c478ec2b23565542715b95",
                    "input": {
                        "prompt": prompt,
                        "num_outputs": n,
                        "width": int(width),
                        "height": int(height),
                    }
                }
                headers = {
                    "Authorization": f"Token {REPLICATE_KEY}",
                    "Content-Type": "application/json"
                }
            
                response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=data)
                response_data = response.json()
                print(response_data)
                prediction_id = response_data["id"]
                prediction_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
            
                while True:
                    prediction_response = requests.get(prediction_url, headers=headers)
                    prediction_data = prediction_response.json()
                    if prediction_data["status"] == "succeeded":
                        output = prediction_data["output"]
                        dict = []
                        for url in output:
                            dict.append({"url": url})
                        return dict
                    if prediction_data["status"] == "failed":
                        return jsonify({"error": "Model failed generating."})
                    time.sleep(2)
            elif model == "deliberate":
                size = size_ratios[size_ratio]
                width, height = size
                data = {
                    "version": "6197db9cdf865a7349acaf20a7d20fe657d9c04cc0c478ec2b23565542715b95",
                    "input": {
                        "prompt": prompt,
                        "num_outputs": n,
                        "width": int(width),
                        "height": int(height),
                    }
                }
                headers = {
                    "Authorization": f"Token {REPLICATE_KEY}",
                    "Content-Type": "application/json"
                }
            
                response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=data)
                response_data = response.json()
                print(response_data)
                prediction_id = response_data["id"]
                prediction_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
            
                while True:
                    prediction_response = requests.get(prediction_url, headers=headers)
                    prediction_data = prediction_response.json()
                    if prediction_data["status"] == "succeeded":
                        output = prediction_data["output"]
                        dict = []
                        for url in output:
                            dict.append({"url": url})
                        return dict
                    if prediction_data["status"] == "failed":
                        return jsonify({"error": "Model failed generating."})
                    time.sleep(2)
            else:
                return jsonify({"error": "Invalid model name"})
        except Exception as e:
            return jsonify({"error": f"{e}"})
    else:
        return jsonify({"error": "Please use POST not GET"})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
