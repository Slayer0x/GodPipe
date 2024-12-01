# 🥷🏽 Welcome to GodPipe

<p align="center">
    <img src="https://github.com/user-attachments/assets/720816d6-63c3-4373-a600-f997096379f1" alt="GodPipe Scapy">
</p>


📚 A tor based data exfiltration tool.

Godpipe simplifies the deployment and usage of tor to perform data exfiltration exercises, useful for red teamers that may want to test the security of their target by using realistic exfiltration methods.

All the infrastructure runs on your side, no need for third party proxy providers or similar, what allows maintaining confidentiality.

## 📖 Requirements

    1. A VPS with Ubuntu Server with at least 4GB of RAM 

    2. Unlimited data transmission plan. ( You will be needing to recieve the exfiltrated files + Tor traffic )

## 🛠️ Setup & Ussage

We are going to be covering the GodPipe depoyment and ussage.

### 🧅 Tor Relay Automated Setup
On your Ubuntu server installation, clone the GodPipe repository and install the Requierements.txt.

```
sudo apt install git -y & sudo apt install pip -y
git clone https://github.com/Slayer0x/GodPipe.git
sudo pip install -r Requirements.txt
```
Execute the `relay_setup.sh` scrip, this will automate the installation of the tor middle / guard, during the installation, you will be asked to provide the following information:
```
# Nickname
How your tor relay will be named
# ContactInfo
A contact email address to advertise with your relay. (You can use a fake one, we need this to get tor network trust as fast as possible)
# ORPort
The port that your relay will use to handle tor circuits. (Enable acess to this port on your VPS firewall)
# Password
A password to access the monitoring software. (nyx)
```

Once the installation completes, you should be able to use nyx to check the status of your relay:
```
nyx
# Will ask you to enter the password you configured during the installation
```
You now need to wait until it gets validated.<br>
The relay will gain more trust the longer it operates without interruptions, this will grant the capability to handle more traffic on the Tor network.

### 🤖 GodPipe Server Setup

Once the relay is operational, we can continue with the GodPipe Server setup, execute the `godpipe_server.py` python script as root, you will be asked to provide the following information:

```
sudo python3 godpipe_server.py

# Hidden Service / GodPipe Server Port
```

This port is the one used by the GodPipe Server to handle the file transfer process with the agents, don´t use the same as the Tor relay ORPort, this port doesn´t need to be open in your firewall, will act as a proxy to your local host. 

Godpipe will generate the TLS certificates and modify your relay configuration so you don´t need to do nothing.

If everything goes as intended, you will be prompted with your tor address as a result ( We can stop the server at this point by CTL + C ).

<p align="center">
    <img src="https://github.com/user-attachments/assets/84849b16-0eb6-401b-b3b6-c129022439fb" alt="Banner Scapy">
</p>

### 🧰 Generate Agents

We are ready to generate our first agent, agent´s will connect to GodPipe Server ussing tor network to transfer the files pre-configured.

Execute the `agent_generator.py` script ( No need to have the  GodPipe Server running ), is important to execute this script on the same VPS as it needs to grab the configuration of your relay and certificates.

```
sudo python3 agent_generator.py
```
The following options are currently supported for file exfiltration:

<p align="center">
    <img src="https://github.com/user-attachments/assets/054910d5-4c04-4ffb-b258-aec591d7baa2" alt="Menu Options">
</p>

Choose the one that fit´s better for your use case, remember that this is an exfiltration tool, so you should already know the path of the file you want to exfiltrate.

Your agent will be generated based on your target OS at the `Agents` directory.

```
ls Agents/

    godpipe_agent.py
    tor_widows
    Requirements.txt

# You can use SCP or any method you want to copy all the content.

scp -r user@IP:GodPipe/Agents/* Agent
```

### 👽 Pack and deliver your agents

Copy all the content from the `Agents`  directory and transfer it to a virtual machine that shares the same architecture and OS as your final target, once there, install python and the `Requirements.txt`:

```
# In case of Windows is your target (Execute this on a VM/Windows host).
# Same steps apply for Linux targets.

C:> cd Agent

C:\Agent> pip install -r Requirements.txt
```
Finally, pack the agent with the tor binary:
```
# Check for pyinstaller.exe on your file system.
# Usually located at C:\Users\YOURUSER\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.<version>\LocalCache\local-packages\Python312\Scripts

C:\Agent> pyinstaller.exe --onefile --noconsole --add-data "tor_windows;tor" godpipe_agent.py
```
As a result, you will get the `.exe` executable in the `/dist` directory, you can transfer this binary to your target and execute it (Remember to start GodPipe Server).

The agent will automatically connect to your server and start the file transfer (Takes a little bit), all the transferred files will be available on your GodPipe Server at `/Output`.

<p align="center">
    <img src="https://github.com/user-attachments/assets/79533f02-af1a-4eaa-8727-da6a6906acdb" alt="Files exfiltrated">
</p>

## 😎 Create custom Agents

In the current version of GodPipe, the agents are generated dynamically on the fly, you may want to create custom agents with different behaviour or new functionalities, that´s why I'm leaving 2 static agent templates at `/Templates` for you.

## 🙋‍♂️ Pull Request

Feel free to pull request in my repo.
