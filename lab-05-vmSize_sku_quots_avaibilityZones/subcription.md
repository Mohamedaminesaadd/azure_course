In Azure, a **subscription** is basically the **billing and resource-management container** for your Azure usage.

Think of Azure like this:

```text
Microsoft Entra Tenant
        │
        └── Subscription
              │
              ├── Resource Group 1
              │      ├── VM
              │      ├── Storage
              │      └── Network
              │
              └── Resource Group 2
                     ├── Database
                     └── Web App
```

### 🧠 Simple analogy

Imagine Azure is a university:

* **Tenant** → the university
* **Subscription** → your student account/budget
* **Resource Group** → a classroom/project
* **Resources** → the things inside the classroom

The subscription is important because Azure uses it to track:

* 💰 **Billing** — how much your resources cost
* 📊 **Usage** — CPU, storage, networking, etc.
* 🔐 **Access** — who can manage resources
* 📦 **Resource limits/quotas**
* 🌍 **Which Azure resources belong to you**

### Example

Suppose you have:

```text
Subscription: Azure Subscription 1
│
├── Resource Group: my-vm-project
│     └── Linux VM
│
├── Resource Group: storage-project
│     └── Storage Account
│
└── Resource Group: database-project
      └── Azure SQL Database
```

All of those resources are associated with the **same subscription**.

### ⚠️ Subscription ≠ Resource Group

This distinction is important for your Azure labs:

**Subscription**

> "Who owns/manages/pays for these Azure resources?"

**Resource Group**

> "Which resources are grouped together for this project?"

So when you run:

```bash
az group create \
  --name myResourceGroup \
  --location westeurope
```

Azure creates the resource group **inside your current subscription**.

And when you create:

```bash
az vm create ...
```

the VM is also created under that subscription.

### 🔑 One sentence to remember

> **An Azure subscription is a boundary for billing, resource management, access control, and quotas.**

