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
                row.SeatsAvailable = row.SeatsAvailable -1


def write_assigned_seat_to_db(s):
    c.execute("update seating set name = " + s.Name + " where row = " + s.Parent.RowNumber + " and seat = " + s.SeatLetter)
    c.commit()


def search_and_assign_most_suitable_seats(rows, booking_size, passenger_name):
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



def assign_seats_where_booking_size_less_than_or_equal_to_row_size(booking_size, rows, num_seats_per_row, passenger_name):

    booking_accomodated_altogether = search_and_assign_most_suitable_seats(rows, booking_size, passenger_name)

    if booking_accomodated_altogether == True:  # booking has been placed together in one row
        return

    # booking could not be placed all together in one row
    split_booking_across_rows(booking_size, rows, num_seats_per_row, passenger_name)


#
# def split_booking_across_rows_old(booking_size, rows, num_seats_per_row, passenger_name):
#
#     # split booking size into two groups
#
#     if booking_size % 2 == 0:
#         group_size = booking_size / 2
#     else:
#         group_size = (booking_size + 1) / 2
#
#     seats_left_to_fill = booking_size
#
#     while seats_left_to_fill > 0:
#         booking_for_group_1_accomodated = search_and_assign_most_suitable_seats(rows, group_size, num_seats_per_row,passenger_name)
#
#         if booking_for_group_1_accomodated == True:
#             seats_left_to_fill = seats_left_to_fill - group_size
#
#             if seats_left_to_fill == 0:
#                 return
#
#             group_size = seats_left_to_fill
#
#         else:
#             group_size = group_size - 1


def get_seat_availability_twos(rows):
    seat_availability_twos = dict()

    for row in rows:
        if row.SeatsAvailable == 2:
            seat_availability_twos[row.RowNumber] = row.SeatsAvailable


def get_seat_availability_threes(rows):
    seat_availability_threes = dict()

    for row in rows:
        if row.SeatsAvailable > 3:
            seat_availability_threes[row.RowNumber] = row.SeatsAvailable


def fill_seats_with_2_and_3_configurations(rows, num_seats_per_row, passenger_name, num_2_bookings, num_3_bookings):
    for i in range(0, num_2_bookings):
        booking_accomodated = search_and_assign_most_suitable_seats(rows, 2, passenger_name)
        if booking_accomodated == False: raise Exception("Booking was not accommodated despite passing sufficienct space checks.")

    for i in range(0, num_3_bookings):
        booking_accomodated = search_and_assign_most_suitable_seats(rows, 3, passenger_name)
        if booking_accomodated == False: raise Exception("Booking was not accommodated despite passing sufficienct space checks.")



def  split_booking_between_twos_and_threes(booking_size, rows, num_seats_per_row, passenger_name):

    seat_availability_twos = get_seat_availability_twos(rows) # reasoning: every number > 1 can be expressed as a sum of 2s and 3s
    seat_availability_threes = get_seat_availability_threes(rows)

    if seat_availability_threes.size != 0 or seat_availability_twos.size != 0:
        booking_size_mod_2 = booking_size % 2
        booking_size_mod_3 = booking_size % 3

        if booking_size_mod_2 == 0:
            num_2_bookings = booking_size / 2
            num_3_bookings = 0

            if seat_availability_twos >= num_2_bookings:
                fill_seats_with_2_and_3_configurations(rows, num_seats_per_row, passenger_name, num_2_bookings, num_3_bookings)
                return True

        if booking_size_mod_2 == 1:
            num_2_bookings = (booking_size - 3)/2
            num_3_bookings = 1

            if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
                fill_seats_with_2_and_3_configurations(rows, num_seats_per_row, passenger_name, num_2_bookings, num_3_bookings)
                return True

        if booking_size_mod_3 == 0:
            num_2_bookings = 0
            num_3_bookings = booking_size / 3

            if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
                fill_seats_with_2_and_3_configurations(rows, num_seats_per_row, passenger_name, num_2_bookings, num_3_bookings)
                return True

        if booking_size_mod_3 == 1:
            num_2_bookings = 2
            num_3_bookings = (booking_size - 4)/3

            if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
                fill_seats_with_2_and_3_configurations(rows, num_seats_per_row, passenger_name, num_2_bookings, num_3_bookings)
                return True

        if booking_size_mod_3 == 2:
            num_3_bookings = (booking_size - 2) / 3
            num_2_bookings = 1

            if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
                fill_seats_with_2_and_3_configurations(rows, num_seats_per_row, passenger_name, num_2_bookings, num_3_bookings)
                return True

    return False


def split_booking_across_rows(booking_size, rows, num_seats_per_row, passenger_name):

    booking_successful = split_booking_between_twos_and_threes(booking_size, rows, num_seats_per_row, passenger_name)

    if booking_successful:
        return

    seats_left_to_fill = booking_size
    subgroup_size = max(booking_size -2, 2) # booking_size = 2 --> subgroup = 2; booking_size == 3 --> subgroup = 2; booking_size > = 4 --> subgroup >= 2

    while seats_left_to_fill > 0:
        booking_for_subgroup_accomodated = search_and_assign_most_suitable_seats(rows, subgroup_size, passenger_name)

        if booking_for_subgroup_accomodated == True:

            if subgroup_size == 1:
                passengers_misplaced = passengers_misplaced + 1

            seats_left_to_fill = seats_left_to_fill - subgroup_size

            if seats_left_to_fill == 0:
                return

             subgroup_size = seats_left_to_fill

        else:
            subgroup_size = subgroup_size - 1



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