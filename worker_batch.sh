#bin/bash

BATCH=$1

echo "Start batch # $BATCH"
PORT1=$((5560+BATCH*3))
PORT2=$((5560+BATCH*3+1))
PORT3=$((5560+BATCH*3+2))

WORKER1=$((BATCH*3))
WORKER2=$((BATCH*3+1))
WORKER3=$((BATCH*3+2))

python scheduler.py $BATCH &
xterm -hold -e python worker_node.py $WORKER1 $PORT1 $BATCH &
xterm -hold -e python worker_node.py $WORKER2 $PORT2 $BATCH &
xterm -hold -e python worker_node.py $WORKER3 $PORT3 $BATCH &

# trap "echo exiting" 2
# killall xterm