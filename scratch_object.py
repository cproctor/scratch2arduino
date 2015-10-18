# This is not ver general_purpose yet...
# Have the app ping the CDN every 30 seconds; track when the student clicks for an update as well.
# Check for when a program's hash changes.

from scratch_blocks import *

TYPE_TRANSLATIONS = {
    "int": "int",
    "str": "String",
    "unicode": "String",
    "float": "float"
}

class ScratchObject(object):
    def __init__(self, object_json):
        if object_json.get('info', {}).get('projectID'):
            self.project_id = object_json.get('info').get('projectID')
        else: 
            self.project_id = None
        self.name = object_json.get('objName')
        self.state = {}
        self.scripts = []
        self.children = []
        self.translation_errors = []
        for var in object_json.get('variables', []):
            self.state[clean_name(var['name'])] = var['value']
        for lis in object_json.get('lists', []):
            self.state[clean_name(lis['listName'])] = lis['contents']
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
        for script in self.get_scripts():
            if script.name == script_name:
                return script

    def get_scripts(self):
        all_scripts = []
        all_scripts += self.scripts
        for child in self.children:
            all_scripts += child.scripts
        return all_scripts

    def get_state(self):
        state = {}
        state.update(self.state)
        for child in self.children:
            state.update(child.get_state())
        return state

    def state_to_arduino(self, exclude=None, include=None, indent=0):
        translations = []
        if not exclude:
            exclude = []
        for key, val in self.get_state().items():
            if (key in exclude) or (include and (key not in include)):
                continue
            if isinstance(val, list):
                type_sigs = list(set(type(i).__name__ for i in val))
                if len(type_sigs) == 1:
                    type_sig = type_sigs[0]
                elif len(type_sigs) == 0:
                    type_sig = 'int'
                    self.warn("Could not infer type for empty list {}".format(key))
                else:
                    type_sig = type_sigs[0]
                    self.warn("Not all items in list {} are of type {}".format(key, type_sig))

                translations.append("{} {}[{}] = {{ {} }};".format(
                    TYPE_TRANSLATIONS[type_sig], 
                    clean_name(key), len(val), ", ".join(json.dumps(v) for v in val)
                ))
            else:
                type_sig = type(val).__name__
                translations.append("{} {} = {};".format(
                    TYPE_TRANSLATIONS[type_sig], clean_name(key), json.dumps(val)
                ))
        return "\n".join(" " * indent + t for t in translations)

    def warn(self, warning):
        self.translation_errors.append(warning)
                    
                    
                   
     
