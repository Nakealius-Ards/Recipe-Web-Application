"""
Developer: Nakealius D. Ards
Date: 24 February 2026
Purpose: This application will generate a simple Website using
Python flask. It will use at least 3 routes, rendering the HTML pages
using the render_template() functionality.
"""

import datetime
import re
import socket
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for

now = datetime.datetime.now() # Get the current time from the system

app = Flask(__name__)

@app.route("/")
def home():
    """Renders the home page."""
    server_date = datetime.datetime.now().strftime("%A, %d %B %Y")
    server_time = datetime.datetime.now().strftime("%H:%M:%S")

    return render_template("index.html", current_time=server_time,
                           current_date=server_date)

@app.route("/recipe1")
def recipe1():
    """Renders the recipe 1 page."""
    return render_template("recipe1.html")

@app.route("/recipe2")
def recipe2():
    """Renders the recipe 2 page."""
    return render_template("recipe2.html")

@app.route("/recipe3")
def recipe3():
    """Renders the recipe 3 page."""
    return render_template("recipe3.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    """Renders the login page and validate username and password."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Try to load the excel file
        try:
            df = pd.read_excel("user_registration.xlsx")

            # Check for matching username and password
            match = df[(df['Username'] == username) & (df['Password'] == password)]

            if not match.empty:
                # Return to homepage if it was successful
                return redirect(url_for('user_home', username=username))

            error_message = "Username or Password does not match! Please return and try again."
            failed_attempt_log()
            return render_template("error1.html", error_message=error_message)

        except FileNotFoundError:
            error_message = "User Registration file not found."
            return render_template("error1.html", error_message=error_message)

    return render_template("login.html")

@app.route("/index2")
def user_home():
    """Renders the new home page after the user logs in."""
    server_date = datetime.datetime.now().strftime("%A, %d %B %Y")
    server_time = datetime.datetime.now().strftime("%H:%M:%S")

    # Get the current username
    username = request.args.get('username', "")
    welcome_message = f"Welcome Back {username}!"

    return render_template("index2.html", current_time=server_time,
                           current_date=server_date, message=welcome_message)

def password_confirmation(password, confirmation):
    """Checks if the password is correct before continuing."""

    # Password Error Message
    password_error = ("Registration Error! Please check your email & password. "
                      "Your password must be between 12-18 characters long and"
                      ", include a uppercase character, a lowercase character, "
                      "a number, and a special character.")
    while True:
        # Confirm the passwords match before continuing
        if len(password) < 12 or len(password) > 18:
            return password_error, 400
        if not re.search("[A-Z]", password) and not re.search("[a-z]", password):
            return password_error, 400
        if not re.search("[0-9]", password):
            return password_error, 400
        if not re.search(r'[^A-Za-z0-9]', password):
            return password_error, 400
        if password != confirmation:
            return "Passwords do not match", 400

        return "Password is Valid!", 200

@app.route("/register", methods=['GET', 'POST'])
def register():
    """Renders the registration page and get the registration information for validation."""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirmation = request.form['confirm_password']

        message, status =password_confirmation(password, confirmation)
        if status != 200:
            return render_template("error.html", error_message=message), status

        # Create a dictionary of data
        user_data = {
            "Name": [name],
            "Email": [email],
            "Username": [username],
            "Password": [password]
        }

        # Convert to DataFrame
        df = pd.DataFrame.from_dict(user_data)

        # Append user_data to an Excel file
        excel_file = "user_registration.xlsx"
        try:
            existing = pd.read_excel(excel_file)
            updated = pd.concat([existing,df], ignore_index=True)
        except FileNotFoundError:
            updated = df

        # Save back to an Excel file
        updated.to_excel(excel_file, index=False)

        # Return to homepage after a success
        return redirect(url_for('home'))

    return render_template("register.html")

@app.route('/action', methods=['POST', 'GET'])
def action():
    """Checked action for if button is clicked."""
    return "Button was clicked."

@app.route("/update_pw", methods=['GET','POST'])
def update_pw():
    """Renders the password update form page and validates the user
    before updating the password."""

    pw_error = ("Password Error Detected! Your password must be between 12-18 characters long and"
                "include a uppercase character, a lowercase character, a number, and a "
                "special character.")

    # Get the username, password, new password and confirm password text
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['current_pw']
        new_pw = request.form['new_pw']
        confirm_pw = request.form['confirm_new_pw']

        # Compare the username and password before continuing
        try:
            df = pd.read_excel("user_registration.xlsx")
            match = df[(df['Username'] == username) & (df['Password'] == password)]
            if match.empty:
                error_message = "Invalid username or password."
                render_template("error1.html", error_message=error_message)

        # Throw error exception if the file is not found
        except FileNotFoundError:
            error_message = "User Registration file not found."
            render_template("error1.html", error_message=error_message)

        # Confirm the new password meets requirements
        if len(new_pw) < 12 or len(new_pw) > 18:
            return pw_error, 400
        if (not re.search("[A-Z]", new_pw) or not re.search("[a-z]", new_pw) or
                not re.search("[0-9]", new_pw) or not re.search(r'[^A-Za-z0-9]', new_pw)):
            return pw_error, 400
        if new_pw != confirm_pw:
            return "Passwords do not match", 400

        # Check against common passwords
        unsecure_pw_check = file_reader(new_pw)
        if unsecure_pw_check:
            return unsecure_pw_check

        # Update the password in the Excel file
        df.loc[df['Username'] == username, 'Password'] = new_pw
        df.to_excel("user_registration.xlsx", index=False)

        # Show a Password updated successfully response, then redirect to index2 page.
        return redirect(url_for('user_home', username=username))

    # For GET requests, just show the form return
    return render_template("update_password.html")

def file_reader(new_pw):
    """Read the common password txt file and traverse each line for a
    match, if one is found, return an error message page."""
    with open("CommonPassword.txt", "r", encoding="utf-8") as file:
        for line in file:
            if line.strip() == new_pw:
                return ("Password is unsecure! Please "
                        "generate a new secure password "
                        "and try again.")
        # If a match is not found continue with the logic
        return None

@app.route("/login", methods=['GET', 'POST'])
def failed_attempt_log():
    """ Get the attempted username and password attempt, then
    log it in a txt file with the time, date, and ip address."""
    failed_attempt_error = "Password Failed Attempt:"
    username = "" # Ensures username is always defined
    password = "" # Ensures password is always defined

    # Get the username and password entry
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

    # Get the user's local hostname and IP Address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Write to the failed attempt txt file documenting the error message
    # the current date and the user's local ip address
    with open("failed_attempt.txt", "a", encoding="utf-8") as log:
        log.write(f"\n{failed_attempt_error}\n"
                  "Attempted Username: " + f"{username}\n"
                  "Attempted Password: " + f"{password}\n"                     
                  "Date: " + f"{now.strftime('%d %B %Y')}\n"
                  "Time: " + f"{now.strftime('%H:%M:%S')}\n"
                  "IP Address: " + f"{local_ip}\n")

if __name__ == "__main__":
    app.run(debug=True)
