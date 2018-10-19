"""Tools for generating dummy data and sending it to PostgreSQL."""

from easyPostgresConnection import connect2IbData

def generateDummyData(whichTable = "bars_5_sec"):
    conn = connect2IbData()
    curs = conn.cursor()
    for m in range(10, 50):
        cmd = "INSERT INTO " + whichTable
        cmd += " (epoch, ticker, open, close, high, low) VALUES ("
        cmd += str(100000 + m*5) + DELIM
        cmd += "'__XYZ'" + DELIM
        cmd += str(m) + DELIM
        cmd += str(m) + DELIM
        cmd += str(m+1) + DELIM
        cmd += str(m-1) + ")"
        cmd += END_QUERY
        curs.execute(cmd)
        conn.commit()

if __name__=="__main__":
    pass
#    generateDummyData()
