> **ARCHIVED** This repository is archived. You can use it to test implementations, but OpenSSH and other
> implementations are not vulnerable. Some custom implementation may be.


# ssh_mitm_poc
POC of an sshd MiTM w/ publickey authentication.
See the `poc` branch for getting an idea of what the check is.

## What's this?
It's a paramiko based ssh/sshd that uses session-fixation in order to generate a verifiable publickey challenge that is non-volatile.

In other word, it's a POC that shows you can have this:

```
[genuine ssh client] ===ssh connect===> [mitm sshd] ===ssh connect===> [genuine sshd]
```


Where:
- mitm sshd: gets the `session id` from genuine sshd
- mitm sshd: fixates/forces `session id` to be the same in the negociated transport with genuine ssh client
- genuine client: signs a blob which comprises (`session id`, `username`, `subsystem name`, `public key`)
- mitm sshd: passes blob + signed blob over the genuine sshd
- genuine sshd: verifies blob + signature successfully, public key authentication succeeeds at this point and mitm sshd has access to genuine sshd subsystem (such as shell or sftp access)
- mitm sshd: can choose to replay all data to the genuine ssh client, while capturing all clear text data for example

## How to avoid this?

NEVER BYPASS HOSTKEY CHECK
NEVER COPY HOSTKEYS OVER MULTIPLE SYSTEMS IF YOU DONT INTEND THEM TO BE MITM'ING EACH OTHER
