from flask import Flask, render_template, request, redirect
import requests, sqlite3
from textblob import TextBlob
from config import ALPHA_VANTAGE_API_KEY

app = Flask(__name__)
DATABASE = 'portfolio.db'

# DB setup
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS portfolio (
                            id INTEGER PRIMARY KEY,
                            symbol TEXT,
                            quantity INTEGER
                        );''')

def get_price(symbol):
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url).json()
    try:
        return float(response['Global Quote']['05. price'])
    except:
        return 0.0

def get_sentiment(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity  # -1 to 1

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        symbol = request.form['symbol'].upper()
        quantity = int(request.form['quantity'])
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("INSERT INTO portfolio (symbol, quantity) VALUES (?, ?)", (symbol, quantity))
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, quantity FROM portfolio")
        rows = cursor.fetchall()

    portfolio_data = []
    total_value = 0

    for symbol, quantity in rows:
        price = get_price(symbol)
        value = price * quantity
        sentiment_score = get_sentiment(f"{symbol} stock news performance and outlook")
        portfolio_data.append({
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'value': value,
            'sentiment': round(sentiment_score, 2)
        })
        total_value += value

    return render_template('dashboard.html', portfolio=portfolio_data, total_value=total_value)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
