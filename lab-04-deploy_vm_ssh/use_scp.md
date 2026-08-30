Yes. You can transfer files from your **host PC → Azure VM**. Since your host PC is Ubuntu and you're already using SSH, the simplest tool is **`scp`**.

### 1. Transfer one file

Suppose you have:

```text
~/Documents/test.txt
```

Run this **from your host PC**, not inside the VM:

```bash
scp -i ~/Downloads/first_key.pem ~/Documents/test.txt azureuser@4.222.218.84:/home/azureuser/
```

The structure is:

```text
scp
 ├── -i first_key.pem       → your SSH private key
 ├── ~/Documents/test.txt   → file on your PC
 └── azureuser@4.222.218.84:/home/azureuser/
                             → destination on Azure VM
```

Then SSH into the VM:

```bash
ssh -i ~/Downloads/first_key.pem azureuser@4.222.218.84
```

and verify:

```bash
ls -l
```

You should see:

```text
test.txt
```

### 2. Transfer a directory

For example, transfer an entire project:

```bash
scp -r -i ~/Downloads/first_key.pem ~/Documents/my-project azureuser@4.222.218.84:/home/azureuser/
```

`-r` means **recursive**, so it copies the directory and everything inside it.

### 3. Transfer in the other direction

You can also copy **Azure VM → your PC**:

```bash
scp -i ~/Downloads/first_key.pem azureuser@4.222.218.84:/home/azureuser/test.txt ~/Downloads/
```

So:

```text
PC → VM
scp local_file user@IP:/destination/

VM → PC
scp user@IP:/remote_file local_destination/
```

### 4. Important distinction

You don't need to copy your private key to the VM.

The private key stays:

```text
Your PC
~/Downloads/first_key.pem 🔐
```

`scp` simply uses that key to authenticate the transfer:

```text
Your PC
   │
   │ SCP over SSH
   │
   ▼
Azure VM
```

So **`scp` is essentially file transfer over SSH**.

For your Azure learning, this is a very useful command to know.
