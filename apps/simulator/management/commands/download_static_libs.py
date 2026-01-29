import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Downloads external JS libraries (Vue, Plotly) for local usage'

    def handle(self, *args, **kwargs):
        # Define target directory
        static_dir = settings.BASE_DIR / 'static' / 'js' / 'vendor'
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            self.stdout.write(f"Created directory: {static_dir}")

        # Define libraries to download
        libs = [
            {
                'name': 'vue.global.js',
                'url': 'https://unpkg.com/vue@3/dist/vue.global.js'
            },
            {
                'name': 'plotly.min.js',
                'url': 'https://cdn.plot.ly/plotly-2.27.0.min.js'
            }
        ]

        for lib in libs:
            self.stdout.write(f"Downloading {lib['name']}...")
            try:
                response = requests.get(lib['url'], stream=True)
                if response.status_code == 200:
                    file_path = static_dir / lib['name']
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    self.stdout.write(self.style.SUCCESS(f"Saved to {file_path}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to download {lib['url']}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))

        self.stdout.write(self.style.SUCCESS("All libraries downloaded successfully!"))
