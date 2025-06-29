import pkg_resources

def generate_requirements(filename="requirements.txt"):
    installed_packages = pkg_resources.working_set
    with open(filename, "w") as f:
        for dist in sorted(installed_packages, key=lambda x: x.project_name.lower()):
            line = f"{dist.project_name}=={dist.version}\n"
            f.write(line)
    print(f"Plik {filename} został wygenerowany.")

if __name__ == "__main__":
    generate_requirements()
    
#skrypt Pythona, który generuje plik requirements.txt na podstawie aktualnie zainstalowanych pakietów