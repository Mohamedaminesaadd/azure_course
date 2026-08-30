Yes — **this is a good configuration for Lab 10**, and using the Azure Portal this time is completely fine. In fact, it's useful to learn both **Portal + CLI**.

Your Application Gateway is now:

```text
Name:       lab10-appgw-san
Region:     South Africa North
Tier:       Standard V2
VNet:       vnet-southafricanorth-1
Subnet:     appgw-subnet
Subnet CIDR:172.16.1.0/24

Public IP:  4.253.76.20
```

And your existing VMs are:

```text
first   → 172.16.0.4
second  → 172.16.0.5
```

So the architecture is currently:

```text
                    Internet
                       |
                       |
                4.253.76.20
                       |
                       ↓
             ┌──────────────────┐
             │ Application      │
             │ Gateway          │
             │ lab10-appgw-san  │
             └────────┬─────────┘
                      |
               appgw-subnet
               172.16.1.0/24
                      |
                      ↓
              Backend Pool
                 /       \
                ↓         ↓
             first      second
           172.16.0.4  172.16.0.5
```

## ⚠️ One important thing

Creating the Application Gateway **doesn't automatically mean traffic can reach your VMs**.

We still need to configure the Application Gateway's:

1. **Backend pool**
2. **Backend settings**
3. **Health probe**
4. **Listener**
5. **Routing rule**

Think of it as:

```text
Application Gateway
│
├── Frontend IP       ✅ 4.253.76.20
│
├── Listener          ⏳
│
├── Backend Pool      ⏳
│    ├── first
│    └── second
│
├── Backend Settings  ⏳
│
├── Health Probe      ⏳
│
└── Routing Rule      ⏳
```

---

# Step 1 — Add the backend VMs

Since you're using the Portal, go to:

**Azure Portal → `lab10-appgw-san`**

Then:

**Backend pools → Add**

Create:

```text
Name:
backend-pool
```

For the targets, select:

```text
Target type: IP address or FQDN
```

Add:

```text
172.16.0.4
172.16.0.5
```

So:

```text
backend-pool
   |
   ├── 172.16.0.4 → first
   └── 172.16.0.5 → second
```

### Why private IPs?

Because the Application Gateway and VMs are inside the same VNet:

```text
vnet-southafricanorth-1
│
├── appgw-subnet
│      └── Application Gateway
│
└── snet-southafricanorth-1
       ├── first  → 172.16.0.4
       └── second → 172.16.0.5
```

This is exactly what we want.

---

# Step 2 — Backend settings

Create backend settings:

```text
Name:        http-backend
Protocol:    HTTP
Port:        80
```

So Application Gateway will communicate with Apache like this:

```text
Application Gateway
        |
        | HTTP :80
        ↓
     first :80
```

or:

```text
Application Gateway
        |
        | HTTP :80
        ↓
    second :80
```

---

# Step 3 — Listener

Create an HTTP listener:

```text
Listener name: http-listener
Protocol:      HTTP
Port:          80
```

This means Application Gateway listens for:

```text
http://4.253.76.20:80
```

---

# Step 4 — Routing rule

Create a basic routing rule:

```text
Listener
   ↓
http-listener
   ↓
Routing rule
   ↓
backend-pool
   ↓
http-backend
   ↓
first / second
```

Use:

```text
Rule name:
http-rule
```

Then select:

```text
Listener:
http-listener

Backend target:
backend-pool

Backend settings:
http-backend
```

---

# Step 5 — Health

After creating the rule, go to:

**Application Gateway → Backend health**

You want to eventually see:

```text
first    → Healthy
second   → Healthy
```

If you get:

```text
Unhealthy
```

**don't immediately recreate anything.**

We'll investigate:

```text
NSG
 ↓
Apache
 ↓
Port 80
 ↓
Backend settings
 ↓
Health probe
```

---

# Step 6 — Test

Your Application Gateway public IP is:

```text
4.253.76.20
```

Use:

```text
http://4.253.76.20
```

⚠️ **Use `http://`, not `https://`.**

Just like your Lab 09 issue:

```text
HTTP  → :80
HTTPS → :443
```

We are currently configuring HTTP.

You can also test:

```bash
curl http://4.253.76.20
```

---

## 🧠 What you're learning compared with Lab 09

Your Lab 09 was:

```text
Client
  |
  ↓
Load Balancer
  |
  ↓
Backend Pool
  |
  ├── first
  └── second
```

Now Lab 10 is:

```text
Client
  |
  ↓
Application Gateway
  |
  ↓
Listener
  |
  ↓
Routing Rule
  |
  ↓
Backend Settings
  |
  ↓
Backend Pool
  |
  ├── first
  └── second
```

Application Gateway has **more HTTP-aware components** because it operates at Layer 7.

### For now

Since you've already created the Application Gateway successfully, **don't modify the Basics configuration**.

👉 Go to **Backend pools → Add**, and add:

```text
172.16.0.4
172.16.0.5
```

Then tell me what you see on the **Backend pools** page, and we'll configure the next component together.
