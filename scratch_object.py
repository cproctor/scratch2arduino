# This is not ver general_purpose yet...
# Have the app ping the CDN every 30 seconds; track when the student clicks for an update as well.
# Check for when a program's hash changes.

# TO DO 
    # - make sure to declare variables as global when expressing a script for a sprite
    # - make it so we can print out a script from a sprite's context

from scratch_blocks import *


class ScratchObject(object):
    def __init__(self, object_json):
        if object_json.get('info', {}).get('projectID'):
            self.project_id = object_json.get('info').get('projectID')
        else: 
            self.project_id = None
        self.name = object_json.get('objName')
        print("INSTANTIATING {}".format(self.name))
        self.state = {}
        self.scripts = []
        self.children = []
        for var in object_json.get('variables', []):
            self.state[var['name']] = var['value']
        for lis in object_json.get('lists', []):
            self.state[lis['listName']] = lis['contents']
        for script_json in object_json.get('scripts', []):
            self.scripts.append(ScratchScript.instantiate(script_json))
        for child_json in object_json.get('children', []):
            if child_json.get('objName'):
                self.children.append(ScratchObject(child_json))

    def __str__(self):
        return "<ScratchObject {}>".format(self.name)

    def __repr__(self):
        return "<ScratchObject {}>".format(self.name)

    def is_a_project(self):
        return self.project_id is not None

    def get_script(self, script_name):
        print("{} looking for script '{}'".format(self, script_name))
        for script in self.scripts:
            print("{} has script {}".format(self, script))
            if script.name == script_name:
                return script
        for child in self.children:
            script = child.get_script(script_name)
            if script: 
                return script
        return None

