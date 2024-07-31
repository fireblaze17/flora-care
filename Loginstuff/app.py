from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import pymysql
from tkmacosx import Button as tkButton
import re 
from tkinter import ttk
import tkinter as tk




def login_hide():
    login_Password_entry.config(show='*')
    login_showbutton.config(text='Show', command=login_reveal)

def login_reveal():
    login_Password_entry.config(show='')
    login_showbutton.config(text='Hide', command=login_hide)

def signup_hide():
    signup_Password_entry.config(show='*')
    signup_showbutton.config(text='Show', command=signup_reveal)

def signup_reveal():
    signup_Password_entry.config(show='')
    signup_showbutton.config(text='Hide', command=signup_hide)


def connect_database():
    
    global signup_Email_entry, signup_Password_entry

    if signup_Email_entry.get() == '' or signup_Password_entry.get() == '':
        messagebox.showerror("ERROR!", "All fields are required")
        return
    elif  not re.match(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$', signup_Email_entry.get()):
         messagebox.showerror("ERROR!", "Enter a Valid Email.")
         clear_signup_fields()
         return


    try:
        con = pymysql.connect(host="localhost", user="root", password="1234", database="userdata")
        mycursor = con.cursor()

        # Create the database if not exists
        query = "CREATE DATABASE IF NOT EXISTS userdata"
        mycursor.execute(query)

        # Use the 'userdata' database
        query = "USE userdata"
        mycursor.execute(query)

        
        query = """
        CREATE TABLE IF NOT EXISTS credentials (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(50),
            password VARCHAR(20)
        )
        """
        mycursor.execute(query)

        # Check if email already exists
        query = "SELECT * FROM credentials WHERE email = %s"
        mycursor.execute(query, (signup_Email_entry.get(),))
        row = mycursor.fetchone()

        if row is not None:
            messagebox.showerror("ERROR!", "Account already exists! Please log in.")
            return

        # Insert new user into 'credentials' table
        insert_query = "INSERT INTO credentials (email, password) VALUES (%s, %s)"
        mycursor.execute(insert_query, (signup_Email_entry.get(), signup_Password_entry.get()))

        # Commit changes and close connection
        con.commit()
        con.close()

        # Inform user about successful registration
        messagebox.showinfo("Success", "Registration was successful!")
        clear_signup_fields()
        logging_in()

    except pymysql.Error as e:
        messagebox.showerror("Database Error", f"Database error: {e}")
        if 'con' in locals():
            con.rollback()
            con.close()


def clear_signup_fields():
    signup_Email_entry.delete(0, END)
    signup_Password_entry.delete(0, END)


def signing_up():
    signup.tkraise()


def logging_in():
    login.tkraise()
def login_user():
    email = login_Email_entry.get().strip()
    password = login_Password_entry.get().strip()
    print("Email value:", email) 
    print("Password value:", password)

    if email and password:
        con = None
        try:
            con = pymysql.connect(host="localhost", user="root", password="1234", database="userdata")
            mycursor = con.cursor()
            query = "SELECT * FROM credentials WHERE email = %s AND password = %s"
            mycursor.execute(query, (email, password))
            row = mycursor.fetchone()
            if row is None:
                messagebox.showerror("ERROR!", "Invalid email or password")
            else:
                messagebox.showinfo("Welcome", "Login Successful!")
                homepage.tkraise()
        except pymysql.Error as e:
            messagebox.showerror("Database Error", f"Error: {e}")
        finally:
            if con:
                con.close()
    else:
        messagebox.showerror("ERROR!", "All fields are required")

root = tk.Tk()

# Import the tcl file
root.tk.call('source','/Users/ankushb/Downloads/ComptuerscienceIA/Theme/forest-light.tcl')

# Set the theme with the theme_use method
style = ttk.Style()
style.theme_use('forest-light')

login = ttk.Frame(root,style='Card', padding=(5, 6, 7, 8))
signup = ttk.Frame(root, style='Card', padding=(5, 6, 7, 8))
homepage = ttk.Frame(root)
login.place(x=0, y=0, relwidth=1, relheight=1)
signup.place(x=0, y=0, relwidth=1, relheight=1)

root.geometry('990x660')
root.resizable(0, 0)

# Login Page UI elements
image_path = 'A21.png'
image = Image.open(image_path)
image = image.resize((990, 660))
background_image = ImageTk.PhotoImage(image)
bg_label_login = ttk.Label(login, image=background_image)
bg_label_login.place(x=0, y=0, relwidth=1, relheight=1)

heading_login = ttk.Label(login, text='Login')
heading_login.place(relx=0.15, rely=0.120)

login_Email_entry = ttk.Entry(login, width=35)
login_Email_entry.place(relx=0.2, rely=0.320, anchor='center')

login_email_label = ttk.Label(login, text='Email:')
login_email_label.place(relx=0.04, rely=0.25)

login_Password_entry = ttk.Entry(login, width=35, show='*')
login_Password_entry.place(relx=0.2, rely=0.470, anchor="center")

login_password_label = ttk.Label(login, text='Password:')
login_password_label.place(relx=0.04, rely=0.4)

login_showbutton = ttk.Button(login, text='Show',style='Accent.TButton', command=login_hide)
login_showbutton.place(relx=0.27, rely=0.5)

if login_Password_entry['show'] == '':
    login_showbutton.config(text='Hide', command=login_hide)
else:
    login_showbutton.config(text='Show', command=login_reveal)

loginbutton = ttk.Button(login, text='Log In',style='Accent.TButton', command=login_user)
loginbutton.place(relx=0.15, rely=0.6)

signuplabel = ttk.Label(login, text="Don't have an account?")
signuplabel.place(relx=0.08, rely=0.7)

signupbutton = ttk.Button(login, text="Sign Up.", style='Accent.TButton',command=signing_up)
signupbutton.place(relx=0.23, rely=0.7)

# Signup Page UI elements
image_path = 'A22.png'
image = Image.open(image_path)
image = image.resize((990, 660))
background_image_signup = ImageTk.PhotoImage(image)

bg_label_signup = ttk.Label(signup, image=background_image_signup)
bg_label_signup.place(x=0, y=0, relwidth=1, relheight=1)

heading_signup = ttk.Label(signup, text='Sign Up')
heading_signup.place(relx=0.15, rely=0.120)

signup_Email_entry = ttk.Entry(signup, width=35)
signup_Email_entry.place(relx=0.2, rely=0.320, anchor='center')

signup_email_label = ttk.Label(signup, text='Email:')
signup_email_label.place(relx=0.04, rely=0.25)

signup_Password_entry = ttk.Entry(signup, width=35, show='*')
signup_Password_entry.place(relx=0.2, rely=0.470, anchor="center")

signup_password_label = ttk.Label(signup, text='Password:')
signup_password_label.place(relx=0.04, rely=0.4)

signup_showbutton = ttk.Button(signup, text='Show',style='Accent.TButton', command=signup_hide)
signup_showbutton.place(relx=0.27, rely=0.5)

if signup_Password_entry['show'] == '':
    signup_showbutton.config(text='Hide', command=signup_hide)
else:
    signup_showbutton.config(text='Show', command=signup_reveal)

signupbutton_signup_page = ttk.Button(signup, text="Sign Up",style='Accent.TButton', command=connect_database)
signupbutton_signup_page.place(relx=0.15, rely=0.6)

loginbutton_signup_page = ttk.Button(signup, text="Log In",style='Accent.TButton', command=logging_in)
loginbutton_signup_page.place(relx=0.23, rely=0.7)

loginlabel = ttk.Label(signup, text="Already have an account?")
loginlabel.place(relx=0.08, rely=0.7)

login.tkraise()
root.mainloop()