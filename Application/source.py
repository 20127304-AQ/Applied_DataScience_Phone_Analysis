from flask import Flask, render_template, request, flash, redirect, url_for

import csv
import markdown

try:
    import google.generativeai as genai
except ModuleNotFoundError:
    print("Error: `google.generativeai` module not found.")

app = Flask(__name__)

def read_csv(file):
    with open(file, 'r', encoding="utf-8") as file:
        reader = csv.DictReader(file)
        products = list(reader)
    return products

if genai:
    try:
        genai.configure(api_key="ENTER YOUR API GEMINI KEY")  # Replace with your actual key
    except Exception as e:
        print(f"Error configuring `genai`: {e}")

def generate_response(input_text):
    if not genai:
        return "Generative AI module not available."

    try:
        model = genai.GenerativeModel(model_name="gemini-pro")
        response = model.generate_content(input_text)
        return response.text
    except Exception as e:
        print(f"Error generating response: {e}")
        return "An error occurred while generating a response."

products = read_csv('data/merged_final_df.csv')

# Route for the home page
@app.route('/')
def index():
    col_names = ['phone_name', 'ram', 'memory', 'price', 'sentiment_score']
    return render_template('index.html', options=col_names)

# Route for handling search queries
@app.route('/search', methods=['POST', 'GET'])
def search():
    name = request.form.get('query')
    ram = request.form.get('ram')
    storage = request.form.get('storage')
    min_price = request.form.get('min_price')
    max_price = request.form.get('max_price')
    sort_order = request.form.get('sort-option')
    
    if not name or not min_price:
        error_message = "Please fill the name of the product and minimum price"
        return render_template('results.html', error_message=error_message)

    # Filter products based on the search criteria
    results = []
    for product in products:
        if (name.lower() in product['phone_name'].lower() and name.lower() != "") and \
            (ram == "" or ram.lower() == product['ram']) and \
            (storage == "" or storage.lower() == product['memory']) and \
            (min_price == "" or int(min_price) <= int(product['price'])) and \
            (max_price == "" or int(max_price) >= int(product['price'])):
                
            product['price'] = int(product['price'])
            product['ram'] = int(product['ram'])
            product['memory'] = int(product['memory'])
            
            results.append(product)
    
    if sort_order == 'sorting': 
        option = request.form.get('value-type')
        results.sort(key=lambda x: x[option])
    
    return render_template('results.html', results=results)

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    if request.method == "POST":
        input_text = request.form.get("text")
        response_text = generate_response(input_text)
        print(response_text)
        rendered_text = markdown.markdown(response_text)
        return render_template("chat.html", 
                               input_text=input_text, 
                               response_text=rendered_text)
    return render_template("chat.html")

if __name__ == '__main__':
    app.run(debug=True)