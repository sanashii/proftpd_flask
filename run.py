#!/usr/bin/env python
import argparse
import subprocess
import sys
import os
from datetime import datetime

def run_app(app_name, port):
    """Run the specified application."""
    print(f"\n{'='*50}")
    print(f"Starting {app_name} on port {port}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    try:
        if app_name == 'admin':
            subprocess.run(['python', 'proftpd_admin_app/app.py'], check=True)
        elif app_name == 'sftp':
            subprocess.run(['python', 'proftpd_sftp_app/app.py'], check=True)
        else:
            print(f"Error: Unknown application '{app_name}'")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running {app_name}: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\nStopping {app_name}...")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Run ProFTPd Admin or SFTP applications')
    parser.add_argument('app', choices=['admin', 'sftp'], help='Application to run (admin or sftp)')
    parser.add_argument('--port', type=int, help='Port to run the application on (default: 5000 for admin, 5001 for sftp)')
    
    args = parser.parse_args()
    
    # Set default ports if not specified
    if not args.port:
        args.port = 5000 if args.app == 'admin' else 5001
    
    # Set environment variable for port
    os.environ['FLASK_RUN_PORT'] = str(args.port)
    
    run_app(args.app, args.port)

if __name__ == '__main__':
    main() 