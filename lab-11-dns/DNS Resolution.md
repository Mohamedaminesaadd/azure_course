Yes. We can move to the **next part of Lesson 1**.

# 🌐 Lesson 1 — Part 3: The DNS Resolution Journey

You now understand:

```text
Application
    ↓
127.0.0.53:53
    ↓
Upstream DNS resolver
```

Now let's understand **what the upstream recursive resolver actually does**.

---

## 1. Imagine you type

```text
www.amine.com
```

Your computer first asks its configured resolver:

```text
"What is the IP address of www.amine.com?"
```

The resolver has two possibilities.

### Case A — It has the answer in cache

```text
Client
  ↓
DNS Resolver
  ↓
Cache HIT
  ↓
IP address
```

Very fast.

### Case B — It doesn't have the answer

Then the resolver has to investigate.

```text
Client
  ↓
Recursive Resolver
  ↓
???
```

And this is where the **DNS hierarchy** becomes important.

---

# 2. The resolver starts at the Root

The resolver asks a root DNS server:

> "Who knows about `.com`?"

The root doesn't normally give the IP of `www.amine.com`.

Instead, it responds approximately:

```text
.com is handled by these nameservers:
a.gtld-servers.net
b.gtld-servers.net
...
```

So:

```text
Recursive Resolver
       ↓
     Root
       ↓
   ".com servers"
```

---

# 3. Then the resolver asks `.com`

Now it asks a `.com` TLD server:

> "Who is authoritative for `amine.com`?"

The `.com` server responds with the authoritative nameservers for `amine.com`:

```text
amine.com

NS1 → ...
NS2 → ...
```

So:

```text
Recursive Resolver
       ↓
      Root
       ↓
     .com
       ↓
amine.com NS
```

---

# 4. Then it asks the authoritative DNS server

Now the resolver knows:

> "These servers are responsible for `amine.com`."

It asks one of them:

```text
"What is www.amine.com?"
```

The authoritative server might answer:

```text
www.amine.com

A → 20.50.100.10
```

Now the resolver finally knows the answer.

---

# 5. The answer travels back

```text
Authoritative DNS
       ↓
20.50.100.10
       ↓
Recursive Resolver
       ↓
127.0.0.53
       ↓
Your application
```

Then your browser can connect:

```text
Browser
   ↓
20.50.100.10
   ↓
Web server
```

---

# 🧠 The complete picture

This is the architecture I want you to memorize:

```text
                         YOU
                          │
                          │ www.amine.com
                          ↓
                  ┌───────────────┐
                  │ Ubuntu        │
                  │ 127.0.0.53    │
                  └───────┬───────┘
                          │
                          ↓
                 Recursive Resolver
                          │
                          │
                          ↓
                    ROOT DNS
                       "."
                          │
                    "Ask .com"
                          ↓
                     .COM TLD
                          │
                 "Ask amine.com"
                          ↓
              Authoritative DNS
                 for amine.com
                          │
                    A record
                          ↓
                   20.50.100.10
                          │
                          ↓
                     Web Server
```

---

# 🔥 One important thing

The **Root DNS server does NOT know every website's IP**.

The `.com` server does **not** know every `www.example.com` IP either.

Their responsibilities are different:

| DNS level     | Main responsibility                   |
| ------------- | ------------------------------------- |
| Root          | Where is `.com`, `.org`, `.tn`, etc.? |
| TLD           | Where is `amine.com`?                 |
| Authoritative | What are the records for `amine.com`? |
| Recursive     | Find the answer and return it to you  |

That's the core of DNS.

---

# 🧪 Your next lab

Now let's **watch this process ourselves** instead of just talking about it.

Run:

```bash
dig +trace google.com
```

This is one of the most useful DNS commands for learning.

You'll see something roughly like:

```text
.                    ← Root
↓
com.                 ← TLD
↓
google.com.          ← Authoritative
↓
142.251.x.x          ← Answer
```

**Send me the output of `dig +trace google.com`.**

Then we'll dissect it line by line. That will be **Lesson 1 — Part 4: Seeing the DNS hierarchy in the real world.**
