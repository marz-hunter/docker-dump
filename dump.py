import os
import json
import argparse
import requests

# Pulls Docker Images from unauthenticated docker registry API.
# and checks for Docker misconfigurations.

apiversion = "v2"
final_list_of_blobs = []

# Disable insecure request warning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

parser = argparse.ArgumentParser(description="Docker Registry Puller")
parser.add_argument('-u', '--url', dest="url", help="URL Endpoint for Docker Registry API v2. Eg https://IP:Port", default="spam")
args = parser.parse_args()
url = args.url

def list_repos():
    req = requests.get(f"{url}/{apiversion}/_catalog", verify=False)
    return json.loads(req.text).get("repositories", [])

def find_tags(reponame):
    req = requests.get(f"{url}/{apiversion}/{reponame}/tags/list", verify=False)
    print("\n")
    data = json.loads(req.content)
    return data.get("tags")

def list_blobs(reponame, tag):
    req = requests.get(f"{url}/{apiversion}/{reponame}/manifests/{tag}", verify=False)
    data = json.loads(req.content)
    if "fsLayers" in data:
        for x in data["fsLayers"]:
            curr_blob = x['blobSum'].split(":")[1]
            if curr_blob not in final_list_of_blobs:
                final_list_of_blobs.append(curr_blob)

def download_blobs(reponame, blobdigest, dirname):
    req = requests.get(f"{url}/{apiversion}/{reponame}/blobs/sha256:{blobdigest}", verify=False)
    filename = f"{blobdigest}.tar.gz"
    with open(os.path.join(dirname, filename), 'wb') as f:
        f.write(req.content)

def main():
    if url != "spam":
        list_of_repos = list_repos()
        print("\n[+] List of Repositories:\n")
        for x in list_of_repos:
            print(x)
        target_repo = input("\nWhich repo would you like to download?:  ")
        if target_repo in list_of_repos:
            tags = find_tags(target_repo)
            if tags:
                print("\n[+] Available Tags:\n")
                for x in tags:
                    print(x)

                target_tag = input("\nWhich tag would you like to download?:  ")
                if target_tag in tags:
                    list_blobs(target_repo, target_tag)

                    dirname = input("\nGive a directory name:  ")
                    os.makedirs(dirname, exist_ok=True)
                    print(f"Now sit back and relax. I will download all the blobs for you in '{dirname}' directory.\nOpen the directory, unzip all the files and explore like a Boss.")

                    for x in final_list_of_blobs:
                        print(f"\n[+] Downloading Blob: {x}")
                        download_blobs(target_repo, x, dirname)
                else:
                    print("No such Tag Available. Quitting....")
            else:
                print("[+] No Tags Available. Quitting....")
        else:
            print("No such repo found. Quitting....")
    else:
        print("\n[-] Please use -u option to define API Endpoint, e.g. https://IP:Port\n")

if __name__ == "__main__":
    main()
