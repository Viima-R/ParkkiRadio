(For Linux)

Create a file "config" in your ~/.ssh/ folder where you also have your key pair. 

The public key must be on the server's authorized keys file.

In the file, write and fill the following:

```
Host serverA
    HostName public-IP-of-the-server
    User username-on-the-server
    IdentityFile ~/.ssh/name-of-your-private-key

```

If you need to proxy hop to a server that has no public IP address:

```
Host serverB
    HostName private-IP-of-the-server
    User username-on-the-server
    IdentityFile ~/.ssh/name-of-your-private-key
    ProxyJump serverA

```

Now you can ssh with the command ``ssh serverA`` or ``ssh serverB``.
