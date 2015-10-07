# scratch2arduino

The `scratch_blocks` and the `scratch_object` modules can parse the JSON 
representation of a Scratch project, and then expresses it as code for Arduino. 

The app uses these modules for a specific purpose in an upcoming workshop; 
it searches for a script in the project named `instructions_for_each_update` 
and translates this script.

## Install and Run

    git clone https://github.com/cproctor/scratch2arduino.git
    cd scratch2arduino
    sudo pip install flask requests
    python scratch2arduino_server.py

## Usage

First, log in to Scratch and remix the [NeoPixel Base Simulation](https://scratch.mit.edu/projects/79412942).
Then, with the app running, go to 
[http://127.0.0.1:5000/translate/79412942](http://127.0.0.1:5000/translate/79412942), 
but use your project's ID instead.

