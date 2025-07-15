# run_app.py
import streamlit.web.bootstrap
from streamlit import config as _config
import os

def run():
    # Define the path to your main Streamlit app script
    main_script_path = os.path.join(os.path.dirname(__file__), "app.py")

    # Set Streamlit server options
    _config.set_option("server.headless", True)  # Don't open a new browser tab
    _config.set_option("server.port", 8501)
    _config.set_option("server.address", "localhost")
    _config.set_option("browser.serverAddress", "localhost")
    _config.set_option("browser.serverPort", 8501)
    _config.set_option("browser.gatherUsageStats", False)

    # Run the Streamlit app
    streamlit.web.bootstrap.run(main_script_path, '', [], {})

if __name__ == "__main__":
    run()