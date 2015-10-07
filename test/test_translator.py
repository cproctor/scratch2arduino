from translator import *
import json

with open('test_cases.json') as testfile:
    test_data = json.load(testfile)

for expression in test_data['expressions']:
    print("EXPRESSION: {}".format(expression))
    exp = ScratchExpression.instantiate(expression)
    print(exp.to_arduino())
    
for statement in test_data['statements']:
    print("STATEMENT: {}".format(statement))
    st = ScratchStatement.instantiate(statement)
    print(st.to_arduino())
    
for script in test_data['scripts']:
    print("SCRIPT: {}".format(script))
    sc = ScratchScript.instantiate(script)
    print(sc.to_arduino())
    
with open('sample_project.json') as projectfile:
    project_json = json.load(projectfile)
    project = ScratchObject(project_json)
    script = project.get_script("instructions_for_each_update")
    print(script.to_arduino())



