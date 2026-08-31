# 🌐 DNS Course — Lesson 2: The DNS Hierarchy

You've now seen that DNS is **hierarchical**. Let's go deeper into exactly what each level does.

## 1. The hierarchy

Take:

```text
www.google.com.
```

Read it from **right to left**:

```text
.          ← Root
└── com    ← TLD
    └── google   ← Domain
        └── www  ← Host/subdomain
```

So the DNS tree looks like:

```text
                         .
                         │
              ┌──────────┼──────────┐
             .com       .org        .tn
               │
            google
               │
              www
```

---

## 2. Root DNS — `.`

The root is at the top:

```text
.
```

The root's job is **not** to know Google's IP.

Instead, it knows where the TLDs are:

```text
. → .com DNS servers
. → .org DNS servers
. → .tn DNS servers
. → .fr DNS servers
...
```

So if the resolver asks:

> "Where can I find `.com`?"

The root can answer:

> "Here are the nameservers responsible for `.com`."

---

## 3. TLD — `.com`

TLD means **Top-Level Domain**.

Examples:

```text
.com
.org
.net
.tn
.fr
.de
```

For:

```text
google.com
```

the `.com` DNS system is responsible for the **`.com` zone**.

It knows where `google.com` is delegated:

```text
.com
 │
 ├── google.com → Google's authoritative nameservers
 ├── microsoft.com → Microsoft's authoritative nameservers
 ├── github.com → GitHub's authoritative nameservers
 └── ...
```

Notice something important:

**The `.com` servers don't need to know the IP of `www.google.com`.**

They need to know:

> "Which authoritative DNS servers are responsible for `google.com`?"

---

# 4. Authoritative DNS

Now we arrive at the domain itself:

```text
google.com
```

Google's authoritative DNS servers contain the actual records.

For example, conceptually:

```text
google.com

www       A       142.251.x.x
mail      MX      ...
```

So when the recursive resolver asks:

```text
"What is www.google.com?"
```

the authoritative server can answer:

```text
www.google.com → 142.251.x.x
```

---

# 5. Why this architecture?

Imagine if one giant DNS server had to contain:

```text
EVERY DOMAIN
EVERY SUBDOMAIN
EVERY RECORD
```

That would be terrible.

Instead, DNS is distributed:

```text
                     ROOT
                       │
          ┌────────────┼─────────────┐
          ↓            ↓             ↓
        .com          .org          .tn
          │
     ┌────┼─────┐
     ↓    ↓     ↓
   google github amazon
     │
     ↓
    www
```

Each level delegates responsibility to the next level.

This is called **delegation**.

---

# 6. Delegation — VERY important

Suppose you own:

```text
amine.com
```

You can tell the `.com` registry:

> "The DNS servers responsible for `amine.com` are these servers."

For example:

```text
amine.com

NS ns1.example-dns.com
NS ns2.example-dns.com
```

Now `.com` doesn't need to manage your records.

It simply delegates:

```text
.com
  │
  │ "Ask these servers"
  ↓
amine.com
  │
  ↓
Your authoritative DNS
```

Then **you** manage:

```text
www.amine.com
api.amine.com
mail.amine.com
```

---

# 7. This explains your earlier question

You asked:

> "How does the machine know where the root DNS server is without asking anybody?"

Excellent question.

The recursive DNS software has access to a **root hints** configuration containing the addresses of root servers.

So a recursive resolver doesn't need to discover the root from another DNS server.

Conceptually:

```text
Recursive DNS Resolver
        │
        ├── Root hints
        │
        ↓
Root DNS servers
```

We'll examine this in detail later.

---

# 🧪 Lab 2 — See the delegation

Run:

```bash
dig NS google.com
```

You'll see Google's authoritative nameservers.

Then:

```bash
dig NS com.
```

You'll see nameservers for `.com`.

And:

```bash
dig NS .
```

You'll see the root nameservers.

Now you can compare:

```text
dig NS .
      ↓
Root nameservers

dig NS com.
      ↓
.com nameservers

dig NS google.com
      ↓
Google authoritative nameservers
```

---