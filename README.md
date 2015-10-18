# scratch2arduino

The `scratch_blocks` and the `scratch_object` modules can parse the JSON 
representation of a Scratch project, and then expresses it as code for Arduino. 
The app returns code formatted for a specific upcoming workshop.

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

## Limitations

- All variables are treated as global. 
- Scratch does not have well-defined types. scratch2arduino tries to infer
  types, defaulting to int. You may need to modify the type of variables
  in Arduino by hand. Similarly, all lists are considered integer lists unless
  every element of the list has a different consistent type. 
