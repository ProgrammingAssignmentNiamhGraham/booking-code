import sqlite3
import csv

db_name = "airline_seating.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()
print("Opened database successfully.")

#[('CREATE TABLE metrics (passengers_refused int, passengers_separated int)',)]
#[('CREATE TABLE seating (\nrow int not null,\nseat char(1) not null,\nname varchar(255),\nconstraint prim_key primary key (row, seat)\n)',)]
#[('CREATE TABLE rows_cols (nrows int, seats varchar(16))',)]


def importdb(db):

    c.execute("SELECT name FROM sqlite_master WHERE type='table';")

    tables = c.fetchall()

    print(tables)

    return 1



def read_bookings(bookings_filename):
    bookings = []
    with open(bookings_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            bookings.append(row)
    return bookings


def get_seating_plan():
    c.execute("select * from rows_cols")
    seating_plan = c.fetchall()
    return seating_plan


def read_previous_bookings(num_rows, num_seats_in_row):
    c.execute("select * from seating")
    seating_plan = c.fetchall()

    seats = []

    for s in seating_plan:
        seats.append([ s[0], s[1], s[2]])


    return seats

def assign_customer_to_row(passenger_name, booking_size, seats):

    count_assigned = 0

    while count_assigned < booking_size:
        for s in seats:
            write_assigned_seat_to_db(s)


def write_assigned_seat_to_db(s):
    s = s
    # write seat to db


def assign_seating(booking, seats, num_seats_per_row):
    passenger_name = booking[0]
    booking_size = booking[1]

    if booking_size <= num_seats_per_row:
        for seat in seats:
            if seat[2] == "":  # searching for any other row which can accommodate the booking
                assign_customer_to_row(passenger_name, seat, booking_size)



bookings_list = read_bookings("bookings.csv")
seating_plan = get_seating_plan()

num_rows = seating_plan[0][0]
cols = list(seating_plan[0][1])

all_rows = read_previous_bookings(num_rows, len(cols))

total_empties = 0
passengers_refused = 0
passengers_misplaced = 0

for row in range(1, len(all_rows) + 1):
    total_empties += row.SeatsAvailable

for booking in bookings_list:
    assign_seating(booking, all_rows, cols)


#print(bookings)



