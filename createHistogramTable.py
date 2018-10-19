eol = "\n"
t = "    "
cmd = "CREATE TABLE tick_histograms (" + eol
cmd += t + "epoch INT," + eol
cmd += t + "ticker VARCHAR(10)," + eol
cmd += t + "duration INT,"  + eol
cmd += t + "lowest_edge FLOAT," + eol
cmd += t + "highest_edge FLOAT,"  + eol

for m in range(30):
    cmd += t + "bin%02d INT," % m + eol

cmd = cmd[:-2] # ditch the last comma
cmd += ");"
print(cmd)