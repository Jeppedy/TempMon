dbloc=$(<./dbloc.cfg)
if [ $# -lt 1 ]; then
	echo "Supply a node name..."
else
	numrecs=${2:-20}
	sqlite3 ${dbloc} "select * from rawdata where nodeid='${1}' order by metricdt desc limit $numrecs;"
fi

