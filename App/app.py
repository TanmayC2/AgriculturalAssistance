# from flask import Flask, render_template, flash, redirect, url_for, session, request, jsonify
# from werkzeug.security import generate_password_hash, check_password_hash
# from flask import Flask, request #Import other required modules
# from functools import wraps
# from dotenv import load_dotenv
# import json
# from Utils.db_connector import Database
# import pandas as pd
# from templates import *
# from Datasets import *
# import numpy as np
# import pickle
# import re
# import joblib
# import matplotlib.pyplot as plt
# from io import BytesIO
# import base64
# import os
# from datetime import datetime
# from sqlalchemy.exc import IntegrityError
# import requests
# import gspread
# from google.oauth2.service_account import Credentials
# from flask import flash
# from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# from flask_restful import Resource, Api
# from functools import wraps
# from Utils.pagination import Pagination
# from Models.usermodel import User
# from Models.predictionmodel import CropPrediction,PricePrediction
# import secrets
# from sklearn.preprocessing import StandardScaler
# from flask_cors import CORS


# # Initialize Flask app
# app = Flask(__name__)
# data = pd.read_csv("agricrop.csv")
# api = Api(app)
# db = Database()
# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '12345678')
# login_manager = LoginManager(app)
# login_manager.login_view = 'login'
# login_manager.login_message_category = 'info'

# # Load models and data
# try:
#     crop_model = pickle.load(open('model.pkl', 'rb'))
#     price_model = joblib.load('RFC_model.pkl')
#     label_encoders = joblib.load('Label_encoder.pkl')

#     #for yield models
#     model = joblib.load('best_xgboost_model.pkl')
#     scaler = joblib.load('scaler.pkl')
#     feature_names = joblib.load('feature_names.pkl')
    
    
#     # Load dataset for price prediction
#     commodity_list = sorted(data['commodity_name'].dropna().unique())
#     state_list = sorted(data['state'].dropna().unique())
#     district_list = sorted(data['district'].dropna().unique())
#     market_list = sorted(data['market'].dropna().unique())
#     data['commodity_name'] = data['commodity_name'].str.lower()
#     data['state'] = data['state'].str.lower()
#     data['district'] = data['district'].str.lower()
#     data['market'] = data['market'].str.lower()
#     # Extract unique values for dropdown menus
#     unique_commodities = sorted(data['commodity_name'].unique())
#     unique_states = sorted(data['state'].unique())
    
#     # Function to get districts based on state
#     def get_districts(state):
#         return sorted(data[data['state'] == state]['district'].unique())
    
#     # Function to get markets based on district
#     def get_markets(district):
#         return sorted(data[data['district'] == district]['market'].unique())
# except FileNotFoundError:
#     data = pd.DataFrame() # create empty dataframe to prevent errors
#     commodity_list = []
#     state_list = []
#     district_list = []
#     market_list = []
#     model=None
#     scaler=None
        
# except Exception as e:
#     print(f"Error loading models or data: {e}")
#     model=None
#     scaler=None

# def json_response(data, status_code=200):
#     if isinstance(data, (list, tuple)):
#         response_data = [item.to_dict() if hasattr(item, 'to_dict') else item for item in data]
#     elif hasattr(data, 'to_dict'):
#         response_data = data.to_dict()
#     else:
#         response_data = data
        
#     return jsonify(response_data), status_code

# # Create
# @app.route('/api/crops', methods=['POST'])
# def create_crop():
#     try:
#         data = request.get_json()
        
#         # Validate required fields
#         if not data or 'name' not in data:
#             return jsonify({'error': 'Name is required'}), 400
            
#         # Create Crop object from request data
#         crop = Crop.from_dict(data)
        
#         # Insert into database
#         query = """
#         INSERT INTO crops (
#             name, nitrogen_requirement, phosphorus_requirement, potassium_requirement,
#             min_temperature, max_temperature, min_ph, max_ph, min_rainfall
#         ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """
#         params = (
#             crop.name, crop.nitrogen_requirement, crop.phosphorus_requirement,
#             crop.potassium_requirement, crop.min_temperature, crop.max_temperature,
#             crop.min_ph, crop.max_ph, crop.min_rainfall
#         )
        
#         crop_id = db.execute_query(query, params)
        
#         if not crop_id:
#             return jsonify({'error': 'Failed to create crop'}), 500
            
#         # Get the created crop
#         query = "SELECT * FROM crops WHERE id = %s"
#         result = db.execute_query(query, (crop_id,), fetch=True)
        
#         if not result:
#             return jsonify({'error': 'Crop not found after creation'}), 404
            
#         created_crop = Crop.from_dict(result[0])
#         return json_response(created_crop, 201)
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# # Read (Single)
# @app.route('/api/crops/<int:crop_id>', methods=['GET'])
# def get_crop(crop_id):
#     try:
#         query = "SELECT * FROM crops WHERE id = %s"
#         result = db.execute_query(query, (crop_id,), fetch=True)
        
#         if not result:
#             return jsonify({'error': 'Crop not found'}), 404
            
#         crop = Crop.from_dict(result[0])
#         return json_response(crop)
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# # Read (All)
# @app.route('/api/crops', methods=['GET'])
# def get_all_crops():
#     try:
#         # Get query parameters for filtering
#         name = request.args.get('name')
        
#         query = "SELECT * FROM crops"
#         params = []
        
#         if name:
#             query += " WHERE name LIKE %s"
#             params.append(f"%{name}%")
            
#         query += " ORDER BY name"
        
#         results = db.execute_query(query, tuple(params), fetch=True)
        
#         if not results:
#             return jsonify([]), 200
            
#         crops = [Crop.from_dict(row) for row in results]
#         return json_response(crops)
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# # Update
# @app.route('/api/crops/<int:crop_id>', methods=['PUT'])
# def update_crop(crop_id):
#     try:
#         data = request.get_json()
        
#         # First check if crop exists
#         check_query = "SELECT id FROM crops WHERE id = %s"
#         exists = db.execute_query(check_query, (crop_id,), fetch=True)
        
#         if not exists:
#             return jsonify({'error': 'Crop not found'}), 404
            
#         # Build update query dynamically based on provided fields
#         update_fields = []
#         params = []
        
#         for field in ['name', 'nitrogen_requirement', 'phosphorus_requirement', 
#                      'potassium_requirement', 'min_temperature', 'max_temperature',
#                      'min_ph', 'max_ph', 'min_rainfall']:
#             if field in data:
#                 update_fields.append(f"{field} = %s")
#                 params.append(data[field])
        
#         if not update_fields:
#             return jsonify({'error': 'No fields to update'}), 400
            
#         params.append(crop_id)
#         query = f"UPDATE crops SET {', '.join(update_fields)} WHERE id = %s"
        
#         db.execute_query(query, tuple(params))
        
#         # Get the updated crop
#         query = "SELECT * FROM crops WHERE id = %s"
#         result = db.execute_query(query, (crop_id,), fetch=True)
        
#         updated_crop = Crop.from_dict(result[0])
#         return json_response(updated_crop)
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# # Delete
# @app.route('/api/crops/<int:crop_id>', methods=['DELETE'])
# def delete_crop(crop_id):
#     try:
#         # First check if crop exists
#         check_query = "SELECT id FROM crops WHERE id = %s"
#         exists = db.execute_query(check_query, (crop_id,), fetch=True)
        
#         if not exists:
#             return jsonify({'error': 'Crop not found'}), 404
            
#         delete_query = "DELETE FROM crops WHERE id = %s"
#         db.execute_query(delete_query, (crop_id,))
        
#         return jsonify({'message': 'Crop deleted successfully'}), 200
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# # Flask-Login setup
# @login_manager.user_loader
# def load_user(user_id):
#     # Use the User.get() method we created for MySQL
#     return User.get(int(user_id),db)
        




# def debug_admin_status():
#     """Debug function to check admin status in database"""
#     try:
#         query = "SELECT id, username, email, is_admin FROM users WHERE email = %s"
#         result = db.execute_query(query, ('admin@example.com',), fetch=True)
#         if result and len(result) > 0:
#             print(f"Admin user details: {result[0]}")
#             return result[0]
#         else:
#             print("Admin user not found in database")
#             return None
#     except Exception as e:
#         print(f"Error checking admin status: {e}")
#         return None




# # 4. Enhanced login route with better debugging
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         print(f"User already authenticated: {current_user.username}, is_admin: {current_user.is_admin}")
#         if current_user.is_admin:
#             print(f"redirected to admin dashboard1")
#             redirect(url_for('admin_dashboard')) 
#         return redirect(url_for('dashboard'))
        
#     if request.method == 'POST':
#         try:
#             email = request.form['email'].strip().lower()
#             password = request.form['password'].strip()
#             print(f"Login attempt for email: {email}")
            
#             if not email or not password:
#                     flash('Both email and password are required', 'danger')
#                     return render_template('login.html')
            
#             user = User.find_by_email(email, db)
            
#             if not user:
#                 print(f"User with email {email} not found")
#                 flash('Login failed. Check your email and password.', 'danger')
#                 return render_template('login.html')
            
#             if check_password_hash(user.password, password):
#                 print(f"{user.password}")
#                 print(f"{password}")
#                 login_user(user)
#                 next_page = request.args.get('next')
#                 flash('Login successful!', 'success')
                
#                 print(f"Login successful, is_admin: {user.is_admin}")
#                 if user.is_admin:
#                     return redirect(next_page) if next_page else redirect(url_for('admin_dashboard')) 
#                 else:
#                     return redirect(next_page) if next_page else redirect(url_for('dashboard'))
#             else:
#                 print(f"{user.password}")
#                 print(f"{password}")
#                 print("Password verification failed")
#                 flash('Login failed. Check your email and password.', 'danger')
                
#         except Exception as e:
#             print(f"Login error: {str(e)}")
#             flash('An error occurred during login. Please try again.', 'danger')
#             return render_template('login.html')
                
#     return render_template('login.html')

# @app.route('/reset_admin', methods=['GET'])
# def reset_admin_password():
#     # Only allow this in development mode
#     if app.debug:
#         try:
#             query = """
#             UPDATE users 
#             SET password = %s 
#             WHERE email = 'admin@example.com'
#             """
#             new_password = generate_password_hash('admin123')
#             db.execute_query(query, (new_password,))
            
#             # Verify the change
#             admin = User.find_by_email('admin@example.com', db)
#             if admin and check_password_hash(admin.password, 'admin123'):
#                 flash('Admin password reset successfully!', 'success')
#             else:
#                 flash('Admin password reset failed!', 'danger')
#         except Exception as e:
#             flash(f'Error: {str(e)}', 'danger')
#         return redirect(url_for('login'))
#     else:
#         flash('This function is only available in debug mode', 'danger')
#         return redirect(url_for('home'))






# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         if current_user.is_admin:
#             print(f"redirected to admin dashboard register")
            
#             redirect(url_for('admin_dashboard')) 
#             # Changed from 'admin' to 'admin_dashboard'
#         return redirect(url_for('dashboard'))

#     if request.method == 'POST':
#         username = request.form['username'].strip()
#         email = request.form['email'].strip().lower()
#         password = request.form['password'].strip()
#         confirm_password = request.form['confirm_password'].strip()
        
#         email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
#         # Password requirements:
#         # - Minimum 8 characters
#         # - At least one uppercase letter
#         # - At least one lowercase letter
#         # - At least one digit
#         # - At least one special character
        
#         password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        
#         if not all([username, email, password, confirm_password]):
#             flash('All fields are required', 'danger')
#             return render_template('register.html')
    
#         if not re.match(password_regex, password):
#             flash('Password must contain: 8+ characters, 1 uppercase, 1 lowercase, 1 digit, and 1 special character', 'danger')
#             return render_template('register.html')
        
#         # Validate password match
#         if password != confirm_password:
#             flash('Passwords do not match.', 'danger')
#             return render_template('register.html')
        
#         if len(username) < 4 or len(username) > 20:
#             flash('Username must be between 4-20 characters', 'danger')
#             return render_template('register.html')
        
#         if len(password) < 8:
#             flash('Password must be at least 8 characters', 'danger')
#             return render_template('register.html')
            
#         # Check for existing user
#         existing_user = User.find_by_username(username, db)
#         existing_email = User.find_by_email(email, db)
        
#         if existing_user:
#             flash('Username is already in use. Please choose a different username.', 'danger')
#         elif existing_email:
#             flash('Email is already registered. Please use a different email.', 'danger')
#         else:
#             # Create new user (non-admin by default)
#             user = User.create(
#                 username=username,
#                 email=email,
#                 password=password,
#                 is_admin=False,  # Explicitly set to False for regular users
#                 db_connection=db
#             )
            
#             if user:
#                 flash('Registration successful! You can now log in.', 'success')
#                 return redirect(url_for('login'))
#             else:
#                 flash('Registration failed. Please try again.', 'danger')
                
#     return render_template('register.html')

# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     flash('You have been logged out.', 'success')
#     return redirect(url_for('home'))

    
# def add_crop_prediction_to_spreadsheet(data):
#     """
#     Adds crop prediction data to a Google Sheets spreadsheet named 'agricros'.
#     Returns:
#         bool: True if data is successfully added, False otherwise.
        
#     """
#     try:
#         # Use credentials from a JSON file (service account key)
#         scope = ['https://www.googleapis.com/auth/spreadsheets']
#         creds = Credentials.from_service_account_file("credentials.json", scopes=scope)  # Fixed variable name 'scope' not 'scopes'
#         client = gspread.authorize(creds)
#         sheet_id = "1zfmgF6t5rePUNkn2W0FC8CiXY7vZQb1f4CZS7WFTsTw"
        
#         # Open the spreadsheet
#         spreadsheet = client.open_by_key(sheet_id)
#         sheet = spreadsheet.croprecomendation  # Access the first sheet, you need to specify which sheet to use
        
#         # Prepare data for insertion
#         row = [data['user_id'], data['nitrogen'], data['phosphorus'], data['potassium'],
#                data['temperature'], data['humidity'], data['ph'], data['rainfall'],
#                data['water_level'], data['predicted_crop']]
        
#         # Insert the row
#         sheet.append_row(row)
        
#         return True
        
#     except Exception as e:
#         flash(f'Error adding data to spreadsheet: {str(e)}', 'danger')
#         return False


# def get_crop_recommendations(crop_name):
#     """Generate recommendations based on the predicted crop."""
#     recommendations = {
#         'rice': [
#             'Maintain standing water of 2-5 cm during vegetative stage',
#             'Apply nitrogen fertilizer in split doses',
#             'Monitor for blast and brown spot diseases',
#             'Ideal temperature: 20-35°C'
#         ],
#         'wheat': [
#             'Sow seeds at 4-5 cm depth',
#             'Irrigate at crown root initiation, tillering, jointing, flowering stages',
#             'Watch for rust and powdery mildew',
#             'Ideal temperature: 15-24°C'
#         ],
#         'maize': [
#             'Ensure proper drainage as maize is sensitive to waterlogging',
#             'Apply fertilizer in bands 5 cm away from plants',
#             'Monitor for fall armyworm and corn borer',
#             'Ideal temperature: 20-30°C'
#         ]
#         # Add more crops and recommendations as needed
#     }
    
#     # Return recommendations for the specific crop or general recommendations
#     return recommendations.get(crop_name.lower(), [
#         'Conduct regular soil testing to maintain optimal nutrient levels',
#         'Implement crop rotation to prevent pest buildup',
#         'Monitor weather forecasts for planning farming operations',
#         'Use organic matter to improve soil structure and water retention'
#     ])

# def kelvin_to_celsius_fahrenheit(kelvin):
#     celsius = kelvin - 273.15
#     fahrenheit = celsius * (9 / 5) + 32
#     return celsius, fahrenheit

# def get_weather(data): #Pass the data directly
#     try:

#         temp_kelvin = data['main']['temp']
#         temp_celsius, temp_fahrenheit = kelvin_to_celsius_fahrenheit(temp_kelvin)

#         feels_like_kelvin = data['main']['feels_like']
#         feels_like_celsius, feels_like_fahrenheit = kelvin_to_celsius_fahrenheit(feels_like_kelvin)

#         weather = {
#             "city": data['name'],
#             "country": data['sys']['country'],
#             "coordinates": {
#                 "latitude": data['coord']['lat'],
#                 "longitude": data['coord']['lon']
#             },
#             "temperature": {
#                 "kelvin": data['main']['temp'],
#                 "celsius": temp_celsius,
#                 "fahrenheit": temp_fahrenheit
#             },
#             "feels_like": {
#                 "kelvin": data['main']['feels_like'],
#                 "celsius": feels_like_celsius,
#                 "fahrenheit": feels_like_fahrenheit
#             },
#             "min_temp": data['main']['temp_min'],
#             "max_temp": data['main']['temp_max'],
#             "humidity": data['main']['humidity'],
#             "pressure": {
#                 "sea_level": data['main'].get('sea_level'),
#                 "ground_level": data['main'].get('grnd_level'),
#                 "pressure": data['main']['pressure']
#             },
#             "visibility": data.get('visibility'),
#             "wind": data.get('wind'),
#             "clouds": data.get('clouds'),
#             "weather_condition": {
#                 "main": data['weather'][0]['main'],
#                 "description": data['weather'][0]['description'],
#                 "icon": data['weather'][0]['icon']
#             },
#             "sunrise": datetime.fromtimestamp(data['sys']['sunrise']).strftime('%Y-%m-%d %H:%M:%S'),
#             "sunset": datetime.fromtimestamp(data['sys']['sunset']).strftime('%Y-%m-%d %H:%M:%S'),
#             "timestamp": datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M:%S'),
#             "datetime_now": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#             "timezone_offset": data.get('timezone'),
#             "response_code": data.get('cod')
#         }

#         return weather
#     except Exception as e:
#         print(f"Error processing weather data: {e}")
#         return None



# # Routes
# @app.route('/')
# def home():
#     return render_template('home.html')

# @app.route('/dashboard')
# @login_required
# def dashboard():
#     crop_predictions = CropPrediction.get_by_user(db,current_user.id, limit=5)
#     price_predictions = PricePrediction.get_by_user(db,current_user.id, limit=5)
    
#     weather_data = get_weather('London')  # You can dynamically set location if needed
    
#     return render_template('dashboard.html', 
#                          crop_predictions=crop_predictions, 
#                          price_predictions=price_predictions,
#                          weather=weather_data)  
    
    
     
# def add_crop_prices_to_spreadsheet(data):
#     try:
#       # Use credentials from a JSON file (service account key)
#         scope = ['https://www.googleapis.com/auth/spreadsheets']
#         creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
#         client = gspread.authorize(creds)
#         sheet_id = "1zfmgF6t5rePUNkn2W0FC8CiXY7vZQb1f4CZS7WFTsTw"
        
#         # Open the spreadsheet
#         spreadsheet = client.open_by_key(sheet_id)
        
#         # Access the specific worksheet - FIXED: use get_worksheet or worksheet method
#         try:
#             # First attempt - try to get by name
#             sheet = spreadsheet.worksheet("cropprices")
#         except Exception:
#             # Second attempt - if named worksheet doesn't exist, use the first sheet
#             sheet = spreadsheet.get_worksheet(1)
        
#         # Format data properly for spreadsheet
#         # Convert user_id and predicted_price to strings to ensure they can be inserted into the spreadsheet
#         row = [str(data['user_id']), 
#                data['commodity'], 
#                data['state'], 
#                data['district'],
#                data['market'], 
#                str(data['predicted_price'])]
        
#         # Insert the row
#         sheet.append_row(row)
        
#         return True
    
#     except Exception as e:
#         flash(f'Error adding data to spreadsheet: {str(e)}', 'danger')
#         return False


# @app.route('/price_prediction', methods=['GET', 'POST'])
# @login_required
# def price_prediction():
#     commodity_name = state = district = market = ""  # Default values for the inputs
#     predicted_price = None
#     error = None
    
#     if request.method == 'POST':
#         if price_model is None or label_encoders is None or data.empty:
#             flash('Price prediction model or data is not available', 'danger')
#             return render_template('prediction.html',
#                                  commodity_list=commodity_list,
#                                  state_list=state_list,
#                                  district_list=district_list,
#                                  market_list=market_list)
#     try:       
#         commodity_name = request.form['commodity_name'].strip().lower()
#         state = request.form['state'].strip().lower()
#         district = request.form['district'].strip().lower()
#         market = request.form['market'].strip().lower()
        
    
#         encoded_commodity = label_encoders['commodity_name'].transform([commodity_name])[0]
#         encoded_state = label_encoders['state'].transform([state])[0]
#         encoded_district = label_encoders['district'].transform([district])[0]
#         encoded_market = label_encoders['market'].transform([market])[0]
            
#         matching_rows = data[
#             (data['commodity_name'] == commodity_name) &
#             (data['state'] == state) &
#             (data['district'] == district) &
#             (data['market'] == market)
#         ]
            
#         if not matching_rows.empty:
#             avg_min_price = matching_rows['min_price'].mean()
#             avg_max_price = matching_rows['max_price'].mean()
#         else:
#             avg_min_price = data['min_price'].mean()
#             avg_max_price = data['max_price'].mean()
            
#         input_data = pd.DataFrame([[encoded_commodity, encoded_state, encoded_district, encoded_market, avg_min_price, avg_max_price]],
#         columns=['commodity_name', 'state', 'district', 'market', 'min_price', 'max_price'])
#         predicted_price = price_model.predict(input_data)[0]
            
#         # Add data to spreadsheet only if prediction was successful
#         if predicted_price is not None:
#             spreadsheet_data = {
#                 'user_id': current_user.id,
#                 'commodity': commodity_name,
#                 'state': state,
#                 'district': district,
#                 'market': market,
#                 'predicted_price': predicted_price
#         }
#         success = add_crop_prices_to_spreadsheet(spreadsheet_data)
#         try:
#             PricePrediction.create(
#                 db=db,
#                 user_id=current_user.id,
#                 commodity=commodity_name,
#                 state=state,
#                 district=district,
#                 market=market,
#                 predicted_price=predicted_price
#             )
#         flash("Price prediction saved successfully!", "success")
#         except Exception as db_error:
#             error = f"Prediction successful but failed to save to database: {str(db_error)}"
#             flash(error, "warning")
                    
#             if not success:
#                 flash("Prediction successful but could not log data to spreadsheet.", "warning")
        
#         except KeyError as e:
#             error = f"Invalid input. Input value not found in training data: {str(e)}"
        
#         except Exception as e:
#             error = f"An error occurred: {str(e)}"
            
#     return render_template('prediction.html',
#                          predicted_price=f"{predicted_price:.2f}" if predicted_price else None,
#                          error=error,
#                          commodity_name=commodity_name,
#                          state=state,
#                          district=district,
#                          market=market,
#                          commodity_list=commodity_list,
#                          state_list=state_list,
#                          district_list=district_list,
#                          market_list=market_list)
    


    
# def add_crop_prediction_to_spreadsheet(data):
#     """
#     Adds crop prediction data to a Google Sheets spreadsheet named 'agricros'.
#     Returns:
#         bool: True if data is successfully added, False otherwise.
        
#     """
#     try:
#         # Use credentials from a JSON file (service account key)
#         scope = ['https://www.googleapis.com/auth/spreadsheets']
#         creds = Credentials.from_service_account_file("credentials.json", scopes=scope)  # Fixed variable name 'scope' not 'scopes'
#         client = gspread.authorize(creds)
#         sheet_id = "1zfmgF6t5rePUNkn2W0FC8CiXY7vZQb1f4CZS7WFTsTw"
        
#         # Open the spreadsheet
#         spreadsheet = client.open_by_key(sheet_id)
        
#         try:
#             # First attempt - try to get by name
#             sheet = spreadsheet.worksheet("croprecomendation")
#         except Exception:
#             # Second attempt - if named worksheet doesn't exist, use the first sheet
#             sheet = spreadsheet.get_worksheet(0)
        
#         # Prepare data for insertion
#         row = [data['user_id'], data['nitrogen'], data['phosphorus'], data['potassium'],
#                data['temperature'], data['humidity'], data['ph'], data['rainfall'],
#                data['water_level'], data['predicted_crop']]
        
#         # Insert the row
#         sheet.append_row(row)
        
#         return True
        
#     except Exception as e:
#         flash(f'Error adding data to spreadsheet: {str(e)}', 'danger')
#         return False

















# @app.route('/predict', methods=['GET', 'POST'])
# @login_required
# def crop_prediction():
#     if request.method == 'POST':
#         int_features = [float(x) for x in request.form.values()]
#         final_features = [np.array(int_features)]
#         proba = crop_model.predict_proba(final_features)[0]
#         crop_probabilities = {crop: round(probability, 2) for crop, probability in zip(crop_model.classes_, proba)}

#         # Get the top three crop probabilities
#         top_three_crops = sorted(crop_probabilities.items(), key=lambda x: x[1], reverse=True)[:3]

#         # Get the predicted crop
#         predicted_crop = max(crop_probabilities, key=crop_probabilities.get)

#         # Create a horizontal bar chart of the top three crop probabilities
#         fig, ax = plt.subplots()
#         crop_names = [crop[0] for crop in top_three_crops]
#         crop_probabilities = [crop[1] for crop in top_three_crops]
#         ax.barh(crop_names, crop_probabilities)
#         ax.set_xlabel('Probability')
#         ax.set_ylabel('Crop')
#         ax.set_title('Top Three Crop Probabilities')

#         # Convert the bar chart to a base64-encoded string for display in the template
#         buffer = BytesIO()
#         plt.savefig(buffer, format='png')
#         buffer.seek(0)
#         image_png = buffer.getvalue()
#         buffer.close()
#         graph = base64.b64encode(image_png).decode()
        
#         prediction_id = CropPrediction.create(
#             db,
#             user_id=current_user.id,
#             nitrogen=int_features[0],
#             phosphorus=int_features[1],
#             potassium=int_features[2],
#             temperature=int_features[3],
#             humidity=int_features[4],
#             ph=int_features[5],
#             rainfall=int_features[6],
#             predicted_crop=predicted_crop
#         )
         
#         spreadsheet_data = {
#                 'user_id': current_user.id,
#                 'nitrogen': int_features[0],
#                 'phosphorus': int_features[1],
#                 'potassium': int_features[2],
#                 'temperature': int_features[3],
#                 'humidity': int_features[4],
#                 'ph': int_features[5],
#                 'rainfall': int_features[6],
#                 'water_level': int_features[7],
#                 'predicted_crop': predicted_crop
#             }
#         add_crop_prediction_to_spreadsheet(spreadsheet_data)
#             # db.session.add(prediction)
#             # db.session.commit()
        
#         return render_template('result.html', 
#                             int_features=int_features, 
#                             top_three_crops=top_three_crops, 
#                             prediction_text=predicted_crop, 
#                             graph=graph)
#     else:   
#         return render_template('predict.html')

# @app.route('/predict_yield', methods=['GET','POST']) # Changed route name to predict_yield
# def predict_yield():

#     if request.method == 'POST':
#         try:
#             # Get form data
#             form_data = request.form.to_dict()
            
            
#              # Define the expected numeric features (based on your data structure)
#             numeric_features = [
#                 'temperature', 'Soil_Moisture', 
#                 'Area_in_hectares', 'Production_in_tons', 'N', 'P', 'K', 
#                 'pH', 'rainfall'
#             ]
                       
#             # Create a dictionary to store processed data
#             processed_data = {}
            
#              # Process numeric features
#             for feature in numeric_features:
#                 if feature in form_data:
#                     try:
#                         # Convert to float, handle empty strings
#                         value = form_data[feature]
#                         if value == '' or value is None:
#                             processed_data[feature] = 0.0  # Default value
#                         else:
#                             processed_data[feature] = float(value)
#                     except (ValueError, TypeError):
#                         processed_data[feature] = 0.0
#                         print(f"Could not convert {feature}: {form_data[feature]} to float, using 0.0")
#                 else:
#                     processed_data[feature] = 0.0
#                     print(f"Feature {feature} not found in form data, using default value 0.0")
         
            
#             # Create DataFrame with processed data
#             # Only use features that were used during model training
#             model_features = []
            
#             # Check which features the model expects
#             if hasattr(model, 'feature_names_in_'):
#                 model_features = model.feature_names_in_
#             elif 'feature_names' in globals():
#                 model_features = feature_names
#             else:
#                 # Fallback to numeric features only
#                 model_features = numeric_features
            
            
#            # Create input data with only the features the model expects
#             input_data = {}
#             for feature in model_features:
#                 if feature in processed_data:
#                     input_data[feature] = processed_data[feature]
#                 else:
#                     input_data[feature] = 0.0  # Default value for missing features 
           
#            # Convert to DataFrame
#             input_df = pd.DataFrame([input_data])
            
#             print(f"Input DataFrame shape: {input_df.shape}")
#             print(f"Input DataFrame columns: {list(input_df.columns)}") 
            
#             # Scale features if scaler exists
#             if scaler is not None:
#                 try:
#                     # Ensure the input has all features the scaler expects
#                     scaler_features = scaler.feature_names_in_
                    
#                     # Reorder columns to match scaler's expected order
#                     input_for_scaling = pd.DataFrame()
#                     for feature in scaler_features:
#                         if feature in input_df.columns:
#                             input_for_scaling[feature] = input_df[feature]
#                         else:
#                             input_for_scaling[feature] = 0.0
                    
#                     scaled_data = scaler.transform(input_for_scaling)
#                     print("Data scaled successfully")
#                 except Exception as e:
#                     print(f"Error scaling data: {str(e)}")
#                     scaled_data = input_df.values
#             else:
#                 scaled_data = input_df.values
#                 print("No scaler found, using raw data")
            
            
#             if(model is None):
#                 print("Model not loaded")
            
#             else:              
#                 # Make prediction
#                 prediction = model.predict(scaled_data)[0]
#                 print(f"Prediction made: {prediction}")
                
#                 # Format prediction
#                 prediction_text = f"Predicted Yield: {prediction:.2f} tons/hectare"
            
#             # Additional insights
#             if prediction < 1.0:
#                 insight = "Low yield expected. Consider improving soil nutrients or irrigation."
#             elif prediction < 3.0:
#                 insight = "Moderate yield expected. Good farming practices in place."
#             elif prediction < 5.0:
#                 insight = "Good yield expected. Excellent farming conditions."
#             else:
#                 insight = "Exceptional yield expected. Optimal farming conditions!"
            
#             return render_template('predict_yield.html',
#                                  prediction=prediction_text,
#                                  insight=insight,
#                                  form_data=form_data,
#                                  success=True)
                                 
#         except Exception as e:
#             print(f"Error in prediction: {str(e)}")
#             return render_template('predict_yield.html',
#                                  prediction=f"Error occurred: {str(e)}",
#                                  insight="Please check your input values and try again.",
#                                  form_data=request.form.to_dict() if request.form else {},
#                                  success=False)
    
#     # GET request - show the form
#     return render_template('predict_yield.html')

# @app.route('/profile')
# @login_required
# def profile():
#     return render_template('profile.html', user=current_user)

# @app.route('/history')
# @login_required
# def prediction_history():
#     crop_predictions = CropPrediction.get_by_user(db,current_user.id, limit=5)
#     price_predictions = PricePrediction.get_by_user(db,current_user.id, limit=5)
    
#     page = request.args.get('page', 1, type=int)
#     per_page = request.args.get('per_page', 10, type=int)
#     search_term = request.args.get('search', '').lower()
    
#     # Base query
#     query = "SELECT * FROM crop_predictions WHERE user_id = %s"
#     params = [current_user.id]
    
#     # Add search filter if provided
#     if search_term:
#         query += " AND predicted_crop LIKE %s"
#         params.append(f"%{search_term}%")
    
#     # Add pagination
#     query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
#     offset = (page - 1) * per_page
#     params.extend([per_page, offset])
    
#     # Get paginated results
#     predictions = db.execute_query(query, params, fetch=True)
    
#     # Get total count for pagination
#     count_query = "SELECT COUNT(*) as total FROM crop_predictions WHERE user_id = %s"
#     count_params = [current_user.id]
#     if search_term:
#         count_query += " AND predicted_crop LIKE %s"
#         count_params.append(f"%{search_term}%")
    
#     total_result = db.execute_query(count_query, count_params, fetch=True)
#     total = total_result[0]['total'] if total_result else 0
    
#     # Create pagination object
#     predictions = Pagination(page=page, per_page=per_page, total=total, items=predictions)
    
#     return render_template('history.html', 
#                          predictions=predictions,
#                          crop_predictions=crop_predictions, 
#                          price_predictions=price_predictions,
#                          per_page=per_page)
    
# @app.route('/pricehistory')
# @login_required
# def prediction_history_price():
#     # Get recent predictions for sidebar (consistent with crop history)
#     crop_predictions = CropPrediction.get_by_user(db, current_user.id, limit=5)
#     price_predictions = PricePrediction.get_by_user(db, current_user.id, limit=5)

#     # Pagination parameters (same as crop history)
#     page = request.args.get('page', 1, type=int)
#     per_page = request.args.get('per_page', 10, type=int)
#     search_term = request.args.get('search', '').lower()

#     # Base query for price predictions (similar structure to crop history)
#     query = "SELECT * FROM price_predictions WHERE user_id = %s"
#     params = [current_user.id]

#     # Add search filter if provided (expanded to include more relevant fields)
#     if search_term:
#         query += " AND commodity LIKE %s"
#         params.append(f"%{search_term}%")

#     # Add pagination (same as crop history)
#     query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
#     offset = (page - 1) * per_page
#     params.extend([per_page, offset])

#     # Get paginated results (same as crop history)
#     price_results = db.execute_query(query, params, fetch=True)

#     # Get total count for pagination (same structure as crop history)
#     count_query = "SELECT COUNT(*) as total FROM price_predictions WHERE user_id = %s"
#     # print(count_query)
#     count_params = [current_user.id]
#     if search_term:
#         count_query += " AND (predicted_crop LIKE %s OR market LIKE %s OR predicted_price::text LIKE %s)"
#         count_params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

#     total_result = db.execute_query(count_query, count_params, fetch=True)
#     total = total_result[0]['total'] if total_result else 0

#     # Create pagination object (same as crop history)
#     predictions = Pagination(
#         page=page,
#         per_page=per_page,
#         total=total,
#         items=price_results
#     )

#     return render_template('price_history.html',
#                          predictions=predictions, 
#                          crop_predictions=crop_predictions,
#                          price_predictions=price_predictions,
#                          per_page=per_page,
#                          is_price_history=True)  # Additional flag for template
   
# # Route to view yield prediction history
# @app.route('/yield_history')
# @login_required
# def yield_history():
#     """Route handler for viewing user's yield prediction history"""
#     page = request.args.get('page', 1, type=int)
#     per_page = request.args.get('per_page', 10, type=int)
#     search_term = request.args.get('search', '').lower()
    
#     # Base query
#     query = "SELECT * FROM yield_predictions WHERE user_id = %s"
#     params = [current_user.id]
    
#     # Add search filter if provided
#     if search_term:
#         query += " AND (crop LIKE %s OR state LIKE %s)"
#         params.extend([f"%{search_term}%", f"%{search_term}%"])
    
#     # Add pagination
#     query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
#     offset = (page - 1) * per_page
#     params.extend([per_page, offset])
    
#     # Get paginated results
#     predictions = db.execute_query(query, params, fetch=True)
    
#     # Get total count for pagination
#     count_query = "SELECT COUNT(*) as total FROM yield_predictions WHERE user_id = %s"
#     count_params = [current_user.id]
#     if search_term:
#         count_query += " AND (crop LIKE %s OR state LIKE %s)"
#         count_params.extend([f"%{search_term}%", f"%{search_term}%"])
    
#     total_result = db.execute_query(count_query, count_params, fetch=True)
#     total = total_result[0]['total'] if total_result else 0
    
#     # Create pagination object
#     paginated_predictions = Pagination(
#         page=page, 
#         per_page=per_page, 
#         total=total, 
#         items=predictions
#     )
    
#     return render_template(
#         'yield_history.html',
#         predictions=paginated_predictions,
#         per_page=per_page
#     )

# @app.route('/admin')
# @login_required 
# def admin_dashboard():
#     user_count = db.execute_query("SELECT COUNT(*) as count FROM users", fetch=True)[0]['count']
#     crop_prediction_count = db.execute_query("SELECT COUNT(*) as count FROM crop_predictions", fetch=True)[0]['count']
#     price_prediction_count = db.execute_query("SELECT COUNT(*) as count FROM price_predictions", fetch=True)[0]['count']
    
#     # Get recent users
#     recent_users_result = db.execute_query(
#         "SELECT * FROM users ORDER BY created_at DESC LIMIT 5", 
#         fetch=True
#     )
    
#     recent_users = [
#         {
#             'id': user['id'],
#             'username': user['username'],
#             'email': user['email'],
#             'created_at': user['created_at'],
#             'is_admin': user['is_admin']  # Add this to show admin status
#         } for user in recent_users_result
#     ] if recent_users_result else []
    
#     return render_template('admin_page.html',
#                           user_count=user_count,
#                           crop_prediction_count=crop_prediction_count,
#                           price_prediction_count=price_prediction_count,
#                           recent_users=recent_users)

# #Error handlers
# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html'), 404

# @app.errorhandler(500)
# def internal_server_error(e):
#     return render_template('500.html'), 500


# def create_tables():
#     """Create database tables if they don't exist"""
#     try:
#         connection = db.connect()
#         cursor = connection.cursor()
        
#         # Inside create_tables()
#         cursor.execute("""
#         CREATE TABLE IF NOT EXISTS users (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             username VARCHAR(20) UNIQUE NOT NULL,
#             email VARCHAR(120) UNIQUE NOT NULL,
#             password VARCHAR(255) NOT NULL,
#             is_admin BOOLEAN DEFAULT FALSE,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# )
# """)
        
#         # Create crop_predictions table
#         cursor.execute("""
#         CREATE TABLE IF NOT EXISTS crop_predictions (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             user_id INT NOT NULL,
#             nitrogen FLOAT NOT NULL,
#             phosphorus FLOAT NOT NULL,
#             potassium FLOAT NOT NULL,
#             temperature FLOAT NOT NULL,
#             humidity FLOAT NOT NULL,
#             ph FLOAT NOT NULL,
#             rainfall FLOAT NOT NULL,
#             predicted_crop VARCHAR(50) NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (user_id) REFERENCES users(id)
#         )
#         """)
        
#         # Create price_predictions table
#         cursor.execute("""
#         CREATE TABLE IF NOT EXISTS price_predictions (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             user_id INT NOT NULL,
#             commodity VARCHAR(100) NOT NULL,
#             state VARCHAR(100) NOT NULL,
#             district VARCHAR(100) NOT NULL,
#             market VARCHAR(100) NOT NULL,
#             predicted_price FLOAT NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (user_id) REFERENCES users(id)
#         )
#         """)
        
#         connection.commit()
#     except Error as e:
#         print(f"Error creating tables: {e}")
#         if connection:
#             connection.rollback()
#     finally:
#         if connection and connection.is_connected():
#             cursor.close()
#             connection.close()

# def create_admin_user():
#     """Create admin user if not exists"""
#     try:
#         admin = User.find_by_email('admin@example.com', db)
#         if not admin:
#             # Use the correct method that will hash the password internally
#             admin_created = User.create(
#                 username='admin',
#                 email='admin@example.com',
#                 password='admin123',  # This will be hashed in the User.create method
#                 is_admin=True,
#                 db_connection=db
#             )
#             if admin_created:
#                 print("Admin user created successfully")
#                 return True
#             else:
#                 print("Failed to create admin user")
#                 return False
#         else:
#             print("Admin user already exists")
#             return True
#     except Exception as e:
#         print(f"Error creating admin user: {e}")
#         return False

# def debug_admin_status():
#     """Debug function to check admin status in database"""
#     try:
#         query = "SELECT id, username, email, is_admin FROM users WHERE email = %s"
#         result = db.execute_query(query, ('admin@example.com',), fetch=True)
#         if result and len(result) > 0:
#             print(f"Admin user details: {result[0]}")
#             return result[0]
#         else:
#             print("Admin user not found in database")
#             return None
#     except Exception as e:
#         print(f"Error checking admin status: {e}")
#         return None
    


# def admin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not current_user.is_authenticated or current_user.id != 1:  # Assuming user with id=1 is admin
#             flash('You need administrator privileges to access this page.', 'danger')
#             print(f"User {current_user.id} is_admin: {current_user.is_admin}")
#             return redirect(url_for('home'))
#         return f(*args, **kwargs)
#     return decorated_function


# # Fix in the admin creation at the bottom of the file:
# if __name__ == '__main__':
#     # Create tables if they don't exist
#     CORS(app)
#     create_tables()  
    
    
#     # Create admin user if needed
#     create_admin_user()
    
#     # Debug admin status
#     if app.debug:
#         debug_admin_status()

#     app.run(debug=True)
    
from flask import Flask, render_template, flash, redirect, url_for, session, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv
import json
from Utils.db_connector import Database
import pandas as pd
from templates import *
from Datasets import *
import numpy as np
import pickle
import re
import joblib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import requests
import gspread
from google.oauth2.service_account import Credentials
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_restful import Resource, Api
from Utils.pagination import Pagination
from Models.usermodel import User
from Models.predictionmodel import CropPrediction, PricePrediction
import secrets
from sklearn.preprocessing import StandardScaler
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
api = Api(app)
db = Database()
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Global variables for models and data
crop_model = None
price_model = None
label_encoders = None
yield_model = None
scaler = None
feature_names = None
data = pd.DataFrame()
commodity_list = []
state_list = []
district_list = []
market_list = []
unique_commodities = []
unique_states = []

def load_models_and_data():
    """Load all models and data with proper error handling"""
    global crop_model, price_model, label_encoders, yield_model, scaler, feature_names
    global data, commodity_list, state_list, district_list, market_list, unique_commodities, unique_states
    
    try:
        print("Loading models and data...")
        
        # Load crop prediction model
        try:
            if os.path.exists('model.pkl'):
                crop_model = pickle.load(open('model.pkl', 'rb'))
                print("✓ Crop model loaded successfully")
            else:
                print("⚠ model.pkl not found")
        except Exception as e:
            print(f"✗ Error loading crop model: {e}")
            crop_model = None

        # Load price prediction model and encoders
        try:
            if os.path.exists('RFC_model.pkl'):
                price_model = joblib.load('RFC_model.pkl')
                print("✓ Price model loaded successfully")
            else:
                print("⚠ RFC_model.pkl not found")
                
            if os.path.exists('Label_encoder.pkl'):
                label_encoders = joblib.load('Label_encoder.pkl')
                print("✓ Label encoders loaded successfully")
            else:
                print("⚠ Label_encoder.pkl not found")
        except Exception as e:
            print(f"✗ Error loading price model/encoders: {e}")
            price_model = None
            label_encoders = None

        # Load yield prediction model components
        try:
            if os.path.exists('best_xgboost_model.pkl'):
                yield_model = joblib.load('best_xgboost_model.pkl')
                print("✓ Yield model loaded successfully")
            else:
                print("⚠ best_xgboost_model.pkl not found")
                
            if os.path.exists('scaler.pkl'):
                scaler = joblib.load('scaler.pkl')
                print("✓ Scaler loaded successfully")
            else:
                print("⚠ scaler.pkl not found")
                
            if os.path.exists('feature_names.pkl'):
                feature_names = joblib.load('feature_names.pkl')
                print("✓ Feature names loaded successfully")
            else:
                print("⚠ feature_names.pkl not found")
        except Exception as e:
            print(f"✗ Error loading yield model components: {e}")
            yield_model = None
            scaler = None
            feature_names = None

        # Load dataset for price prediction
        try:
            if os.path.exists('agricrop.csv'):
                data = pd.read_csv("agricrop.csv")
                print("✓ Dataset loaded successfully")
                
                # Process data for dropdowns
                data['commodity_name'] = data['commodity_name'].str.lower()
                data['state'] = data['state'].str.lower()
                data['district'] = data['district'].str.lower()
                data['market'] = data['market'].str.lower()
                
                # Extract unique values for dropdown menus
                commodity_list = sorted(data['commodity_name'].dropna().unique())
                state_list = sorted(data['state'].dropna().unique())
                district_list = sorted(data['district'].dropna().unique())
                market_list = sorted(data['market'].dropna().unique())
                unique_commodities = sorted(data['commodity_name'].unique())
                unique_states = sorted(data['state'].unique())
                
                print(f"✓ Processed {len(data)} records for price prediction")
            else:
                print("⚠ agricrop.csv not found")
                data = pd.DataFrame()
        except Exception as e:
            print(f"✗ Error loading dataset: {e}")
            data = pd.DataFrame()
            
    except Exception as e:
        print(f"✗ Critical error in load_models_and_data: {e}")

# Load models on startup
load_models_and_data()

# Helper functions
def get_districts(state):
    """Get districts based on state"""
    if not data.empty:
        return sorted(data[data['state'] == state]['district'].unique())
    return []

def get_markets(district):
    """Get markets based on district"""
    if not data.empty:
        return sorted(data[data['district'] == district]['market'].unique())
    return []

def json_response(data, status_code=200):
    """Helper function to format JSON responses"""
    if isinstance(data, (list, tuple)):
        response_data = [item.to_dict() if hasattr(item, 'to_dict') else item for item in data]
    elif hasattr(data, 'to_dict'):
        response_data = data.to_dict()
    else:
        response_data = data
    return jsonify(response_data), status_code

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id), db)

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    crop_predictions = CropPrediction.get_by_user(db, current_user.id, limit=5)
    price_predictions = PricePrediction.get_by_user(db, current_user.id, limit=5)
    return render_template('dashboard.html', 
                         crop_predictions=crop_predictions, 
                         price_predictions=price_predictions)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        try:
            email = request.form['email'].strip().lower()
            password = request.form['password'].strip()
            
            if not email or not password:
                flash('Both email and password are required', 'danger')
                return render_template('login.html')
            
            user = User.find_by_email(email, db)
            
            if not user:
                flash('Login failed. Check your email and password.', 'danger')
                return render_template('login.html')
            
            if check_password_hash(user.password, password):
                login_user(user)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                
                if user.is_admin:
                    return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
                else:
                    return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Login failed. Check your email and password.', 'danger')
                
        except Exception as e:
            flash('An error occurred during login. Please try again.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()
        
        # Validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if not re.match(email_regex, email):
            flash('Please enter a valid email address', 'danger')
            return render_template('register.html')
    
        if not re.match(password_regex, password):
            flash('Password must contain: 8+ characters, 1 uppercase, 1 lowercase, 1 digit, and 1 special character', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        if len(username) < 4 or len(username) > 20:
            flash('Username must be between 4-20 characters', 'danger')
            return render_template('register.html')
            
        # Check for existing user
        existing_user = User.find_by_username(username, db)
        existing_email = User.find_by_email(email, db)
        
        if existing_user:
            flash('Username is already in use. Please choose a different username.', 'danger')
        elif existing_email:
            flash('Email is already registered. Please use a different email.', 'danger')
        else:
            # Create new user
            user = User.create(
                username=username,
                email=email,
                password=password,
                is_admin=False,
                db_connection=db
            )
            
            if user:
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'danger')
                
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))



def kelvin_to_celsius_fahrenheit(kelvin):
    celsius = kelvin - 273.15
    fahrenheit = celsius * (9 / 5) + 32
    return celsius, fahrenheit

def get_weather(data): #Pass the data directly
    try:

        temp_kelvin = data['main']['temp']
        temp_celsius, temp_fahrenheit = kelvin_to_celsius_fahrenheit(temp_kelvin)

        feels_like_kelvin = data['main']['feels_like']
        feels_like_celsius, feels_like_fahrenheit = kelvin_to_celsius_fahrenheit(feels_like_kelvin)

        weather = {
            "city": data['name'],
            "country": data['sys']['country'],
            "coordinates": {
                "latitude": data['coord']['lat'],
                "longitude": data['coord']['lon']
            },
            "temperature": {
                "kelvin": data['main']['temp'],
                "celsius": temp_celsius,
                "fahrenheit": temp_fahrenheit
            },
            "feels_like": {
                "kelvin": data['main']['feels_like'],
                "celsius": feels_like_celsius,
                "fahrenheit": feels_like_fahrenheit
            },
            "min_temp": data['main']['temp_min'],
            "max_temp": data['main']['temp_max'],
            "humidity": data['main']['humidity'],
            "pressure": {
                "sea_level": data['main'].get('sea_level'),
                "ground_level": data['main'].get('grnd_level'),
                "pressure": data['main']['pressure']
            },
            "visibility": data.get('visibility'),
            "wind": data.get('wind'),
            "clouds": data.get('clouds'),
            "weather_condition": {
                "main": data['weather'][0]['main'],
                "description": data['weather'][0]['description'],
                "icon": data['weather'][0]['icon']
            },
            "sunrise": datetime.fromtimestamp(data['sys']['sunrise']).strftime('%Y-%m-%d %H:%M:%S'),
            "sunset": datetime.fromtimestamp(data['sys']['sunset']).strftime('%Y-%m-%d %H:%M:%S'),
            "timestamp": datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M:%S'),
            "datetime_now": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "timezone_offset": data.get('timezone'),
            "response_code": data.get('cod')
        }

        return weather
    except Exception as e:
        print(f"Error processing weather data: {e}")
        return None







def get_crop_recommendations(crop_name):
    """Generate recommendations based on the predicted crop."""
    recommendations = {
        'rice': [
            'Maintain standing water of 2-5 cm during vegetative stage',
            'Apply nitrogen fertilizer in split doses',
            'Monitor for blast and brown spot diseases',
            'Ideal temperature: 20-35°C'
        ],
        'wheat': [
            'Sow seeds at 4-5 cm depth',
            'Irrigate at crown root initiation, tillering, jointing, flowering stages',
            'Watch for rust and powdery mildew',
            'Ideal temperature: 15-24°C'
        ],
        'maize': [
            'Ensure proper drainage as maize is sensitive to waterlogging',
            'Apply fertilizer in bands 5 cm away from plants',
            'Monitor for fall armyworm and corn borer',
            'Ideal temperature: 20-30°C'
        ]
        # Add more crops and recommendations as needed
    }
    
    # Return recommendations for the specific crop or general recommendations
    return recommendations.get(crop_name.lower(), [
        'Conduct regular soil testing to maintain optimal nutrient levels',
        'Implement crop rotation to prevent pest buildup',
        'Monitor weather forecasts for planning farming operations',
        'Use organic matter to improve soil structure and water retention'
    ])



def add_crop_prediction_to_spreadsheet(data):
    try:
        # Use credentials from a JSON file (service account key)
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)  # Fixed variable name 'scope' not 'scopes'
        client = gspread.authorize(creds)
        sheet_id = "1zfmgF6t5rePUNkn2W0FC8CiXY7vZQb1f4CZS7WFTsTw"
        
        # Open the spreadsheet
        spreadsheet = client.open_by_key(sheet_id)
        
        try:
            # First attempt - try to get by name
            sheet = spreadsheet.worksheet("croprecomendation")
        except Exception:
            # Second attempt - if named worksheet doesn't exist, use the first sheet
            sheet = spreadsheet.get_worksheet(0)
        
        # Prepare data for insertion
        row = [data['user_id'], data['nitrogen'], data['phosphorus'], data['potassium'],
               data['temperature'], data['humidity'], data['ph'], data['rainfall'],
               data['water_level'], data['predicted_crop']]
        
        # Insert the row
        sheet.append_row(row)
        
        return True
        
    except Exception as e:
        flash(f'Error adding data to spreadsheet: {str(e)}', 'danger')
        return False


@app.route('/predict', methods=['GET', 'POST'])
@login_required
def crop_prediction():
    if request.method == 'POST':
        if crop_model is None:
            flash('Crop prediction model is not available', 'danger')
            return render_template('predict.html')
            
        try:
            int_features = [float(x) for x in request.form.values()]
            final_features = [np.array(int_features)]
            proba = crop_model.predict_proba(final_features)[0]
            crop_probabilities = {crop: round(probability, 2) for crop, probability in zip(crop_model.classes_, proba)}

            # Get the top three crop probabilities
            top_three_crops = sorted(crop_probabilities.items(), key=lambda x: x[1], reverse=True)[:3]
            predicted_crop = max(crop_probabilities, key=crop_probabilities.get)

            # Create visualization
            fig, ax = plt.subplots()
            crop_names = [crop[0] for crop in top_three_crops]
            crop_probs = [crop[1] for crop in top_three_crops]
            ax.barh(crop_names, crop_probs)
            ax.set_xlabel('Probability')
            ax.set_ylabel('Crop')
            ax.set_title('Top Three Crop Probabilities')

            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            plt.close()  # Important: close the figure to free memory
            graph = base64.b64encode(image_png).decode()
            
            spreadsheet_data = {
                'user_id': current_user.id,
                'nitrogen': int_features[0],
                'phosphorus': int_features[1],
                'potassium': int_features[2],
                'temperature': int_features[3],
                'humidity': int_features[4],
                'ph': int_features[5],
                'rainfall': int_features[6],
                'water_level': int_features[7],
                'predicted_crop': predicted_crop
            }
            add_crop_prediction_to_spreadsheet(spreadsheet_data)
            
            # Save prediction
            CropPrediction.create(
                db,
                user_id=current_user.id,
                nitrogen=int_features[0],
                phosphorus=int_features[1],
                potassium=int_features[2],
                temperature=int_features[3],
                humidity=int_features[4],
                ph=int_features[5],
                rainfall=int_features[6],
                predicted_crop=predicted_crop
            )

            
            return render_template('result.html', 
                                int_features=int_features, 
                                top_three_crops=top_three_crops, 
                                prediction_text=predicted_crop, 
                                graph=graph)
        except Exception as e:
            flash(f'Error making prediction: {str(e)}', 'danger')
            return render_template('predict.html')
    
    return render_template('predict.html')





     
def add_crop_prices_to_spreadsheet(data):
    try:
      # Use credentials from a JSON file (service account key)
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        client = gspread.authorize(creds)
        sheet_id = "1zfmgF6t5rePUNkn2W0FC8CiXY7vZQb1f4CZS7WFTsTw"
        
        # Open the spreadsheet
        spreadsheet = client.open_by_key(sheet_id)
        
        # Access the specific worksheet - FIXED: use get_worksheet or worksheet method
        try:
            # First attempt - try to get by name
            sheet = spreadsheet.worksheet("cropprices")
        except Exception:
            # Second attempt - if named worksheet doesn't exist, use the first sheet
            sheet = spreadsheet.get_worksheet(1)
        
        # Format data properly for spreadsheet
        # Convert user_id and predicted_price to strings to ensure they can be inserted into the spreadsheet
        row = [str(data['user_id']), 
               data['commodity'], 
               data['state'], 
               data['district'],
               data['market'], 
               str(data['predicted_price'])]
        
        # Insert the row
        sheet.append_row(row)
        
        return True
    
    except Exception as e:
        flash(f'Error adding data to spreadsheet: {str(e)}', 'danger')
        return False





@app.route('/price_prediction', methods=['GET', 'POST'])
@login_required
def price_prediction():
    error = None
    
    if request.method == 'POST':
        if price_model is None or label_encoders is None or data.empty:
            flash('Price prediction model or data is not available', 'danger')
            return render_template('prediction.html',
                                 commodity_list=commodity_list,
                                 state_list=state_list,
                                 district_list=district_list,
                                 market_list=market_list)
    try:       
        commodity_name = request.form['commodity_name'].strip().lower()
        state = request.form['state'].strip().lower()
        district = request.form['district'].strip().lower()
        market = request.form['market'].strip().lower()
                
            
        encoded_commodity = label_encoders['commodity_name'].transform([commodity_name])[0]
        encoded_state = label_encoders['state'].transform([state])[0]
        encoded_district = label_encoders['district'].transform([district])[0]
        encoded_market = label_encoders['market'].transform([market])[0]
                    
        matching_rows = data[
            (data['commodity_name'] == commodity_name) &
            (data['state'] == state) &
            (data['district'] == district) &
            (data['market'] == market)
        ]
                    
        if not matching_rows.empty:
            avg_min_price = matching_rows['min_price'].mean()
            avg_max_price = matching_rows['max_price'].mean()
        else:
            avg_min_price = data['min_price'].mean()
            avg_max_price = data['max_price'].mean()
                    
            input_data = pd.DataFrame([[encoded_commodity, encoded_state, encoded_district, encoded_market, avg_min_price, avg_max_price]],
            columns=['commodity_name', 'state', 'district', 'market', 'min_price', 'max_price'])
            predicted_price = price_model.predict(input_data)[0]
                    
                # Add data to spreadsheet only if prediction was successful
            if predicted_price is not None:
                spreadsheet_data = {
                    'user_id': current_user.id,
                    'commodity': commodity_name,
                    'state': state,
                    'district': district,
                    'market': market,
                   'predicted_price': predicted_price
                }
                success = add_crop_prices_to_spreadsheet(spreadsheet_data)
            try:
                PricePrediction.create(
                    db=db,
                    user_id=current_user.id,
                    commodity=commodity_name,
                    state=state,
                    district=district,
                    market=market,
                    predicted_price=predicted_price
                )
                flash("Price prediction saved successfully!", "success")
            except Exception as db_error:
                    error = f"Prediction successful but failed to save to database: {str(db_error)}"
                    flash(error, "warning")
                            
                    if not success:
                        flash("Prediction successful but could not log data to spreadsheet.", "warning")
    except Exception as e:            
            flash("Prediction failed")
                
    return render_template('prediction.html',
                predicted_price=f"{predicted_price:.2f}" if predicted_price else None,
                error=error,
                commodity_name=commodity_name,
                state=state,
                district=district,
                market=market,
                commodity_list=commodity_list,
                state_list=state_list,
                district_list=district_list,
                market_list=market_list)
    





def add_crop_yield_to_spreadsheet(data):

    print(f"\n📊 ATTEMPTING TO ADD DATA TO GOOGLE SPREADSHEET")
    print("-" * 40)
    try:

        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        client = gspread.authorize(creds)
        sheet_id = "1zfmgF6t5rePUNkn2W0FC8CiXY7vZQb1f4CZS7WFTsTw"
        spreadsheet = client.open_by_key(sheet_id)
        
        # Attempt to open a specific worksheet by name, otherwise use the first one
        try:
            # Change "CropYieldPredictionsLog" to your desired worksheet name
            sheet = spreadsheet.worksheet("CropYieldPredictionsLog") 
        except Exception:
            sheet = spreadsheet.get_worksheet(2)
            print("Warning: 'CropYieldPredictionsLog' worksheet not found, using the first sheet.")
            
       row = [
            data.get('user_id', 'anonymous'),
            str(data.get('State_Name', '')), # Ensure string
            str(data.get('District_Name', '')), # Ensure string
            int(data.get('Crop_Year', 0)), # Ensure int
            str(data.get('Season', '')), # Ensure string
            str(data.get('Crop', '')), # Ensure string
            float(data.get('temperature', 0.0)), # Ensure float
            int(data.get('humidity', 0)), # Ensure int
            int(data.get('Soil_Moisture', 0)), # Ensure int
            float(data.get('Area_in_hectares', 0.0)), # Ensure float
            float(data.get('Production_in_tons', 0.0)), # Ensure float
            # data.get('Unnamed: 0', 0), # Removed as it's often an index, adjust if truly a feature
            str(data.get('Crop_Type', '')), # Ensure string
            int(data.get('N', 0)), # Ensure int
            int(data.get('P', 0)), # Ensure int
            int(data.get('K', 0)), # Ensure int
            float(data.get('pH', 0.0)), # Ensure float
            float(data.get('rainfall', 0.0)), # Ensure float
            float(data.get('Yield_ton_per_hec', 0.0)) # FIX: Ensure this is a standard Python float
        ]
        
        # Append the row to the Google Sheet
        sheet.append_row(row)
        
        print("✅ Data successfully added to Google Spreadsheet.")
        return True
        
    except Exception as e:
        print(f'❌ Error adding data to spreadsheet: {str(e)}')
        return False



@app.route('/predict_yield', methods=['GET', 'POST'])
@login_required
def predict_yield():
    if request.method == 'POST':
        if yield_model is None:
            flash('Yield prediction model is not available', 'danger')
            return render_template('predict_yield.html')
            
        try:
            # Get form data
            form_data = request.form.to_dict()
            
            # Define expected numeric features
            numeric_features = [
                'temperature', 'Soil_Moisture', 'Area_in_hectares', 
                'Production_in_tons', 'N', 'P', 'K', 'pH', 'rainfall'
            ]
            
            # Process numeric features
            processed_data = {}
            for feature in numeric_features:
                if feature in form_data and form_data[feature]:
                    try:
                        processed_data[feature] = float(form_data[feature])
                    except (ValueError, TypeError):
                        processed_data[feature] = 0.0
                else:
                    processed_data[feature] = 0.0
            
            # Determine model features
            if hasattr(yield_model, 'feature_names_in_'):
                model_features = yield_model.feature_names_in_
            elif feature_names is not None:
                model_features = feature_names
            else:
                model_features = numeric_features
            
            # Create input data
            input_data = {}
            for feature in model_features:
                input_data[feature] = processed_data.get(feature, 0.0)
            
            input_df = pd.DataFrame([input_data])
            
            # Scale if scaler available
            if scaler is not None:
                try:
                    scaler_features = scaler.feature_names_in_
                    input_for_scaling = pd.DataFrame()
                    for feature in scaler_features:
                        input_for_scaling[feature] = input_df.get(feature, 0.0)
                    scaled_data = scaler.transform(input_for_scaling)
                except Exception as e:
                    print(f"Scaling error: {e}")
                    scaled_data = input_df.values
            else:
                scaled_data = input_df.values
            
            # Make prediction
            prediction = yield_model.predict(scaled_data)[0]
            prediction_text = f"Predicted Yield: {prediction:.2f} tons/hectare"
            
            spreadsheet_data = {
                'user_id': current_user.id, # Example user ID
                'State_Name': form_data.get('State_Name'),
                'District_Name': form_data.get('district'), # Map 'district' from HTML to 'District_Name'
                'Crop_Year': form_data.get('Crop_Year'),
                'Season': form_data.get('Season'), # Placeholder: get this from HTML if relevant
                'Crop': form_data.get('Crop'),     # Placeholder: get this from HTML if relevant
                'temperature': form_data.get('temperature'),
                'humidity': form_data.get('humidity'),
                'Soil_Moisture': form_data.get('Soil_Moisture'),
                'Area_in_hectares': form_data.get('Area_in_hectares'),
                'Production_in_tons': form_data.get('Production_in_tons'),
                'Crop_Type': form_data.get('Crop_Type'), # Placeholder: get this from HTML if relevant
                'N': form_data.get('N'),
                'P': form_data.get('P'),
                'K': form_data.get('K'),
                'pH': form_data.get('pH'),
                'rainfall': form_data.get('rainfall'),
                'Yield_ton_per_hec': prediction # The actual predicted yield from your model
            }
            
            # Call the function to add data to the spreadsheet
            add_crop_yield_to_spreadsheet(spreadsheet_data)

            # Generate insight
            if prediction < 1.0:
                insight = "Low yield expected. Consider improving soil nutrients or irrigation."
            elif prediction < 3.0:
                insight = "Moderate yield expected. Good farming practices in place."
            elif prediction < 5.0:
                insight = "Good yield expected. Excellent farming conditions."
            else:
                insight = "Exceptional yield expected. Optimal farming conditions!"
            
            return render_template('predict_yield.html',
                                 prediction=prediction_text,
                                 insight=insight,
                                 form_data=form_data,
                                 success=True)
                                 
        except Exception as e:
            return render_template('predict_yield.html',
                                 prediction=f"Error occurred: {str(e)}",
                                 insight="Please check your input values and try again.",
                                 form_data=request.form.to_dict(),
                                 success=False)
    
    return render_template('predict_yield.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/history')
@login_required
def prediction_history():
    crop_predictions = CropPrediction.get_by_user(db, current_user.id, limit=5)
    price_predictions = PricePrediction.get_by_user(db, current_user.id, limit=5)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', '').lower()
    
    # Base query
    query = "SELECT * FROM crop_predictions WHERE user_id = %s"
    params = [current_user.id]
    
    # Add search filter
    if search_term:
        query += " AND predicted_crop LIKE %s"
        params.append(f"%{search_term}%")
    
    # Add pagination
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    offset = (page - 1) * per_page
    params.extend([per_page, offset])
    
    # Get results
    predictions = db.execute_query(query, params, fetch=True)
    
    # Get total count
    count_query = "SELECT COUNT(*) as total FROM crop_predictions WHERE user_id = %s"
    count_params = [current_user.id]
    if search_term:
        count_query += " AND predicted_crop LIKE %s"
        count_params.append(f"%{search_term}%")
    
    total_result = db.execute_query(count_query, count_params, fetch=True)
    total = total_result[0]['total'] if total_result else 0
    
    # Create pagination object
    predictions = Pagination(page=page, per_page=per_page, total=total, items=predictions)
    
    return render_template('history.html', 
                         predictions=predictions,
                         crop_predictions=crop_predictions, 
                         price_predictions=price_predictions,
                         per_page=per_page)
    
    
@app.route('/pricehistory')
@login_required
def prediction_history_price():
    # Get recent predictions for sidebar (consistent with crop history)
    crop_predictions = CropPrediction.get_by_user(db, current_user.id, limit=5)
    price_predictions = PricePrediction.get_by_user(db, current_user.id, limit=5)

    # Pagination parameters (same as crop history)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', '').lower()

    # Base query for price predictions (similar structure to crop history)
    query = "SELECT * FROM price_predictions WHERE user_id = %s"
    params = [current_user.id]

    # Add search filter if provided (expanded to include more relevant fields)
    if search_term:
        query += " AND commodity LIKE %s"
        params.append(f"%{search_term}%")

    # Add pagination (same as crop history)
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    # Get paginated results (same as crop history)
    price_results = db.execute_query(query, params, fetch=True)

    # Get total count for pagination (same structure as crop history)
    count_query = "SELECT COUNT(*) as total FROM price_predictions WHERE user_id = %s"
    # print(count_query)
    count_params = [current_user.id]
    if search_term:
        count_query += " AND (predicted_crop LIKE %s OR market LIKE %s OR predicted_price::text LIKE %s)"
        count_params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

    total_result = db.execute_query(count_query, count_params, fetch=True)
    total = total_result[0]['total'] if total_result else 0

    # Create pagination object (same as crop history)
    predictions = Pagination(
        page=page,
        per_page=per_page,
        total=total,
        items=price_results
    )

    return render_template('price_history.html',
                         predictions=predictions, 
                         crop_predictions=crop_predictions,
                         price_predictions=price_predictions,
                         per_page=per_page,
                         is_price_history=True)  # Additional flag for template
   
    
# Route to view yield prediction history
@app.route('/yield_history')
@login_required
def yield_history():
    """Route handler for viewing user's yield prediction history"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', '').lower()
    
    # Base query
    query = "SELECT * FROM yield_predictions WHERE user_id = %s"
    params = [current_user.id]
    
    # Add search filter if provided
    if search_term:
        query += " AND (crop LIKE %s OR state LIKE %s)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    # Add pagination
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    offset = (page - 1) * per_page
    params.extend([per_page, offset])
    
    # Get paginated results
    predictions = db.execute_query(query, params, fetch=True)
    
    # Get total count for pagination
    count_query = "SELECT COUNT(*) as total FROM yield_predictions WHERE user_id = %s"
    count_params = [current_user.id]
    if search_term:
        count_query += " AND (crop LIKE %s OR state LIKE %s)"
        count_params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    total_result = db.execute_query(count_query, count_params, fetch=True)
    total = total_result[0]['total'] if total_result else 0
    
    # Create pagination object
    paginated_predictions = Pagination(
        page=page, 
        per_page=per_page, 
        total=total, 
        items=predictions
    )
    
    return render_template(
        'yield_history.html',
        predictions=paginated_predictions,
        per_page=per_page
    )


@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Administrator privileges required.', 'danger')
        return redirect(url_for('dashboard'))
        
    user_count = db.execute_query("SELECT COUNT(*) as count FROM users", fetch=True)[0]['count']
    crop_prediction_count = db.execute_query("SELECT COUNT(*) as count FROM crop_predictions", fetch=True)[0]['count']
    price_prediction_count = db.execute_query("SELECT COUNT(*) as count FROM price_predictions", fetch=True)[0]['count']
    
    # Get recent users
    recent_users_result = db.execute_query(
        "SELECT * FROM users ORDER BY created_at DESC LIMIT 5", 
        fetch=True
    )
    
    recent_users = [
        {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at'],
            'is_admin': user['is_admin']
        } for user in recent_users_result
    ] if recent_users_result else []
    
    return render_template('admin_page.html',
                          user_count=user_count,
                          crop_prediction_count=crop_prediction_count,
                          price_prediction_count=price_prediction_count,
                          recent_users=recent_users)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Database setup functions
def create_tables():
    """Create database tables if they don't exist"""
    try:
        connection = db.connect()
        cursor = connection.cursor()
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(20) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Crop predictions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crop_predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            nitrogen FLOAT NOT NULL,
            phosphorus FLOAT NOT NULL,
            potassium FLOAT NOT NULL,
            temperature FLOAT NOT NULL,
            humidity FLOAT NOT NULL,
            ph FLOAT NOT NULL,
            rainfall FLOAT NOT NULL,
            predicted_crop VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # Price predictions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            commodity VARCHAR(100) NOT NULL,
            state VARCHAR(100) NOT NULL,
            district VARCHAR(100) NOT NULL,
            market VARCHAR(100) NOT NULL,
            predicted_price FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        connection.commit()
        print("✓ Database tables created successfully")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def create_admin_user():
    """Create admin user if not exists"""
    try:
        admin = User.find_by_email('admin@example.com', db)
        if not admin:
            admin_created = User.create(
                username='admin',
                email='admin@example.com',
                password='admin123',
                is_admin=True,
                db_connection=db
            )
            if admin_created:
                print("✓ Admin user created successfully")
                return True
            else:
                print("✗ Failed to create admin user")
                return False
        else:
            print("✓ Admin user already exists")
            return True
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        return False

if __name__ == '__main__':
    # Initialize database
    create_tables()
    create_admin_user()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)