import paramiko
ssh = paramiko.SSHClient()
class fake_pkey(paramiko.pkey.PKey):
    def sign_ssh_data(self, data):
        print(data)
        return ""


fpk = fake_pkey()
fpk.load_certificate("client.pub")

ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="localhost", port=2200, username="kang", pkey=fpk, look_for_keys=False)
t = ssh.get_transport()
print("session id from client is ", t.session_id)
print("EOF")
