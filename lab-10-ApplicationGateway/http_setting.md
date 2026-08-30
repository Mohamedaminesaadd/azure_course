Yes. **HTTP settings are one of the key concepts in Application Gateway.**

## What are HTTP settings?

Think of them as the **instructions Application Gateway uses to talk to your backend VM**.

For example, we create:

```text
http-backend
Protocol: HTTP
Port: 80
```

The traffic flow becomes:

```text
Client
   |
   | HTTP :80
   ↓
Application Gateway
   |
   | HTTP :80   ← HTTP settings
   ↓
Backend VM
```

So there are two separate sides:

### Frontend

How the **client talks to Application Gateway**:

```text
Client → Application Gateway
          HTTP :80
```

This is controlled by the **listener**.

### Backend

How **Application Gateway talks to your VM**:

```text
Application Gateway → VM
                      HTTP :80
```

This is controlled by **HTTP settings**.

---

## Example with your VMs

You have:

```text
first  → 172.16.0.4
second → 172.16.0.5
```

And Apache listens on:

```text
HTTP :80
```

Therefore our HTTP settings are:

```text
Name:     http-backend
Protocol: HTTP
Port:     80
```

Application Gateway can then do:

```text
                  Application Gateway
                         |
                  http-backend
                    HTTP :80
                    /       \
                   ↓         ↓
              172.16.0.4  172.16.0.5
                 first       second
```

---

# What else can HTTP settings control?

They're not only about port 80.

They can control things such as:

* Backend protocol: HTTP/HTTPS
* Backend port
* Connection behavior
* Cookie-based affinity
* Request timeout
* Host-name handling

For this beginner lab, the important ones are:

```text
Protocol = HTTP
Port     = 80
```

---

# 🧠 Very important distinction

Don't confuse:

### Listener

> **"What do I accept from the client?"**

```text
HTTP :80
```

### HTTP settings

> **"How do I connect to the backend?"**

```text
HTTP :80
```

They can be different.

For example:

```text
Client
  |
  | HTTPS :443
  ↓
Application Gateway
  |
  | HTTP :80
  ↓
Backend VM
```

That's a very common architecture called **TLS/SSL termination** at the Application Gateway.

---

# What's next?

Now that you understand HTTP settings, we move to the **Backend Pool**.

You already have the two backend servers:

```text
first  → 172.16.0.4
second → 172.16.0.5
```

We'll create:

```text
first-pool
    └── 172.16.0.4

second-pool
    └── 172.16.0.5
```

Then we'll create the **listener**, and finally the most important part:

```text
Path-based routing

/first/*  → first-pool
/second/* → second-pool
```

So the flow we'll build is:

```text
                    Client
                       |
                       ↓
                 Listener :80
                       |
                       ↓
               Path-based rule
                 /          \
                ↓            ↓
           /first/*      /second/*
                ↓            ↓
           first-pool    second-pool
                ↓            ↓
             first          second
                ↓            ↓
             HTTP :80      HTTP :80
```

### 👉 Next step: create the two backend pools with `az`.

Run:

```bash
az network application-gateway address-pool create \
  --resource-group amine_machine \
  --gateway-name lab10-appgw-san \
  --name first-pool \
  --servers 172.16.0.4
```

Then:

```bash
az network application-gateway address-pool create \
  --resource-group amine_machine \
  --gateway-name lab10-appgw-san \
  --name second-pool \
  --servers 172.16.0.5
```

Then we'll connect these pools to the **URL path rules**.
