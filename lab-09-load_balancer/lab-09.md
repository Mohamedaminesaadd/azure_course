# 🌐 Lab 09 — Azure Load Balancer

## 1. 🎯 Objective

The goal of Lab 09 is to move from **one VM serving users directly** to an architecture with **multiple backend VMs, high availability, and traffic distribution**.

Instead of:

```text
Internet
   |
   ↓
  VM1
```

we build:

```text
                    Internet
                       |
                       ↓
                  Public IP :80
                       |
                       ↓
              Azure Load Balancer
                   /          \
                  ↓            ↓
               VM first     VM second
               Apache        Apache
```

The client sees **one public endpoint**, while the Load Balancer distributes traffic between healthy backend VMs. 

---

# 2. 🚨 What problem does a Load Balancer solve?

With only one server:

```text
User
  |
  ↓
 VM1
```

VM1 becomes a **single point of failure**.

If VM1 crashes:

```text
User
  |
  X
 VM1 ❌
```

The application becomes unavailable.

With two VMs:

```text
             User
               |
               ↓
        Load Balancer
          /         \
         ↓           ↓
       VM1          VM2
```

If VM1 becomes unhealthy:

```text
             User
               |
               ↓
        Load Balancer
             |
             ↓
            VM2
```

The Load Balancer can stop sending new traffic to an unhealthy backend based on the health probe. 

### 🔑 Core definition

> **Azure Load Balancer provides a single frontend endpoint while distributing network traffic across healthy backend resources.** 

---

# 3. 🧠 Azure Load Balancer

Azure Load Balancer operates at:

> **Layer 4 — Transport/Network-level traffic distribution**

It works primarily with:

```text
TCP
UDP
IP
Port
```

It does **not** primarily understand HTTP URLs or paths. 

For example:

```text
TCP :80
   ↓
Load Balancer
   ↓
VM1 / VM2
```

---

# 4. ⭐ The 5 concepts you MUST understand

The entire lab revolves around these concepts:

```text
                    Load Balancer
                         |
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
   Frontend IP      Backend Pool      Health Probe
        |                |                |
        |             VM1 + VM2        checks :80
        |
        ↓
 Load-Balancing Rule
```



---

## 4.1 Frontend IP

The **frontend IP** is the address users connect to.

In your lab:

```text
102.37.12.93
```

The user accesses:

```text
http://102.37.12.93
```

The user does **not** need to know:

```text
172.16.0.4
172.16.0.5
```

### Mental model

> **Frontend = the door through which users enter.**

```text
Internet
   |
   ↓
Public IP
   |
   ↓
Load Balancer
```



---

# 5. Backend Pool

The **backend pool** is the collection of servers that can receive traffic.

Your architecture:

```text
backend-pool
     |
     ├── first
     │    └── 172.16.0.4
     |
     └── second
          └── 172.16.0.5
```

### Definition

> **Backend pool = the servers available behind the Load Balancer.**



---

# 6. Why use private IPs?

Your VMs have private addresses:

```text
first
Private IP → 172.16.0.4

second
Private IP → 172.16.0.5
```

The Load Balancer communicates with the backend resources through the private network.

```text
Internet
   |
   ↓
Public Load Balancer IP
   |
   ↓
Private backend network
   |
   ├── first
   └── second
```

The client only sees the public Load Balancer endpoint. 

---

# 7. NIC

Remember from networking:

> **NIC = Network Interface Card**

Your resources are:

```text
first
  ↓
first178
  ↓
ipconfig1
  ↓
172.16.0.4
```

and:

```text
second
  ↓
second779
  ↓
ipconfig1
  ↓
172.16.0.5
```

So the relationship is:

```text
VM
 ↓
NIC
 ↓
IP Configuration
 ↓
Private IP
 ↓
Backend Pool
```



---

# 8. Health Probe

The Load Balancer needs to answer:

> **"Is this backend healthy?"**

That's the purpose of the **health probe**.

Your probe:

```text
Name:     http-probe
Protocol: TCP
Port:     80
```

It checks whether the backend is responding on TCP port 80. 

Conceptually:

```text
Load Balancer
      |
      ├──→ first :80
      |       ↓
      |    healthy?
      |
      └──→ second :80
              ↓
           healthy?
```

If:

```text
first → unhealthy
second → healthy
```

the Load Balancer can stop sending traffic to `first`.

### Important distinction

**Health probe does NOT distribute traffic.**

It answers:

> **"Is this backend healthy?"**

---

# 9. Load-Balancing Rule

The rule tells the Load Balancer how traffic moves between frontend and backend.

Your rule:

```text
http-rule

Protocol:      TCP
Frontend port: 80
Backend port:  80
Probe:         http-probe
Pool:          backend-pool
```

So:

```text
Client
   |
   | TCP :80
   ↓
Frontend :80
   |
   ↓
Load Balancer
   |
   ↓
Backend Pool
   |
   ↓
Healthy VM :80
```

### Mental model

> **Load-balancing rule = traffic forwarding instruction.** 

---

# 10. 🏗️ Complete architecture

```text
                         INTERNET
                            |
                            | TCP :80
                            ↓
                    ┌───────────────────┐
                    │    Frontend IP    │
                    │    102.37.12.93   │
                    └─────────┬─────────┘
                              |
                              ↓
                    ┌───────────────────┐
                    │ Azure Load        │
                    │ Balancer          │
                    │ lab09-lb-sa       │
                    └─────────┬─────────┘
                              |
                     Load-Balancing Rule
                            :80 → :80
                              |
                              ↓
                     ┌────────────────┐
                     │  Backend Pool  │
                     └───────┬────────┘
                             |
                       ┌─────┴─────┐
                       ↓           ↓
                    first       second
                  172.16.0.4   172.16.0.5
                       |           |
                       ↓           ↓
                   Apache :80  Apache :80
                       ↑           ↑
                       └─────┬─────┘
                             |
                       Health Probe
                          TCP :80
```

This combines the frontend, backend pool, health probe, and rule into one architecture. 

---

# 11. 🛠️ Implementation

## Step 1 — Create Resource Group

If necessary:

```bash
az group create \
  --name lab09-rg \
  --location <REGION>
```

Your actual lab can reuse an existing resource group. 

---

# 12. Create the VNet

```bash
az network vnet create \
  --resource-group lab09-rg \
  --name lab09-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name web-subnet \
  --subnet-prefix 10.0.1.0/24
```

Architecture:

```text
lab09-vnet
10.0.0.0/16
    |
    └── web-subnet
        10.0.1.0/24
```



---

# 13. Create NSG

```bash
az network nsg create \
  --resource-group lab09-rg \
  --name web-nsg \
  --location <REGION>
```

### Allow SSH

```bash
az network nsg rule create \
  --resource-group lab09-rg \
  --nsg-name web-nsg \
  --name AllowSSH \
  --priority 100 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --destination-port-range 22
```

### Allow HTTP

```bash
az network nsg rule create \
  --resource-group lab09-rg \
  --nsg-name web-nsg \
  --name AllowHTTP \
  --priority 110 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --destination-port-range 80
```



---

# 14. Associate NSG with subnet

```bash
az network vnet subnet update \
  --resource-group lab09-rg \
  --vnet-name lab09-vnet \
  --name web-subnet \
  --network-security-group web-nsg
```



---

# 15. Create the backend VMs

## VM-Web1

```bash
az vm create \
  --resource-group lab09-rg \
  --name VM-Web1 \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --ssh-key-values ~/.ssh/id_rsa.pub \
  --vnet-name lab09-vnet \
  --subnet web-subnet \
  --public-ip-address ""
```

## VM-Web2

```bash
az vm create \
  --resource-group lab09-rg \
  --name VM-Web2 \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --ssh-key-values ~/.ssh/id_rsa.pub \
  --vnet-name lab09-vnet \
  --subnet web-subnet \
  --public-ip-address ""
```

### Why no public IP?

The backend VMs don't need to be directly exposed to the Internet. The Load Balancer provides the public entry point.



---

# 16. Find private IPs

```bash
az vm list-ip-addresses \
  --resource-group lab09-rg \
  --output table
```

Example:

```text
VM-Web1 → 10.0.1.4
VM-Web2 → 10.0.1.5
```

Your actual addresses may differ. 

---

# 17. Install Apache

Because the backend VMs have no public IP, use Azure Run Command.

### VM-Web1

```bash
az vm run-command invoke \
  --resource-group lab09-rg \
  --name VM-Web1 \
  --command-id RunShellScript \
  --scripts "apt update && apt install apache2 -y"
```

### VM-Web2

```bash
az vm run-command invoke \
  --resource-group lab09-rg \
  --name VM-Web2 \
  --command-id RunShellScript \
  --scripts "apt update && apt install apache2 -y"
```



---

# 18. Give each VM a different page

This makes load balancing visible.

### VM-Web1

```bash
az vm run-command invoke \
  --resource-group lab09-rg \
  --name VM-Web1 \
  --command-id RunShellScript \
  --scripts "echo '<h1>Hello from VM-Web1</h1>' > /var/www/html/index.html"
```

### VM-Web2

```bash
az vm run-command invoke \
  --resource-group lab09-rg \
  --name VM-Web2 \
  --command-id RunShellScript \
  --scripts "echo '<h1>Hello from VM-Web2</h1>' > /var/www/html/index.html"
```

Now:

```text
VM-Web1 → Hello from VM-Web1
VM-Web2 → Hello from VM-Web2
```



---

# 19. Create Public IP

```bash
az network public-ip create \
  --resource-group lab09-rg \
  --name lb-public-ip \
  --sku Standard \
  --allocation-method Static
```

The public IP becomes the **frontend endpoint**. 

---

# 20. Create Load Balancer

```bash
az network lb create \
  --resource-group lab09-rg \
  --name lab09-lb \
  --sku Standard \
  --public-ip-address lb-public-ip \
  --frontend-ip-name frontend \
  --backend-pool-name backend-pool
```

Now:

```text
Internet
   |
Public IP
   |
Load Balancer
```



---

# 21. Find NICs

```bash
az network nic list \
  --resource-group lab09-rg \
  --output table
```

Or get a specific VM's NIC:

```bash
az vm show \
  --resource-group lab09-rg \
  --name VM-Web1 \
  --query "networkProfile.networkInterfaces[0].id" \
  --output tsv
```



---

# 22. Add backend VMs

The original lab demonstrates adding the backend private IPs:

```bash
az network lb address-pool address add \
  --resource-group lab09-rg \
  --lb-name lab09-lb \
  --pool-name backend-pool \
  --vnet lab09-vnet \
  --ip-address <VM_WEB1_PRIVATE_IP>
```

Then:

```bash
az network lb address-pool address add \
  --resource-group lab09-rg \
  --lb-name lab09-lb \
  --pool-name backend-pool \
  --vnet lab09-vnet \
  --ip-address <VM_WEB2_PRIVATE_IP>
```



---

# 23. 🩺 Create Health Probe

```bash
az network lb probe create \
  --resource-group lab09-rg \
  --lb-name lab09-lb \
  --name http-probe \
  --protocol Tcp \
  --port 80
```

Azure periodically checks:

```text
VM1 → TCP :80 ?
VM2 → TCP :80 ?
```

If one fails:

```text
VM1 → UNHEALTHY
```

The Load Balancer can stop sending new traffic there. 

---

# 24. ⚙️ Create Load-Balancing Rule

```bash
az network lb rule create \
  --resource-group lab09-rg \
  --lb-name lab09-lb \
  --name http-rule \
  --protocol Tcp \
  --frontend-port 80 \
  --backend-port 80 \
  --frontend-ip-name frontend \
  --backend-pool-name backend-pool \
  --probe-name http-probe
```

This creates:

```text
Frontend :80
     ↓
Backend :80
```



---

# 25. Test the Load Balancer

Get the public IP:

```bash
az network public-ip show \
  --resource-group lab09-rg \
  --name lb-public-ip \
  --query ipAddress \
  --output tsv
```

Then:

```bash
curl http://<LOAD_BALANCER_IP>
```

Or open:

```text
http://<LOAD_BALANCER_IP>
```

You should receive either:

```text
Hello from VM-Web1
```

or:

```text
Hello from VM-Web2
```



---

# 26. Test traffic distribution

```bash
for i in {1..10}; do
    curl -s http://<LOAD_BALANCER_IP>
    echo
done
```

You may see responses from both backend VMs over multiple requests. 

The key idea:

```text
                 ONE public IP
                      |
                      ↓
               Load Balancer
                  /       \
                 ↓         ↓
               VM1       VM2
```

The client doesn't need to know the backend addresses.

---

# 27. 🔥 Failure Test

This is one of the most important parts of the lab.

Stop Apache on VM-Web1:

```bash
az vm run-command invoke \
  --resource-group lab09-rg \
  --name VM-Web1 \
  --command-id RunShellScript \
  --scripts "systemctl stop apache2"
```

Now:

```text
VM-Web1
   ↓
TCP :80
   ↓
FAILED
```

The health probe detects the failure.

Then test:

```bash
for i in {1..10}; do
    curl -s http://<LOAD_BALANCER_IP>
    echo
done
```

Traffic should continue to the healthy VM-Web2. 

Restart Apache:

```bash
az vm run-command invoke \
  --resource-group lab09-rg \
  --name VM-Web1 \
  --command-id RunShellScript \
  --scripts "systemctl start apache2"
```

Once the health probe sees VM-Web1 as healthy again, it can become eligible for traffic again. 

---

# 28. 🐛 Problems encountered

## Problem 1 — Missing `--name`

Error:

```text
the following arguments are required:
-n/--name
```

### Cause

The Azure CLI command expected a resource/address name.

### Solution

Provide:

```bash
--name first
```

or:

```bash
--name second
```

### Lesson

> Always read the Azure CLI error carefully; it often tells you exactly which required parameter is missing.



---

# 29. Problem 2 — Wrong Azure region

This was the major real-world problem in your lab.

You initially had:

```text
Load Balancer
      ↓
East US

VMs
      ↓
South Africa North
```

Azure returned:

```text
InvalidResourceReference
```

The Load Balancer couldn't be associated with those backend resources in that configuration because they were in different regions.

### Solution

Create the Load Balancer in the same region as the VMs:

```text
South Africa North
│
├── Load Balancer
├── first
└── second
```

You created:

```text
lab09-lb-sa
```

in:

```text
South Africa North
```

### Lesson

> **Always check regional compatibility before connecting Azure resources.**



---

# 30. Problem 3 — VNet lookup confusion

You initially tried to use:

```text
--vnet vnet-southafricanorth-1
```

and received a `NotFound` error.

Instead of blindly repeating the command, you inspected the NIC:

```bash
az network nic show ...
```

and confirmed:

```text
VNet:
vnet-southafricanorth-1

Subnet:
snet-southafricanorth-1
```

### Lesson

> When Azure says a network resource cannot be found, inspect the actual resource relationships instead of assuming the name.



---

# 31. 🆚 Load Balancer vs Application Gateway

This distinction is essential because **Lab 10 follows Lab 09**.

|                       | Azure Load Balancer          | Application Gateway     |
| --------------------- | ---------------------------- | ----------------------- |
| OSI layer             | Layer 4                      | Layer 7                 |
| Main protocols        | TCP / UDP                    | HTTP / HTTPS            |
| Understands URL       | No                           | Yes                     |
| Understands host/path | No                           | Yes                     |
| Main purpose          | Network traffic distribution | Intelligent web routing |

The source specifically frames Load Balancer as Layer 4 and Application Gateway as Layer 7. 

### Example

Load Balancer:

```text
TCP :80
   ↓
VM1 / VM2
```

Application Gateway:

```text
example.com/api/*
        ↓
   API servers

example.com/images/*
        ↓
   Image servers
```

---

# 32. 🧠 The complete Lab 09 process

Memorize this:

```text
1. Prepare backend VMs
        ↓
2. Check region compatibility
        ↓
3. Configure network/security
        ↓
4. Install Apache
        ↓
5. Create different web pages
        ↓
6. Create Public IP
        ↓
7. Create Load Balancer
        ↓
8. Create Backend Pool
        ↓
9. Add backend VMs
        ↓
10. Create Health Probe
        ↓
11. Create Load-Balancing Rule
        ↓
12. Test
        ↓
13. Simulate backend failure
        ↓
14. Verify traffic continues
        ↓
15. Restore backend
```

This is the overall workflow extracted from the lab. 

---

# 33. 📌 Commands to remember

### Find VM IPs

```bash
az vm list-ip-addresses \
  --resource-group <RESOURCE_GROUP> \
  --output table
```

### Run commands inside a VM

```bash
az vm run-command invoke \
  --resource-group <RESOURCE_GROUP> \
  --name <VM> \
  --command-id RunShellScript \
  --scripts "<COMMAND>"
```

### Create Public IP

```bash
az network public-ip create \
  --resource-group <RESOURCE_GROUP> \
  --name <PUBLIC_IP> \
  --sku Standard \
  --allocation-method Static
```

### Create Load Balancer

```bash
az network lb create \
  --resource-group <RESOURCE_GROUP> \
  --name <LB_NAME> \
  --sku Standard \
  --public-ip-address <PUBLIC_IP> \
  --frontend-ip-name frontend \
  --backend-pool-name backend-pool
```

### Create Health Probe

```bash
az network lb probe create \
  --resource-group <RESOURCE_GROUP> \
  --lb-name <LB_NAME> \
  --name http-probe \
  --protocol Tcp \
  --port 80
```

### Create Load-Balancing Rule

```bash
az network lb rule create \
  --resource-group <RESOURCE_GROUP> \
  --lb-name <LB_NAME> \
  --name http-rule \
  --protocol Tcp \
  --frontend-port 80 \
  --backend-port 80 \
  --frontend-ip-name frontend \
  --backend-pool-name backend-pool \
  --probe-name http-probe
```

---

# 34. 🎯 Definitions to memorize

**Load Balancer**

> Layer 4 Azure service that distributes network traffic among healthy backend resources.

**Frontend IP**

> Public entry point where clients connect.

**Backend Pool**

> Collection of backend resources capable of receiving traffic.

**Health Probe**

> Mechanism that checks whether a backend is healthy.

**Load-Balancing Rule**

> Defines how frontend traffic is forwarded to the backend.

**NIC**

> Network interface connecting a VM to the virtual network.

**Private IP**

> Internal IP used for communication inside the private network.

**High Availability**

> Ability of an application to remain available when one backend resource fails.

---

# 35. 🎤 Interview questions

### Q1. Why do we need a Load Balancer?

Because a single VM creates a single point of failure. Multiple backend resources allow traffic to continue if one becomes unhealthy.

### Q2. What is the frontend?

The endpoint through which clients access the Load Balancer.

### Q3. What is a backend pool?

The collection of resources that can receive traffic.

### Q4. What is the health probe?

It determines whether a backend is healthy and eligible to receive traffic.

### Q5. What does the load-balancing rule do?

It defines how traffic arriving at the frontend is forwarded to the backend.

### Q6. Why do we use private IPs for backend VMs?

The Load Balancer communicates with backend resources through the private network, while clients use the public frontend IP.

### Q7. What happens if VM1 fails?

The health probe detects that VM1 is unhealthy, and the Load Balancer can stop sending new traffic to it.

### Q8. What is the difference between Load Balancer and Application Gateway?

Load Balancer operates at **Layer 4**, while Application Gateway operates at **Layer 7** and can make decisions based on HTTP/HTTPS information such as host and URL path. 

---

# 36. 🏆 Final mental model

If someone asks you:

> **"Explain Azure Load Balancer."**

Think:

```text
                    INTERNET
                       |
                       ↓
                 FRONTEND IP
                       |
                       ↓
               LOAD BALANCER
                       |
                LOAD-BALANCING
                    RULE
                       |
                       ↓
                 BACKEND POOL
                  /         \
                 ↓           ↓
              VM first    VM second
                 ↑           ↑
                 └─────┬─────┘
                       |
                  HEALTH PROBE
```

And remember these four words:

```text
FRONTEND
   ↓
BACKEND
   ↓
HEALTH
   ↓
RULE
```

**Frontend** → Where the client enters.

**Backend Pool** → Which servers can receive traffic.

**Health Probe** → Which servers are healthy.

**Rule** → How traffic moves from frontend to backend.

Finally, the Azure progression is:

```text
Lab 07
IP + NIC + NSG
       ↓
Lab 08
Private VM-to-VM communication
       ↓
Lab 09
Multiple VMs + Load Balancer
       ↓
Lab 10
Application Gateway
       ↓
HTTP/HTTPS intelligent routing
```

This progression is explicitly reflected in the Lab 09 material. 
