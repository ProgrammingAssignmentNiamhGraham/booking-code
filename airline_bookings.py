import sqlite3
import csv

global conn
global c

#[('CREATE TABLE metrics (passengers_refused int, passengers_separated int)',)]
#[('CREATE TABLE seating (\nrow int not null,\nseat char(1) not null,\nname varchar(255),\nconstraint prim_key primary key (row, seat)\n)',)]
#[('CREATE TABLE rows_cols (nrows int, seats varchar(16))',)]

class Seat:
    Assigned = False
    Name = str
    SeatLetter = str

    def __init__(self, seatLetter, name, assigned):
        self.Assigned = assigned
        self.Name = name
        self.SeatLetter = seatLetter

class Row:
    SeatsAvailable = int
    RowNumber = int
    Seats = list()

    def __init__(self, rowNumber, seatsAvailable):
        self.Seats = list()
        self.RowNumber = rowNumber
        self.SeatsAvailable = seatsAvailable

    def AddSeatToRow(self, seat):
        self.Seats.append(seat)



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
    seats_db = c.fetchall()

    rows = dict()

    for row_number in range(1, num_rows + 1):
        row = Row(row_number, num_seats_in_row)
        rows[row_number] = row

    for s in seats_db:
        rowNumber = s[0]
        seat_Letter = s[1]
        name = s[2]

        if len(name) == 0:
            assigned = False
        else:
            assigned = True

        seat = Seat(seat_Letter, name, assigned)

        for r in rows:
            if rows[r].RowNumber == rowNumber:
                rows[r].AddSeatToRow(seat)

                if len(seat.Name) != 0:
                    rows[r].SeatsAvailable = rows[r].SeatsAvailable - 1

    return rows

def assign_customer_to_row(passenger_name, row, booking_size):

    count_assigned = 0

    for s in row.Seats:
        if s.Assigned == False:
            s.Name = passenger_name
            s.Assigned = True
            count_assigned += 1
            write_assigned_seat_to_db(row, s)
            row.SeatsAvailable = row.SeatsAvailable -1

            if count_assigned == booking_size:
                return


def write_assigned_seat_to_db(row, seat):
    sql_text = "update seating set name = '" + seat.Name + "' where row = " + str(row.RowNumber) + " and seat = '" +seat.SeatLetter + "'"
    c.execute(sql_text)
    conn.commit()


def write_passenger_stats_to_db(passengers_refused, passengers_separated):
    sql_text = "update metrics set passengers_refused =" + str(passengers_refused) + ", passengers_separated = " + str(passengers_separated)
    c.execute(sql_text)
    conn.commit()




def check_for_space(booking_size, total_empties):
    if booking_size <= total_empties:
        return True

    return False

def assign_seating(booking_size, passenger_name, rows, num_seats_per_row):

    if booking_size <= num_seats_per_row:
        passengers_separated = assign_seats_where_booking_size_less_than_or_equal_to_row_size(booking_size, rows, num_seats_per_row, passenger_name)
    else:
        passengers_separated = assign_seats_where_booking_size_exceeds_row_size(booking_size, rows, num_seats_per_row, passenger_name)

    return passengers_separated


def search_and_assign_most_suitable_seats(rows, booking_size, passenger_name):
    for row in rows:  # searching for a row with the exact amount of seats to accommodate booking
        if rows[row].SeatsAvailable == booking_size:
            assign_customer_to_row(passenger_name,  rows[row], booking_size)
            return True

    for row in rows:
        if  rows[row].SeatsAvailable >= booking_size + 2:  # searching for a row with the number of seats + 2 to leave space for a pair to also be accomodated
            assign_customer_to_row(passenger_name,  rows[row], booking_size)
            return True

    for row in rows:
        if  rows[row].SeatsAvailable > booking_size:  # searching for any other row which can accommodate the booking
            assign_customer_to_row(passenger_name,  rows[row], booking_size)
            return True

    return False    # no row has available seating


def assign_seats_where_booking_size_less_than_or_equal_to_row_size(booking_size, rows, num_seats_per_row, passenger_name):

    booking_accomodated_altogether = search_and_assign_most_suitable_seats(rows, booking_size, passenger_name)

    if booking_accomodated_altogether == True:  # booking has been placed together in one row
        return 0

    # booking could not be placed all together in one row
    passengers_separated = split_booking_across_rows(booking_size, rows, num_seats_per_row, passenger_name)

    return passengers_separated


def get_seat_availability_twos(rows):
    seat_availability_twos = 0

    for i in rows:
        if rows[i].SeatsAvailable == 2:
            seat_availability_twos += 1

    return seat_availability_twos

def get_seat_availability_threes(rows):
    seat_availability_threes = 0

    for i in rows:
        if rows[i].SeatsAvailable >= 3:
            seat_availability_threes += 1

    return seat_availability_threes

def get_seat_availability_row_size(rows, num_seats_in_row):
    seat_availability_row_size = 0

    for i in rows:
        if rows[i].SeatsAvailable == num_seats_in_row:
            seat_availability_row_size +=1

    return seat_availability_row_size



def split_booking_across_rows(booking_size, rows, num_seats_per_row, passenger_name):

    booking_successful = split_booking_between_twos_and_threes(booking_size, rows, num_seats_per_row, passenger_name)
    passengers_separated = 0

    if booking_successful:
        return passengers_separated

    seats_left_to_fill = booking_size
    subgroup_size = max(booking_size -2, 2) # booking_size = 2 --> subgroup = 2; booking_size == 3 --> subgroup = 2; booking_size > = 4 --> subgroup >= 2

    while seats_left_to_fill > 0:
        booking_for_subgroup_accomodated = search_and_assign_most_suitable_seats(rows, subgroup_size, passenger_name)

        if booking_for_subgroup_accomodated == True:

            if subgroup_size == 1:
                passengers_separated = passengers_separated + 1

            seats_left_to_fill = seats_left_to_fill - subgroup_size

            if seats_left_to_fill == 0:
                return passengers_separated

            subgroup_size = seats_left_to_fill

        else:
            subgroup_size = subgroup_size - 1

    return passengers_separated


def  split_booking_between_twos_and_threes(booking_size, rows, num_seats_per_row, passenger_name):

    seat_availability_twos = get_seat_availability_twos(rows) # reasoning: every number > 1 can be expressed as a sum of 2s and 3s
    seat_availability_threes = get_seat_availability_threes(rows)

    if seat_availability_threes != 0 or seat_availability_twos != 0:
        booking_size_mod_2 = booking_size % 2
        booking_size_mod_3 = booking_size % 3

        if booking_size_mod_2 == 0:
            num_2_bookings = booking_size / 2

            if seat_availability_twos >= num_2_bookings:
                fill_seats_with_2_and_3_configurations(rows, passenger_name, num_2_bookings, 0)
                return True

        if booking_size_mod_2 == 1:
            num_2_bookings = (booking_size - 3)/2
            num_3_bookings = 1

            if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
                fill_seats_with_2_and_3_configurations(rows, passenger_name, num_2_bookings, num_3_bookings)
                return True

        if booking_size_mod_3 == 0:
            num_2_bookings = 0
            num_3_bookings = booking_size / 3

            if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
                fill_seats_with_2_and_3_configurations(rows, passenger_name, 0, num_3_bookings)
                return True

        if booking_size_mod_3 == 1:
            num_2_bookings = 2
            num_3_bookings = (booking_size - 4)/3

            if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
                fill_seats_with_2_and_3_configurations(rows, passenger_name, num_2_bookings, num_3_bookings)
                return True

        if booking_size_mod_3 == 2:
            num_3_bookings = (booking_size - 2) / 3
            num_2_bookings = 1

            if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
                fill_seats_with_2_and_3_configurations(rows, passenger_name, num_2_bookings, num_3_bookings)
                return True

    return False


def fill_seats_with_2_and_3_configurations(rows,  passenger_name, num_2_bookings, num_3_bookings):

    for i in range(0, num_2_bookings):
        booking_accomodated = search_and_assign_most_suitable_seats(rows, 2, passenger_name)
        if booking_accomodated == False: raise Exception("Booking was not accommodated despite passing sufficienct space checks.")

    for i in range(0, num_3_bookings):
        booking_accomodated = search_and_assign_most_suitable_seats(rows, 3, passenger_name)
        if booking_accomodated == False: raise Exception("Booking was not accommodated despite passing sufficienct space checks.")


def assign_seats_where_booking_size_exceeds_row_size(booking_size, rows, num_seats_per_row, passenger_name):

    # booking could not be placed all together in one row

    remainder_to_seat = split_booking_into_row_size_groups(booking_size, rows, num_seats_per_row, passenger_name)

    if remainder_to_seat == 0:
        return 0

    passengers_separated = split_booking_across_rows(remainder_to_seat, rows, num_seats_per_row, passenger_name)

    return passengers_separated



def  split_booking_into_row_size_groups(booking_size, rows, num_seats_per_row, passenger_name):

    seat_availability_row_size = get_seat_availability_row_size(rows, num_seats_per_row)

    booking_size_mod_row_size = booking_size % num_seats_per_row
    num_full_rows_required = (booking_size - booking_size_mod_row_size)/ num_seats_per_row
    unassigned_seats = booking_size_mod_row_size

    if booking_size_mod_row_size == 1:
        num_full_rows_required = num_full_rows_required - 1
        unassigned_seats = unassigned_seats + num_seats_per_row

    if seat_availability_row_size >= num_full_rows_required:
        for i in range(0, num_full_rows_required):
            booking_accommodated = search_and_assign_most_suitable_seats(rows, num_seats_per_row, passenger_name)
            if booking_accommodated == False: raise Exception("Seats unassigned.")
    else:
        unassigned_seats += num_seats_per_row * (num_full_rows_required - seat_availability_row_size)
        for i in range(0, seat_availability_row_size):
            booking_accommodated = search_and_assign_most_suitable_seats(rows, num_seats_per_row, passenger_name)
            if booking_accommodated == False: raise Exception("Seats unassigned.")

    return unassigned_seats





if __name__ == "__main__":

    passengers_refused = 0
    passengers_separated = 0

    conn = sqlite3.connect("airline_seating.db")
    c = conn.cursor()
    print("Opened database successfully.")

    c.execute("select * from metrics")
    metrics = c.fetchall()

    bookings_list = read_bookings("bookings.csv")
    seating_plan = get_seating_plan()

    num_rows = seating_plan[0][0]
    num_cols = len(list(seating_plan[0][1]))

    all_rows = read_previous_bookings(num_rows, num_cols)

    total_empties = 0

    for row in all_rows:
        total_empties += all_rows[row].SeatsAvailable

    for booking in bookings_list:

        passenger_name = booking[0]
        booking_size = int(booking[1])

        if booking_size > 0:
            seats_available = check_for_space(booking_size, total_empties)

            if seats_available == True:
               passengers_separated_in_booking = assign_seating(booking_size, passenger_name, all_rows, num_cols)
               passengers_separated += passengers_separated_in_booking
               total_empties = total_empties - booking_size
            else:
                passengers_refused += booking_size


    write_passenger_stats_to_db(passengers_refused, passengers_separated)


#print(bookings)

