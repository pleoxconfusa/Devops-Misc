# -*- coding: utf-8 -*-
"""
Cisco Config Modifier

Cyrus Jian Bonyadi
"""

from netmiko import ConnectHandler
import getpass


#setup var for global variables
connection = None;
state = "setup";
cur_switch = "";
err_count = 0;
err_limit = 5;

def get_details():
    """
    get_details gets credentials from the user to begin the process. 
    this method contains no error checking, so don't mess it up.
    
    Args:
        None.
    Returns:
        A list of switch names.
        A string username.
        A string password.
    """
    global state;
    
    switch_names = [];
    
    name = input("\nSwitches:\n");
    
    while name:
        switch_names.append(name);
        name = input();
    
    state = "next";
    
    return switch_names, input("\nUsername:\n"), getpass.getpass("\nPassword:\n");
    

#open connection to switch
def open_connection(username, password):
    """
    This open_connection method opens and returns a connection to global cur_switch.
    Args:
        A username string
        A password string
    Returns:
        A netmiko connection to a switch
    """
    global connection, state, cur_switch, err_count, err_limit;
    
    switch = {
        'device_type': 'cisco_ios',
        'ip':   cur_switch,
        'username': username,
        'password': password,
        'port' : 22,          # optional, defaults to 22
        'secret': '',     # optional, defaults to ''
        'verbose': False,       # optional, defaults to False
    }
    
    
    if err_count < err_limit:
        try:
            connection = ConnectHandler(**switch);
            state = "init";
            print('Connected to ' + cur_switch + ".");
            err_count = 0;
            return connection;
            
        except Exception as e:
            err_count += 1;
            print(e);
    
    else:
        print("Could not connect to " + cur_switch + ".");
        err_count = 0;
        state = "next";
        return;
        
        
        
#issues commands and returns output from inputted command, could be null if nothing is returned.
def issue(command):
    """
    This issues commands to connections.  This method is easier to type.
    Args:
        String: A command.
    Returns:
        String: command output.
    """
    global connection;
    return connection.send_command(command);
        
        
        
#issues commands and returns output from inputted command, could be null if nothing is returned.
def issue_cft(command):
    """
    This issues conf t commands to connections.  We like this method more.
    Args:
        String: A command.
    Returns:
        String: command output.
    """
    global connection;
    return connection.send_config_set(command);


def controller_init():
    """
    The controller_init method is designed to begin a connection with a switch,
    making it ready for the looping of a switch.
    Args:
        None.
    Returns:
        A list of tuples.
    """    
    global state;
    print("init.");
    
    #controller init: call show lldp nei 
    device_text = issue("show lldp nei");
    
    interfaces = [];    
    #grab all Device ID's and Local Intf as tuples where Capability is W
    for line in device_text.splitlines():
        #check to see if we're on the right line in the first place
        if len(line) > 47:
            #see if it's a wireless
            if line[46] == "W": #cisco specific
                #grab the name and the interface and put it on the list.
                interfaces.append((line[0:20].strip(),line[20:35].strip()));
    
    print("Found:");
    print(interfaces);
    
    state = "update";
    
    return interfaces;


def determine_exclusion(list):
    """
    This method presents the contents of a list then asks for input on which elements to skip.
    Args:
        A list.
    Returns:
        A list of equal or lesser size.
    """
    index = 0;
    for item in list:
        print(index, "\t", item);
        index += 1;
        
    exclude = input("Enter the list numbers you'd like to exclude, separated by spaces.\n").split();
    
    return_list = [];
    
    for i in range(len(list)):
        if str(i) not in exclude:
            return_list.append(list[i]);
            
    
    
    return return_list;
    


#update interface function: grab tuple 
def controller_update(interfaces):
    """
    For each interface, run the ocmmands specified in the script.
    This now prompts you to exclude some interfaces.
    Args:
        List: Tuples of description and interface
    Returns:
        Nothing.
    """
    global state;
    print("updating.");
    
    #Let's ask which interfaces to skip.
    interfaces = determine_exclusion(interfaces);
    
    
    for intf in interfaces:
        print("Modifying:");
        print(intf);
        #issue: do sh run int tuple[1]
        run_cfg = issue("sh run int " + intf[1]);
        
        #out of this output, we need to grab:
            #switchport access vlan ###
        for line in run_cfg.splitlines():
            if line[0:24].strip() == "switchport access vlan":
                vlan_id = line[24] + "2";   
        
        #issue: int tuple[1]
        #issue: shut
        issue_cft("int " + intf[1] 
                + "\nshut"
                + "\nexit");
        
        #issue: default tuple[1]
        #issue: int tuple[1]
        #issue: description tuple[0]
        #issue: switchport access vlan #2(from before)
        #issue: switchport mode access
        #issue: no sh
        issue_cft("default int " + intf[1] 
                + "\nint " + intf[1]
                + "\ndescription " + intf[0]
                + "\nswitchport access vlan " + vlan_id
                + "\nswitchport mode access"
                + "\nno sh"
                + "\nexit");
        
        print("\tdone.");
        
    
    state = "end";

    return;

#controller end: issue: end
def controller_end(switches):
    """
    Ends the controller and ends the program.
    
    Args:
        The list of switches
    Returns:
        None.
    """
    global state, cur_switch, connection;
    
    print('end.');    
    connection.disconnect();
    connection = None;
    cur_switch = "";
    
    state = "next";
    
    return;




def next_switch(switches):
    """
    Next_switch method pops the switches list into cur_switch.
    
    Args:
        List of switch strings.
    Returns:
        Nothing.
    """
    
    global state, cur_switch;
    
    
    
    #If we have switches left to connect to, let's do it otherwise end.
    if switches:
        cur_switch = switches.pop(0);
        state = "connect";
    else:
        state = "";
    
    return;


# Controller: 
def controller():
    """
    This is the controller for the entire program.
    Args:
        None
    Returns:
        None
    """
    global connection, state;
    
    while True:
        if state == "setup":
            # setup
            switches, username, password = get_details();
            
        elif state == "next":
            next_switch(switches);
            
        elif state == "connect":
            connection = open_connection(username, password);
        
        elif state == "init":
            # init.
            interfaces = controller_init();
        
        elif state == "update":
            # call update
            controller_update(interfaces);
            
        elif state == "end":
            # call end
            controller_end(switches);
        
        else:
            break;
        



# main
def main():
    """
    Our main should just initiate the
    controller.
    """
    controller(); #run the controller
    
    
if __name__== "__main__":
    main();
