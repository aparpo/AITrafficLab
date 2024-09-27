# AITrafficLab

**AITrafficLab** is a powerful and easy-to-use tool for coding and deploying multi-agent based solutions to traffic problems. It extends Mesa's functionalities by adapting them to the field of urban mobility. With AITrafficLab, users can create networks, manage swarms of vehicles by defining their logic once, and gather performance data. Not only vehicles can exhibit intelligent behavior; roads and junctions can also act as intelligent agents. View full documentation at [Read the Docs](https://aitrafficlab.readthedocs.io/en/latest/)

> **Note**  
> AITrafficLab currently supports only one traffic simulator: **Simulation of Urban Mobility (SUMO)**. To work with other traffic simulators, users may need to create their own connection class extending from the `Connection` class.

---

## Installation Guide

To use AITrafficLab, you first need to install a traffic simulator. For beginners, we highly recommend using **SUMO**. After understanding AITrafficLab's basic functions, you may try other simulators by creating a custom connection.

Follow the instructions in the SUMO installation guide to install SUMO.

After installing a traffic simulator, select your virtual environment and install AITrafficLab by running the following commands:

```bash
# Upgrade pip
pip install --upgrade pip

# Install AITrafficLab
pip install AITrafficLab

