import os

TEMPLATE_DIR = 'templates'

class TemplateManager:
    def __init__(self, template_dir=TEMPLATE_DIR):
        self.template_dir = template_dir
        os.makedirs(self.template_dir, exist_ok=True)

    def list_templates(self):
        templates = [f for f in os.listdir(self.template_dir)
                     if os.path.isfile(os.path.join(self.template_dir, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        return templates

    def add_template(self, filename, filedata):
        path = os.path.join(self.template_dir, filename)
        with open(path, 'wb') as f:
            f.write(filedata)
        return path

    def remove_template(self, filename):
        path = os.path.join(self.template_dir, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
