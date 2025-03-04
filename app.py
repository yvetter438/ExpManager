from flask import Flask, request, redirect, url_for, session, jsonify
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
            
            # Store both tokens and user data in session
            session['user'] = {
                'email': response.user.email,
                'id': response.user.id,
            }
            session['access_token'] = response.session.access_token
            session['refresh_token'] = response.session.refresh_token
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

@app.route("/profile", methods=["GET", "POST", "DELETE"])
def profile():
    if 'user' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user']['id']
    
    # Enhanced debugging
    print("=" * 50)
    print("Session data:", {
        'user_id': user_id,
        'access_token': session.get('access_token')[:20] + "..." if session.get('access_token') else None,
        'refresh_token': session.get('refresh_token')[:20] + "..." if session.get('refresh_token') else None,
        'session_keys': list(session.keys())
    })
    
    # Ensure auth token is set for this request
    if 'access_token' in session:
        try:
            supabase.auth.set_session(
                access_token=session['access_token'],
                refresh_token=session.get('refresh_token', '')
            )
        except Exception as e:
            print(f"Error setting session in route: {str(e)}")
    
    # Check if Supabase client has auth
    print("Supabase auth status:", {
        'is_authenticated': hasattr(supabase.auth, 'current_user') and supabase.auth.current_user is not None
    })
    
    # Handle DELETE request (from JavaScript)
    if request.method == "DELETE":
        try:
            result = (
                supabase.table('profile')
                .delete()
                .eq('user_id', user_id)
                .execute()
            )
            return jsonify({"success": True, "message": "Profile deleted successfully"})
        except Exception as e:
            print("Error:", str(e))
            return jsonify({"success": False, "error": str(e)}), 500
    
    # Fetch existing profile data
    try:
        profile_data = (
            supabase.table('profile')
            .select("*")
            .eq('user_id', user_id)
            .execute()
        )
        existing_profile = profile_data.data[0] if profile_data.data else None
        print("Existing profile:", existing_profile)
    except Exception as e:
        print("Error fetching profile:", str(e))
        existing_profile = None

    if request.method == "POST":
        # Get form data with proper validation
        profile_info = {
            'name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'linkedin': request.form.get('linkedin', '').strip(),
            'github': request.form.get('github', '').strip(),
            'portfolio': request.form.get('portfolio', '').strip(),
            'professional_summary': request.form.get('professional_summary', '').strip(),
            'user_id': user_id
        }
        
        # Debug: Print profile info being sent
        print("Profile data to be saved:", profile_info)
        
        try:
            if existing_profile:
                # Try a different approach for updating
                # First, get the record ID
                record_id = existing_profile.get('id')
                print(f"Updating record with ID: {record_id}")
                
                # Update using the record ID instead of user_id
                result = (
                    supabase.table('profile')
                    .update(profile_info)
                    .eq('id', record_id)
                    .execute()
                )
                print("Update result:", result)
            else:
                # Create new profile
                result = (
                    supabase.table('profile')
                    .insert(profile_info)
                    .execute()
                )
                print("Insert result:", result)
            
            # Force a refresh of the page to show updated data
            return redirect(url_for('profile'))
        except Exception as e:
            print("Error saving profile:", str(e))
            return str(e)

    # Get values safely with empty string as default
    name = existing_profile.get('name', '') if existing_profile else ''
    email = existing_profile.get('email', '') if existing_profile else ''
    phone = existing_profile.get('phone', '') if existing_profile else ''
    linkedin = existing_profile.get('linkedin', '') if existing_profile else ''
    github = existing_profile.get('github', '') if existing_profile else ''
    portfolio = existing_profile.get('portfolio', '') if existing_profile else ''
    professional_summary = existing_profile.get('professional_summary', '') if existing_profile else ''

    # Display form with existing data if available
    return f'''
    <nav>
        <a href="{url_for('dashboard')}">Dashboard</a> | 
        <a href="{url_for('logout')}">Logout</a>
    </nav>
    <h1>Profile Setup</h1>
    <form method="post">
        Name: <input type="text" name="name" value="{name}" required><br>
        Email: <input type="text" name="email" value="{email}" required><br>
        Phone: <input type="text" name="phone" value="{phone}"><br>
        LinkedIn: <input type="text" name="linkedin" value="{linkedin}"><br>
        GitHub: <input type="text" name="github" value="{github}"><br>
        Portfolio: <input type="text" name="portfolio" value="{portfolio}"><br>
        Professional Summary:<br>
        <textarea name="professional_summaryy" rows="4" cols="50">{professional_summary}</textarea><br>
        <input type="submit" value="{'Update' if existing_profile else 'Create'} Profile">
    </form>
    {f'<form method="post" action="{url_for("delete_profile")}"><input type="submit" value="Delete Profile"></form>' if existing_profile else ''}
    '''

@app.route("/delete_profile", methods=["POST"])
def delete_profile():
    if 'user' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user']['id']
    
    try:
        result = (
            supabase.table('profile')
            .delete()
            .eq('user_id', user_id)
            .execute()
        )
        return redirect(url_for('profile'))
    except Exception as e:
        print("Error deleting profile:", str(e))
        return str(e)

@app.route("/test_db")
def test_db():
    if 'user' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user']['id']
    
    try:
        # Try a simple query that doesn't require RLS
        # Using a different approach to get count
        result = supabase.table('profile').select('*').execute()
        count = len(result.data) if result.data else 0
        
        # Also try to get the table structure
        columns = list(result.data[0].keys()) if result.data and len(result.data) > 0 else []
        
        return f"""
        <h1>Database Test</h1>
        <p>Connection successful</p>
        <p>Record count: {count}</p>
        <p>Columns: {', '.join(columns) if columns else 'No data to show columns'}</p>
        <p>User ID from session: {user_id}</p>
        <p>Auth status: {'Authenticated' if 'access_token' in session else 'Not authenticated'}</p>
        """
    except Exception as e:
        return f"""
        <h1>Database Error</h1>
        <p>{str(e)}</p>
        <p>User ID from session: {user_id}</p>
        <p>Auth status: {'Authenticated' if 'access_token' in session else 'Not authenticated'}</p>
        """

@app.route("/check_user_id")
def check_user_id():
    if 'user' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user']['id']
    
    return f"""
    <h1>User ID Check</h1>
    <p>User ID: {user_id}</p>
    <p>Type: {type(user_id).__name__}</p>
    <p>Length: {len(user_id)}</p>
    """

@app.route("/check_auth")
def check_auth():
    try:
        # This will fail if auth is not properly set
        user = supabase.auth.get_user()
        return f"Authenticated as: {user.user.id}"
    except Exception as e:
        return f"Not authenticated: {str(e)}"

@app.route("/check_auth_token")
def check_auth_token():
    if 'user' not in session:
        return redirect(url_for('signin'))
    
    # Print detailed session info
    print("=" * 50)
    print("Session data:", {
        'user_id': session['user']['id'],
        'access_token': session.get('access_token')[:20] + "..." if session.get('access_token') else None,
    })
    
    # Try to get the current user directly from Supabase
    try:
        user = supabase.auth.get_user()
        auth_id = user.user.id if hasattr(user, 'user') else "Not available"
        
        # Try a simple query with RLS enabled
        try:
            profile_data = supabase.table('profile').select('*').execute()
            profile_count = len(profile_data.data) if profile_data.data else 0
            
            # Try to insert a test record
            test_result = None
            try:
                test_result = supabase.table('profile').insert({
                    'name': 'Test User',
                    'email': 'test@example.com',
                    'user_id': session['user']['id']
                }).execute()
            except Exception as insert_error:
                test_result = f"Insert error: {str(insert_error)}"
            
            return f"""
            <h1>Auth Token Check</h1>
            <p>Session User ID: {session['user']['id']}</p>
            <p>Supabase Auth ID: {auth_id}</p>
            <p>Do they match? {'Yes' if session['user']['id'] == auth_id else 'No'}</p>
            <p>Profile count: {profile_count}</p>
            <p>Test insert result: {test_result}</p>
            """
        except Exception as query_error:
            return f"""
            <h1>Auth Token Check</h1>
            <p>Session User ID: {session['user']['id']}</p>
            <p>Supabase Auth ID: {auth_id}</p>
            <p>Do they match? {'Yes' if session['user']['id'] == auth_id else 'No'}</p>
            <p>Query error: {str(query_error)}</p>
            """
    except Exception as e:
        return f"""
        <h1>Auth Token Check</h1>
        <p>Session User ID: {session['user']['id']}</p>
        <p>Error getting Supabase user: {str(e)}</p>
        """

if __name__ == "__main__":
    app.run(debug=True)


