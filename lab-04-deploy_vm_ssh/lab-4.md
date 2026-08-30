# 🔵 Lab 04 — Connect to an Azure VM with SSH & Deploy Apache

## 🎯 Objective

By the end of this lab, you will have:

```text
Your PC
   |
   | SSH :22
   ↓
Azure Linux VM
   |
   | install
   ↓
Apache2
   |
   | HTTP :80
   ↓
Web Browser
```

You will practice **three important things**:

1. Connect to a Linux VM using SSH.
2. Install and manage Apache2.
3. Open HTTP port `80` and access your website from the Internet.

---

# Part 1 — Verify your VM

Go to **Azure Portal → Virtual Machines**.

Select your VM and verify:

* VM status: **Running**
* Operating system: **Ubuntu/Linux**
* Public IP address exists
* SSH is allowed on port `22`

You can also use Azure CLI:

```bash
az vm list \
  --resource-group <RESOURCE_GROUP> \
  --output table
```

You should see something similar to:

```text
Name       Location       Size        PowerState
---------  -------------  ----------  -----------
myVM       ...            Standard...  VM running
```

---

# Part 2 — Get the VM Public IP

Run:

```bash
az vm list-ip-addresses \
  --resource-group <RESOURCE_GROUP> \
  --output table
```

You'll get something like:

```text
VirtualMachine    PublicIPAddresses
----------------  -----------------
myVM              20.x.x.x
```

Copy the public IP.

For the rest of the lab, I'll call it:

```text
<VM_PUBLIC_IP>
```

---

# Part 3 — Connect using SSH

If you created the VM with an SSH key, use:

```bash
ssh azureuser@<VM_PUBLIC_IP>
```

For example:

```bash
ssh azureuser@20.10.20.30
```

The first time, you may see:

```text
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Type:

```text
yes
```

If authentication succeeds, you'll see something similar to:

```text
azureuser@myVM:~$
```

🎉 **You are now inside your Azure VM.**

---

# Part 4 — Understand where you are

Run:

```bash
whoami
```

You should get:

```text
azureuser
```

Check the operating system:

```bash
lsb_release -a
```

Check the kernel:

```bash
uname -a
```

Check your current directory:

```bash
pwd
```

List files:

```bash
ls
```

---

# Part 5 — Update Ubuntu

Before installing Apache:

```bash
sudo apt update
```

Then:

```bash
sudo apt upgrade -y
```

### What happened?

`apt` is Ubuntu's package management system.

```text
apt update
     ↓
Download latest package information
     ↓
apt upgrade
     ↓
Upgrade installed packages
```

---

# Part 6 — Install Apache2

Run:

```bash
sudo apt install apache2 -y
```

Check Apache:

```bash
sudo systemctl status apache2
```

You should see:

```text
Active: active (running)
```

If you see that, Apache is running.

---

# Part 7 — Test Apache locally

Inside the VM, run:

```bash
curl localhost
```

You should receive HTML.

You can also test:

```bash
curl http://127.0.0.1
```

This proves:

```text
VM
 |
 └── Apache
       |
       └── HTTP :80
```

is working.

---

# Part 8 — Understand the problem

At this point Apache is running.

But try opening:

```text
http://<VM_PUBLIC_IP>
```

You might **not** be able to access it yet.

Why?

Because Azure has a **Network Security Group (NSG)** controlling network traffic.

Your VM needs:

```text
Internet
   |
   | TCP :80
   ↓
 NSG
   |
   ↓
 VM
   |
   ↓
Apache
```

We need to allow port `80`.

---

# Part 9 — Open HTTP port 80

You can do this from Azure CLI.

First find the NSG:

```bash
az network nsg list \
  --resource-group <RESOURCE_GROUP> \
  --output table
```

Then create an inbound rule:

```bash
az network nsg rule create \
  --resource-group <RESOURCE_GROUP> \
  --nsg-name <NSG_NAME> \
  --name Allow-HTTP \
  --protocol Tcp \
  --priority 1000 \
  --destination-port-range 80 \
  --access Allow \
  --direction Inbound
```

Check the rule:

```bash
az network nsg rule list \
  --resource-group <RESOURCE_GROUP> \
  --nsg-name <NSG_NAME> \
  --output table
```

You should see something similar to:

```text
Name         Priority    Access    Direction    Port
-----------  ----------  --------  -----------  ----
Allow-HTTP   1000        Allow     Inbound      80
```

---

# Part 10 — Test from your computer

Now open your normal browser and go to:

```text
http://<VM_PUBLIC_IP>
```

You should see the **Apache2 Ubuntu Default Page**.

🎉 Your Azure VM is now a web server.

---

# Part 11 — Replace the Apache page

Let's create our own webpage.

Inside the VM:

```bash
sudo nano /var/www/html/index.html
```

Delete the existing content and put:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Azure VM</title>
</head>
<body>
    <h1>Hello from Azure!</h1>
    <p>This website is running on my Linux VM.</p>
</body>
</html>
```

Save:

```text
CTRL + O
ENTER
CTRL + X
```

Now refresh:

```text
http://<VM_PUBLIC_IP>
```

You should see your new page.

---

# Part 12 — Understand the complete architecture

You have now built this:

```text
                   Internet
                       |
                       | HTTP :80
                       ↓
              ┌─────────────────┐
              │   Public IP     │
              └────────┬────────┘
                       |
                       ↓
              ┌─────────────────┐
              │      NSG        │
              │ Allow TCP :80   │
              └────────┬────────┘
                       |
                       ↓
              ┌─────────────────┐
              │      NIC        │
              └────────┬────────┘
                       |
                       ↓
              ┌─────────────────┐
              │   Linux VM      │
              │                 │
              │    Apache2      │
              │      :80        │
              └─────────────────┘
```

And SSH works separately:

```text
Your PC
   |
   | SSH :22
   ↓
Public IP
   |
   ↓
NSG
   |
   ↓
NIC
   |
   ↓
Linux VM
```

---

# 🧠 What you should understand from Lab 04

Don't just memorize:

```bash
sudo apt install apache2
```

Understand the roles:

| Component       | Purpose                                    |
| --------------- | ------------------------------------------ |
| Public IP       | Gives the VM an Internet-reachable address |
| NIC             | Connects the VM to the network             |
| NSG             | Controls network traffic                   |
| Port 22         | SSH                                        |
| Port 80         | HTTP                                       |
| Ubuntu          | Operating system                           |
| Apache2         | Web server                                 |
| `/var/www/html` | Default website directory                  |
| `systemctl`     | Controls Linux services                    |

The most important concept is:

```text
SSH :22
   ↓
Remote administration

HTTP :80
   ↓
Web traffic
```

---

## 🧪 Lab 04 Challenge

After completing the basic lab, try these yourself **without following the commands above**:

1. Stop Apache.
2. Verify that the website stops working.
3. Start Apache again.
4. Check its status.
5. Change the webpage.
6. Restart Apache.
7. Test the website with `curl`.
8. Remove the HTTP NSG rule.
9. Try accessing the website.
10. Add the rule again.

Useful commands:

```bash
sudo systemctl stop apache2
sudo systemctl start apache2
sudo systemctl restart apache2
sudo systemctl status apache2
curl localhost
```

### 🔥 Final test

Once you finish, you should be able to explain this sentence:

> **"A user connects to my Azure VM through its public IP; the NSG allows TCP port 80; the traffic reaches the VM's NIC, and Apache listens on port 80 and returns the webpage."**

If you can explain that clearly, **Lab 04 is complete**.



### the ssh error and solution 
Absolutely. This is a very good thing to document because the problem teaches an important Azure + SSH concept.

## 1. The objective

We wanted to establish an SSH connection:

```text
Ubuntu PC
    │
    │ SSH
    ▼
Azure VM
Ubuntu 24.04
```

The Azure VM was:

```text
VM name:       first
Username:      azureuser
Public IP:     4.222.218.84
Authentication: SSH public key
Key pair:      first_key
```

---

# 2. How SSH public/private keys work

SSH uses a **key pair**:

```text
              SSH KEY PAIR
             ┌─────────────┐
             │             │
             ▼             ▼
       PRIVATE KEY     PUBLIC KEY
          🔐               🔓
```

The two keys are mathematically related.

### Private key

The private key belongs to the client — in our case, your PC.

```text
first_key.pem
```

It must remain secret.

```text
PC
└── first_key.pem 🔐
```

You **never copy the private key to the Azure VM**.

### Public key

The public key can be shared.

Azure puts the public key on the VM, normally in:

```text
/home/azureuser/.ssh/authorized_keys
```

So:

```text
Azure VM
└── ~/.ssh/authorized_keys
        └── public key 🔓
```

---

# 3. What happened when we created the VM

When creating the Azure VM, we selected:

```text
Authentication type: SSH public key
Username: azureuser
SSH key format: RSA
Key pair name: first_key
```

Azure generated/provisioned an SSH key pair.

We downloaded:

```text
first_key.pem
```

This file is the **private key**.

Azure used the corresponding **public key** during VM creation.

Conceptually:

```text
                first_key
                   │
             ┌─────┴─────┐
             ▼           ▼
       first_key.pem   Public key
          🔐              🔓
           │               │
           │               │
           ▼               ▼
       YOUR PC          AZURE VM
```

---

# 4. Our first mistake

We later generated another key using PuTTYgen:

```text
azure-vm.ppk
```

This was a **new key pair**.

It was not the key pair that Azure installed when the VM was created.

So we had:

```text
Azure VM
└── Public Key A
```

but our PC was trying to authenticate using:

```text
azure-vm.ppk
Private Key B
```

These don't match.

Therefore authentication failed.

---

# 5. The first error

We tried:

```bash
ssh -i azure-vm.ppk first@4.222.218.84
```

and got:

```text
Load key "azure-vm.ppk": error in libcrypto
```

There were actually **two problems to understand**.

### Problem A — Wrong username

We initially tried:

```text
first
```

as the username.

But the VM configuration showed:

```text
Username: azureuser
```

So the correct username was:

```text
azureuser
```

### Problem B — Wrong private key

We used:

```text
azure-vm.ppk
```

But the Azure VM was configured with the key pair:

```text
first_key
```

The correct private key was:

```text
first_key.pem
```

---

# 6. Why `.ppk` caused another problem

`azure-vm.ppk` is a **PuTTY private-key format**.

Linux's normal `ssh` command expects an OpenSSH-compatible private key.

Therefore:

```bash
ssh -i azure-vm.ppk ...
```

produced:

```text
error in libcrypto
```

This is another reason not to use the PuTTY key here.

Since your PC is Ubuntu, the natural solution is to use the `.pem` key Azure already provided.

---

# 7. Finding the correct key

We discovered that you had downloaded:

```text
~/Downloads/first_key.pem
```

This was the important discovery.

It corresponds to the key pair Azure used when creating the VM.

We then protected the private key:

```bash
chmod 600 ~/Downloads/first_key.pem
```

This gives the owner read/write permissions while restricting access from other users.

---

# 8. The correct SSH command

We finally used:

```bash
ssh -i ~/Downloads/first_key.pem azureuser@4.222.218.84
```

Breaking it down:

```text
ssh
 │
 ├── -i ~/Downloads/first_key.pem
 │       │
 │       └── private key 🔐
 │
 └── azureuser@4.222.218.84
         │          │
         │          └── Azure VM public IP
         │
         └── Linux username
```

And it worked.

We received:

```text
Welcome to Ubuntu 24.04.4 LTS
```

That proves SSH authentication succeeded.

---

# 9. What actually happens during SSH authentication?

This is the most important theoretical part.

When you execute:

```bash
ssh -i first_key.pem azureuser@4.222.218.84
```

your PC does **not** send:

```text
first_key.pem
```

to Azure.

Instead, SSH uses cryptography to prove that your PC possesses the private key corresponding to the public key stored on the server.

Conceptually:

```text
              SSH CONNECTION

PC                                      Azure VM
│                                           │
│ Private key 🔐                            │ Public key 🔓
│                                           │
│ ──────── SSH connection ────────────────► │
│                                           │
│     "Prove you own the private key"       │
│ ◄──────────────────────────────────────── │
│                                           │
│ cryptographic proof                      │
│ ─────────────────────────────────────────► │
│                                           │
│           Authentication succeeds         │
│                                           │
└───────────────────────────────────────────┘
```

The private key remains on your PC.

---

# 10. Final architecture

Your working configuration is:

```text
┌─────────────────────────────────────┐
│             YOUR PC                 │
│          Ubuntu / Linux             │
│                                     │
│  ~/Downloads/first_key.pem         │
│             🔐                      │
│        PRIVATE KEY                  │
└──────────────────┬──────────────────┘
                   │
                   │ SSH
                   │
                   ▼
            Internet / Azure
                   │
                   ▼
┌─────────────────────────────────────┐
│            AZURE VM                  │
│              first                   │
│          Ubuntu 24.04               │
│                                     │
│  /home/azureuser/.ssh/              │
│          authorized_keys            │
│              🔓                     │
│          PUBLIC KEY                 │
└─────────────────────────────────────┘
```

### The golden rule

> **Private key stays with the client. Public key goes to the server.**

In our case:

```text
PC:
first_key.pem
     ↓
PRIVATE 🔐

Azure VM:
authorized_keys
     ↓
PUBLIC 🔓
```

---

# 11. Problem → diagnosis → solution

| Problem                           | Cause                                               | Solution                            |
| --------------------------------- | --------------------------------------------------- | ----------------------------------- |
| SSH authentication failed         | Wrong username `first`                              | Use `azureuser`                     |
| `error in libcrypto`              | `.ppk` wasn't appropriate for Linux `ssh`           | Use Azure's `first_key.pem`         |
| New `azure-vm.ppk` didn't work    | Its public key wasn't installed on the VM           | Use the original `first_key.pem`    |
| Concern about sending private key | Misunderstanding of SSH                             | **Never send private key to VM**    |
| SSH finally worked                | Matching private/public key pair + correct username | `ssh -i first_key.pem azureuser@IP` |

## 12. The lesson

The most important thing you learned here isn't the command itself.

It's this mental model:

```text
CREATE VM
    │
    ├── Public key → VM
    │
    └── Private key → Client
                       │
                       ▼
                    SSH
                       │
                       ▼
                  VM verifies
                       │
                       ▼
                   Access ✓
```

Once you understand this, SSH problems become much easier to diagnose:

**1. What username?**
**2. What IP?**
**3. Which public key is installed on the VM?**
**4. Do I have the matching private key?**
**5. Is my private-key format compatible with my SSH client?**




### how i can login in azure cli with azure identity use the browser/device authentication flow.

Yes — that's possible. If your Azure account is associated with your **GitHub account**, you can sign in to Azure CLI using the same GitHub-linked Microsoft/Azure identity.

But there's an important distinction:

```text
GitHub account
     │
     │ "Sign in with GitHub"
     ▼
Microsoft/Azure identity
     │
     ▼
Azure CLI
     │
     ▼
Your Azure subscription
```

### If `az login` is asking for a password

If you normally access Azure through:

**"Sign in with GitHub"**

you generally **shouldn't enter your GitHub password into an Azure CLI password prompt**.

Instead, use the browser/device authentication flow.

Run:

```bash
az login --use-device-code
```

You should get something like:

```text
To sign in, use a web browser to open the page:

https://microsoft.com/devicelogin

Enter the code:
XXXXXXXXX
```

Open that page in your browser and complete the login using your **GitHub-linked Azure account**.

### After login

Check that Azure CLI sees your subscription:

```bash
az account show
```

You should see information such as:

```text
"name": "Azure subscription 1"
"isDefault": true
```

Then you can run your VM command again:

```bash
az vm show \
  --resource-group amine_machine \
  --name first \
  --query osProfile.linuxConfiguration.adminUsername \
  -o tsv
```

You already know the answer is `azureuser`, but this is a good exercise because you're learning how Azure CLI authenticates and accesses your subscription.


