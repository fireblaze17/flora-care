from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pymysql
import re
from datetime import datetime

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
    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('login'))

    try:
        mycursor.execute("USE userdata")
        mycursor.execute("SELECT * FROM plants")
        plants = mycursor.fetchall()
        return render_template('homepage.html', plants=plants)
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        return redirect(url_for('login'))
    finally:
        con.close()


@app.route('/editplant/<int:plant_id>', methods=['GET', 'POST'])
def editplant(plant_id):
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
            mycursor.execute("UPDATE plants SET plant_name=%s, location=%s, watering_frequency=%s WHERE id=%s",
                             (name, location, frequency, plant_id))
            con.commit()
            flash("Plant updated successfully!", 'success')
            return redirect(url_for('homepage'))
        except pymysql.Error as e:
            flash(f"Database error: {e}", 'danger')
            con.rollback()
        finally:
            con.close()
    
    try:
        print(f"Retrieving plant with ID {plant_id}")
        mycursor.execute("SELECT * FROM plants WHERE id=%s", (plant_id,))
        plant = mycursor.fetchone()
        if plant:
            print(f"Plant retrieved: {plant}")
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
    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('login'))

    try:
        mycursor.execute("USE userdata")
        mycursor.execute("DELETE FROM plants WHERE id=%s", (plant_id,))
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

    if email == '' or password == '':
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
            password VARCHAR(20)
        )""")
        mycursor.execute("SELECT * FROM credentials WHERE email = %s", (email,))
        row = mycursor.fetchone()
        if row:
            flash("Account already exists! Please log in.", 'danger')
            return redirect(url_for('login'))

        mycursor.execute("INSERT INTO credentials (email, password) VALUES (%s, %s)", (email, password))
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
    email = request.form['email']
    password = request.form['password']

    if email == '' or password == '':
        flash("All fields are required", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('login'))

    try:
        mycursor.execute("SELECT * FROM credentials WHERE email = %s AND password = %s", (email, password))
        row = mycursor.fetchone()
        if not row:
            flash("Invalid email or password", 'danger')
            return redirect(url_for('login'))
        flash("Login Successful!", 'success')
        return redirect(url_for('homepage'))
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
    finally:
        con.close()

@app.route('/homepage', methods=['GET'])
def addingplant():
    return redirect(url_for('plantadd'))

@app.route('/add_plant', methods=['POST'])
def add_plant():
    plant_name = request.form['plant_name']
    location = request.form['location']
    watering_frequency = request.form['watering_frequency']

    con, mycursor = connect_database()
    if not con:
        flash("Database connection failed", 'danger')
        return redirect(url_for('plantadd'))

    try:
        # Create the plants table if it does not exist
        mycursor.execute("""
        CREATE TABLE IF NOT EXISTS plants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            plant_name VARCHAR(100),
            location VARCHAR(100),
            watering_frequency INT,
            last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Insert the new plant into the database
        mycursor.execute("INSERT INTO plants (plant_name, location, watering_frequency) VALUES (%s, %s, %s)",
                         (plant_name, location, watering_frequency))
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
    con, mycursor = connect_database()
    if not con:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        mycursor.execute("USE userdata")
        mycursor.execute("UPDATE plants SET last_reset = CURRENT_TIMESTAMP WHERE id = %s", (plant_id,))
        con.commit()
        return jsonify({'status': 'success', 'message': 'Timer reset successfully'})
    except pymysql.Error as e:
        con.rollback()
        return jsonify({'status': 'error', 'message': 'Failed to reset timer'}), 500
    finally:
        con.close()

@app.route('/get_last_reset/<int:plant_id>', methods=['GET'])
def get_last_reset(plant_id):
    con, mycursor = connect_database()
    if not con:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        mycursor.execute("USE userdata")
        mycursor.execute("SELECT last_reset FROM plants WHERE id = %s", (plant_id,))
        last_reset = mycursor.fetchone()
        if last_reset:
            return jsonify({'status': 'success', 'last_reset': last_reset[0].strftime('%Y-%m-%d %H:%M:%S')})
        else:
            return jsonify({'status': 'error', 'message': 'Plant not found'}), 404
    except pymysql.Error as e:
        return jsonify({'status': 'error', 'message': 'Failed to fetch last reset time'}), 500
    finally:
        con.close()




if __name__ == '__main__':
    app.run(debug=True)