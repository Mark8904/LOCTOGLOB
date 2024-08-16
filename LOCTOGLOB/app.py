from flask import Flask, render_template, request
import subprocess
import threading
import time
import re

app = Flask(__name__)

# Function to run Serveo and capture the public URL
def run_serveo(localhost_port, result):
    serveo_command = (
        f"ssh -o StrictHostKeyChecking=no "
        f"-o UserKnownHostsFile=/dev/null "
        f"-R 80:localhost:{localhost_port} serveo.net"
    )
    process = subprocess.Popen(serveo_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    public_url = None
    timeout = time.time() + 15  # 15 seconds timeout

    while not public_url and time.time() < timeout:
        output = process.stdout.readline()
        if output:
            # Remove ANSI escape sequences and extract the URL
            cleaned_output = re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', output)
            match = re.search(r'https://[^\s]+.serveo.net', cleaned_output)
            if match:
                public_url = match.group(0)
                result['public_url'] = public_url
                break

        time.sleep(1)  # Wait a bit before checking again

    if not public_url:
        result['error'] = "Could not retrieve the public URL. Please try again."

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        localhost_url = request.form['localhost_url']
        localhost_port = localhost_url.split(':')[-1]
        
        result = {}
        # Run Serveo in a background thread and capture the result
        thread = threading.Thread(target=run_serveo, args=(localhost_port, result))
        thread.start()
        thread.join()  # Wait for the Serveo process to finish

        if 'public_url' in result:
            return render_template('index.html', public_url=result['public_url'])
        else:
            return render_template('index.html', error=result['error'])
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

