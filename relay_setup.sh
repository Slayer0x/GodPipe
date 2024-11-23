#!/bin/bash

RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
RESET="\e[0m"

trap 'echo -e "${RED}\n [!]Exiting...${RESET}"; exit 1' SIGINT

if [[ $EUID -ne 0 ]]; then
  echo -e "${RED}\n[X] This script must be run as root. Exiting.${RESET}"
  exit 1
fi

echo -e "${YELLOW}\n[+] Updating & Enabling automatic updates\n${RESET}"
#Updating
apt update -y && apt full-upgrade -y

#Enable automatic software updates
apt-get install unattended-upgrades apt-listchanges -y 

cat <<EOF > /etc/apt/apt.conf.d/50unattended-upgrades
    Unattended-Upgrade::Allowed-Origins {
        "${distro_id}:${distro_codename}-security";
        "TorProject:${distro_codename}";
    };
    Unattended-Upgrade::Package-Blacklist {
    };
    Unattended-Upgrade::Automatic-Reboot "true";
EOF

cat <<EOF > /etc/apt/apt.conf.d/20auto-upgrades
    APT::Periodic::Update-Package-Lists "1";
    APT::Periodic::AutocleanInterval "5";
    APT::Periodic::Unattended-Upgrade "1";
    APT::Periodic::Verbose "1";
EOF

unattended-upgrade --debug

echo -e "${YELLOW}\n[+] Configuring tor project repository\n${RESET}"

#Configure tor project repository
apt install apt-transport-https
codename=$(lsb_release -c | awk '{print $2}')

cat <<EOF > /etc/apt/sources.list.d/tor.list
    deb     [signed-by=/usr/share/keyrings/deb.torproject.org-keyring.gpg] https://deb.torproject.org/torproject.org $codename main
    deb-src [signed-by=/usr/share/keyrings/deb.torproject.org-keyring.gpg] https://deb.torproject.org/torproject.org $codename main
EOF

wget -qO- https://deb.torproject.org/torproject.org/A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89.asc | gpg --dearmor | tee /usr/share/keyrings/deb.torproject.org-keyring.gpg >/dev/null

echo -e "${YELLOW}\n[+] Installing tor and nyx\n${RESET}"

#Install tor, tor debian keyring and nyx
apt update
apt install tor deb.torproject.org-keyring nyx -y

#Configure tor relay
echo -e "${YELLOW}\n[+] Configuring Relay\n${RESET}"

while [[ -z $nickname ]]; do
  read -p "[?] Enter a Nickname for your relay: " nickname
done

while [[ -z $contact ]]; do
  read -p "[?] Enter a contact email for your relay: " contact
done

while [[ -z $ORPort ]]; do
  read -p "[?] Enter the desired port to advertise for incoming Tor connections: " ORPort
done

while [[ -z $password ]]; do
  read -p "[?] Enter a password to access nyx: " password
done
sleep 3
hashed_password=$(tor --hash-password $password | grep -o '16.*')

cat <<EOF > /etc/tor/torrc
    Nickname $nickname
    ContactInfo $contact
    ORPort $ORPort IPv4Only
    ExitRelay 0
    SocksPort 0
    ControlPort 9051
    HashedControlPassword $hashed_password
EOF

#Restart tor service
systemctl restart tor@default

echo -e "${GREEN}\n[V] Relay installation completed successfully\n"
echo -e "${GREEN}\n[i] Remember to enable TCP/UDP access over the port $ORPort in your firewall${RESET}"