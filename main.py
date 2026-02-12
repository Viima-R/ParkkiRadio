import sqlite3
import threading
import time

'''
HUOM! Keskeneräinen puuttuu vielä miten id_value saadaan inputattua.
'''



db_name = "test.db" #database name

time_amount = 5 # 2h30min in seconds(9000)

active_timers = {} #dictionary for parked cars timers

overtime = False #This boolean is used to determine what to do when timer goes over no fucntionality yet

file_name = "tpms.txt"


def id_in_db(id_value): #function for determining if detected ID in DB
    conn = sqlite3.connect(db_name)     #Connection
    cursor = conn.cursor()              #to database
    cursor.execute("SELECT 1 FROM tbl1 WHERE id = ?", (id_value,)) #returns 1 if found
    result = cursor.fetchone() #If found variable result is 1 if not its "none"
    conn.close() #close connection
    return result is not None #function returns true if ID in db and false if ID not in DB


def overtime_reached(id_value): #threading timer calls this function if timer goes over thus changing the overtime variable to true. Deletes the timer from dictionary
    global overtime #specifies the global variable
    print(f"Overtime car ID {id_value} not seen again in 2h 30min")
    overtime = True #changes it to true
    active_timers.pop(id_value, None) #deletion

#DELETE LATER used for testing
'''
def get_id_from_sensor(): #function made for testing my test DB has IDs A123 and B123
    sample_ids = ["A123", "D123", "C123", "B123"]
    for id_value in sample_ids:
        yield id_value
        time.sleep(5)
'''


def start_or_cancel_timer(id_value): #function to start timer when new car is detected and delete when it leaves

    # If a timer already exists for this ID you can assume the car is leaving parking and can delete timer
    if id_value in active_timers: #is id in active timers dictionary
        active_timers[id_value].cancel() #cancel timer
        active_timers.pop(id_value, None) #remove entry from dictionary
        print(f"Cancelled {id_value} left parking. Timer removed")
        return #exits the functions without adding another timer

    # If not then start a new timer
    timer = threading.Timer(time_amount, overtime_reached, args=[id_value])  #creating a new timer
    active_timers[id_value] = timer #new entry to dictionary for the ID
    timer.start() #starts the timer
    print(f"Started timer for new car {id_value}")

def check_for_new_id(): #function to continuously check the tpms text file for additions
    print("a")
    while True: # repeats endlessly, takes a 1s(voi muuttaa jos on liian raskas) break inbetween can change if its too taxing
        try:
            with open(file_name, "r") as f: #opens the ID file in read mode
                lines = f.readlines()       #creates list of lines

            if lines:  # If file has IDs in it
                print(f"\nFound {len(lines)} new IDs in file") 
                for line in lines:
                    id_value = line.strip()
                    if not id_value:
                        continue

                    print(f"Sensed ID from file: {id_value}")

                    if not id_in_db(id_value):
                        start_or_cancel_timer(id_value)
                    else:
                        print("Known ID, ignoring.")

                # Clear the file after processing
                open(file_name, "w").close()

        except FileNotFoundError:
            # File might not exist yet — that's fine
            pass

        time.sleep(1)  # check every second


#Main loop for testing
'''
for id_value in get_id_from_sensor(): #Goes through the values in the testing function and sees if they're in the db or not
    print(f"Captured ID: {id_value}")

    if not id_in_db(id_value):
        start_or_cancel_timer(id_value)
    else:
        print(f"Known car, ignoring")

    print(f"Overtime value: {overtime}")
    print(f"Active timers: {list(active_timers.keys())}")
    print("*" * 40)
    '''

#main program that runs the check_for_new_id function that should stay running
check_for_new_id()