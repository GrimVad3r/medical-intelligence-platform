import subprocess

def main():
    print("Starting Medical Intelligence Platform services...")
    # Start API
    api_proc = subprocess.Popen(["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"])
    # Start dashboard
    dash_proc = subprocess.Popen(["streamlit", "run", "dashboards/streamlit_app.py"])
    # Start Dagster
    dagster_proc = subprocess.Popen(["dagster", "dev", "-m", "src.orchestration.definitions"])
    print("Services started. Press Ctrl+C to exit.")
    try:
        api_proc.wait()
        dash_proc.wait()
        dagster_proc.wait()
    except KeyboardInterrupt:
        print("Shutting down services...")
        api_proc.terminate()
        dash_proc.terminate()
        dagster_proc.terminate()

if __name__ == "__main__":
    main()
