import subprocess

output = subprocess.check_output(["uname", "-n"])
print(output.decode("utf-8"))
