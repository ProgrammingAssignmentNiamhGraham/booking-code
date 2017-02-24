#Overview

The goal of the code provided is to efficiently & effectively allocate seats to passengers on a flight, conditional on two components:-

  	1)	The seating configuration of the plane
	
  	2)	The size of the booking (i.e., number of seats requested)
  
The seating configuration of the plane is provided through a .db file, whereas bookings are provided through a .csv file. 
On the provision of seat allocation, the following order of priority is maintained:-

  	1)	Seat everyone together in the same row, OR
	
  	2)	Break bookings into pairs &/or threes, if required, OR
	
  	3)	Seat people alone, if necessary, OR
	
  	4)	Refuse booking if not enough seats are available for the whole booking
  
Two metrics are initialised & updated in the database for each booking considered:-

  	•	passengers_refused – not enough free seats available for the booking, so the count of seats requested is added
	
  	•	passengers_separated – not enough free seats to sit the booking alongside one another, so the count of seats requested is added
    
#Assumptions

  	•	The structure (table names, column names, etc.) of any future database this code will be implemented on will be the same as the sample database (“airline_seating.db”) provided.
		
  	•	The format of any future .csv file this code will be implemented on will be the same as the sample file (“bookings.csv”) provided.
		
  	•	All seats – both available and unavailable – will be present in the “seating” table and thus do not have to be inferred from the “rows_cols” table.

#Code Implementation

At a high level, the (Python) code provided here has method(s) relating to the following activities:-

  	•	Initializing a class for Seat and Row, respectively
		
  	•	Importing the relevant bookings from the .csv file in question
		
  	•	Obtaining the plane seating configuration from the .db file in question
		
	•	Importing any existing bookings and establishing a row/seat framework
		
	•	Determining if the booking size is feasible (i.e., too large, given the available seating)
		
	•	Determining if feasible booking sizes can be accommodated within one row of seats
		
	•	Determining the best way to minimise passengers sitting by themselves / away from everyone else within their respective booking (for booking sizes greater than 1) – assignment in pairs and trios is sought, here
		
	•	Feeding relevant information back to the .db file in question
  
Once these are declared, the code performs the following actions sequentially:-

	•	Reads the filenames provided for both the .db file and .csv file (both of which are saved in the directory of 	interest) through the command line, e.g. python seat_assign_1620xxxx_1620yyyy.py "airline_seating.db" "bookings.csv"
		
	•	Opens a connection with the database

	•	Reads in the bookings of interest

	•	Obtains the seating plan 

	•	Populates pre-existing bookings

	•	Assigns seating for new bookings, records in the database

	•	Updates the two passenger metrics in the database

#Testing

The code was first tested by editing the .csv file to give different size bookings, stepping through the code to ensure that all booking sizes were accommodated as expected. Although not hard-coded into the final output, this step was vital in ensuring that all components of the final code were working for the various row sizes &/or seat availabilities one may expect.

Within the code, there is an additional method – named test() – which tests a number of different database structures by first creating a structure and then assigning seating as per normal. In order to run this, the user must comment out run_bookings_assignment() in the main method and introduce test() instead. Further details are contained within the .py file.

