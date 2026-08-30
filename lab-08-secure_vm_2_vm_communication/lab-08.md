# 🌐 Lab 08 — Secure and Test VM-to-VM Communication

Now we move from **one VM communicating with the Internet** to **multiple VMs communicating privately inside Azure**.

## 🎯 Objective

We'll build:

```text
                    Internet
                       |
                       ↓
                    VM-Web
                 Private IP
                       |
                       | HTTP
                       ↓
                    VM-App
                 Private IP
```

The important idea is:

> **VM-to-VM communication should normally use private IP addresses, not public IPs.**

---

# Part 1 — Architecture

We'll create two Linux VMs:

```text
┌──────────────────────────── Azure VNet ────────────────────────────┐
│                                                                    │
│   Web Subnet                         App Subnet                    │
│   10.0.1.0/24                        10.0.2.0/24                  │
│                                                                    │
│   ┌──────────────┐                   ┌──────────────┐              │
│   │    VM-Web    │                   │    VM-App    │              │
│   │ 10.0.1.4     │ ─── HTTP :80 ───→ │ 10.0.2.4     │              │
│   └──────────────┘                   └──────────────┘              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

We'll use the existing VM from previous labs as **VM-Web** and create **VM-App**.

---

# Part 2 — Create a VNet

If you already have a VNet from Lab 06, you can use it.

Otherwise:

```bash
az network vnet create \
  --resource-group <RESOURCE_GROUP> \
  --name lab08-vnet \
  --location <REGION> \
  --address-prefix 10.0.0.0/16 \
  --subnet-name web-subnet \
  --subnet-prefix 10.0.1.0/24
```

You now have:

```text
10.0.0.0/16
      |
      └── web-subnet
          10.0.1.0/24
```

---

# Part 3 — Create the App Subnet

```bash
az network vnet subnet create \
  --resource-group <RESOURCE_GROUP> \
  --vnet-name lab08-vnet \
  --name app-subnet \
  --address-prefix 10.0.2.0/24
```

Now:

```text
VNet: 10.0.0.0/16
│
├── Web subnet
│   └── 10.0.1.0/24
│
└── App subnet
    └── 10.0.2.0/24
```

---

# Part 4 — Create VM-App

We'll create the second Ubuntu VM.

```bash
az vm create \
  --resource-group <RESOURCE_GROUP> \
  --name VM-App \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --ssh-key-values ~/.ssh/id_rsa.pub \
  --vnet-name lab08-vnet \
  --subnet app-subnet \
  --public-ip-address ""
```

### Important

We're intentionally not giving the App VM a public IP.

That's a good security practice.

Our architecture becomes:

```text
Internet
   |
   ↓
VM-Web
Public IP
   |
   | Private network
   ↓
VM-App
NO Public IP
```

---

# Part 5 — Find VM-App's Private IP

Run:

```bash
az vm list-ip-addresses \
  --resource-group <RESOURCE_GROUP> \
  --name VM-App \
  --output table
```

You should see something like:

```text
VirtualMachine    PrivateIPAddresses
----------------  ------------------
VM-App            10.0.2.4
```

Save this IP:

```text
VM_APP_PRIVATE_IP=10.0.2.4
```

Your actual address may be different.

---

# Part 6 — Configure VM-App

Because VM-App has no public IP, you can't directly SSH into it from the Internet.

Instead, we'll connect through VM-Web.

First SSH into VM-Web:

```bash
ssh azureuser@<VM_WEB_PUBLIC_IP>
```

Then from VM-Web:

```bash
ssh azureuser@<VM_APP_PRIVATE_IP>
```

For example:

```bash
ssh azureuser@10.0.2.4
```

If your SSH key is not available inside VM-Web, don't worry—we'll use another method later. The important concept here is:

```text
Your PC
   |
   | SSH
   ↓
VM-Web
   |
   | SSH through private network
   ↓
VM-App
```

This is called a **jump/bastion-style access pattern**.

---

# Part 7 — Install Apache on VM-App

Once you're inside VM-App:

```bash
sudo apt update
```

Then:

```bash
sudo apt install apache2 -y
```

Check:

```bash
sudo systemctl status apache2
```

You want:

```text
Active: active (running)
```

---

# Part 8 — Create an App Server Page

Edit:

```bash
sudo nano /var/www/html/index.html
```

Put:

```html
<!DOCTYPE html>
<html>
<head>
    <title>VM App</title>
</head>
<body>
    <h1>Hello from VM-App!</h1>
    <p>This response came through the Azure private network.</p>
</body>
</html>
```

Save with:

```text
CTRL + O
ENTER
CTRL + X
```

---

# Part 9 — Test Locally

On VM-App:

```bash
curl localhost
```

You should see:

```text
Hello from VM-App!
```

Apache works.

Now we need to test **VM-Web → VM-App**.

---

# Part 10 — Test VM-to-VM Communication

Exit from VM-App:

```bash
exit
```

You're back on VM-Web.

Run:

```bash
curl http://10.0.2.4
```

Replace `10.0.2.4` with your actual VM-App private IP.

You should receive:

```text
Hello from VM-App!
```

🎉

You've just demonstrated:

```text
VM-Web
  |
  | TCP :80
  ↓
VM-App
```

without using the Internet.

---

# Part 11 — Secure the Communication with an NSG

Now we'll make the security more realistic.

We want:

```text
VM-Web ────→ VM-App :80
```

But we don't want:

```text
Internet ────→ VM-App :80
```

Create an NSG for the App subnet:

```bash
az network nsg create \
  --resource-group <RESOURCE_GROUP> \
  --name app-nsg \
  --location <REGION>
```

---

# Part 12 — Allow HTTP Only from the Web Subnet

Create:

```bash
az network nsg rule create \
  --resource-group <RESOURCE_GROUP> \
  --nsg-name app-nsg \
  --name Allow-Web-Subnet-HTTP \
  --priority 100 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes 10.0.1.0/24 \
  --destination-port-ranges 80
```

This means:

```text
Source:
10.0.1.0/24

Destination:
VM-App

Port:
80

Action:
ALLOW
```

So:

```text
VM-Web
10.0.1.4
   |
   | TCP 80
   | ALLOWED
   ↓
VM-App
10.0.2.4
```

---

# Part 13 — Associate the NSG with the App Subnet

```bash
az network vnet subnet update \
  --resource-group <RESOURCE_GROUP> \
  --vnet-name lab08-vnet \
  --name app-subnet \
  --network-security-group app-nsg
```

Now the App subnet is protected.

---

# Part 14 — Test Again

From VM-Web:

```bash
curl http://10.0.2.4
```

You should still get:

```text
Hello from VM-App!
```

Why?

Because:

```text
VM-Web
10.0.1.x
   |
   | TCP :80
   ↓
NSG
   |
   | Source = 10.0.1.0/24
   | ALLOW
   ↓
VM-App
10.0.2.x
```

---

# Part 15 — Test the Security

Now imagine another machine outside the Web subnet tries:

```text
Internet → VM-App :80
```

It should be blocked because our rule only allows:

```text
10.0.1.0/24
```

This demonstrates a very important security principle:

> **Allow only the traffic that is actually required.**

Instead of:

```text
ANY → VM-App :80
```

we have:

```text
Web Subnet → VM-App :80
```

Much better.

---

# 🧠 Part 16 — Why Private IP?

Suppose:

```text
VM-Web
Public IP: 20.x.x.x
Private IP: 10.0.1.4

VM-App
Private IP: 10.0.2.4
```

For VM-Web → VM-App, use:

```text
10.0.2.4
```

not:

```text
20.x.x.x
```

because the communication is internal to the VNet.

Think:

```text
Public IP
    ↓
External communication

Private IP
    ↓
Internal communication
```

---

# 🔥 Part 17 — Troubleshooting Exercise

This is the most valuable part of the lab.

On VM-App:

```bash
sudo systemctl stop apache2
```

From VM-Web:

```bash
curl http://10.0.2.4
```

It fails.

Is the NSG necessarily the problem?

**No.**

Check:

```bash
sudo systemctl status apache2
```

You'll discover Apache is stopped.

Start it:

```bash
sudo systemctl start apache2
```

Then:

```bash
curl http://10.0.2.4
```

It works again.

---

# 🧩 The troubleshooting model

When VM-to-VM communication fails, don't immediately blame the NSG.

Check systematically:

```text
1. Is VM running?
       ↓
2. Is the private IP correct?
       ↓
3. Is the application running?
       ↓
4. Is the application listening on the expected port?
       ↓
5. Is the NSG allowing traffic?
       ↓
6. Is the subnet correct?
       ↓
7. Is routing correct?
```

Useful commands:

```bash
ip addr
```

```bash
ss -tulpn
```

```bash
curl <PRIVATE_IP>
```

```bash
sudo systemctl status apache2
```

And from Azure:

```bash
az network nsg rule list \
  --resource-group <RESOURCE_GROUP> \
  --nsg-name app-nsg \
  --output table
```

---

# 🏆 Lab 08 Final Architecture

You should now understand this architecture:

```text
                         Internet
                            |
                            |
                     Public IP :22/:80
                            |
                            ↓
                    ┌──────────────┐
                    │    VM-Web    │
                    │ 10.0.1.x     │
                    └──────┬───────┘
                           |
                           | Private HTTP :80
                           ↓
                 ┌─────────────────────┐
                 │       App NSG        │
                 │                     │
                 │ Web subnet → :80    │
                 │       ALLOW         │
                 └──────────┬──────────┘
                            |
                            ↓
                    ┌──────────────┐
                    │    VM-App    │
                    │ 10.0.2.x     │
                    │              │
                    │   Apache     │
                    └──────────────┘
```

## ✅ Lab 08 checklist

* [ ] Create/use a VNet
* [ ] Create Web and App subnets
* [ ] Create a second VM
* [ ] Give App VM only a private IP
* [ ] Install Apache on App VM
* [ ] Test `VM-Web → VM-App`
* [ ] Use private IP communication
* [ ] Create an App NSG
* [ ] Allow HTTP only from the Web subnet
* [ ] Test the NSG
* [ ] Stop Apache and troubleshoot the failure
* [ ] Explain **Public IP vs Private IP vs NIC vs NSG**

### 🔑 Core lesson

The key idea from Lab 08 is:

> **A secure Azure architecture doesn't expose every VM to the Internet. Internal services should communicate through private networking, while NSGs restrict which internal traffic is allowed.**

Next in your roadmap is **Lab 09 — Build a Load-Balanced Application with Azure Load Balancer**, where we'll take the idea of multiple VMs and put a **Load Balancer in front of them**.
