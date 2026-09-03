#!/usr/bin/env python3

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


SITES = {
    "GitHub": {
        "url": "https://api.github.com/users/{}",
        "type": "api",
    },
    "Reddit": {
        "url": "https://www.reddit.com/user/{}/about.json",
        "type": "json",
    },
}

HEADERS = {
    "User-Agent": "ReconX/1.0"
}

TIMEOUT = 10
RESULTS_DIR = "results"


def preparar_directorio():
    os.makedirs(RESULTS_DIR, exist_ok=True)


def validar_usuario(username):
    username = username.strip()

    if not username:
        return False

    if len(username) > 39:
        return False

    return re.match(r"^[A-Za-z0-9_.-]+$", username) is not None


def check_site(site, info, username):
    url = info["url"].format(username)

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            if info["type"] == "api":
                data = response.json()

                return {
                    "site": site,
                    "found": True,
                    "status": response.status_code,
                    "url": url,
                    "data": {
                        "login": data.get("login"),
                        "name": data.get("name"),
                        "bio": data.get("bio"),
                        "public_repos": data.get("public_repos"),
                        "followers": data.get("followers"),
                        "following": data.get("following"),
                    }
                }

            return {
                "site": site,
                "found": True,
                "status": response.status_code,
                "url": url,
                "data": {}
            }

        if response.status_code == 404:
            return {
                "site": site,
                "found": False,
                "status": 404,
                "url": url,
                "data": {}
            }

        return {
            "site": site,
            "found": None,
            "status": response.status_code,
            "url": url,
            "data": {}
        }

    except requests.RequestException as error:
        return {
            "site": site,
            "found": None,
            "status": None,
            "url": url,
            "error": str(error),
            "data": {}
        }


def check_username(username):
    print()
    print("=" * 60)
    print(f"ReconX - Usuario: {username}")
    print("=" * 60)

    results = []

    with ThreadPoolExecutor(max_workers=4) as executor:

        futures = {
            executor.submit(
                check_site,
                site,
                info,
                username
            ): site
            for site, info in SITES.items()
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    results.sort(key=lambda item: item["site"])

    for result in results:

        if result["found"] is True:
            print(
                f"[+] {result['site']}: encontrado "
                f"({result['url']})"
            )

        elif result["found"] is False:
            print(
                f"[-] {result['site']}: no encontrado"
            )

        else:
            print(
                f"[!] {result['site']}: "
                f"no se pudo comprobar"
            )

    report = {
        "tool": "ReconX",
        "username": username,
        "results": results
    }

    filename = os.path.join(
        RESULTS_DIR,
        f"{username}.json"
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    print()
    print(f"[+] Reporte guardado: {filename}")


def main():
    preparar_directorio()

    print("=" * 60)
    print("                 ReconX")
    print("          OSINT público básico")
    print("=" * 60)

    username = input(
        "Ingresa un nombre de usuario: "
    ).strip()

    if not validar_usuario(username):
        print("[!] Nombre de usuario no válido.")
        return

    try:
        check_username(username)

    except KeyboardInterrupt:
        print("\n[+] Operación cancelada.")

    except Exception as error:
        print(f"[!] Error inesperado: {error}")


if __name__ == "__main__":
    main()