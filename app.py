from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests

app = Flask(__name__)

# Alpha Vantage API configuration
API_KEY = '...............'  # Replace with your Alpha Vantage API key
BASE_URL = 'https://www.alphavantage.co/query'

# In-memory data structure to hold portfolio data
portfolio = {}

# Helper function to fetch real-time stock data
def fetch_stock_data(symbol):
    try:
        params = {'function': 'GLOBAL_QUOTE', 'symbol': symbol, 'apikey': API_KEY}
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            return {'price': float(quote["05. price"]), 'symbol': quote["01. symbol"]}
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error fetching stock data for {symbol}: {e}")
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portfolio')
def portfolio_page():
    for symbol in portfolio:
        stock_data = fetch_stock_data(symbol)
        if stock_data:
            current_price = stock_data['price']
            portfolio[symbol]['current_price'] = current_price
            portfolio[symbol]['performance'] = ((current_price - portfolio[symbol]['purchase_price']) /
                                                portfolio[symbol]['purchase_price']) * 100
    return render_template('portfolio.html', portfolio=portfolio)

@app.route('/add_stock', methods=['POST'])
def add_stock():
    symbol = request.form.get('symbol').upper()
    quantity = int(request.form.get('quantity'))
    purchase_price = float(request.form.get('purchase_price'))

    stock_data = fetch_stock_data(symbol)
    if stock_data:
        if symbol in portfolio:
            total_quantity = portfolio[symbol]['quantity'] + quantity
            total_investment = (portfolio[symbol]['quantity'] * portfolio[symbol]['purchase_price']) + \
                               (quantity * purchase_price)
            portfolio[symbol]['quantity'] = total_quantity
            portfolio[symbol]['purchase_price'] = total_investment / total_quantity
        else:
            portfolio[symbol] = {
                'quantity': quantity,
                'purchase_price': purchase_price,
                'current_price': stock_data['price'],
                'performance': 0.0
            }
    else:
        return jsonify({"error": f"Stock {symbol} not found or unavailable."}), 404

    return redirect(url_for('portfolio_page'))

@app.route('/remove_stock', methods=['POST'])
def remove_stock():
    symbol = request.form.get('symbol').upper()
    if symbol in portfolio:
        del portfolio[symbol]
    return redirect(url_for('portfolio_page'))

@app.route('/refresh', methods=['POST'])
def refresh_prices():
    for symbol in portfolio:
        stock_data = fetch_stock_data(symbol)
        if stock_data:
            current_price = stock_data['price']
            portfolio[symbol]['current_price'] = current_price
            portfolio[symbol]['performance'] = ((current_price - portfolio[symbol]['purchase_price']) /
                                                portfolio[symbol]['purchase_price']) * 100
    return redirect(url_for('portfolio_page'))

@app.route('/news')
def news_page():
    API_KEY = '........................'
    NEWS_API_URL = f'https://newsapi.org/v2/top-headlines?category=business&apiKey={API_KEY}'

    response = requests.get(NEWS_API_URL)
    news_data = response.json()

    news_items = []
    if news_data and 'articles' in news_data:
        news_items = [
            {
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'image_url': article['urlToImage'] if article['urlToImage'] else '/static/default-news.jpg',
                'source': article['source']['name']
            }
            for article in news_data['articles']
        ]

    return render_template('news.html', news_items=news_items)

@app.route('/dashboard')
def dashboard_page():
    total_invested = sum(data['quantity'] * data['purchase_price'] for data in portfolio.values())
    current_value = sum(data['quantity'] * data['current_price'] for data in portfolio.values())
    overall_performance = ((current_value - total_invested) / total_invested * 100) if total_invested else 0

    top_stocks = sorted(
        [{'symbol': symbol, 'performance': data['performance']} for symbol, data in portfolio.items()],
        key=lambda x: x['performance'],
        reverse=True
    )[:5]

    return render_template('dashboard.html', total_invested=total_invested, current_value=current_value,
                           overall_performance=overall_performance, top_stocks=top_stocks)

if __name__ == '__main__':
    app.run(debug=True)
