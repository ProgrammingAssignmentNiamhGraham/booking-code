import sqlite3
import csv

db_name = "airline_seating.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()
print("Opened database successfully.")

#[('CREATE TABLE metrics (passengers_refused int, passengers_separated int)',)]
#[('CREATE TABLE seating (\nrow int not null,\nseat char(1) not null,\nname varchar(255),\nconstraint prim_key primary key (row, seat)\n)',)]
#[('CREATE TABLE rows_cols (nrows int, seats varchar(16))',)]

class Seat:
    Assigned = False
    Name = ""
    SeatLetter = ""

class Row:
    SeatsAvailable = int
    RowNumber = int
    Seats = list()




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

    rows = dict()

    for row_number in range(1, num_rows + 1):
        row = Row()
        row.RowNumber = row_number
        row.SeatsAvailable = num_seats_in_row
        rows[row_number]= row

    for s in seating_plan:
        seat = Seat()
        seat_row = s[0]
        seat.Seat_Letter = s[1]
        seat.Name = s[2]

        corresponding_row = rows[seat_row]

        if len(seat.Name) == 0:
            seat.Assigned = False
        else:
            seat.Assigned = True
            corresponding_row.SeatsAvailable = corresponding_row.SeatsAvailable - 1

        corresponding_row.Seats.append(seat)

    return rows

def assign_customer_to_row(passenger_name, row, booking_size):

    count_assigned = 0

    while count_assigned < booking_size:
        for s in row.Seats:
            if s.Assigned == False:
                s.Name = passenger_name
                s.Assigned = True
                count_assigned += 1;
                write_assigned_seat_to_db(s)

def write_assigned_seat_to_db(s):
    c.execute("update seating set name = " + s.Name + " where row = " + s.Parent.RowNumber + " and seat = " + s.SeatLetter)
    c.commit()


def search_and_assign_most_suitable_seats(rows, booking_size, cols, passenger_name):
    for row in range(1, len(rows) + 1):
        if row.SeatsAvailable > booking_size:  # searching for any other row which can accommodate the booking
            assign_customer_to_row(passenger_name, row, booking_size, cols)
            return True

    return False    # no row has available seating



def assign_seating(booking, rows, num_seats_per_row, total_empties, passengers_refused):
    passenger_name = booking[0]
    booking_size = booking[1]

    if booking_size > total_empties:
        passengers_refused += booking_size
        return

    if booking_size <= num_seats_per_row:
        booking_accomodated = search_and_assign_most_suitable_seats(rows, booking_size, cols, passenger_name)

        if booking_accomodated == True:
            return



        #
        # for row in range(1, len(rows) + 1): # searching for a row across which to split the booking
        #     if row.SeatsAvailable


    #if booking_size < len(cols):
        #for i in rows:





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
    assign_seating(booking, all_rows, num_rows, cols, total_empties, passengers_refused, passengers_misplaced)


#print(bookings)



