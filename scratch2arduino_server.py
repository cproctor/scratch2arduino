# Note: log everything in sqlite!


from flask import Flask
from scratch_object import ScratchObject
import requests
import json

class NotFoundError(Exception):
    pass

app = Flask(__name__)

def get_scratch_project(scratch_id):
    response = requests.get("http://cdn.projects.scratch.mit.edu/internalapi/project/{}/get/".format(scratch_id))
    if response.ok:
        return response.json()
    elif response.status_code == 404:
        raise NotFoundError("Invalid project ID")
    else:
        return 0
    

@app.route('/')
def landing():
    return "HELLO"

@app.route('/translate/<int:scratch_id>')
def translate(scratch_id):
    try:
        project_json = get_scratch_project(scratch_id)
        project = ScratchObject(project_json)
        script = project.get_script("instructions_for_each_update")
        return """
<!DOCTYPE html>
    <head></head>
    <body>
        <pre>{}</pre>
    </body>
</html>
    """.format(script.to_arduino())
    except:
        return "Something went wrong."

        
app.run()
