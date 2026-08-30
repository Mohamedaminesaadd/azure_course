Yes 👍. If you have successfully implemented **Application Gateway path-based routing**, then **Lab 10 is complete**.

But one small correction: you said "pass to lab 10" — you're already on **Lab 10**. So I assume you mean **pass to Lab 11**.

# 🌐 Lab 11 — Configure DNS Zones and DNS Records

The goal is to understand how DNS connects a **domain name** to your Azure resources.

Currently you access your Application Gateway like:

```text
http://20.164.204.33
```

With DNS, we want something conceptually like:

```text
http://myapp.example.com
        ↓
      DNS
        ↓
20.164.204.33
        ↓
Application Gateway
```

## What you'll learn

We'll work with:

```text
DNS Zone
   ↓
DNS Record
   ↓
Domain name
   ↓
Azure resource
```

### Main concepts

**DNS Zone**

The container for DNS records.

Example:

```text
example.com
```

**A record**

Maps a hostname to an IPv4 address:

```text
app.example.com → 20.164.204.33
```

**CNAME**

Maps one hostname to another hostname:

```text
www.example.com → app.example.com
```

**DNS resolution**

```text
Browser
   ↓
app.example.com
   ↓
DNS
   ↓
20.164.204.33
   ↓
Application Gateway
```

---

## Important for our lab

You **do not need to buy a domain** to understand the Azure DNS concepts.

We can first create an Azure DNS zone and learn:

```text
DNS Zone
   ├── A record
   ├── CNAME
   └── NS records
```

using `az`.

However, for a real public domain such as:

```text
app.mydomain.com
```

you need to own/control that domain and delegate its nameservers to Azure DNS.

---

## Lab 11 roadmap

We'll do it step by step:

```text
1. Create DNS Zone
        ↓
2. Understand Nameservers
        ↓
3. Create A record
        ↓
4. Point record to an Azure Public IP
        ↓
5. Query DNS
        ↓
6. Understand CNAME
        ↓
7. Test DNS resolution
```

And we'll continue using **Azure CLI (`az`)**, just like Lab 10.

If you want, we can start **Lab 11 — Step 1: Create the Azure DNS Zone** now.
