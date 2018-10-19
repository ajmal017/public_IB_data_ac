"""This file generates SQL command that creates a stats table """

cmd = "CREATE TABLE tick_stats (epoch INT, ticker VARCHAR(10), "

def make2dig(n):
    """Returns a 2 digit integer"""
    return "%02d" % n

# Create count column:
cmd += "num_prev_1_sec INT, "

# Create moment columns:
for m in range(0,8): # Integer moment component
    for f in range(0, 10): # Fractional moment component
        cmd += " mom_" + str(m) + "_" + str(f) + " FLOAT,"
        if m == 7 and f == 5:
            break

# Create histogram count columns:
for m in range(0, 30):
    cmd += " hist_bin_" + make2dig(m) + " INT,"

# Create histogram edge columns:
for m in range(0, 30):
    cmd += " hist_edge_" + make2dig(m) + " FLOAT,"

cmd = cmd[:-1] # Lop off trailing comma
cmd += ");"

print(cmd)

# """This file generates SQL command that creates a stats table """
#
# interval_periods = ["001","003","010","030","090","270", "810"]
#
# cmd = "CREATE TABLE tick_stats (epoch INT, ticker VARCHAR(10), "
#
# def make3dig(n):
#     """Returns a 3 digit integer"""
#     return "%03d" % n
#
# # Create count columns:
# for i in interval_periods:
#     cmd += "num_prev_" + i + " INT, "
#
# # Create moment columns:
# for i in interval_periods:
#     for m in range(0,7): # Integer moment component
#         for f in range(0, 10): # Fractional moment component
#             cmd += " mom_" + i + "_" + make3dig(m) + "_" + make3dig(f) + " FLOAT,"
#
#
# cmd = cmd[:-1] # Lop off trailing comma
# cmd += ");"
#
# print(cmd)