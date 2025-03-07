import asyncio
from flask import Flask, render_template_string, request, jsonify
import requests
import os
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from dotenv import load_dotenv

app = Flask(__name__, template_folder="templates")

load_dotenv()


# Vehicle specifications
VEHICLES = {
    "2012_audi_a6": {"mpg": 22, "tank_size": 19.8},
    "2022_bmw_425i": {"mpg": 28, "tank_size": 15.6},
}

# Gas station data
GAS_STATIONS = {
    "WAWA": {"id": "202167", "address": "5600 State Rte 100, Palm Coast, FL 32164", "coords": (29.4763476, -81.2089708)},
    "RaceTrac": {"id": "192722", "address": "5893 100 Blvd E, Palm Coast, FL 32164", "coords": (29.4756055, -81.2258978)},
    "BJ's": {"id": "211766", "address": "5857 State Rte 100, Palm Coast, FL 32164", "coords": (29.4734432, -81.1975036)},
    "Buc-ee's": {"id": "203711", "address": "2330 Gateway N Dr, Daytona Beach, FL 32117", "coords": (29.223603, -81.1034819)},
    "Sam's Club": {"id": "199941", "address": "1460 Cornerstone Blvd, Daytona Beach, FL 32117", "coords": (29.220019, -81.1010839)},
    "Love's US-1": {"id": "46108", "address": "1657 US-1, Ormond Beach, FL 32174", "coords": (29.3394279, -81.1375444)},
    "Bunnel Gas": {"id": "87397", "address": "6700 US-1, Bunnell, FL 32110", "coords": (29.3905715, -81.1898412)},
    "Shell (2557 Moody Blvd)": {"id": "45616", "address": "2557 Moody Blvd, Flagler Beach, FL 32136", "coords": (29.4761307, -81.1516109)},
    "Shell (1900 LPGA)": {"id": "45556", "address": "1900 LPGA Blvd, Daytona Beach, FL 32117", "coords": (29.2272291, -81.0899191)},
    "Shell (5 Old Kings Rd, Palm Coast)": {"id": "46134", "address": "5 Old Kings Rd, Palm Coast, FL 32137", "coords": (29.5164252, -81.2508059)},
    "Buc-ee's St. Augustine": {"id": "203473", "address": "200 World Commerce Pkwy, St. Augustine, FL 32092", "coords": (29.983727, -81.4666229)},
    "Costco St. Augustine": {"id": "207162", "address": "215 World Commerce Pkwy, St. Augustine, FL 32092", "coords": (29.9815517, -81.4660102)},
    "Costco Daytona": {"id": "210257", "address": "150 Pit Rd, Daytona Beach, FL 32114", "coords": (29.1930838, -81.0754555)},
}

HERE_API_KEY = os.getenv("HERE_API_KEY")
GAS_CANS_VOLUME = 7.75

async def get_dummy_price(station_id):
    """Return dummy prices for testing when API fails"""
    dummy_prices = {
        "202167": 10.00,  # WAWA
        "192722": 10.00,  # RaceTrac
        "211766": 10.00,  # BJ's
        "210257": 10.00,  # Costco
        "203711": 10.00,  # Buc-ee's
        "199941": 10.00,   # Sam's Club
        "46108": 10.00,     # Loves US-1
        "87397": 10.00,     # Bunnel Gas
        "45616": 10.00,     # Shell (Moody)
        "45556": 10.00,     # Shell (LPGA)
        "46134": 10.00,     # Shell (old kings)
        "203473": 10.00,    # Buc-ee's St. Aug
        "207162": 10.00     # Costco St. Aug
    }
    return dummy_prices.get(station_id, 10.00)


# Async function for getting gas prices from API or returning dummy prices
async def get_gas_price(station_id):
    url = "https://www.gasbuddy.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Connection": "keep-alive"
    }
    
    query = """
    query GetStation($id: ID!) {
        station(id: $id) {
            prices {
                credit {
                    nickname
                    postedTime
                    price
                }
            }
        }
    }
    """
    
    variables = {"id": station_id}
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            json={"query": query, "variables": variables},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data for station {station_id}: {data}")
            
            try:
                if data and 'data' in data and data['data']['station'] and data['data']['station']['prices']:
                    # The prices are in a different structure than expected
                    prices = data['data']['station']['prices']
                    if isinstance(prices, list) and len(prices) > 0:
                        # Get the first price entry
                        first_price = prices[0]
                        if 'credit' in first_price and 'price' in first_price['credit']:
                            return float(first_price['credit']['price'])
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error parsing price data: {e}")
        
        # If we can't get real prices, return dummy prices
        return get_dummy_price(station_id)
        
    except Exception as e:
        print(f"Error fetching gas price for station {station_id}: {str(e)}")
        return get_dummy_price(station_id)


# Async function for calculating driving distance via HERE API
async def get_driving_distance(origin_coords, dest_coords):
    try:
        url = (
            "https://router.hereapi.com/v8/routes"
            f"?transportMode=car"
            f"&origin={origin_coords[0]},{origin_coords[1]}"
            f"&destination={dest_coords[0]},{dest_coords[1]}"
            f"&units=imperial"
            f"&return=summary"
            f"&apiKey={HERE_API_KEY}"
        )
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Convert meters to miles
            distance_miles = data["routes"][0]["sections"][0]["summary"]["length"] / 1609
            return distance_miles
        else:
            print(f"Error response: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error getting driving distance: {e}")
        return None


def calculate_total_cost(distance, gas_price, mpg):
    # Calculate round-trip fuel cost
    gallons_needed = (distance * 2) / mpg
    return gallons_needed * gas_price


def calculate_combined_fill_cost(gas_price, tank_size, gas_cans_volume):
    return gas_price * (tank_size + gas_cans_volume)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gas Station Cost Calculator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .form-group { margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; font-size: 0.9em; }
        th { background-color: #f5f5f5; }
        .best-total { background-color: #e6ffe6; }
        .best-car { background-color: #fff3e6; }
        .best-cans { background-color: #e6f3ff; }
        .legend { margin-top: 10px; font-size: 0.9em; }
        .legend-item { margin-right: 20px; display: inline-block; padding: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Gas Station Cost Calculator</h1>
        <form method="POST">
    <div class="form-group">
        <label for="vehicle">Select Vehicle:</label>
        <select name="vehicle" id="vehicle" required>
            <option value="audi">2012 Audi A6</option>
            <option value="bmw">2022 BMW 425i</option>
        </select>
    </div>
    <div class="form-group">
	    <label>Choose Location:</label>
	    <div>
	        <input type="radio" id="use_browser_location" name="location_choice" value="browser" checked>
	        <label for="use_browser_location">Use Browser Location</label>
	    </div>
	    <div>
	        <input type="radio" id="use_address_manual" name="location_choice" value="manual">
	        <label for="use_address_manual">Enter Address Manually</label>
	    </div>
	</div>
    <div class="form-group" id="manual_address_input" style="display: none;">
	    <label for="manual_address">Enter Address:</label>
	    <input type="text" id="manual_address" name="manual_address">
	</div>

	<div class="form-group" id="coords_field">
	    <label for="coords">Your Location (Auto-Fill, if browser location is selected):</label>
	    <input type="text" id="coords" name="coords" readonly required>
	</div>
    <button type="submit">Find Best Gas Prices</button>
</form>
        {% if results %}
        <div class="legend">
            <span class="legend-item best-total">Best Combined Total</span>
            <span class="legend-item best-car">Best for Car Only</span>
            <span class="legend-item best-cans">Best for Gas Cans Only</span>
        </div>
        <table>
            <tr>
                <th>Station</th>
                <th>Gas Price</th>
                <th>Distance (miles)</th>
                <th>Travel Cost (round trip)</th>
                <th>Car Fill Cost</th>
                <th>Gas Cans Cost</th>
                <th>Combined Travel and Fill Cost</th>
                <th>Total Cost</th>
            </tr>
            {% for result in results %}
            <tr class="{{ result.highlight_class }}">
                <td>{{ result.station }}</td>
                <td>${{ "%.2f"|format(result.gas_price) }}</td>
                <td>{{ "%.1f"|format(result.distance) }}</td>
                <td>${{ "%.2f"|format(result.travel_cost) }}</td>
                <td>${{ "%.2f"|format(result.car_fill_cost) }}</td>
                <td>${{ "%.2f"|format(result.gas_cans_cost) }}</td>
                <td>${{ "%.2f"|format(result.combined_fill_cost) }}</td>
                <td>${{ "%.2f"|format(result.total_cost) }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
    </div>
    <script>
	    document.addEventListener('DOMContentLoaded', function () {
	        const browserLocationRadio = document.getElementById('use_browser_location');
	        const manualAddressRadio = document.getElementById('use_address_manual');
	        const manualAddressInput = document.getElementById('manual_address_input');
	        const coordsField = document.getElementById('coords_field');
	
	        // Event listeners for toggling
	        browserLocationRadio.addEventListener('change', function () {
	            if (browserLocationRadio.checked) {
	                manualAddressInput.style.display = 'none';
	                coordsField.style.display = 'block';
	                if (navigator.geolocation) {
	                    navigator.geolocation.getCurrentPosition(function (position) {
	                        document.getElementById('coords').value = position.coords.latitude + ',' + position.coords.longitude;
	                    });
	                } else {
	                    alert("Geolocation is not supported by your browser.");
	                }
	            }
	        });
	
	        manualAddressRadio.addEventListener('change', function () {
	            if (manualAddressRadio.checked) {
	                manualAddressInput.style.display = 'block';
	                coordsField.style.display = 'none';
	                document.getElementById('coords').value = ''; // Clear coords to avoid confusion
	            }
	        });
	
	        // Default behavior for browser geolocation
	        if (navigator.geolocation && browserLocationRadio.checked) {
	            navigator.geolocation.getCurrentPosition(function (position) {
	                document.getElementById('coords').value = position.coords.latitude + ',' + position.coords.longitude;
	            });
	        }
	    });
	</script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
async def index():
    results = []
    if request.method == "POST":
        # Get user's choice of location input
        location_choice = request.form.get("location_choice")
        user_coords = None

        if location_choice == "browser":
            # Use browser geolocation
            coords = request.form.get("coords")
            if not coords:
                return "Location data not provided. Please allow location services in your browser."
            user_coords = tuple(map(float, coords.split(",")))

        elif location_choice == "manual":
            # Use manually entered address
            manual_address = request.form.get("manual_address")
            if not manual_address:
                return "Address not provided. Please enter a valid address."

            # Geocode the address to get coordinates
            geolocator = Nominatim(user_agent="GasStationCostCalculator")
            location = geolocator.geocode(manual_address)
            if location:
                user_coords = (location.latitude, location.longitude)
            else:
                return "Could not determine location from the provided address. Please try again."

        # If user_coords is not set at this point, return an error
        if not user_coords:
            return "Could not determine your location."

        # Select vehicle specs
        vehicle = request.form.get("vehicle")
        vehicle_key = "2012_audi_a6" if vehicle == "audi" else "2022_bmw_425i"
        vehicle_specs = VEHICLES[vehicle_key]

        # Gather results asynchronously
        tasks = []
        for station_name, station_data in GAS_STATIONS.items():
            task = asyncio.create_task(
                process_station_data(
                    station_name, station_data, user_coords, vehicle_specs
                )
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Determine the best (cheapest) options
        best_combined = min(results, key=lambda x: x["total_cost"])
        best_car = min(results, key=lambda x: x["car_total"])
        best_cans = min(results, key=lambda x: x["cans_total"])

        # Set highlight class for best options
        for result in results:
            if result == best_combined:
                result["highlight_class"] = "best-total"
            elif result == best_car:
                result["highlight_class"] = "best-car"
            elif result == best_cans:
                result["highlight_class"] = "best-cans"

        # Sort results by total cost
        results.sort(key=lambda x: x["total_cost"])

    return render_template_string(HTML_TEMPLATE, results=results)


async def process_station_data(station_name, station_data, user_coords, vehicle_specs):
    station_coords = station_data["coords"]
    gas_price = await get_gas_price(station_data["id"])
    distance = await get_driving_distance(user_coords, station_coords)
    if distance is None:
        distance = geodesic(user_coords, station_coords).miles  # fallback to geodesic
    travel_cost = calculate_total_cost(distance, gas_price, vehicle_specs["mpg"])
    car_fill_cost = gas_price * vehicle_specs["tank_size"]
    gas_cans_cost = gas_price * GAS_CANS_VOLUME
    combined_fill_cost = calculate_combined_fill_cost(gas_price, vehicle_specs["tank_size"], GAS_CANS_VOLUME)

    return {
        "station": station_name,
        "gas_price": gas_price,
        "distance": distance,
        "travel_cost": travel_cost,
        "car_fill_cost": car_fill_cost,
        "gas_cans_cost": gas_cans_cost,
        "combined_fill_cost": combined_fill_cost,
        "total_cost": travel_cost + combined_fill_cost,
        "car_total": travel_cost + car_fill_cost,
        "cans_total": travel_cost + gas_cans_cost,
        "highlight_class": "",
    }


if __name__ == "__main__":
    app.run(debug=False)