import csv
import datetime
import os
import sys

#File
VEHICLE_FILE = "vehicle_log.csv"
CAPACITY = 20  # Slots for vehicles (you can change it)

#Ensure file exists with header
if not os.path.exists(VEHICLE_FILE):
    with open(VEHICLE_FILE, "w", newline="") as f:
        f.write("plate,date,time,iso_timestamp,status,slot\n")

# Helpers - load rows and compute latest record per plate (keys normalized to uppercase)
def load_rows_and_latest():
    rows = []
    if os.path.exists(VEHICLE_FILE):
        with open(VEHICLE_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
    latest = {}
    for r in rows:
        plate_key = r.get("plate", "").upper()
        try:
            ts = datetime.datetime.fromisoformat(r.get("iso_timestamp", ""))
        except ValueError:
            ts = datetime.datetime.min
        if plate_key not in latest or ts > latest[plate_key][0]:
            latest[plate_key] = (ts, r)
    latest_rows = {k.upper(): v[1] for k, v in latest.items()}
    return rows, latest_rows

def is_valid_plate(p):
    p = p.strip().upper()
    if not (1 <= len(p) <= 10):
        return False
    for ch in p:
        if not (('A' <= ch <= 'Z') or ('0' <= ch <= '9') or ch == '-'):
            return False
    return True

def occupied_slots(latest_rows):
    return {
        int(v["slot"])
        for v in latest_rows.values()
        if v.get("status", "").upper() == "IN" and v.get("slot", "").isdigit()
    }

#Append a record to CSV (ensures string values)
def append_record(plate, dt, status, slot):
    with open(VEHICLE_FILE, "a", newline="") as f:
        csv.writer(f).writerow([
            plate,
            dt.date().isoformat(),
            dt.time().replace(microsecond=0).isoformat(),
            dt.isoformat(),
            status,
            str(slot),
        ])

#LOG-IN SYSTEM
USERS = {
    "attendant": "123456789",
    "supervisor": "1234567890"
}

def login(role):
    """Login restricted to chosen role"""
    print("\n==============================")
    print("   Vehicle Parking Log System")
    print("===============================")
    username = input("Username: ").strip().lower()
    if username == "exit":
        return "exit"
    password = input("Password: ").strip()
    if username == role and USERS.get(username) == password:
        print("Login Success!\n")
        return role
    else:
        print("Invalid, please try again.\n")
        return None

#Attendant actions
def record_entry():
    _, latest_rows = load_rows_and_latest()
    active = sum(1 for v in latest_rows.values() if v.get("status", "").upper() == "IN")
    if active >= CAPACITY:
        print("Parking full. Cannot record new entry.")
        return

    raw_plate = input("Plate: ").strip().upper()
    if not is_valid_plate(raw_plate):
        print("Invalid plate. Use 1-10 chars, letters/digits/-.")
        return

    if raw_plate in latest_rows and latest_rows[raw_plate].get("status", "").upper() == "IN":
        print("This vehicle is already inside.")
        return

    occupied = occupied_slots(latest_rows)

    slot_input = input(f"Slot (1-{CAPACITY}): ").strip()
    if not slot_input.isdigit():
        print("Slot must be a number.")
        return
    s = int(slot_input)
    if s < 1 or s > CAPACITY:
        print("Slot out of range.")
        return
    if s in occupied:
        print("Slot is already occupied.")
        return

    dt = datetime.datetime.now()
    append_record(raw_plate, dt, "IN", slot_input)
    print("Entry recorded. Slot:", slot_input)

def record_exit():
    raw_plate = input("Plate: ").strip().upper()
    if not is_valid_plate(raw_plate):
        print("Invalid plate.")
        return

    slot_input = input(f"Slot (1-{CAPACITY}): ").strip()
    if not slot_input.isdigit():
        print("Slot must be a number.")
        return

    _, latest_rows = load_rows_and_latest()
    if raw_plate not in latest_rows or latest_rows[raw_plate].get("status", "").upper() != "IN":
        print("This vehicle is not currently inside.")
        return

    recorded_slot = latest_rows[raw_plate].get("slot", "")
    if slot_input != recorded_slot:
        print("Slot mismatch. Vehicle is recorded in slot", recorded_slot)
        return

    dt = datetime.datetime.now()
    append_record(raw_plate, dt, "OUT", slot_input)
    print("Exit recorded. Slot:", slot_input)

def show_slots():
    _, latest_rows = load_rows_and_latest()
    occupied = occupied_slots(latest_rows)
    print("\nSlot Status:")
    for s in range(1, CAPACITY + 1):
        print(f"Slot {s}: {'OCCUPIED' if s in occupied else 'AVAILABLE'}")

#Supervisor actions
def monitor_vehicle_list():
    _, latest_rows = load_rows_and_latest()
    print("\nLatest per plate:")
    for plate in sorted(latest_rows.keys()):
        r = latest_rows[plate]
        print(f"{r.get('plate',''):10} {r.get('date',''):10} {r.get('status',''):4} slot={r.get('slot','')}")

def generate_today_report():
    rows, latest_rows = load_rows_and_latest()
    active = sum(1 for v in latest_rows.values() if v.get("status", "").upper() == "IN")
    slots_left = max(CAPACITY - active, 0)
    today = datetime.date.today().isoformat()
    print("\nReport for", today)
    print("Capacity:", CAPACITY)
    print("Cars inside:", active)
    print("Slots left:", slots_left)
    print("Entries today:")
    for r in rows:
        if r.get("date", "") == today:
            print(r.get("iso_timestamp", ""), r.get("plate", ""), r.get("status", ""), "slot=" + r.get("slot", ""))

#Main program loop
def main():
    while True:
        print("\n==============================")
        print("   Vehicle Parking Log System")
        print("===============================")
        print("Select Role:")
        print("1. Attendant")
        print("2. Supervisor")
        print("3. Exit")
        role_choice = input("Choice: ").strip()

        if role_choice == "1":
            chosen_role = "attendant"
        elif role_choice == "2":
            chosen_role = "supervisor"
        elif role_choice == "3":
            print("Goodbye.")
            sys.exit(0)
        else:
            print("Invalid choice. Please select 1, 2, or 3.")
            continue

        #Login loop for chosen role
        user_role = None
        while user_role is None:
            user_role = login(chosen_role)
            if user_role == "exit":
                print("Goodbye.")
                sys.exit(0)

        print("Welcome to the Vehicle Parking Log System!")
        print("-------------------------------------")

        #Route based on role
        if user_role == "attendant":
            while True:
                print("\nParking Attendant Dashboard")
                print("1. Record Entry (IN)")
                print("2. Record Exit (OUT)")
                print("3. View Slot Availability")
                print("0. Logout")
                choice = input("Choice: ").strip()

                if choice == "1":
                    record_entry()
                elif choice == "2":
                    record_exit()
                elif choice == "3":
                    show_slots()
                elif choice == "0":
                    print("Logging out...")
                    break
                else:
                    print("Choose 1, 2, 3 or 0.")

        elif user_role == "supervisor":
            while True:
                print("\nSecurity Supervisor Dashboard")
                print("1. Monitor Vehicle List")
                print("2. Generate Today's Report")
                print("0. Logout")
                choice = input("Choice: ").strip()

                if choice == "1":
                    monitor_vehicle_list()
                elif choice == "2":
                    generate_today_report()
                elif choice == "0":
                    print("Logging out...")
                    break
                else:
                    print("Choose 1, 2 or 0.")
                    
try:
    main()
except KeyboardInterrupt:
    print("\nInterrupted. Exiting.")

