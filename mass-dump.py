import os
import json
import argparse
import requests

# Disable insecure request warning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

apiversion = "v2"
final_list_of_blobs = []

def list_repos(url):
    req = requests.get(f"{url}/{apiversion}/_catalog", verify=False)
    return json.loads(req.text).get("repositories", [])

def find_tags(url, reponame):
    req = requests.get(f"{url}/{apiversion}/{reponame}/tags/list", verify=False)
    data = json.loads(req.content)
    return data.get("tags")

def list_blobs(url, reponame, tag):
    blobs = []
    req = requests.get(f"{url}/{apiversion}/{reponame}/manifests/{tag}", verify=False)
    data = json.loads(req.content)
    if "fsLayers" in data:
        for x in data["fsLayers"]:
            curr_blob = x['blobSum'].split(":")[1]
            if curr_blob not in blobs:
                blobs.append(curr_blob)
    return blobs

def download_blob(url, reponame, blobdigest, dirname):
    req = requests.get(f"{url}/{apiversion}/{reponame}/blobs/sha256:{blobdigest}", verify=False)
    filename = f"{blobdigest}.tar.gz"
    filepath = os.path.join(dirname, filename)
    with open(filepath, 'wb') as f:
        f.write(req.content)

def main():
    parser = argparse.ArgumentParser(description="Mass Docker Registry Puller")
    parser.add_argument('-u', '--url', dest="url", required=True, help="URL Docker Registry v2 API, e.g. https://IP:PORT")
    parser.add_argument('-d', '--dir', dest="outdir", required=True, help="Output directory for downloaded blobs")
    args = parser.parse_args()

    url = args.url
    basedir = args.outdir

    os.makedirs(basedir, exist_ok=True)

    print(f"[+] Getting list of repositories from {url}...")
    repos = list_repos(url)

    for repo in repos:
        print(f"\n[+] Repo: {repo}")
        tags = find_tags(url, repo)
        if not tags:
            print("   [-] No tags found, skipping...")
            continue

        for tag in tags:
            print(f"   [+] Tag: {tag}")
            blobs = list_blobs(url, repo, tag)
            tagdir = os.path.join(basedir, repo.replace("/", "_"), tag)
            os.makedirs(tagdir, exist_ok=True)

            for blob in blobs:
                print(f"      [>] Downloading blob {blob}...")
                download_blob(url, repo, blob, tagdir)

    print("\n[✓] Done downloading all repositories.")

if __name__ == "__main__":
    main()
