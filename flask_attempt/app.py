from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response, send_from_directory
import pymysql
import re
from datetime import datetime, timedelta
import pymysql.cursors
import firebase_admin
from firebase_admin import credentials, messaging
from apscheduler.schedulers.background import BackgroundScheduler



cred = credentials.Certificate('flask_attempt/static/computer-science-ia-floracare-firebase-adminsdk-rm6go-e589ffd970.json')
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def connect_database():
    try:
        con = pymysql.connect(host="localhost", user="root", password="1234", database="userdata")
        mycursor = con.cursor()
        return con, mycursor
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        return None, None

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/homepage')
def homepage():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('login'))

    try:
        # Select only the plants that belong to the logged-in user
        mycursor.execute("SELECT * FROM plants WHERE user_id=%s", (session['user_id'],))
        plants = mycursor.fetchall()
        return render_template('homepage.html', plants=plants)
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        return redirect(url_for('login'))
    finally:
        con.close()



@app.route('/editplant/<int:plant_id>', methods=['GET', 'POST'])
def editplant(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('homepage'))

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        frequency = request.form['frequency']

        if name == '' or location == '' or frequency == '':
            flash("All fields are required", 'danger')
            return redirect(url_for('editplant', plant_id=plant_id))

        try:
            mycursor.execute("""
                UPDATE plants SET plant_name=%s, location=%s, watering_frequency=%s 
                WHERE id=%s AND user_id=%s
            """, (name, location, frequency, plant_id, session['user_id']))
            con.commit()
            flash("Plant updated successfully!", 'success')
            return redirect(url_for('homepage'))
        except pymysql.Error as e:
            flash(f"Database error: {e}", 'danger')
            con.rollback()
        finally:
            con.close()

    try:
        mycursor.execute("SELECT * FROM plants WHERE id=%s AND user_id=%s", (plant_id, session['user_id']))
        plant = mycursor.fetchone()
        if plant:
            return render_template('editplant.html', plant=plant)
        else:
            flash("Plant not found", 'danger')
            return redirect(url_for('homepage'))
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        return redirect(url_for('homepage'))
    finally:
        con.close()



@app.route('/deleteplant/<int:plant_id>', methods=['POST'])
def deleteplant(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('login'))

    try:
        mycursor.execute("DELETE FROM plants WHERE id=%s AND user_id=%s", (plant_id, session['user_id']))
        con.commit()
        flash("Plant deleted successfully!", 'success')
        return redirect(url_for('homepage'))
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        if 'con' in locals():
            con.rollback()
    finally:
        con.close()



@app.route('/plantadd')
def plantadd():
    return render_template('plantadd.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    token = request.form.get('token')  # Get the token from the form or a JSON body

    if email == '' or password == '' or not token:
        flash("All fields are required", 'danger')
        return redirect(url_for('signup'))

    if not re.match(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$', email):
        flash("Enter a valid email", 'danger')
        return redirect(url_for('signup'))

    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('signup'))
    
    try:
        mycursor.execute("CREATE DATABASE IF NOT EXISTS userdata")
        mycursor.execute("USE userdata")
        mycursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(50),
            password VARCHAR(20),
            token VARCHAR(255)            
        )""")
        mycursor.execute("SELECT * FROM credentials WHERE email = %s", (email,))
        row = mycursor.fetchone()
        if row:
            flash("Account already exists! Please log in.", 'danger')
            return redirect(url_for('login'))

        # Insert email, password, and token into the database
        mycursor.execute("INSERT INTO credentials (email, password, token) VALUES (%s, %s, %s)", (email, password, token))
        con.commit()
        flash("Registration was successful!", 'success')
        return redirect(url_for('login'))
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        if 'con' in locals():
            con.rollback()
    finally:
        con.close()

@app.route('/login', methods=['POST'])
def login_user():
    email = request.form.get('email')
    password = request.form.get('password')
    token = request.form.get('token')  # Retrieve the token from the form data
    print("Token to be used for notification:", token)

    if not email or not password:
        flash("All fields are required", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        flash("Database connection failed", 'danger')
        return redirect(url_for('login'))

    try:
        # Verify user credentials
        mycursor.execute("SELECT id FROM credentials WHERE email = %s AND password = %s", (email, password))
        user = mycursor.fetchone()
        if not user:
            flash("Invalid email or password", 'danger')
            return redirect(url_for('login'))

        # Update the token in the database
        user_id = user[0]  # Assuming 'id' is the first column
        mycursor.execute("UPDATE credentials SET token = %s WHERE id = %s", (token, user_id))
        con.commit()  # Commit the transaction

        # Store user details in session
        session['user_id'] = user_id
        session['token'] = token  # Store the user's Firebase token in the session

        flash("Login Successful!", 'success')
        return redirect(url_for('homepage'))
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
    finally:
        con.close()





@app.route('/add_plant', methods=['POST'])
def add_plant():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    plant_name = request.form['plant_name']
    location = request.form['location']
    watering_frequency = request.form['watering_frequency']

    con, mycursor = connect_database()
    if not con:
        flash("Database connection failed", 'danger')
        return redirect(url_for('plantadd'))

    try:
        # Insert the new plant into the database with user_id
        mycursor.execute("""
            INSERT INTO plants (plant_name, location, watering_frequency, user_id) 
            VALUES (%s, %s, %s, %s)
        """, (plant_name, location, watering_frequency, session['user_id']))
        con.commit()
        flash("Plant added successfully!", 'success')
        return redirect(url_for('homepage'))
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        if 'con' in locals():
            con.rollback()
        return redirect(url_for('plantadd'))
    finally:
        con.close()



@app.route('/reset_timer/<int:plant_id>', methods=['POST'])
def reset_timer(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return jsonify({'status': 'error', 'message': 'You are not logged in!'}), 403

    con, mycursor = connect_database()
    if not con:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        # Update only the plant that belongs to the logged-in user
        mycursor.execute("UPDATE plants SET last_reset = CURRENT_TIMESTAMP WHERE id = %s AND user_id = %s", (plant_id, session['user_id']))
        con.commit()
        return jsonify({'status': 'success', 'message': 'Timer reset successfully'})
    except pymysql.Error as e:
        con.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to reset timer: {e}'}), 500
    finally:
        con.close()


@app.route('/get_last_reset/<int:plant_id>', methods=['GET'])
def get_last_reset(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return jsonify({'status': 'error', 'message': 'You are not logged in!'}), 403

    con, mycursor = connect_database()
    if not con:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        mycursor.execute("SELECT last_reset FROM plants WHERE id = %s AND user_id = %s", (plant_id, session['user_id']))
        last_reset = mycursor.fetchone()
        if last_reset:
            return jsonify({'status': 'success', 'last_reset': last_reset[0].strftime('%Y-%m-%d %H:%M:%S')})
        else:
            return jsonify({'status': 'error', 'message': 'Plant not found'}), 404
    except pymysql.Error as e:
        return jsonify({'status': 'error', 'message': 'Failed to fetch last reset time'}), 500
    finally:
        con.close()

@app.route('/search_plants', methods=['GET'])
def search_plants():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    query = request.args.get('query', '')  # Get the search term from the query string
    con, mycursor = connect_database()
    if not con:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('homepage'))

    try:
        # Search for plants where the name or location matches the query and is owned by the logged-in user
        mycursor.execute("""
        SELECT * FROM plants 
        WHERE (plant_name LIKE %s OR location LIKE %s) AND user_id=%s
        """, ('%' + query + '%', '%' + query + '%', session['user_id']))
        plants = mycursor.fetchall()
        return render_template('homepage.html', plants=plants)  # Render homepage with results
    except pymysql.Error as e:
        flash(f'Database error: {e}', 'danger')
        return redirect(url_for('homepage'))
    finally:
        con.close()









def check_and_notify():
    # Set up the database connection
    con = pymysql.connect(host='localhost',
                          user='root',
                          password='1234',
                          db='userdata',
                          charset='utf8mb4',
                          cursorclass=pymysql.cursors.DictCursor)  # Use DictCursor

    try:
        with con.cursor() as cursor:
            # Execute your query
            cursor.execute("""
                SELECT p.plant_name, p.location, p.watering_frequency, p.last_reset, c.token 
                FROM plants p 
                JOIN credentials c ON p.user_id = c.id
            """)
            plants = cursor.fetchall()
            print("Type of fetched data:", type(plants))
            if plants:
                print("Type of first item in fetched data:", type(plants[0]))
            
            # Process each plant
            for plant in plants:
                plant_name = plant['plant_name']
                location = plant['location']
                watering_frequency = plant['watering_frequency']
                last_reset = plant['last_reset']  
                token = str(plant['token'])  # Ensure token is treated as a string
                
                next_water_time = last_reset + timedelta(hours=watering_frequency)
                if datetime.now() >= next_water_time:
                 token = "fkpa3gUpNDWByUaqC278yQ:APA91bGTlBGA2jtc1ScjprWpf2qfSDi3ZfU50E2-iDj5JEbaeIt6cS-MPr-v1wenoKcs3DJBPYSYCR3KdZTXTd-tmi8AaBjzNxzl1AbjjtYxXckxx5QfF-jZNA1sW_1ef8kI3e1fZAaZ"
                send_notification(token, plant_name, location)

    except Exception as e:
        print("Database error:", e)
    finally:
        if con:
            con.close()


scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_notify, trigger="interval", minutes=1)  # Runs every hour
scheduler.start()


def send_notification(token, plant_name, location):
    message = messaging.Message(
        notification=messaging.Notification(
            title="Watering Reminder",
            body=f"Time to water {plant_name} at {location}",
            
        ),
        token=token,
    )

    try:
        response = messaging.send(message)
        print('Successfully sent message:', response)
    except Exception as e:
        print('Failed to send message:', str(e))




@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

@app.route('/firebase-messaging-sw.js')
def serve_firebase_sw():
    return send_from_directory(app.static_folder, 'firebase-messaging-sw.js')



if __name__ == '__main__':
    app.run(debug=True)