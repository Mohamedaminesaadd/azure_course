# 🔵 Lab 05 — VM Sizes, SKUs, Quotas & Availability Zones

Now we move from **"how do I create a VM?"** to **"how do I choose the right VM and understand Azure's capacity limitations?"**

## 🎯 Lab Objective

By the end of this lab, you should understand:

* VM sizes
* VM SKUs
* vCPU and RAM
* Disk limitations
* Region availability
* Azure quotas
* Availability Zones
* Why a VM size may be unavailable
* How to choose an appropriate VM

---

# 1. Understand VM Size

A VM size defines the hardware resources allocated to your VM.

For example:

```text
Standard_B2s
│
├── 2 vCPUs
├── RAM
├── Network bandwidth
├── Temporary storage
└── Disk limits
```

Think of a VM size like choosing a physical computer:

```text
Small VM
   ↓
Low CPU + low RAM
   ↓
Cheap

Large VM
   ↓
More CPU + RAM
   ↓
More expensive
```

---

# 2. List Available VM Sizes

First log into Azure:

```bash
az login
```

Then choose your subscription:

```bash
az account list --output table
```

Set the subscription if necessary:

```bash
az account set --subscription "<SUBSCRIPTION_NAME>"
```

Now list VM sizes available in your region:

```bash
az vm list-sizes \
  --location <REGION> \
  --output table
```

For example:

```bash
az vm list-sizes \
  --location westeurope \
  --output table
```

You'll get information similar to:

```text
Name              NumberOfCores    MemoryInMb
----------------  ---------------  -----------
Standard_B1s      1                1024
Standard_B2s      2                4096
Standard_D2s_v5   2                8192
Standard_D4s_v5   4                16384
...
```

---

# 3. Understand the VM Naming

Azure VM names can look complicated:

```text
Standard_D4s_v5
```

Don't try to memorize every character. The important idea is that Azure uses naming conventions to describe VM families and capabilities.

For example:

```text
Standard_D4s_v5
         │
         ├── D = VM family
         │
         ├── 4 = vCPU count
         │
         └── v5 = generation
```

The exact naming conventions vary by family, so always check Microsoft's current SKU documentation when making a production decision.

---

# 4. VM Families

Azure has different VM families for different workloads.

### General purpose

Examples:

```text
B
D
```

Good for:

* Web servers
* Development
* Small applications
* Testing

---

### Compute optimized

Examples:

```text
F
```

Good when CPU performance is the priority.

Examples:

* Batch processing
* Compute-heavy applications
* Some analytics workloads

---

### Memory optimized

Examples:

```text
E
M
```

Good when applications require a lot of RAM.

Examples:

* Large databases
* In-memory workloads
* Analytics

---

### GPU

Examples include GPU-enabled VM families.

Useful for:

* Machine learning
* AI workloads
* Rendering
* GPU computing

---

# 5. Check Your Current VM Size

For your existing VM:

```bash
az vm show \
  --resource-group <RESOURCE_GROUP> \
  --name <VM_NAME> \
  --query hardwareProfile.vmSize \
  --output tsv
```

You might get:

```text
Standard_B2s
```

You can also use:

```bash
az vm show \
  --resource-group <RESOURCE_GROUP> \
  --name <VM_NAME> \
  --output json
```

Look for:

```json
"hardwareProfile": {
    "vmSize": "Standard_B2s"
}
```

---

# 6. Check the SKU in Your Region

This is very important.

A VM size existing in Azure **doesn't mean it is available everywhere**.

Check SKUs:

```bash
az vm list-skus \
  --location <REGION> \
  --resource-type virtualMachines \
  --output table
```

You can filter:

```bash
az vm list-skus \
  --location <REGION> \
  --resource-type virtualMachines \
  --query "[?contains(name, 'B2s')].{Name:name,Restrictions:restrictions}" \
  --output table
```

This helps you investigate:

```text
VM size
   ↓
Is it offered in this region?
   ↓
Are there restrictions?
```

---

# 7. Quotas

Now an important Azure concept:

## What is a quota?

A quota is a limit Azure places on how much of a resource you can use.

For example:

```text
Your subscription
       |
       ├── vCPU quota
       ├── VM quota
       └── Regional limits
```

Suppose your quota is:

```text
Region: West Europe
vCPU quota: 10
```

You already use:

```text
VM1 → 4 vCPUs
VM2 → 4 vCPUs
```

You have:

```text
10 - 8 = 2 vCPUs
```

Trying to create another VM requiring 4 vCPUs could fail because of quota.

---

# 8. Check Your Quotas

You can inspect quota-related information using Azure CLI commands and the Azure Portal.

Start by checking your subscription:

```bash
az account show --output table
```

Then in the Azure Portal:

**Subscriptions → Your Subscription → Usage + quotas**

Choose the relevant:

* Region
* Compute provider
* VM family/quota

You'll see information such as:

```text
Quota
Current usage
Limit
```

---

# 9. Quota vs Capacity

This distinction is **very important**.

### Quota

Your subscription is allowed to use:

```text
20 vCPUs
```

### Capacity

Azure must actually have physical capacity available for the requested VM in that location.

So you can have:

```text
Quota = enough
Capacity = unavailable
```

and still fail to create the VM.

Think:

```text
Quota
"What am I allowed to use?"

Capacity
"Is Azure able to give it to me right now?"
```

---

# 10. Availability Zones

Now let's introduce **Availability Zones**.

An Azure region can contain multiple physically separate zones.

Conceptually:

```text
             Azure Region
        ┌─────────────────────┐
        │                     │
        │ Zone 1   Zone 2   Zone 3
        │   │        │        │
        │  VM1      VM2      VM3
        │                     │
        └─────────────────────┘
```

The zones are designed to provide isolation from failures affecting a single datacenter location.

---

# 11. Why Zones Matter

Imagine your application has only one VM:

```text
User
 |
 ↓
VM
```

If the infrastructure hosting that VM has a serious failure:

```text
User
 |
 X
VM unavailable
```

Instead:

```text
             Load Balancer
             /     |     \
            ↓      ↓      ↓
          VM1     VM2    VM3
         Zone1   Zone2   Zone3
```

If one zone experiences a failure, the application can potentially continue serving traffic from other zones.

---

# 12. Region vs Availability Zone

Don't confuse these:

### Region

A geographic Azure location:

```text
West Europe
France Central
North Europe
```

### Availability Zone

An isolated physical location **inside a region**.

```text
Region
│
├── Zone 1
├── Zone 2
└── Zone 3
```

---

# 13. Check Zone Support

Not every VM SKU supports every configuration in every region.

You can investigate with:

```bash
az vm list-skus \
  --location <REGION> \
  --resource-type virtualMachines \
  --output table
```

Look at:

* SKU
* Restrictions
* Locations
* Capabilities

This is one reason you should **always verify a VM SKU before designing around it**.

---

# 14. VM Resize

You can change the VM size.

First list possible sizes:

```bash
az vm list-vm-resize-options \
  --resource-group <RESOURCE_GROUP> \
  --name <VM_NAME> \
  --output table
```

You may see:

```text
Name
----------------
Standard_B1s
Standard_B2s
Standard_D2s_v5
...
```

Then resize:

```bash
az vm resize \
  --resource-group <RESOURCE_GROUP> \
  --name <VM_NAME> \
  --size <NEW_SIZE>
```

For example:

```bash
az vm resize \
  --resource-group myResourceGroup \
  --name myVM \
  --size Standard_B2s
```

⚠️ **Important:** Resizing can cause downtime because Azure may need to stop/reallocate the VM.

For this lab, don't resize your production/important VM just for experimentation.

---

# 15. Mini Experiment 🧪

Let's make this a real hands-on lab.

### Experiment A — Identify your VM

Run:

```bash
az vm show \
  --resource-group <RESOURCE_GROUP> \
  --name <VM_NAME> \
  --query "{Name:name,Size:hardwareProfile.vmSize,Location:location}" \
  --output table
```

Record:

```text
VM:
Size:
Region:
```

---

### Experiment B — Investigate the SKU

Run:

```bash
az vm list-skus \
  --location <REGION> \
  --resource-type virtualMachines \
  --query "[?name=='<YOUR_VM_SIZE>']" \
  --output json
```

Look for:

* capabilities
* restrictions
* locations

---

### Experiment C — Find resize options

```bash
az vm list-vm-resize-options \
  --resource-group <RESOURCE_GROUP> \
  --name <VM_NAME> \
  --output table
```

Ask yourself:

> Which sizes could I potentially use instead?

---

# 🧠 Final Challenge

Imagine your company tells you:

> "Deploy a Linux web server. It needs 2 vCPUs and 4 GB RAM. It should be cheap because it's a development environment."

You need to determine:

```text
1. Which VM family?
       ↓
2. Which VM size?
       ↓
3. Is it available in my region?
       ↓
4. Is there enough quota?
       ↓
5. Is there Azure capacity?
       ↓
6. Do I need an Availability Zone?
```

That's the actual skill this lab is teaching.

---

# ✅ Lab 05 Completion Checklist

* [ ] List VM sizes with Azure CLI
* [ ] Identify your current VM size
* [ ] Understand VM families
* [ ] Understand vCPU and RAM
* [ ] Check SKU availability
* [ ] Understand subscription quotas
* [ ] Understand Azure capacity
* [ ] Understand Availability Zones
* [ ] Distinguish region vs zone
* [ ] Inspect VM resize options
* [ ] Explain why a VM deployment can fail even when the SKU exists

### 🔑 The key lesson

Remember this chain:

```text
                    VM Deployment
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       VM Size          Region         Quota
          │              │              │
          ↓              ↓              ↓
      Resources       SKU exists?    Enough?
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                    Azure Capacity
                         │
                         ↓
                  Deployment works
```

Once you understand **size + SKU + region + quota + capacity + zones**, you understand why Azure VM deployment errors happen instead of simply treating them as random errors.
