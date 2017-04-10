NACA="0005 0008 0009 0010 0015 0020"
# Re="50 100 150 200 250 300 350 400 450 500 550 600 650 700 750 800 850 900 950 1000"
Re="950 1000"

for r in $Re
do
    for n in $NACA
    do
        ./genpolar.sh $n $r
    done
done
