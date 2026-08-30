Yes. We can move to **Lab 07**. We'll skip Lab 06 for now and come back to it if needed.

# 🌐 Lab 07 — Public & Private IPs, NICs and NSGs

## 🎯 Goal

By the end of this lab, you should understand how an Azure VM connects to a network:

```text
                    Internet
                       │
                       │
                  Public IP
                       │
                       ↓
                     NIC
                       │
                       ↓
                 Private IP
                       │
                       ↓
                    Azure VM
                       │
                    Ubuntu
```

And how an **NSG** controls the traffic:

```text
Internet
   │
   │ TCP :22
   ↓
  NSG ──── Allow/Deny
   │
   ↓
  NIC
   │
   ↓
  VM
```

---

# Part 1 — Public IP vs Private IP

Your VM can have two important IP addresses.

### 🌍 Public IP

A public IP allows communication between the VM and the Internet.

Example:

```text
20.x.x.x
```

You might use it for:

```bash
ssh azureuser@20.x.x.x
```

or:

```text
http://20.x.x.x
```

### 🔒 Private IP

The VM also has a private IP inside its VNet.

Example:

```text
10.0.1.4
```

This is used for communication inside Azure's private network.

For example:

```text
VM1
10.0.1.4
   │
   │ private network
   ↓
VM2
10.0.2.4
```

---

# Part 2 — Find Your VM's IPs

Run:

```bash
az vm list-ip-addresses \
  --resource-group <RESOURCE_GROUP> \
  --name <VM_NAME> \
  --output table
```

You'll see something similar to:

```text
VirtualMachine    PrivateIPAddresses    PublicIPAddresses
----------------  --------------------  -----------------
myVM              10.0.1.4              20.x.x.x
```

So remember:

```text
Public IP  → Internet
Private IP → Internal Azure network
```

---

# Part 3 — What is a NIC?

**NIC = Network Interface Card**

In Azure, a VM doesn't directly connect to the VNet.

Instead:

```text
VM
 │
 ↓
NIC
 │
 ↓
Subnet
 │
 ↓
VNet
```

The NIC is the network interface attached to your VM.

It can contain/configure things such as:

* Private IP
* Public IP association
* NSG association
* Subnet association
* IP configurations

---

# Part 4 — Find Your NIC

Run:

```bash
az vm show \
  --resource-group <RESOURCE_GROUP> \
  --name <VM_NAME> \
  --query "networkProfile.networkInterfaces[].id" \
  --output tsv
```

You'll get something like:

```text
/subscriptions/.../resourceGroups/.../providers/Microsoft.Network/networkInterfaces/myVM-nic
```

Now retrieve the NIC:

```bash
az network nic show \
  --resource-group <RESOURCE_GROUP> \
  --name <NIC_NAME> \
  --output json
```

Look for:

```text
ipConfigurations
```

You should find the private IP and subnet information.

---

# Part 5 — What is an NSG?

**NSG = Network Security Group**

An NSG is essentially a collection of network traffic rules.

For example:

```text
Allow SSH :22
Allow HTTP :80
Deny everything else
```

Conceptually:

```text
                 NSG
                  │
       ┌──────────┼──────────┐
       ↓          ↓          ↓
    TCP 22     TCP 80    TCP 443
     Allow       Allow      Allow
```

NSGs can control inbound and outbound traffic.

---

# Part 6 — Find Your NSG

Run:

```bash
az network nsg list \
  --resource-group <RESOURCE_GROUP> \
  --output table
```

You'll see something like:

```text
Name             Location
---------------  ------------
myVM-nsg         westeurope
```

---

# Part 7 — Look at NSG Rules

Run:

```bash
az network nsg rule list \
  --resource-group <RESOURCE_GROUP> \
  --nsg-name <NSG_NAME> \
  --output table
```

You might see:

```text
Name          Priority    Direction    Access    Protocol    Port
------------  ----------  -----------  --------  ----------  ----
AllowSSH      1000        Inbound      Allow     Tcp         22
AllowHTTP     1010        Inbound      Allow     Tcp         80
```

---

# Part 8 — Understand Priority

NSG rules have priorities.

For example:

```text
Priority 100
Priority 200
Priority 300
```

**Lower number = higher priority.**

So:

```text
100 → evaluated first
200 → evaluated second
300 → evaluated third
```

This matters when rules conflict.

For example:

```text
Priority 100
Allow TCP 80

Priority 200
Deny TCP 80
```

The `Allow` rule wins because it has the higher priority.

---

# Part 9 — Create an NSG Rule

Let's create a rule allowing HTTP.

```bash
az network nsg rule create \
  --resource-group <RESOURCE_GROUP> \
  --nsg-name <NSG_NAME> \
  --name AllowHTTP \
  --priority 1000 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --destination-port-range 80
```

Check it:

```bash
az network nsg rule list \
  --resource-group <RESOURCE_GROUP> \
  --nsg-name <NSG_NAME> \
  --output table
```

---

# Part 10 — SSH vs HTTP

You should now understand why your Lab 04 required two different ports.

### SSH

```text
TCP 22
```

Used by:

```bash
ssh azureuser@<PUBLIC_IP>
```

Purpose:

> Administration of the VM.

### HTTP

```text
TCP 80
```

Used by:

```text
http://<PUBLIC_IP>
```

Purpose:

> Web traffic.

So:

```text
                 VM
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
     TCP :22             TCP :80
        ↓                   ↓
       SSH                Apache
```

---

# Part 11 — Test Your NSG

This is the interesting part of the lab.

First make sure Apache is running:

```bash
sudo systemctl status apache2
```

Then from your computer:

```bash
curl http://<VM_PUBLIC_IP>
```

You should receive your webpage.

Now remove the HTTP rule:

```bash
az network nsg rule delete \
  --resource-group <RESOURCE_GROUP> \
  --nsg-name <NSG_NAME> \
  --name AllowHTTP
```

Try again:

```bash
curl http://<VM_PUBLIC_IP>
```

It should no longer be reachable through HTTP.

Then recreate the rule:

```bash
az network nsg rule create \
  --resource-group <RESOURCE_GROUP> \
  --nsg-name <NSG_NAME> \
  --name AllowHTTP \
  --priority 1000 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --destination-port-range 80
```

Test again:

```bash
curl http://<VM_PUBLIC_IP>
```

This demonstrates the role of the NSG.

---

# 🧠 The most important concept

Don't think:

> "NSG is a firewall."

That's useful as a first approximation, but understand the architecture more precisely:

```text
Internet
    │
    ↓
Public IP
    │
    ↓
NIC
    │
    ↓
NSG rules
    │
    ↓
Private IP
    │
    ↓
VM
```

The NSG determines whether network traffic is allowed according to its rules.

---


## 🏁 Lab 07 Architecture

You should now be able to explain:

```text
                      Internet
                         │
                  Public IP
                         │
                         ↓
                  ┌─────────────┐
                  │     NSG     │
                  │             │
                  │ :22 Allow   │
                  │ :80 Allow   │
                  └──────┬──────┘
                         │
                         ↓
                       NIC
                         │
                  Private IP
                    10.0.1.4
                         │
                         ↓
                    Azure VM
                   Ubuntu Linux
                    /       \
                   /         \
                SSH          Apache
                :22           :80
```
