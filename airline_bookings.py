
import sqlite3
import csv

global conn
global c

# Plane structure classes
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
    # reads bookings from a csv file

    bookings = []
    with open(bookings_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            bookings.append(row)
    return bookings

def get_seating_plan():
    # reads plane structure from the rows_cols table in the db

    c.execute("select * from rows_cols")
    seating_plan = c.fetchall()
    return seating_plan

def read_previous_bookings(num_rows, num_seats_in_row):
    # reads the seating and current bookings from the seating table in the db
    # sorts it into rows and seats structure
    # returns a dictionary of rows

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

        # if seat has an empty name section, then the seat is unassigned
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
    # assigns customer to seats within a row

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
    # updates seating table in database with the relevant customer name to the seat they have been assigned to

    sql_text = "update seating set name = '" + seat.Name + "' where row = " + str(row.RowNumber) + " and seat = '" +seat.SeatLetter + "'"
    c.execute(sql_text)
    conn.commit()


def write_passenger_stats_to_db(passengers_refused, passengers_separated):
    # writes passenger stats to the metrics table at the end of the process

    sql_text = "update metrics set passengers_refused =" + str(passengers_refused) + ", passengers_separated = " + str(passengers_separated)
    c.execute(sql_text)
    conn.commit()




def check_for_space(booking_size, total_empties):
    # checks that there are enough seats on the plane to accommodate the full booking size

    if booking_size <= total_empties:
        return True

    return False


def assign_seating(booking_size, passenger_name, rows, num_seats_per_row):
    # checks if booking will fit in one row
    # assigns customer booking to seats

    if booking_size <= num_seats_per_row:
        # booking is small enough that it should fit in one row
        passengers_separated = assign_seats_where_booking_size_less_than_or_equal_to_row_size(booking_size, rows, num_seats_per_row, passenger_name)
        return passengers_separated
    else:
        # booking exceeds row size and must be split across several rows
        assign_seats_where_booking_size_exceeds_row_size(booking_size, rows, num_seats_per_row, passenger_name)
        return booking_size


def search_and_assign_most_suitable_seats(rows, booking_size, passenger_name):
    # searches for the most suitable row to allocate customer seats
    # allocates seats accordingly

    # searching for a row with the exact amount of seats to accommodate booking
    for row in rows:
        if rows[row].SeatsAvailable == booking_size:
            assign_customer_to_row(passenger_name,  rows[row], booking_size)
            return True

    # searching for a row with the number of seats + 2 to leave space for a pair to also be accomodated
    for row in rows:
        if  rows[row].SeatsAvailable >= booking_size + 2:
            assign_customer_to_row(passenger_name,  rows[row], booking_size)
            return True

    # searching for any other row which can accommodate the booking
    for row in rows:
        if  rows[row].SeatsAvailable > booking_size:
            assign_customer_to_row(passenger_name,  rows[row], booking_size)
            return True

    # if no row has available seating to accommodate the full booking
    return False


def assign_seats_where_booking_size_less_than_or_equal_to_row_size(booking_size, rows, num_seats_per_row, passenger_name):
    # booking is small enough in theory to be accommodated in one row
    # returns the number of passengers that could not be seated together
    # i.e. returns 0 if the booking was accommodated together, and returns the booking_size if it wasn't possible and they had to be split up

    # attempts to assign the booking in one row (as is theoretically possible)
    booking_accomodated_altogether = search_and_assign_most_suitable_seats(rows, booking_size, passenger_name)

    if booking_accomodated_altogether == True:
        # booking has been placed together in one row
        # all passengers seated together
        return 0

    # booking could not be placed all together in one row and must be split
    split_booking_across_rows(booking_size, rows, num_seats_per_row, passenger_name)

    # booking has been split up
    return booking_size


def get_seat_availability_twos(rows):
    # returns the total number of rows that has exactly two seats available

    seat_availability_twos = 0

    for i in rows:
        if rows[i].SeatsAvailable == 2:
            seat_availability_twos += 1

    return seat_availability_twos

def get_seat_availability_threes(rows):
    # returns the total number of rows that has three or more seats available, but is not an empty row

    seat_availability_threes = 0

    for i in rows:
        if rows[i].SeatsAvailable >= 3:
            seat_availability_threes += 1

    return seat_availability_threes

def get_total_empty_rows(rows, num_seats_in_row):
    # returns the total number of completely empty rows available

    empty_rows_available = 0

    for i in rows:
        if rows[i].SeatsAvailable == num_seats_in_row:
            empty_rows_available +=1

    return empty_rows_available



def split_booking_across_rows(booking_size, rows, num_seats_per_row, passenger_name):
    # every number > 1 can be split into twos and threes
    # attempts to accommodate booking in twos and threes so that no member of the party is on their own
    # if this fails, it attempts to accommodate the booking wherever there is empty space

    booking_successful = split_booking_between_twos_and_threes(booking_size, rows, passenger_name)

    if booking_successful:
        return

    seats_left_to_fill = booking_size
    subgroup_size = max(booking_size -2, 2)
    # splits group in half and tries to accommodate from here
    # booking_size = 2 --> subgroup = 2; booking_size == 3 --> subgroup = 2; booking_size > = 4 --> subgroup >= 2

    while seats_left_to_fill > 0:
        booking_for_subgroup_accomodated = search_and_assign_most_suitable_seats(rows, subgroup_size, passenger_name)

        if booking_for_subgroup_accomodated == True:

            seats_left_to_fill = seats_left_to_fill - subgroup_size

            if seats_left_to_fill == 0:
                return

            subgroup_size = seats_left_to_fill

        else:
            # subgroup cannot be accommodated together - so subtracts 1 and tries again
            subgroup_size = subgroup_size - 1


def  split_booking_between_twos_and_threes(booking_size, rows, passenger_name):
    # reasoning: every number > 1 can be expressed as a sum of 2s and 3s
    # checks for seat availability of twos and threes
    # attempts to assign the booking across rows in groups of twos or threes as availability permits

    seat_availability_twos = get_seat_availability_twos(rows)
    seat_availability_threes = get_seat_availability_threes(rows)

    if seat_availability_threes == 0 or seat_availability_twos == 0:
        # there are no seats available beside each other on the plane
        return False

    booking_size_mod_2 = booking_size % 2
    booking_size_mod_3 = booking_size % 3

    if booking_size_mod_2 == 0:
        # booking can be split evenly into groups of two
        num_2_bookings = booking_size / 2

        if seat_availability_twos >= num_2_bookings:
            fill_seats_with_2_and_3_configurations(rows, passenger_name, num_2_bookings, 0)
            return True

    if booking_size_mod_2 == 1:
        # booking can be split evenly into one group of three and a number of groups of two
        num_2_bookings = (booking_size - 3)/2
        num_3_bookings = 1

        if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
            fill_seats_with_2_and_3_configurations(rows, passenger_name, num_2_bookings, num_3_bookings)
            return True

    if booking_size_mod_3 == 0:
        # booking can be split evenly into groups of three
        num_2_bookings = 0
        num_3_bookings = booking_size / 3

        if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
            fill_seats_with_2_and_3_configurations(rows, passenger_name, 0, num_3_bookings)
            return True

    if booking_size_mod_3 == 1:
        # booking can be split evenly into two groups of two and a number of groups of three
        num_2_bookings = 2
        num_3_bookings = (booking_size - 4)/3

        if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
            fill_seats_with_2_and_3_configurations(rows, passenger_name, num_2_bookings, num_3_bookings)
            return True

    if booking_size_mod_3 == 2:
        # booking can be split evenly into one group of two and a number of groups of three
        num_3_bookings = (booking_size - 2) / 3
        num_2_bookings = 1

        if seat_availability_threes >= num_3_bookings and seat_availability_twos >= num_2_bookings:
            fill_seats_with_2_and_3_configurations(rows, passenger_name, num_2_bookings, num_3_bookings)
            return True

    # booking cannot be accommodated as above
    return False


def fill_seats_with_2_and_3_configurations(rows,  passenger_name, num_2_bookings, num_3_bookings):
    # our booking can be split into a number of bookings of 2 and a number of bookings of 3
    # the number of groups of 2 and gropus of 3 are passed in
    # the relevant number of seats are assigned to each group of 2 and group of 3

    for i in range(0, num_2_bookings):
        booking_accomodated = search_and_assign_most_suitable_seats(rows, 2, passenger_name)
        if booking_accomodated == False: raise Exception("Booking was not accommodated despite passing sufficienct space checks.")

    for i in range(0, num_3_bookings):
        booking_accomodated = search_and_assign_most_suitable_seats(rows, 3, passenger_name)
        if booking_accomodated == False: raise Exception("Booking was not accommodated despite passing sufficienct space checks.")


def assign_seats_where_booking_size_exceeds_row_size(booking_size, rows, num_seats_per_row, passenger_name):
    # booking size is greater than the row size

    # splits booking into row size groups and returns
    remainder_to_seat = split_booking_into_row_size_groups(booking_size, rows, num_seats_per_row, passenger_name)

    if remainder_to_seat == 0:
        # all passengers have been seated; no more to do
        return

    # attempts to split the excess of passengers into smaller groups and seat accordingly
    split_booking_across_rows(remainder_to_seat, rows, num_seats_per_row, passenger_name)



def  split_booking_into_row_size_groups(booking_size, rows, num_seats_per_row, passenger_name):
    # checks how many full rows the booking size could fill, and what the excess is
    # fills as many rows as possible out of the booking size
    # if the excess is 1, it assigns one less full size row (to avoid one person being seated on their own)

    seat_availability_row_size = get_total_empty_rows(rows, num_seats_per_row)

    booking_size_mod_row_size = booking_size % num_seats_per_row
    num_full_rows_required = (booking_size - booking_size_mod_row_size)/ num_seats_per_row
    unassigned_seats = booking_size_mod_row_size

    if booking_size_mod_row_size == 1:
        # excess is 1; try to avoid one passenger being seated on their own
        num_full_rows_required = num_full_rows_required - 1
        unassigned_seats = unassigned_seats + num_seats_per_row

    if seat_availability_row_size >= num_full_rows_required:
        # the total number of rows required are available; passengers seated accordingly
        for i in range(0, num_full_rows_required):
            booking_accommodated = search_and_assign_most_suitable_seats(rows, num_seats_per_row, passenger_name)
            if booking_accommodated == False: raise Exception("Seats unassigned.")
    else:
        # less than the total number of rows required are available; passengers seated in as many rows as possible and the remainder returned
        unassigned_seats += num_seats_per_row * (num_full_rows_required - seat_availability_row_size)
        for i in range(0, seat_availability_row_size):
            booking_accommodated = search_and_assign_most_suitable_seats(rows, num_seats_per_row, passenger_name)
            if booking_accommodated == False: raise Exception("Seats unassigned.")

    # returns the excess of passengers who were not seated in a full row
    return unassigned_seats





if __name__ == "__main__":

    data_file_path = str(sys.argv[1]) # "airline_seating.db"
    bookings_file_path = str(sys.argv[2]) # "bookings.csv"

    # initialise metrics
    passengers_refused = 0
    passengers_separated = 0

    # open database connection
    conn = sqlite3.connect(data_file_path)
    c = conn.cursor()
    print("Opened database successfully.")

    # get bookings and seating plan
    bookings_list = read_bookings(bookings_file_path)
    seating_plan = get_seating_plan()

    # plane structure
    num_rows = seating_plan[0][0]
    num_cols = len(list(seating_plan[0][1]))

    # get all seating and current bookings
    all_rows = read_previous_bookings(num_rows, num_cols)

    total_empties = 0

    # finding total empty seats on aircraft
    for row in all_rows:
        total_empties += all_rows[row].SeatsAvailable

    # loops through bookings and attempts to assign them accordingly
    for booking in bookings_list:

        passenger_name = booking[0]
        booking_size = int(booking[1])

        if booking_size > 0: # probably unnecessary; more of an error check

            # checks to see if there is availabilty for the booking
            seats_available = check_for_space(booking_size, total_empties)

            if seats_available == True:
                passengers_separated_in_booking = assign_seating(booking_size, passenger_name, all_rows, num_cols)
                passengers_separated += passengers_separated_in_booking
                total_empties = total_empties - booking_size
            else:
                passengers_refused += booking_size

    # writes metrics to database
    write_passenger_stats_to_db(passengers_refused, passengers_separated)

    print("Bookings complete.")


#project name = seat_assign_16202504 16201265.py
