import sqlite3
import csv

db_name = "airline_seating.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()
passengers_refused = 0
passengers_misplaced = 0

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
                count_assigned += 1
                write_assigned_seat_to_db(s)



def write_assigned_seat_to_db(s):
    c.execute("update seating set name = " + s.Name + " where row = " + s.Parent.RowNumber + " and seat = " + s.SeatLetter)
    c.commit()


def search_and_assign_most_suitable_seats(rows, booking_size, num_seats_per_row, passenger_name):
    for row in rows:  # searching for a row with the exact amount of seats to accommodate booking
        if row.SeatsAvailable == booking_size:
            assign_customer_to_row(passenger_name, row, booking_size)
            return True

    for row in rows:
        if row.SeatsAvailable >= booking_size + 2:  # searching for a row with the number of seats + 2 to leave space for a pair to also be accomodated
            assign_customer_to_row(passenger_name, row, booking_size)
            return True

    for row in rows:
        if row.SeatsAvailable > booking_size:  # searching for any other row which can accommodate the booking
            assign_customer_to_row(passenger_name, row, booking_size)
            return True

    return False    # no row has available seating



def assign_seating_old(booking, rows, num_seats_per_row, total_empties):
    passenger_name = booking[0]
    booking_size = booking[1]

    if booking_size > total_empties:
        passengers_refused += booking_size
        return

    if booking_size <= num_seats_per_row:
        booking_accomodated = search_and_assign_most_suitable_seats(rows, booking_size, num_seats_per_row, passenger_name)

        if booking_accomodated == True:
            return

    if booking_size == 2:
        booking_accomodated_1 = search_and_assign_most_suitable_seats(rows, 1, num_seats_per_row, passenger_name)
        booking_accomodated_2 = search_and_assign_most_suitable_seats(rows, 1, num_seats_per_row, passenger_name)

        if booking_accomodated_1 == True and booking_accomodated_2 == True:
            return

        raise Exception('Booking size less than total available seats yet code was unable to allocate seating.')

    if booking_size == 3:
        booking_for_two_accomodated = search_and_assign_most_suitable_seats(rows, 2, num_seats_per_row, passenger_name)

        if booking_for_two_accomodated == True:
            booking_for_one_accomodated = search_and_assign_most_suitable_seats(rows, 1, num_seats_per_row, passenger_name)

            if booking_for_one_accomodated == True:
                return

        booking_for_one_accomodated_1 = search_and_assign_most_suitable_seats(rows, 1, num_seats_per_row, passenger_name)
        booking_for_one_accomodated_2 = search_and_assign_most_suitable_seats(rows, 1, num_seats_per_row, passenger_name)
        booking_for_one_accomodated_3 = search_and_assign_most_suitable_seats(rows, 1, num_seats_per_row, passenger_name)

        if booking_for_one_accomodated_1 == True and booking_for_one_accomodated_2 == True and booking_for_one_accomodated_3 == True:
            return

        raise Exception('Booking size is less than total available seats yet code was unable to allocate seating.')

    if booking_size == 4:
        booking_for_two_accomodated_1 = search_and_assign_most_suitable_seats(rows, 2, num_seats_per_row,passenger_name)

        if booking_for_two_accomodated_1 == True:
            booking_for_two_accomodated_2  = search_and_assign_most_suitable_seats(rows, 2, num_seats_per_row, passenger_name)

            if booking_for_two_accomodated_2 == True:
                return

            booking_for_one_accomodated_1 = search_and_assign_most_suitable_seats(rows, 1, num_seats_per_row, passenger_name)
            booking_for_one_accomodated_2 = search_and_assign_most_suitable_seats(rows, 1, num_seats_per_row, passenger_name)

            if booking_for_one_accomodated_1 == True and booking_for_one_accomodated_2 == True:
                return
            raise Exception('Booking size is less than total available seats yet code was unable to allocate seating.')

        for i in range(0,4):
            booking_for_one_accomodated = search_and_assign_most_suitable_seats(rows, 1, num_seats_per_row, passenger_name)
            if booking_for_one_accomodated == False:
                raise Exception('Booking size is less than total available seats yet code was unable to allocate seating.')

        #
        # for row in range(1, len(rows) + 1): # searching for a row across which to split the booking
        #     if row.SeatsAvailable


    #if booking_size < len(cols):
        #for i in rows:


def split_booking_across_rows(booking_size, rows, num_seats_per_row, passenger_name):

    # split booking size into two groups

    if booking_size % 2 == 0:
        group_size = booking_size / 2
    else:
        group_size = (booking_size + 1) / 2

    seats_left_to_fill = booking_size

    while seats_left_to_fill > 0:
        booking_for_group_1_accomodated = search_and_assign_most_suitable_seats(rows, group_size, num_seats_per_row,passenger_name)

        if booking_for_group_1_accomodated == True:
            seats_left_to_fill = seats_left_to_fill - group_size

            if seats_left_to_fill == 0:
                return

            group_size = seats_left_to_fill

        else:
            group_size = group_size - 1


def assign_seats_where_booking_size_less_than_or_equal_to_row_size(booking_size, rows, num_seats_per_row, passenger_name):

    booking_accomodated_altogether = search_and_assign_most_suitable_seats(rows, booking_size, num_seats_per_row, passenger_name)

    if booking_accomodated_altogether == True:  # booking has been placed together in one row
        return

    # booking could not be placed all together in one row
    split_booking_across_rows(booking_size, rows, num_seats_per_row, passenger_name)


def assign_seating(booking, rows, num_seats_per_row, total_empties):
    passenger_name = booking[0]
    booking_size = booking[1]

    if booking_size > total_empties:
        passengers_refused += booking_size
        return

    if booking_size <= num_seats_per_row:
        assign_seats_where_booking_size_less_than_or_equal_to_row_size(booking_size, rows, num_seats_per_row, passenger_name)

    else:
        possible_bookings = []

        booking_size_modulo_seats_per_row = booking_size % num_seats_per_row

        num_rows_can_fill = (booking_size - booking_size_modulo_seats_per_row)/num_seats_per_row

        if booking_size_modulo_seats_per_row == 1:
            for i in range(0, num_rows_can_fill - 1):
                possible_bookings.append(num_seats_per_row)
            possible_bookings.append(num_seats_per_row -1)
            possible_bookings.append(2)
        else:
            for i in range(0, num_rows_can_fill):
                possible_bookings.append(num_seats_per_row)
            if booking_size_modulo_seats_per_row <> 0:
                possible_bookings.append(booking_size_modulo_seats_per_row)







bookings_list = read_bookings("bookings.csv")
seating_plan = get_seating_plan()

num_rows = seating_plan[0][0]
num_cols = len(list(seating_plan[0][1]))

all_rows = read_previous_bookings(num_rows, num_cols)

total_empties = 0

for row in all_rows:
    total_empties += row.SeatsAvailable

for booking in bookings_list:
    assign_seating(booking, all_rows, num_cols, total_empties)


#print(bookings)








def importdb(db):

    c.execute("SELECT name FROM sqlite_master WHERE type='table';")

    tables = c.fetchall()

    print(tables)

    return 1