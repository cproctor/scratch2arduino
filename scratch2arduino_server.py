# Note: log everything in sqlite!


from flask import Flask
from scratch_object import *
import requests
import json
from jinja2 import Environment, FileSystemLoader
from os.path import dirname, realpath
import traceback
import logging
import datetime

log = logging.getLogger(__name__)
handler = logging.FileHandler("/var/log/scratch2arduino.log")
log.addHandler(handler)
log.setLevel(logging.INFO)


class NotFoundError(Exception):
    pass

env = Environment(loader=FileSystemLoader(dirname(realpath(__file__))))
program_template = env.get_template("neopixel_template.html")
base_template = env.get_template("base_template.html")
landing_template = env.get_template("landing_template.html")
app = Flask(__name__)

excluded_vars = [
"acceleration",
  "colorOffset",
  "isMoving",
  "howManyLights",
  "mainColor",
  "mainColorValue",
  "lightColor",
  "myLightNumber",
  "lightMode",
  "secondColorValue",
  "lightIndex",
  "secondColor",
  "ready",
  "changeInAcceleration",
  "speed"
]

excluded_scripts = [
    "waitATick",
    "setLightToRgb",
    "findMainAndSecondColors",
    "loop",
    "setup",
    "findColorOffset",
    "turnOffLight",
    "turnOnLight",
    "setupLights",
    "scaleColorValues",
    "reset"
]

def include_script(script):
    if not script.name:
        return False
    if script.name in excluded_scripts:
        return False
    if isinstance(script, EventBinding):
        return False
    return True

def change_indent(code, spaces):
    statements = code.split("\n")
    if spaces > 0:
        statements = [(" " * spaces) + s for s in statements]
    else:
        statements = [s[(spaces * -1):] for s in statements]
    return "\n".join(statements)

# We mocked reading the motion sensor with a variable. Time to undo that.
motion_sensor = False
unpatched_to_arduino = Equals.to_arduino
def patched_to_arduino(self):
    special_case = False
    if (isinstance(self.arg1, ReadVar) and self.arg1.varName == "isMoving"):
        special_case = True
        val = self.arg2
    if (isinstance(self.arg2, ReadVar) and self.arg2.varName == "isMoving"):
        special_case = True
        val = self.arg1
    if special_case and isinstance(val, LiteralString):
        if val.value == "YES":
            return "motionSensor.moving()"
        else:
            return "!motionSensor.moving()"
    else:
        return unpatched_to_arduino(self)
Equals.to_arduino = patched_to_arduino
unpatched_init = Equals.__init__
def patched_init(*args, **kwargs):
    global motion_sensor
    motion_sensor = True
    unpatched_init(*args, **kwargs)
Equals.__init__ = patched_init

unpatched_rv_init = ReadVar.__init__
def patched_rv_init(self, *args, **kwargs):
    unpatched_rv_init(self, *args, **kwargs)
    if self.varName == "acceleration":
        global motion_sensor
        motion_sensor = True
ReadVar.__init__ = patched_rv_init
unpatched_rv_to_arduino = ReadVar.to_arduino
def patched_rv_to_arduino(self):
    if self.varName == "acceleration":
        return "motionSensor.intensity()"
    else:
        return unpatched_rv_to_arduino(self)
ReadVar.to_arduino = patched_rv_to_arduino
    

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
    try:
        return landing_template.render()
    except e: 
        return traceback.format_exc()

def scratch_project_json_to_arduino(scratch_project):
    project = ScratchObject(scratch_project)
    init_vars = project.state_to_arduino(exclude=excluded_vars, indent=0)
    setup = project.get_script("setup").block.to_arduino()
    loop = project.get_script("loop").block.to_arduino()
    helpers = "\n".join(s.to_arduino() for s in project.get_scripts() if include_script(s))
    return program_template.render(
        init_vars=init_vars, 
        setup=setup, 
        loop=loop, 
        helpers=helpers, 
        motion_sensor=motion_sensor
    )

@app.route('/translate/<int:scratch_id>')
def translate(scratch_id):
    try:
        project_json = get_scratch_project(scratch_id)
        program = scratch_project_json_to_arduino(project_json)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log.info(json.dumps({"time": now, "project": project_json}))
        return baes_template.render(
            program=program,
            project_id=scratch_id
        )
    except Exception, e:
        return "<h1>Something went wrong:</h1> <pre>{}</pre>".format(traceback.format_exc())

if __name__ == '__main__':        
    app.run()
