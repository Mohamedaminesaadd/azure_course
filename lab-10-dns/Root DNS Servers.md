# 🌐 DNS Course — Lesson 4: Root DNS Servers

Now we're going to answer one of your **original questions**:

> **"How does a DNS resolver know where the Root DNS servers are if it can't ask another DNS server?"**

This is a very good DNS question.

---

## 1. First: what is the Root?

The DNS hierarchy starts at:

```text
.
```

This is called the **DNS root**.

Under it are the TLDs:

```text
.
├── com
├── org
├── net
├── tn
├── fr
├── de
└── ...
```

So if you're resolving:

```text
www.google.com
```

the resolver eventually needs to ask:

```text
.
 ↓
.com
 ↓
google.com
```

---

# 2. The resolver needs a starting point

Imagine you're building your own recursive DNS resolver.

It receives:

```text
www.google.com
```

It doesn't know Google's DNS servers yet.

So it needs to start somewhere.

But here's the problem:

> Who tells the resolver where the root DNS servers are?

The answer is:

## **Root hints**

A recursive DNS server has a configuration containing information about the root servers.

On Linux/BIND, you can have a file containing entries similar to:

```text
a.root-servers.net
b.root-servers.net
c.root-servers.net
...
m.root-servers.net
```

along with their IP addresses.

So the resolver already has a **bootstrap list**.

---

# 3. Why doesn't it need DNS to resolve the root?

Because that would create a circular dependency.

Imagine:

```text
Need google.com
    ↓
Need root server
    ↓
Need DNS to find root server
    ↓
Need root server...
```

😂 Infinite loop.

Instead, the resolver is initially given the root server addresses.

Think of it like:

```text
Recursive Resolver
       │
       │ built-in configuration
       ↓
Root server addresses
       │
       ↓
Start DNS resolution
```

This is called **bootstrapping**.

---

# 4. There are 13 root server identities

You'll often hear:

```text
A-root
B-root
C-root
...
M-root
```

That's **13 root server identities**.

But this does **NOT** mean there are only 13 physical computers.

This is extremely important.

There are many physical/anycast instances around the world.

Conceptually:

```text
                 A-root
              /    |    \
             /     |     \
           🇺🇸     🇫🇷     🇯🇵
```

All of those can serve the same root service.

---

# 5. Anycast

This is one of the concepts we'll study later.

Imagine the same root server IP is announced from multiple locations:

```text
                 Same IP
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
       USA         Europe       Asia
        │           │           │
      Server      Server       Server
```

Your DNS resolver sends traffic to that IP.

Internet routing generally delivers it to an appropriate nearby/available instance.

So if one physical instance fails:

```text
🇫🇷 Server ❌
```

another instance can still answer:

```text
🇩🇪 Server ✅
```

This is one reason the root DNS infrastructure is highly resilient.

---

# 6. The resolver now starts the lookup

Suppose:

```text
www.google.com
```

is **not in the resolver's cache**.

The resolver chooses a root server from its root hints.

It asks:

```text
"Who is responsible for .com?"
```

The root responds with information about `.com` nameservers.

Conceptually:

```text
Resolver
   │
   │ www.google.com?
   ↓
Root
   │
   │ "Ask .com"
   ↓
.com TLD
```

---

# 7. Then `.com`

The resolver asks a `.com` TLD server:

```text
"Who is responsible for google.com?"
```

The `.com` server responds:

```text
"Ask Google's authoritative nameservers."
```

So:

```text
Resolver
   ↓
Root
   ↓
.com
   ↓
Google authoritative DNS
```

---

# 8. Finally authoritative DNS

The resolver asks Google's authoritative DNS:

```text
"What is www.google.com?"
```

It might return:

```text
www.google.com
        ↓
142.251.x.x
```

Then the answer goes back:

```text
Authoritative
      ↓
Recursive Resolver
      ↓
Your Ubuntu
      ↓
Your application
```

---

# 🧠 Full resolution

Now you should understand this diagram:

```text
                     YOUR UBUNTU
                          │
                          ↓
                   127.0.0.53
                          │
                          ↓
                Recursive Resolver
                          │
                          │ cache miss
                          ↓
                    ROOT HINTS
                          │
                          ↓
                    ROOT DNS
                          │
                  "Ask .com"
                          ↓
                     .COM TLD
                          │
               "Ask google.com"
                          ↓
              AUTHORITATIVE DNS
                          │
                          ↓
                 www.google.com
                          │
                          ↓
                    IP ADDRESS
```

---

# 🔥 Important distinction

There are **three different things** here:

### Root hints

A **configuration/bootstrap mechanism**.

```text
"Here are the root servers."
```

### Root DNS servers

The actual DNS infrastructure responsible for the root zone.

```text
"."
```

### Recursive resolver

The server doing the work:

```text
"Let me find the answer."
```

Don't confuse these.

---

# 🧪 Lab 4 — See the root servers yourself

Run:

```bash
dig NS .
```

You'll see the root nameservers.

Then:

```bash
dig +trace google.com
```

Look at the beginning of the output.

You'll see the root zone participating in the resolution.

And you can inspect your local root hints if you're running BIND9 later.

---

# 🎯 Next Lesson

We've now covered:

```text
Lesson 1 → What is DNS?
Lesson 2 → DNS hierarchy
Lesson 3 → Recursive resolver
Lesson 4 → Root DNS
```

Next:

## **Lesson 5 — TLD DNS and Domain Delegation**

We'll answer:

> **Who controls `.com`, `.tn`, `.org`, etc.?**

and more importantly:

> **How does `google.com` become delegated from `.com` to Google's authoritative nameservers?**

This is where **ICANN, registries, registrars, nameservers, and delegation** all come together.
