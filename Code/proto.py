import sqlite3
import threading
import time


#Configuration
db_name = "test.db" #database name
file_name = "tpms.txt" #file where new IDs are saved

time_amount = 15 # 2h30min in seconds(9000)
pass_window = 10 # seconds

#Globals

active_timers = {} #dictionary for parked cars timers
overtime = False #This boolean is used to determine what to do when timer goes over no fucntionality yet
last_seen = {} #dictionary to track last detection time

lock = threading.Lock() #Protect shared dictionaries

#DB Check

def id_in_db(id_value): #function for determining if detected ID in DB
    conn = sqlite3.connect(db_name)     #Connection
    cursor = conn.cursor()              #to database
    cursor.execute("SELECT 1 FROM tbl1 WHERE id = ?", (id_value,)) #returns 1 if found
    result = cursor.fetchone() #If found variable result is 1 if not its "none"
    conn.close() #close connection
    return result is not None #function returns true if ID in db and false if ID not in DB

#Parking overtime action

def overtime_reached(carId): #threading timer calls this function if timer goes over thus changing the overtime variable to true. Deletes the timer from dictionary
    global overtime

    with lock:
        print(f"Overtime car ID {carId} not seen again in 2h 30min")
        overtime = True
        active_timers.pop(carId, None)

#Timer management

def start_or_cancel_timer(carId): #function to start timer when new car is detected and delete when it leaves
    with lock:
        # If a timer already exists for this ID you can assume the car is leaving parking and can delete timer
        if carId in active_timers: #is id in active timers dictionary
            active_timers[carId].cancel() #cancel timer
            active_timers.pop(carId, None) #remove entry from dictionary
            print(f"Cancelled timer, car: {carId} left parking. Timer removed")
            return #exits the functions without adding another timer

        # If not then start a new timer
        timer = threading.Timer(time_amount, overtime_reached, args=[carId])  #creating a new timer
        active_timers[carId] = timer #new entry to dictionary for the ID
        timer.start() #starts the timer
        print(f"Started timer for new car: {carId}")

#Filtering multiple readings from one car

def clear_last_seen(): #Clears last seen dictionary after set passing window
    now = time.time()
    to_delete = []
    with lock:
        for carId, timestamp in last_seen.items():
            if now - timestamp > pass_window:
                to_delete.append(carId)

        for carId in to_delete:
            del last_seen[carId]

def group_ids(id_value):
    carId = id_value[:3] #Takes the first 3 digits from the ID and assumes it is the same car
    now = time.time()

    clear_last_seen()

    with lock:
        if carId in last_seen:
            if now - last_seen[carId] < pass_window:
                print(f"Ignored {carId} multiple TPMS from one car detected")
                return
    
    last_seen[carId] = now
    start_or_cancel_timer(carId)

#File checker

def check_for_new_id(): #function to continuously check the tpms text file for additions
    print("a")
    while True: # repeats endlessly every 1 seconds
        try:
            with open(file_name, "r") as f: #opens the ID file in read mode
                lines = f.readlines()       #creates list of lines

            if lines:  # If file has IDs in it
                print(f"\nFound {len(lines)} new IDs in file") 
                for line in lines:
                    id_value = line.strip()
                    if not id_value:
                        continue

                    print(f"Found ID from file: {id_value}")

                    if not id_in_db(id_value):
                        group_ids(id_value)
                    else:
                        print("Known ID, ignoring.")

                open(file_name, "w").close() #Clears file

        except FileNotFoundError: #If file doesn't exist
            pass

        time.sleep(1)  # check every second

#main

if __name__ == "__main__":
    check_for_new_id()