# VTOL interface 🚁+✈

## Place and period of internship:

NTI Center for Component «Technologies robotics and mechatronics», unmanned technology laboratory.
The Unmanned Technology Laboratory develops specialized robotic systems designed for specific tasks
in a variety of applications. The field of special robotics includes both the sphere of interaction
with a person and the replacement of a person in hazardous and harmful operations, such as work on
nuclear reactors or in the immediate vicinity of hazardous substances and emissions, work on oil
production plants, maintenance of infrastructure in difficult natural conditions, work under extreme
weather conditions and strong magnetic fields.

## Technical task

## A little bit of theory

**VTOL** (Vertical Take-Off and Landing) — aircraft is one that can hover, take off, and land
vertically. This classification can include a variety of types of aircraft including fixed-wing
aircraft as well as helicopters and other aircraft with powered rotors, such as
cyclogyros/cyclocopters and tiltrotors

**UAVCAN** is an open technology for intra-corporate distributed computing and real-time 
communication, based on modern network standards (Ethernet, CAN FD, etc.). It was created 
to solve the problem of onboard deterministic computing and data distribution in next-generation
intelligent vehicles: manned and unmanned aircraft, spacecraft, robots and cars.

## AIRFRAME.JSON
We have a configuration file, thanks to which we can determine which devices(nodes) we will have, 
as well as which VTOL we use.

**Example:**
```
{
  "elvator_right": {
    "id": 66,
    "name": "R_elvator",
    "fields": [
      "voltage uavcan.equipment.power.CircuitStatus voltage"
    ],
    "channels": "[5]",
    "params": [
      "A1_ch/mode 5",
      "A1_min 2000",
      "A1_max 1000",
      "A1_def 2000"
    ]
  },
  "engine": {
    "id": 70,
    "name": "engine",
    "fields": [
      "voltage uavcan.equipment.power.CircuitStatus voltage",
      "rpm uavcan.equipment.ice.reciprocating.Status engine_speed_rpm",
      "fuel uavcan.equipment.ice.FuelTankStatus available_fuel_volume_percent"
    ]
  },
  "vtol_object": 1
}
```  
«vtol_object» - responsible for selecting the VTOL of the device


## Revisions

### v4.0
- [It's him](https://github.com/PrincePepper/inno_uavcan_VTOL_interface/commit/d3126e953a19e12e2fc243077761847a5c8144d0)
```
1) Revision of the new file structure.
2) There are no buttons for saving a file and restarting CAN devices yet.
3) Minor bugs were fixed, but it's not a fact that everything
4) While the control widget is disabled, it will most likely be deleted later
```
The first release of the project was made😻:
```
The first prototype of the program was implemented. It has an implementation (crutch)
of displaying the VTOL image of the device. There is a Scroll menu with UAVCAN. 
All the configuration takes place thanks to the JSON file, and there is also a certain
implementation of testing this file.
```
### v3.0
- [It's him](https://github.com/PrincePepper/inno_uavcan_VTOL_interface/commit/70329a0bf080ac9649b3bc72fbf0a5602e46741a)
```
 1) the project structure was redesigned, the official UAVCAN repository was taken as a basis
 2) the application design was redesigned
 3) automatic connection of sliders to nodes has been made, but crookedly, it will be redone
 4) fixed bugs and fixes
```

### v2.0
- [It's him](https://github.com/PrincePepper/inno_uavcan_VTOL_interface/commit/712ecef025f5e7de4d2562ffaf8b42499a45cead)
```
 1) new JSON structure of airframe file:
  - stores all the nodes
  - information about the position of the ailerons and rudders
 2) Now the presence of voltage  is optional and appears only if it is present on the device
 3) Refactoring of the code was carried out all this is supported by comments for greater readability
 4) Update file "data_type" it is planned to use as a checker of data types in the future
 5) Add TODO where code improvement and fixing is required
 
 This is a version where nodes are displayed on top of the image in certain places, and on the right 
 there is a control widget that has not yet been fully completed
```
### v1.0
```
the code was written on my knees, which somehow worked, but we were not satisfied with it, 
so read the next version
```


The initial release.

***the project was released for our internship in Innopolis***

## Responsible for the project

- [Semen Sereda](https://github.com/PrincePepper)
- [Alexander Terletsky](https://github.com/GinormousSalmon)

## Our teachers - mentors

- [Kostya😎](https://github.com/sainquake)
- [Dima P.👨‍💻](https://github.com/PonomarevDA)
- [Ayrat🧑‍🔬](https://github.com/beljjay)
- [Dima D.👨‍✈️](https://github.com/GigaFlopsis)
