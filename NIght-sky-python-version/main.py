from models import DataManager
from ui_auth import LoginWindow
from ui_store import OnlineBookstoreApp

def run_application():
    # 1. Initialize data
    dm = DataManager()

    # 2. Callback function when someone successfully logs in
    def on_login_success(username: str):
        # When logging out, we trigger run_application() again to restart the flow
        app = OnlineBookstoreApp(username, dm, on_logout_callback=run_application)
        app.run()

    # 3. Start at the login screen
    login = LoginWindow(dm, on_login_success)
    login.run()

if __name__ == "__main__":
    run_application()