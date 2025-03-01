from flask import Flask, request, redirect, url_for, session
from supabase_client import supabase  # Import the supabase client from your custom module
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_default_secret_key")


#Home screen that redirects to dashboard if user is logged in
@app.route("/")
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return "Hello, World!"

#Signup screen that creates a new user
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return redirect(url_for('verify'))
        except Exception as e:
            return str(e)
    return '''
        <h1>Sign Up</h1>
        <form method="post">
            Email: <input type="text" name="email"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Sign Up">
        </form>
    '''

#Signin screen that logs in a user
@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Convert User object to dictionary before storing in session
            session['user'] = {
                'email': response.user.email,
                'id': response.user.id,
                # Add any other user properties you need
            }
            session['access_token'] = response.session.access_token
            return redirect(url_for('dashboard'))
        except Exception as e:
            return str(e)
    
    return '''
        <h1>Sign In</h1>
        <form method="post">
            Email: <input type="text" name="email"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Sign In">
        </form>
    '''

#Dashboard screen that displays a welcome message when logged in
@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    return f"Welcome to your dashboard, {session['user']['email']}!"

#Logout screen that logs out a user
@app.route("/logout")
def logout():
    supabase.auth.sign_out()
    session.clear()
    return redirect(url_for('home'))

@app.route("/verify")
def verify():
    return '''
        <h1>Email Verification Required</h1>
        <p>Please check your email and click the verification link to complete your registration.</p>
        <p>Once verified, you can <a href="/signin">sign in</a> to your account.</p>
    '''

@app.route("/password-reset", methods=["GET", "POST"])
def password_reset():
    if request.method == "POST":
        email = request.form.get("email")
        try:
            response = supabase.auth.reset_password_email(email)
            return "Password reset instructions have been sent to your email."
        except Exception as e:
            return str(e)
    return '''
        <h1>Reset Password</h1>
        <form method="post">
            Email: <input type="text" name="email"><br>
            <input type="submit" value="Reset Password">
        </form>
    '''

@app.route("/verify-callback")
def verify_callback():
    # Handle the email verification callback
    token = request.args.get("token")
    type = request.args.get("type")
    
    if type == "signup":
        try:
            response = supabase.auth.verify_signup({"token": token})
            return redirect(url_for('signin'))
        except Exception as e:
            return str(e)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)


