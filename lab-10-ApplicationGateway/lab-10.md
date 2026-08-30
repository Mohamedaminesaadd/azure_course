# 🌐 Lab 10 — HTTP Routing with Azure Application Gateway

Yes. Now we move from **Layer 4 Load Balancer** to **Layer 7 Application Gateway**.

This lab is important because you'll see **why Application Gateway is different from the Load Balancer you just built**.

---

# 🎯 What we're going to build

We'll create:

```text
                         Internet
                            |
                            | HTTP :80
                            ↓
                 ┌────────────────────┐
                 │ Application Gateway │
                 │                    │
                 │ Frontend :80       │
                 │ Listener           │
                 │ Routing Rule       │
                 └─────────┬──────────┘
                           |
                    Backend Pool
                       /       \
                      ↓         ↓
                   first      second
                 Apache :80  Apache :80
```

But unlike the Load Balancer, Application Gateway can make decisions based on **HTTP information**.

For example:

```text
http://myapp.com/
          ↓
       Backend 1

http://myapp.com/api
          ↓
       Backend 2
```

That's **Layer 7 routing**.

---

# 🧠 First: Load Balancer vs Application Gateway

You just completed Lab 09, so compare them.

|                       | Load Balancer | Application Gateway |
| --------------------- | ------------- | ------------------- |
| OSI layer             | Layer 4       | Layer 7             |
| Understands HTTP      | Limited       | Yes                 |
| TCP                   | ✅             | ✅                   |
| UDP                   | ✅             | ❌                   |
| URL path routing      | ❌             | ✅                   |
| Host-based routing    | ❌             | ✅                   |
| HTTP listener         | ❌             | ✅                   |
| HTTPS/TLS termination | ❌             | ✅                   |
| WAF capability        | ❌             | ✅                   |

### Load Balancer

Think:

> **"Where should this TCP connection go?"**

### Application Gateway

Think:

> **"What HTTP request is this, and which backend should handle it?"**

---

# 🏗️ Our Lab Architecture

We'll use your existing VNet:

```text
VNet
vnet-southafricanorth-1
        |
        ├── snet-southafricanorth-1
        │       ├── first
        │       └── second
        │
        └── Application Gateway subnet
```

⚠️ **Important:** Application Gateway requires a **dedicated subnet**.

We cannot simply put Application Gateway into the same subnet as your VMs.

So we'll create:

```text
VNet
│
├── snet-southafricanorth-1
│       ├── first
│       └── second
│
└── appgw-subnet
        └── Application Gateway
```

---

# Part 1 — Verify your existing VNet

You already discovered:

```text
VNet:
vnet-southafricanorth-1

VM subnet:
snet-southafricanorth-1
```

Verify:

```bash
az network vnet show \
  --resource-group amine_machine \
  --name vnet-southafricanorth-1 \
  --query "{Name:name,AddressSpace:addressSpace.addressPrefixes}" \
  --output table
```

Your VNet uses the `172.16.0.0/16` network based on your VM addresses.

---

# Part 2 — Create a dedicated Application Gateway subnet

We'll use:

```text
172.16.1.0/24
```

Run:

```bash
az network vnet subnet create \
  --resource-group amine_machine \
  --vnet-name vnet-southafricanorth-1 \
  --name appgw-subnet \
  --address-prefixes 172.16.1.0/24
```

Now:

```text
vnet-southafricanorth-1
│
├── snet-southafricanorth-1
│   ├── first
│   └── second
│
└── appgw-subnet
    └── Application Gateway
```

---

# Part 3 — Create a Public IP

Application Gateway needs a frontend IP.

Create:

```bash
az network public-ip create \
  --resource-group amine_machine \
  --name appgw-public-ip \
  --location southafricanorth \
  --sku Standard \
  --allocation-method Static
```

Get the IP:

```bash
az network public-ip show \
  --resource-group amine_machine \
  --name appgw-public-ip \
  --query ipAddress \
  --output tsv
```

You'll get something like:

```text
102.x.x.x
```

We'll use your actual IP later.

---

# Part 4 — Create the Application Gateway

Now we can create the gateway.

```bash
az network application-gateway create \
  --resource-group amine_machine \
  --name lab10-appgw \
  --location southafricanorth \
  --sku Standard_v2 \
  --capacity 2 \
  --vnet-name vnet-southafricanorth-1 \
  --subnet appgw-subnet \
  --public-ip-address appgw-public-ip \
  --frontend-port 80
```

This creates several components for us.

Conceptually:

```text
lab10-appgw
│
├── Frontend IP
│
├── Frontend Port :80
│
├── Listener
│
├── Backend Pool
│
├── HTTP Settings
│
└── Routing Rule
```

---

# Part 5 — Understand the Application Gateway components

This is the **most important part of Lab 10**.

Application Gateway has several pieces.

## ① Frontend IP

The public IP users connect to.

```text
Internet
   |
   ↓
Public IP
   |
   ↓
Application Gateway
```

---

## ② Listener

The listener waits for incoming traffic.

For example:

```text
HTTP
Port 80
```

So:

```text
Client
  |
  | HTTP :80
  ↓
Listener
```

A listener can also use:

* HTTPS
* Hostnames
* Different ports

---

## ③ Backend Pool

Contains the servers that receive traffic.

For our lab:

```text
Backend Pool
    |
    ├── first
    └── second
```

---

## ④ HTTP Settings

This tells Application Gateway **how to communicate with the backend**.

For example:

```text
Protocol: HTTP
Port: 80
```

So:

```text
Client → Application Gateway :80
                       |
                       ↓
                 Backend :80
```

---

## ⑤ Routing Rule

The rule connects:

```text
Listener
    ↓
Backend Pool
```

Conceptually:

```text
HTTP Listener :80
       |
       ↓
Routing Rule
       |
       ↓
Backend Pool
```

---

# Part 6 — Add `first` and `second` to the Backend Pool

Your private IPs are:

```text
first  → 172.16.0.4
second → 172.16.0.5
```

We can add them to the backend pool.

First inspect the gateway:

```bash
az network application-gateway address-pool list \
  --resource-group amine_machine \
  --gateway-name lab10-appgw \
  --output table
```

You should see a default backend pool.

---

# Part 7 — Add the backend IPs

Get the backend pool name:

```bash
az network application-gateway address-pool list \
  --resource-group amine_machine \
  --gateway-name lab10-appgw \
  --query "[].name" \
  --output tsv
```

The automatically created pool will typically be:

```text
appGatewayBackendPool
```

Then add `first`:

```bash
az network application-gateway address-pool update \
  --resource-group amine_machine \
  --gateway-name lab10-appgw \
  --name appGatewayBackendPool \
  --servers 172.16.0.4 172.16.0.5
```

Verify:

```bash
az network application-gateway address-pool show \
  --resource-group amine_machine \
  --gateway-name lab10-appgw \
  --name appGatewayBackendPool \
  --output json
```

You should see:

```text
172.16.0.4
172.16.0.5
```

---

# Part 8 — Backend HTTP Settings

Let's see the existing settings:

```bash
az network application-gateway http-settings list \
  --resource-group amine_machine \
  --gateway-name lab10-appgw \
  --output table
```

The important values are:

```text
Protocol → HTTP
Port     → 80
```

This means:

```text
Application Gateway
        |
        | HTTP :80
        ↓
Apache on VM
```

---

# Part 9 — Health Probe

Application Gateway also needs to know whether the backend is healthy.

Unlike the Load Balancer, Application Gateway's health checking is closely tied to **HTTP application behavior**.

We can check backend health with:

```bash
az network application-gateway show-backend-health \
  --resource-group amine_machine \
  --name lab10-appgw \
  --output json
```

You want to eventually see:

```text
first   → Healthy
second  → Healthy
```

If you see:

```text
Unhealthy
```

don't panic. We'll troubleshoot it.

---

# Part 10 — Test the Application Gateway

Get its public IP:

```bash
az network public-ip show \
  --resource-group amine_machine \
  --name appgw-public-ip \
  --query ipAddress \
  --output tsv
```

Then:

```bash
curl http://<APP_GATEWAY_PUBLIC_IP>
```

or open:

```text
http://<APP_GATEWAY_PUBLIC_IP>
```

---

# 🧠 The BIG difference from Lab 09

In Lab 09:

```text
Client
  |
  ↓
Load Balancer
  |
  ↓
TCP :80
  |
  ├── first
  └── second
```

The Load Balancer doesn't care about:

```text
/api
/images
/admin
```

But Application Gateway can:

```text
Client
  |
  ↓
Application Gateway
  |
  ├── /api     → API backend
  |
  ├── /images  → Image backend
  |
  └── /        → Web backend
```

That's why we call it **Layer 7 routing**.

---

# 🔥 Lab 10 Challenge

Once the basic configuration works, we'll make the lab more interesting.

We'll configure:

```text
http://<APPGW-IP>/first
             ↓
           first

http://<APPGW-IP>/second
             ↓
           second
```

Then we'll have:

```text
                 Application Gateway
                         |
                  Path-based routing
                    /          \
                   ↓            ↓
               /first        /second
                  ↓              ↓
                first          second
```

This is where you'll really see the difference between **Azure Load Balancer and Application Gateway**.

---

# 🏆 What you should know after Lab 10

You should be able to explain:

```text
Frontend IP
     ↓
Listener
     ↓
Routing Rule
     ↓
Backend Pool
     ↓
HTTP Settings
     ↓
Backend VM
```

And distinguish:

```text
Load Balancer
    ↓
Layer 4
    ↓
TCP / UDP
```

from:

```text
Application Gateway
    ↓
Layer 7
    ↓
HTTP / HTTPS
    ↓
URL / Host / Path routing
```

### ⚠️ Important

Because we're using your **existing VNet and VMs**, don't blindly execute all the commands at once. We already learned in Lab 09 that **region, VNet, subnet, NIC, and resource names matter**.

**Start only with Part 1 and Part 2: verify the VNet and create `appgw-subnet`.** Then show me the output. We'll build the Application Gateway step-by-step using your actual Azure configuration.
