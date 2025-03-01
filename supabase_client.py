import os
from flask import g, session
from werkzeug.local import LocalProxy
from supabase.client import Client, ClientOptions
from flask_storage import FlaskSessionStorage

url = os.environ.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_ANON_KEY", "")

def get_supabase() -> Client:
    if "supabase" not in g:
        g.supabase = Client(
            url,
            key,
            options=ClientOptions(
                storage=FlaskSessionStorage(),
                flow_type="pkce"
            ),
        )
        
        # Set both access_token and refresh_token if they exist in session
        if 'access_token' in session:
            try:
                print("Setting Supabase auth token...")
                g.supabase.auth.set_session(
                    access_token=session['access_token'],
                    refresh_token=session.get('refresh_token', '')
                )
                
                # Verify the token was set
                user = g.supabase.auth.get_user()
                print(f"Auth token set successfully. User ID: {user.user.id if hasattr(user, 'user') else 'Unknown'}")
            except Exception as e:
                print(f"Error setting auth token: {str(e)}")
            
    return g.supabase

supabase: Client = LocalProxy(get_supabase)
