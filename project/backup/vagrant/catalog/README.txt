---
# Item Catalog App

---

## Introduction
This Item Catalog project aims to implement an application that provides a list of items variety of categories, as well as provide a user registration and authentication system.
The homepage displays all current categories along with the latest added items. By selecting a specific category, all the items available for that category will be shown. Also, the detailed description of a specific item wll be shown when you select a specific item.
After logging in, a user has the ability to add, update, or delete a category or a item info.
This application provides JSON endpoints.

---

## Prerequisites and Installation
### Prerequisites
1. [Git](https://git-scm.com/doc)
2. [VirtualBox](https://classroom.udacity.com/nanodegrees/nd004/parts/af045689-1d81-46e7-8a3b-ad05de1142ce/modules/353202897075460/lessons/3423258756/concepts/14c72fe3-e3fe-4959-9c4b-467cf5b7c3a0): You do not need the extension pack or the SDK. You do not need to launch VirtualBox after installing it; Vagrant will do that.
3. [Vagrant](https://www.vagrantup.com/):  Install the version for your operating system.

### Installation steps
1. Open your terminal:
    * Mac or Linux system: regular terminal program will do just fine.
    * Windows: use the Git Bash terminal that comes with the Git software, if you don't have Git installed, download Git from the link above.
2.  Install VirtualBox
3.  Install Vagrant
4.  Clone the VM configuration:
    * Change to the desired directory for you to run this project
        *  eg. Run: `cd ~/Desktop`
    * Run: `git clone  https://github.com/udacity/fullstack-nanodegree-vm. fullstack` in your terminal
5.  Clone this project:
    * Change to *vagrant* folder:
        * Run: `cd fullstack/vagrant/`
    * Clone this project:
        * Run: `git clone https://github.com/MomokoXu/Project-Tournament-Database.git tournament`
6. Start the virtual machine:
    * Run: `vagrant up`
---
### How to use it
1. Log into the VM:
    * Run:  `vagrant ssh`
2. Change directory for the files of this project:
    * Run: `cd /vagrant/project/catalog`
3. Run this app:
    * Run: python project.py
4. Open http://localhost:8000 in your browser.
---
## Future work
This project currently only support single tournament, in the future it is supposed to be extended to support multiple tournaments.

---

## Author
[Yingtao Xu](https://github.com/MomokoXu)

---
## Copyright
This is a project for practicing skills in databses and backend courses not for any business use. Some templates and file description are used from [Udacity FSND program](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004). Please contact me if you think it violates your rights.