# Find Best Gas Prices

**Find Best Gas Prices** is a Flask-based web application that helps users to find the best gas prices near their location, based on vehicle fuel efficiency and driving distance. Utilizing an external API to fetch live gas prices, this application calculates the total cost of purchasing gas including travel costs, making it easier for users to make informed decisions about where to fill up their vehicles.

## Features
- **Live Pricing**: Fetches real-time gas prices from various stations.
- **Vehicle Selection**: Users can select from a list of vehicles, each with their own fuel efficiency.
- **Location Options**: Users can input their location either via browser geolocation or by manually entering an address.
- **Cost Calculations**: The app computes various costs including travel, car fill-up, and combined costs for gas canisters.
- **User-friendly UI**: A clean and simple interface that allows users to quickly obtain the necessary information.

## Technologies Used
- **Flask**: A lightweight WSGI web application framework for Python.
- **Requests**: A simple HTTP library for Python for making requests to external APIs.
- **Geopy**: A Python client for geocoding and distance calculation.
- **HTML/CSS**: For the front-end user interface.

## Installation

To get started, clone the repository and install the necessary dependencies.

```bash
git clone https://github.com/yourusername/find-best-gas-prices.git
cd find-best-gas-prices
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the root directory of the project and add your HERE API key:

```plaintext
HERE_API_KEY=your_here_api_key
```

Make sure to replace `your_here_api_key` with a valid API key from HERE.

## Usage

To run the application, execute the following command:

```bash
python app.py
```

Open your web browser and navigate to `http://127.0.0.1:5000/`.

### Input Requirements

1. **Select Vehicle**: Choose from the available vehicle options.
2. **Choose Location**: 
   - Use your browser's location services.
   - Manually enter an address if preferred.

## Application Flow

1. **Homepage**: Users will be greeted with a form to select their vehicle and input their location.
2. **Processing**: Once the form is submitted, the app fetches live pricing data and calculates travel costs based on the selected vehicle's fuel efficiency.
3. **Results**: The app displays a table with all gas stations, including their prices, distances from the user, and the calculated costs. The best options are highlighted for easy reference.

## Sample Code

Here is a snippet of how the gas price fetching function works:

```python
async def get_gas_price(station_id):
    url = "https://www.gasbuddy.com/graphql"
    # Create headers and the GraphQL query
    ...
    try:
        response = requests.post(
            url,
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=10
        )
        if response.status_code == 200:
            ...
        else:
            return get_dummy_price(station_id)
    except Exception as e:
        return get_dummy_price(station_id)
```

## Contributing

Contributions are welcome! To contribute to this project:

1. Fork the repository.
2. Create a branch for your feature or bug fix.
3. Make your changes and test them.
4. Submit a pull request with a clear description of your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
