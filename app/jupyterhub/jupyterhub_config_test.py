# Plik konfiguracyjny JupyterHub dla wersji testowej
# Wersja testowa z DummyAuthenticator do celów testowych

import os
import sys
from dockerspawner import DockerSpawner
import subprocess

c = get_config()

# Ustawienia limitów aktywności
c.JupyterHub.active_server_limit = int(os.environ.get("ACTIVE_SERVER_LIMIT", 100))
c.JupyterHub.activity_resolution = int(os.environ.get("ACTIVITY_RESOLUTION", 300))

# Ustawienia dla DockerSpawner
c.DockerSpawner.mem_limit = os.environ.get("MEM_LIMIT", "1G")
c.DockerSpawner.cpu_limit = int(os.environ.get("CPU_LIMIT", 1))
c.DockerSpawner.image = os.environ.get("DOCKER_NOTEBOOK_IMAGE", "notebook_img")
c.DockerSpawner.cmd = os.environ.get("DOCKER_SPAWN_CMD", "start-singleuser.sh")
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = os.environ.get("DOCKER_NETWORK_NAME")
c.DockerSpawner.remove = True  # Usuwanie kontenerów po zakończeniu pracy
c.DockerSpawner.debug = True  # Ustawienia debugowania

# Ustawienia adresu JupyterHub
c.JupyterHub.base_url = '/test/'
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 9090
c.JupyterHub.cookie_secret_file = "/data/jupyterhub_cookie_secret"  # Lokalizacja pliku cookie
c.JupyterHub.db_url = "sqlite:////data/jupyterhub.sqlite"

def is_six_digits_username(username):
    return username[:6].isdigit() and len(username) >= 6

def setup_user_environment(spawner):
    """Ustawia zmienne środowiskowe, volumes i komendę post-start"""
    username = spawner.user.name
    notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR", "/home/jovyan/work")
    my_public_dir = "/home/jovyan/work/my_public"
    public_dir = "/home/jovyan/public"

    volumes = {
        f"jupyterhub-user-{username}-work": {"bind": notebook_dir, "mode": "rw"},
        "jupyterhub-public": {"bind": public_dir, "mode": "ro"}
    }

    environment = {}

    if not is_six_digits_username(username):
        volumes[f"jupyterhub-user-{username}-my_public"] = {"bind": my_public_dir, "mode": "rw"}
        environment["JUPYTERHUB_MY_PUBLIC_VOLUME"] = "true"

        #spawner.post_start_cmd = "/usr/local/bin/custom_start.sh"
    else:
        environment["JUPYTERHUB_MY_PUBLIC_VOLUME"] = "false"
         # Dla użytkowników 6-cyfrowych usuń katalog jeśli istnieje
        spawner.post_start_cmd = f"""
        /bin/bash -c '
        if [ -d {my_public_dir} ]; then
            rm -rf {my_public_dir}
        fi
        '
        """

    spawner.volumes = volumes
    spawner.environment = environment

c.Spawner.pre_spawn_hook = setup_user_environment

c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"



# Ustawienia trybu testowego (DummyAuthenticator)
c.Authenticator.admin_users = {"admin"}
c.JupyterHub.authenticator_class = "dummy"  # Użycie DummyAuthenticator w trybie testowym

# Konfiguracja Idle Culler (usuwanie bezczynnych serwerów)
c.JupyterHub.load_roles = [
    {
        "name": "jupyterhub-idle-culler-role",
        "scopes": [
            "list:users",
            "read:users:activity",
            "read:servers",
            "delete:servers",
        ],
        "services": ["jupyterhub-idle-culler-service"],
    }
]

c.JupyterHub.services = [
    {
        "name": "jupyterhub-idle-culler-service",
        "command": [
            sys.executable,
            "-m", "jupyterhub_idle_culler",
            "--timeout={0}".format(os.environ.get("JUPYTERHUB_IDLE_CULLER_TIMEOUT", "3600")),
        ],
    }
]