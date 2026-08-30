Yes. What you want is a very good **Azure Application Gateway URL path-based routing lab**.

Your architecture will look like this:

```text
                    Internet
                       │
                       │ HTTP :80
                       ▼
             ┌─────────────────────┐
             │ Azure Application   │
             │ Gateway             │
             │ Public IP           │
             └──────────┬──────────┘
                        │
              URL Path Routing
                 /vm1/*   /vm2/*
                  │          │
          ┌───────▼───┐  ┌──▼────────┐
          │   VM1     │  │    VM2    │
          │  Apache2  │  │  Apache2  │
          │  10.x.x.4  │  │ 10.x.x.5  │
          └───────────┘  └───────────┘
```

Application Gateway supports exactly this: it can examine the URL path and send requests to different backend pools. ([Microsoft Learn][1])

For example:

```text
http://<APPLICATION-GATEWAY-IP>/vm1/
                         │
                         └──► VM1 Apache

http://<APPLICATION-GATEWAY-IP>/vm2/
                         │
                         └──► VM2 Apache
```

Let's build it **step by step in the Azure Portal**, since you've been creating your Application Gateway through the portal.

---

# 1. First, verify your two VMs

You should have something like:

```text
VM1
Private IP: 10.0.1.4
Apache2: running

VM2
Private IP: 10.0.1.5
Apache2: running
```

The important thing is that **both VMs are in a VNet/subnet reachable by the Application Gateway**.

On VM1:

```bash
sudo systemctl status apache2
```

Then:

```bash
curl localhost
```

You should get HTML.

Do the same on VM2:

```bash
sudo systemctl status apache2
curl localhost
```

---

# 2. Make the two Apache servers different

This is very important for testing.

On **VM1**:

```bash
sudo nano /var/www/html/index.html
```

Put:

```html
<h1>Hello from VM1</h1>
<p>This page is served by Apache on VM1.</p>
```

On **VM2**:

```bash
sudo nano /var/www/html/index.html
```

Put:

```html
<h1>Hello from VM2</h1>
<p>This page is served by Apache on VM2.</p>
```

Restart Apache:

```bash
sudo systemctl restart apache2
```

Now:

```text
VM1 → Hello from VM1
VM2 → Hello from VM2
```

This makes the routing very easy to see.

---

# 3. Create the Application Gateway

In Azure Portal:

**Application Gateway → Create**

You already created something similar in your previous lab.

For example:

### Basics

```text
Subscription:
Azure subscription 1

Resource group:
amine_machine

Name:
lab10-appgw-url

Region:
South Africa North

Tier:
Standard V2
```

You can use **Standard V2** for this lab.

For a simple lab:

```text
Autoscaling: Disabled
Instance count: 1
```

If you're using availability zones, you can keep:

```text
Zones: 1, 2, 3
```

but it isn't necessary for understanding URL routing.

---

# 4. Frontend IP

You need a frontend IP because users connect to the Application Gateway.

Choose:

```text
Frontend IP type:
Public

Public IP:
Create new
```

For example:

```text
Name:
lab10-appgw-pip
```

Your final architecture will therefore have:

```text
Internet
   │
   ▼
Public IP
   │
   ▼
Application Gateway
```

A public IP is required when the Application Gateway is internet-facing. ([Microsoft Learn][2])

---

# 5. Application Gateway subnet

This is important.

Application Gateway needs its **own dedicated subnet**.

For example:

```text
VNet:
vnet

Application Gateway subnet:
appgw-subnet

Address range:
10.0.2.0/24
```

Your VMs might be:

```text
VM subnet:
10.0.1.0/24
```

So:

```text
VNet
│
├── vm-subnet
│    ├── VM1
│    └── VM2
│
└── appgw-subnet
     └── Application Gateway
```

Don't put the Application Gateway in the same subnet as the VMs.

---

# 6. Listener

For the first lab, keep it simple.

Create:

```text
Listener name:
listener-http

Frontend IP:
Public

Protocol:
HTTP

Port:
80
```

So the Application Gateway listens on:

```text
http://<public-ip>:80
```

The listener is the component that receives the incoming HTTP request. ([Microsoft Learn][2])

---

# 7. Backend pools

Now we create the two destinations.

Go to:

**Application Gateway → Backend pools**

Create:

### Backend pool 1

```text
Name:
backend-vm1
```

Add:

```text
VM1
```

Don't add VM2.

---

### Backend pool 2

```text
Name:
backend-vm2
```

Add:

```text
VM2
```

Now:

```text
backend-vm1
      │
      └── VM1

backend-vm2
      │
      └── VM2
```

Application Gateway backend pools can contain VMs, VM scale sets, IP addresses/FQDNs, or App Service backends. ([Microsoft Learn][2])

---

# 8. Backend settings

Create an HTTP backend setting.

For VM1:

```text
Name:
http-setting-vm1

Protocol:
HTTP

Port:
80
```

For VM2:

```text
Name:
http-setting-vm2

Protocol:
HTTP

Port:
80
```

Since Apache is listening on port 80:

```text
Application Gateway
        │
        │ HTTP :80
        ▼
      Apache
        │
        │ :80
```

The backend HTTP settings determine the protocol and port that Application Gateway uses to communicate with your backend servers. ([Microsoft Learn][3])

---

# 9. The important part — URL path routing

Now we create the routing rule.

Go to:

**Application Gateway → Rules**

Create:

```text
Rule type:
Path-based
```

Something like:

```text
Name:
url-routing-rule

Listener:
listener-http
```

Then configure the path rules.

---

## Rule 1 → VM1

Path:

```text
/vm1/*
```

Backend pool:

```text
backend-vm1
```

Backend setting:

```text
http-setting-vm1
```

So:

```text
/vm1/*
      │
      ▼
backend-vm1
      │
      ▼
VM1
```

---

## Rule 2 → VM2

Path:

```text
/vm2/*
```

Backend pool:

```text
backend-vm2
```

Backend setting:

```text
http-setting-vm2
```

So:

```text
/vm2/*
      │
      ▼
backend-vm2
      │
      ▼
VM2
```

Azure path patterns must start with `/`, and `*` can be used at the end, so `/vm1/*` and `/vm2/*` are valid patterns. ([Microsoft Learn][1])

---

# 10. Default backend

You also need a default backend.

For your lab, choose:

```text
Default backend:
backend-vm1

Default HTTP setting:
http-setting-vm1
```

That means:

```text
/anything-that-doesn't-match
              │
              ▼
            VM1
```

Conceptually:

```text
                    Application Gateway
                           │
                    Path-based rule
                           │
              ┌────────────┼────────────┐
              │            │            │
           /vm1/*       /vm2/*       default
              │            │            │
              ▼            ▼            ▼
             VM1          VM2          VM1
```

If no path matches, Application Gateway sends the request to the default backend. ([Microsoft Learn][4])

---

# 11. Very important: NSG

This is one of the places where Azure labs often fail.

Your VM must allow HTTP traffic from the Application Gateway.

For the VM subnet/VM NSG, make sure you have:

```text
Inbound
TCP
Port 80
Allow
```

For a lab, you can temporarily allow:

```text
Source:
Any
```

Later, for better security, restrict it appropriately.

You don't need a public IP on the VMs for Application Gateway to reach them.

The architecture should ideally become:

```text
Internet
   │
   │ HTTP
   ▼
Application Gateway
   │
   │ private network
   ├──────────────► VM1 :80
   │
   └──────────────► VM2 :80
```

---

# 12. Test backend health

After deployment, go to:

**Application Gateway → Backend health**

You want to see something like:

```text
backend-vm1
    VM1
    Healthy

backend-vm2
    VM2
    Healthy
```

If you see:

```text
Unhealthy
```

don't test URL routing yet.

First fix the backend connection.

Typical causes:

```text
❌ Apache isn't running
❌ Port 80 isn't allowed
❌ Wrong private IP
❌ Wrong backend setting
❌ VMs aren't reachable from App Gateway subnet
❌ NSG blocking traffic
```

Application Gateway uses health probes to determine which backend servers are healthy before forwarding requests. ([Microsoft Learn][2])

---

# 13. Test URL routing

Suppose your Application Gateway public IP is:

```text
20.50.100.10
```

Open:

```text
http://20.50.100.10/vm1/
```

Expected:

```text
Hello from VM1
```

Then:

```text
http://20.50.100.10/vm2/
```

Expected:

```text
Hello from VM2
```

So you have successfully built:

```text
http://20.50.100.10/vm1/*
                       │
                       ▼
                      VM1


http://20.50.100.10/vm2/*
                       │
                       ▼
                      VM2
```

---

## ⚠️ One important detail about Apache

There is a subtle issue here.

When you request:

```text
/vm1/
```

Application Gateway normally forwards the **full path** to the backend. So VM1's Apache receives:

```text
GET /vm1/
```

not simply:

```text
GET /
```

Microsoft explicitly documents this behavior. If your backend application expects `/` instead, you can use **URL rewrite** or **override the backend path**. ([Microsoft Learn][1])

For your first lab, I recommend **not adding rewrite yet**. It's actually useful because you will see exactly how path-based routing works.

If Apache returns a 404 for `/vm1/`, then we'll add a rewrite rule afterward.

---

# Your complete Lab 10

I would structure your lab like this:

### Lab 10 — Azure Application Gateway URL Path Routing

**Step 1 — Prepare VMs**

```text
VM1 → Apache2
VM2 → Apache2
```

**Step 2 — Differentiate the websites**

```text
VM1 → Hello from VM1
VM2 → Hello from VM2
```

**Step 3 — Create Application Gateway**

```text
Standard V2
Public IP
HTTP listener :80
```

**Step 4 — Create backend pools**

```text
backend-vm1 → VM1
backend-vm2 → VM2
```

**Step 5 — Create backend HTTP settings**

```text
VM1 → HTTP :80
VM2 → HTTP :80
```

**Step 6 — Create path-based routing**

```text
/vm1/* → VM1
/vm2/* → VM2
```

**Step 7 — Configure NSG**

```text
Allow TCP 80
```

**Step 8 — Check Backend health**

```text
VM1 → Healthy
VM2 → Healthy
```

**Step 9 — Test**

```text
http://APPGW-IP/vm1/
http://APPGW-IP/vm2/
```

This is the cleanest way to understand the difference between **frontend IP → listener → routing rule → URL path map → backend pool → backend HTTP setting → VM**. Microsoft's current portal tutorial follows this same general VM + Application Gateway + path-based routing model. ([Microsoft Learn][5])

If you want, **we can do it interactively from your current Azure Portal screen**: you show me the Application Gateway **Basics** page/settings, and I'll tell you exactly what to select for each field.