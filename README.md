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
  "motor_front_left": {
    "id": -1,
    "item": 1,
    "name": "FL_motor",
    "turnovers": "",
    "voltage": "uavcan.equipment.power.CircuitStatus voltage"
  },
  "engine": {
    "id": -1,
    "item": 15,
    "name": "engine",
    "fuel level": ""
  },
  "_control_widget": {
    "motor_front_left": -1,
  },
  "vtol_object": 1
}
```
«_control_widget» - responsible for connections to control sliders and their default values  
«vtol_object» - responsible for selecting the VTOL of the device


## Revisions

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
