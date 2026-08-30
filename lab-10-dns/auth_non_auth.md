First, a quick clarification on the terminology: the correct terms are **Authoritative** and **Non-authoritative**. "Unauthorized" makes it sound like something illegal or broken, but a non-authoritative server is actually just a helpful middleman doing exactly what it was designed to do.

Here is the difference between the two:

### 1. The Authoritative DNS Server (The Boss)

An authoritative server is the official, master record-holder for a specific domain name. When the owner of a website (like `mbc2.com`) sets up their domain, they enter their server IP addresses into an authoritative DNS server.

* **Its Job:** To hold the original, definitive DNS records (the "zone file") and provide them to anyone who asks.
* **Who runs it:** The domain registrar or hosting company (like GoDaddy, Amazon Route 53, or Cloudflare).
* **The Analogy:** Calling a business directly to ask what their official operating hours are. You are getting the answer straight from the source.

### 2. The Non-Authoritative DNS Server (The Middleman)

A non-authoritative server does not own or manage the domain's records. Instead, it goes out to the internet, asks the authoritative server for the IP address, and then **saves (caches) that answer** for a set amount of time.

* **Its Job:** To speed up web browsing. If 100 people on your Wi-Fi network all try to load `mbc2.com`, the non-authoritative server only asks the authoritative server once. It gives the other 99 people the saved answer from its memory.
* **Who runs it:** Your local computer, your home router, your Internet Service Provider (ISP), or public DNS providers like Google (8.8.8.8).
* **The Analogy:** Asking a friend for a restaurant's phone number because they called it yesterday and still have it saved in their phone. They have the right answer, but they aren't the official source.

### Summary Comparison

| Feature | Authoritative Server | Non-Authoritative Server |
| --- | --- | --- |
| **Data Source** | Reads from original, official configuration files. | Reads from a temporary cache (saved memory). |
| **Speed** | Slightly slower (must be fetched across the internet). | Extremely fast (usually local to your network or ISP). |
| **Accuracy** | 100% up-to-date. | Usually accurate, but can occasionally be outdated if the website *just* changed its IP address. |

When you ran your `nslookup` command, your computer checked with `127.0.0.53` (your local machine's DNS cache). Because your computer doesn't officially own `mbc2.com`, it correctly warned you that it was handing you a **Non-authoritative answer** from its saved memory.




You are exactly right about the first half, but the second half has a slight misunderstanding about what happens when a domain isn't owned.

Here is the breakdown of what you got right, and how the rest actually works:

### What you got exactly right:

When you buy a domain name from a provider like GoDaddy or Hostinger, they become the **Authoritative DNS Server** for your domain. You type your server's IPv4 or IPv6 address into their dashboard, and they hold the official "master copy" of that information. Any time the internet needs to know where your website lives, GoDaddy or Hostinger provides the official, authoritative answer.

### The correction (What happens if you don't buy or renew a domain):

"Non-authoritative" does **not** mean a domain is unregistered or expired. Remember, "non-authoritative" just means *saved in a temporary cache*.

Here is what actually happens if a domain doesn't belong to anyone:

**1. If the domain has NEVER been purchased:**
If you search for a completely made-up domain (like `sdjfhskdjfhskdjf.com`), there is no authoritative server for it, and no cache has it saved.

* Your local DNS server will go out to the internet, ask around, and realize the domain doesn't exist.
* Instead of giving you an IP address, it will return an error code called **NXDOMAIN** (Non-Existent Domain). It will essentially say, "I checked, and this doesn't exist."

**2. If you bought a domain, but let it EXPIRE:**
This is where the cache comes in, but it has a strict time limit.

* Every DNS record has a timer attached to it called **TTL (Time to Live)**. This timer usually lasts anywhere from 5 minutes to 24 hours.
* If your domain expires today at noon, someone's local DNS server might still have your old IP address saved in its cache. If they search for your site at 1:00 PM, they might get a **non-authoritative answer** and still reach your server.
* However, as soon as that TTL timer hits zero, the local DNS server deletes its cache. The next time someone searches for your domain, the local server will go looking for the Authoritative server. Since you didn't pay your bill, GoDaddy will say "we don't manage this anymore." The search fails, and the user gets an **NXDOMAIN** error.

### The Bottom Line

A **non-authoritative** answer is a perfectly healthy, working response for a registered, active domain—it just means your computer remembered the answer to save time. If a domain is truly unregistered, the DNS system simply returns an error.