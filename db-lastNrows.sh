dbloc=$(<./dbloc.cfg)
numrecs=${1:-20}
sqlite3 ${dbloc} "select * from rawdata order by metricdt desc limit ${numrecs};"

