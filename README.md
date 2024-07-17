# person-and-colour-detection-alarm-system
Created for Apocalypse Toronto Hackathon 2024

## General Process Of Project:
Motion sensor activates, LED turns on
Camera sends information to a python script, where object and colour detection occurs
A Flask web server is used to display the updated stream 
If a person has a border box that's dominantly green, script sends an HTTP GET request to ESP32 which is connected to wifi
When signal message "1" is received, the buzzer will play a brief melody.

Cooldowns on the HTTP GET request are in place to prevent spam of requests

YOLO files taken from https://pjreddie.com/darknet/yolo/, uses v3. Make sure to download the cfg, weights, and names files and place in same folder as the .py file. 
Add the file location into the python script. 

```
@misc{darknet13,
  author =   {Joseph Redmon},
  title =    {Darknet: Open Source Neural Networks in C},
  howpublished = {\url{http://pjreddie.com/darknet/}},
  year = {2013--2016}
}
```

