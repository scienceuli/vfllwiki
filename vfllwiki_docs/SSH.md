---
kind: reference
---
# SSH

SSH (Secure Shell) ist ein Netzwerkprotokoll, das eine sichere, verschlüsselte Verbindung zwischen zwei Computern ermöglicht.

### What Exactly Is SSH?

SSH stands for Secure Shell, which, in plain English, is a "secure remote connection protocol." Think back to the days before SSH - people used telnet, where all data, including your password, was transmitted in plain text. Grab any packet sniffer, and your password would be exposed on the wire.

With SSH, all communication is encrypted. An intermediary trying to snoop? No chance.

The client and server sides of SSH are:

- **Client**: `ssh` (OpenSSH-client)
- **Server**: `sshd` (OpenSSH-server)

### Detailed Breakdown of SSH Configuration Files

There are two main SSH configuration files - don’t mix them up:

- **Client configuration**: `~/.ssh/config`
- **Server configuration**: `/etc/ssh/sshd_config`

Let’s start with the key parameters on the server side, which determine what your SSH service looks like:

- **Port 22** — Listening port. Honestly, changing the port is the most basic security measure. Switch it to something like 2222, and you’ll block the majority of script kiddies.
- **PermitRootLogin yes/no/prohibit-password** — Whether to allow root login. Strongly recommended to set to `no` or `prohibit-password`. The risk of brute-forcing the root password is too high.
- **PasswordAuthentication yes/no** — Toggle for password login. Once you switch to key-based login, decisively set this to `no` to completely disable password authentication.
- **PubkeyAuthentication yes** — Toggle for key authentication. This must be enabled.
- **MaxAuthTries 6** — Maximum number of authentication attempts. Setting it to 3 is enough; anything more is just wasteful.
- **LoginGraceTime 120** — Login timeout in seconds. If authentication isn’t completed within this time, the connection is dropped.
- **ClientAliveInterval 300** — The server sends a heartbeat packet to the client every 300 seconds to prevent disconnection.
- **ClientAliveCountMax 3** — If the heartbeat packet goes unanswered 3 times in a row, the client is kicked off.
- **AllowUsers user1 user2** — Whitelist: only allows specified users to log in. This works great in combination with `DenyUsers`.

### Passwordless SSH Login (Key-Based Login)

Typing a password every time you connect to a server? That’s way too annoying. The principle behind passwordless login is quite simple: asymmetric encryption. You generate a pair of keys locally—a public key and a private key. Put the public key on the server and keep the private key to yourself. When connecting, the server verifies your identity using the public key. If it matches, you’re in.

Here are the specific steps, summarized in three lines:

- **Step one: Generate the key pair:**

ssh-keygen -t ed25519 -C "your_email@example.com"

It’s recommended to use the `ed25519` algorithm here - it’s faster and more secure than RSA. Just press Enter all the way through. You can also add a passphrase for protection (though that wouldn’t be completely "passwordless").

- **Step two: Send the public key to the server:**

ssh-copy-id user@remote-server

This step requires entering the password once, after which the public key is automatically added to the server's `~/.ssh/authorized_keys`.

- **Step three: Direct Connection:**

ssh user@remote-server

Done, no more password needed.

Press enter or click to view image in full size

![](https://miro.medium.com/v2/resize:fit:1400/1*clIOLQEb1K0lD54CfAAm4Q.png)

Here’s another tip for client configuration. Edit `~/.ssh/config` to give the server an alias:

Host myserver  
    HostName 192.168.1.100  
    User root  
    Port 2222  
    IdentityFile ~/.ssh/id_ed25519

Once configured, you only need to type `ssh myserver` to connect. How satisfying is that?

### SSH Port Forwarding (Detailed Explanation of Three Types)

When it comes to port forwarding, many people have heard of it, but few truly understand it. Honestly, this feature is where SSH is most "magical." It allows you to bridge various network islands and achieve connections that seem impossible.

**Local Forwarding (-L)**

Here’s the scenario: You have a local machine A, a remote server B, and behind B is a database server C (C can only be accessed by B). You want to directly access C’s database from A. What do you do?

Local forwarding solves this problem. The principle is: open a local port on A, and all data sent to this port will be forwarded to C through the SSH tunnel.

ssh -L [local_port]:[target_host]:[target_port] user@jump_host

Here’s a practical example:

ssh -L 3307:localhost:3306 dbadmin@remote-server

This command means: open port 3307 on your local machine, and all requests to port 3307 will be forwarded to port 3306 on remote-server. When you connect to 127.0.0.1:3307 with a MySQL client locally, you’re actually connecting to the remote server’s MySQL.

Another example: you want to access a web management interface on an internal network:

ssh -L 8080:10.0.0.5:80 jump@bastion-host

Open your browser and visit localhost:8080—you’ll see the web page from the internal machine 10.0.0.5. The entire connection is encrypted, so no one can see it.

Press enter or click to view image in full size

![](https://miro.medium.com/v2/resize:fit:1400/1*Pmx6H1B99GheFg_ACRGYAQ.png)

**Remote Forwarding (-R)**

Local forwarding "brings remote services to the local machine," while remote forwarding does the opposite - "pushes local services to the remote machine."

When would you need this? Imagine you have a NAS or a test server at home, but you can’t access it from outside your home network (no public IP). By setting up remote forwarding on a company server with a public IP, you can access your home services from work.

ssh -R [remote_port]:[local_host]:[local_port] user@public_server

Here’s the specific operation:

ssh -R 9090:localhost:8080 user@public-server

After running this command, anyone accessing public-server:9090 will actually be accessing your local port 8080.

One pitfall to note: by default, the remote forwarding port is only bound to localhost on the remote server, so it’s not accessible from outside. To allow other machines to access it, you need to add the following to the server’s `sshd_config`:

GatewayPorts yes

**Dynamic Forwarding (-D)**

Dynamic forwarding is the slickest of the three. It turns your local machine into a SOCKS5 proxy server, so all traffic going through this proxy exits via the SSH server.

ssh -D [local proxy port] user@remote-server

Practical example:

ssh -D 1080 user@remote-server

Once connected, you’ll have a SOCKS5 proxy running locally at 127.0.0.1:1080. Set your browser to use this proxy, and all your web browsing traffic will go through the remote server.

What’s the difference from local forwarding? Local forwarding requires you to specify a specific target host and port - it’s a one-to-one custom setup. Dynamic forwarding doesn’t need a target; it’s a universal SOCKS proxy that lets you access any remote service. Think of local forwarding as a dedicated line, and dynamic forwarding as a master key.

**Summary of the three forwarding types:**

- **-L Local forwarding**: Pulls a remote service to your local machine—connecting to your local port equals connecting to the remote service.
- **-R Remote forwarding**: Pushes a local service to a remote machine—others connecting to the remote port equals connecting to your service.
- **-D Dynamic forwarding**: Opens a SOCKS5 proxy locally for universal forwarding.