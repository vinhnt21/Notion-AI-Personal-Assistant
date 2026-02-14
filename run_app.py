import os
import sys
import streamlit.web.cli as stcli

def resolve_path(path):
    """
    Resolve absolute path to resources, works for dev and for PyInstaller
    """
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app 
        # path into variable _MEIPASS'.
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, path)

if __name__ == "__main__":
    # Check if .env exists, if not warn the user but don't crash immediately
    # (The user might configuring it via the UI later if we add that feature)
    
    # Resolve the path to main.py
    main_script = resolve_path("main.py")
    
    # Mock the command line arguments for streamlit
    sys.argv = [
        "streamlit",
        "run",
        main_script,
        "--global.developmentMode=false",
        "--server.headless=true",  # Make it act more like a backend server
    ]
    
    # Start the streamlit application
    sys.exit(stcli.main())
